# python main.py

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import functions from our phases
from interpreter.prompt_handler import get_concept
from hypothesis_refinement.hypothesis_generator import generate_hypotheses
from time_series_evaluator.create_time_series import (
    create_timeseries_function,
    flag_dataframe,
    clean_data,
    get_input,
)
from time_series_evaluator.smoothness_evaluator import calculate_smoothness_score
from ts_results.plot_timeseries import plot_ts

# Neethi: This contains new code to detect the breaks in our timeseries.
from break_detection.break_detector import break_detector


def run_pipeline(user_desc):
    """Run the ICD code mapping pipeline"""
    print(f"Analyzing: '{user_desc}'")
    config = get_input(user_desc)

    # Load and prepare data
    print("Loading synthetic claims data...")
    claims_df = pd.read_csv(config["data_filepath"])
    claims_df = clean_data(claims_df, config["target_colnames"])

    # Phase 1/2: Extract medical concepts AND ICD codes
    print("Phase 1: Extracting medical concepts and ICD codes...")
    concept_result = get_concept(user_desc)
    codes = {"icd9": concept_result["icd9"], "icd10": concept_result["icd10"]}
    
    print(f"Found {len(codes['icd9'])} ICD-9 codes and {len(codes['icd10'])} ICD-10 codes")

    # Phase 2.5: Baseline break analysis for hypothesis generation
    baseline_break_analysis = break_detector.detect_breaks(
        claims_df,
        value_col=None,            # auto-pick count/rolling col if available
        hypothesis_name="baseline",
        plot_results=False
    )

    artificial_break = baseline_break_analysis["break_dates"][0] if baseline_break_analysis["break_dates"] else None
    artificial_slope = baseline_break_analysis["segments"][0]["slope"] if baseline_break_analysis["segments"] else None

    # Phase 3: Generate hypotheses
    print("Phase 3: Generating hypotheses...")
    hypotheses = generate_hypotheses(codes, artificial_break, artificial_slope)
    print(f"Generated {len(hypotheses)} hypotheses to test.")

    # Phase 4: Evaluate hypotheses with break detection
    print("Phase 4: Evaluating hypotheses with break detection...")
    results = []
    for h in hypotheses:
        print(f"Testing hypothesis: '{h['name']}'...")

        # Flag, then create time series
        target_flag_col = f"flag_{h['name'].replace(' ', '_')}"
        all_codes = list(h["icd9_codes"]) + list(h["icd10_codes"])

        flagged_df = flag_dataframe(
            claims_df.copy(), all_codes, config["target_colnames"], target_flag_col
        )

        ts = create_timeseries_function(
            flagged_df,
            config["date_colname"],
            target_flag_col,
            cap_year=config["cap_year"],
        )

        # Find the rolling sum column
        rolling_col_name = [
            col for col in ts.columns 
            if col.startswith(f"{target_flag_col.split('_')[0]}_count")
        ][0]

        # Calculate smoothness score
        smoothness_score = calculate_smoothness_score(ts, config["date_colname"], rolling_col_name)
        
        # NEW: Perform break detection analysis
        break_analysis = break_detector.detect_breaks(
            ts, 
            value_col=rolling_col_name, 
            hypothesis_name=h['name'],
            plot_results=False  # Can set to True for debugging
        )
        
        # Combine scores (you can adjust weights)
        combined_score = smoothness_score + break_analysis['break_score'] * 0.5

        results.append({
            "hypothesis": h,
            "smoothness_score": smoothness_score,
            "break_score": break_analysis['break_score'],
            "combined_score": combined_score,
            "timeseries": ts,
            "rolling_col": rolling_col_name,
            "break_analysis": break_analysis
        })
        
        print(f"  Smoothness: {smoothness_score:.4f}, Break: {break_analysis['break_score']:.4f}, Combined: {combined_score:.4f}")

    # Phase 5: Select best result considering breaks
    print("Phase 5: Selecting best result considering break analysis...")
    best_result = min(results, key=lambda x: x["combined_score"])
    best_hypothesis = best_result["hypothesis"]

    print(f"Best hypothesis: '{best_hypothesis['name']}'")
    print(f"  Smoothness: {best_result['smoothness_score']:.4f}")
    print(f"  Break score: {best_result['break_score']:.4f}")
    print(f"  Combined: {best_result['combined_score']:.4f}")

    # Show detailed break analysis for the best result
    print("\n📊 Detailed break analysis for best hypothesis:")
    break_detector.detect_breaks(
        best_result["timeseries"], 
        value_col=best_result["rolling_col"], 
        hypothesis_name=best_hypothesis['name'],
        plot_results=True
    )

    # Phase 6: Refinement feedback (could feed back to LLM)
    _provide_refinement_feedback(best_result)

    return best_result


def _provide_refinement_feedback(best_result):
    """Provide feedback for hypothesis refinement based on break analysis"""
    break_analysis = best_result["break_analysis"]
    
    if break_analysis['total_breaks'] > 0:
        print("\n💡 REFINEMENT SUGGESTIONS:")
        print("The time series shows structural breaks that may indicate:")
        
        for i, (break_date, alignment) in enumerate(zip(break_analysis['break_dates'], 
                                                      break_analysis['icd_transition_alignment'])):
            if alignment > 0.7:
                print(f"  - Break near ICD transition ({break_date.date()}): Consider ICD-9/ICD-10 mapping issues")
            else:
                print(f"  - Break at {break_date.date()}: Check code specificity or clinical relevance")
    
    if break_analysis['break_score'] > 0.1:
        print("  - High break score: Hypothesis may need better code selection")


if __name__ == "__main__":
    print("ICD Code Mapping Pipeline")
    print(
        "Example: 'I want to find all claims related to cardiomyopathy and atherosclerosis.'"
    )
    print()

    USER_INPUT_DESC = input("Your description: ").strip()

    if not USER_INPUT_DESC:
        print("No input provided, using default example...")
        USER_INPUT_DESC = (
            "I want to find all claims related to cardiomyopathy and atherosclerosis."
        )

    run_pipeline(USER_INPUT_DESC)

