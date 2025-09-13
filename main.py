# python main.py
import pandas as pd

# Import functions from our phases
from mapping.interpreter.prompt_handler import get_concept
from mapping.hypothesis_refinement.hypothesis_generator import generate_hypotheses
from mapping.time_series_evaluator.create_time_series import (
    create_timeseries_function,
    flag_dataframe,
    clean_data,
    get_input,
)
from mapping.ts_results.plot_timeseries import plot_ts
from mapping.break_detection.break_detector import break_detector

def evaluate_hypothesis(claims_df, hypothesis, config, break_threshold = 500.00):
    """
    Consolidated function to evaluate a single hypothesis.
    It creates a time series and runs break detection.
    """

    target_flag_col = f"flag_{hypothesis['name'].replace(' ', '_')}"
    all_codes = list(hypothesis["icd9_codes"]) + list(hypothesis["icd10_codes"])

    flagged_df = flag_dataframe(
        claims_df.copy(), all_codes, config["target_colnames"], target_flag_col
    )

    ts = create_timeseries_function(
        flagged_df,
        config["date_colname"],
        target_flag_col,
        cap_year=config["cap_year"],
    )

    # Find the rolling sum column name
    rolling_col_name = [
        col
        for col in ts.columns
        if col.startswith(f"{target_flag_col.split('_')[0]}_count")
    ][0]

    # Perform break detection analysis
    break_analysis = break_detector.detect_breaks(
        ts,
        value_col=rolling_col_name,
        hypothesis_name=f"{hypothesis['name']}",
        plot_results=True,
    )

    score = 0
    if break_analysis.get("local_chow"):
        f_stats = [bp.get("F", 0) for bp in break_analysis["local_chow"]]
        if f_stats:
            score = max(f_stats) # Score is the F-statistic of the worst break
    
    artificial_slope = (
            break_analysis["segments"][1]["slope"] if break_analysis["segments"] else None
        )
    if artificial_slope > 0:
        comment = "The slope of the break area is artificially and significantly positive. There are either extra ICD10 codes or too few ICD9 codes in this set."
    else:
        comment = "The slope of the break area is artificially and significantly negative. There are either extra ICD9 codes or too few ICD10 codes in this set."
    
    return {
        "hypothesis": hypothesis,
        "score": score,  # Use the new, more meaningful score
        "timeseries": ts,
        "rolling_col": rolling_col_name,
        "artificial_break": score > break_threshold,
        "artificial_slope": artificial_slope,
        "comment": comment,
        "break_analysis": break_analysis,
    }


def run_pipeline(user_desc, max_iterations=3, break_threshold = 500.00):
    """Run the ICD code mapping pipeline"""
    # PARSE INPUT AND LOAD SYNTHETIC TEST DATA
    print(f"Analyzing: '{user_desc}'")
    config = get_input(user_desc)
    print("Loading synthetic claims data...")
    claims_df = pd.read_csv(config["data_filepath"])
    claims_df = clean_data(claims_df, config["target_colnames"])

    history = []

    # 1. FIRST PASS: EXTRACT ICD CODES
    print(
        "PHASE 1: Extracting medical concepts and ICD codes with function 'generate_hypotheses'..."
    )
    current_hypothesis = generate_hypotheses(
        history,
        prev_results=None,
        user_input_desc=config["target_category"],
    )
    current_hypothesis["name"] += " 0"

    # --- 2. EVALUATION & REFINEMENT LOOP ---
    print("PHASE 2: EVALUATION & REFINEMENT LOOP")
    for i in range(max_iterations):
        print(f"\n--- Iteration {i+1}/{max_iterations} ---")

        # a. Evaluate the current hypothesis
        print(
        f"      Hypothesis{i}: Found {len(current_hypothesis['icd9_codes'])} ICD-9 codes and {len(current_hypothesis['icd10_codes'])} ICD-10 codes"
        )
        result = evaluate_hypothesis(claims_df, current_hypothesis, config, break_threshold)
        history.append(result)
        print(f"  Break Score: {result['score']:.4f}")

        # b. Check for exit condition (if score is good enough)
        print(f"  Worst Break (F-statistic): {result['score']:.4f}")
        # A low F-statistic (e.g., < 4) is statistically insignificant.
        if result["score"] < break_threshold:
            print(
                "YAY!! Breaks are no longer statistically significant. Concluding refinement."
            )
            break

        # c. Use the result to generate the next hypothesis
        if i < max_iterations - 1:  # Don't generate a new one on the last loop
            print("   LOOP: Refining hypothesis based on break analysis...")

            current_hypothesis = generate_hypotheses(
                history=history,
                prev_results = result,
                user_input_desc=config["target_category"],
            )
            current_hypothesis["name"] += f" {i+1}"

    # --- 3. FINAL SELECTION ---
    print("\n--- Phase 3: Selecting Best Result ---")
    best_result = min(history, key=lambda x: x["score"])
    best_hypothesis = best_result["hypothesis"]

    print(
        f"\nBest hypothesis found: '{best_hypothesis['name']}' with a final score of {best_result['score']:.4f}"
    )
    print("\n📊 Plotting detailed break analysis for the best result...")
    break_detector.detect_breaks(
        best_result["timeseries"],
        value_col=best_result["rolling_col"],
        hypothesis_name=best_hypothesis["name"],
        plot_results=True,
    )

    print("\n--- Final Code Sets ---")
    print(
        f"ICD-9 Codes ({len(best_hypothesis['icd9_codes'])}): {sorted(list(best_hypothesis['icd9_codes']))}"
    )
    print(
        f"ICD-10 Codes ({len(best_hypothesis['icd10_codes'])}): {sorted(list(best_hypothesis['icd10_codes']))}"
    )

    return best_result


def _provide_refinement_feedback(best_result):
    """Provide feedback for hypothesis refinement based on break analysis"""
    break_analysis = best_result["break_analysis"]

    if break_analysis["total_breaks"] > 0:
        print("\n💡 REFINEMENT SUGGESTIONS:")
        print("The time series shows structural breaks that may indicate:")

        for i, (break_date, alignment) in enumerate(
            zip(
                break_analysis["break_dates"],
                break_analysis["icd_transition_alignment"],
            )
        ):
            if alignment > 0.7:
                print(
                    f"  - Break near ICD transition ({break_date.date()}): Consider ICD-9/ICD-10 mapping issues"
                )
            else:
                print(
                    f"  - Break at {break_date.date()}: Check code specificity or clinical relevance"
                )

    if break_analysis["break_score"] > 0.1:
        print("  - High break score: Hypothesis may need better code selection")


if __name__ == "__main__":
    print("ICD Code Mapping Pipeline:\n")
    USER_INPUT_DESC = input(
        "Enter your target category (e.g., 'cocaine abuse'): "
    ).strip()

    if not USER_INPUT_DESC:
        print("No input provided, using default example 'cocaine abuse'...")
        USER_INPUT_DESC = "cocaine abuse"

    run_pipeline(USER_INPUT_DESC)
