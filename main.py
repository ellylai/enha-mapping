# python main.py

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import functions from our phases
from interpreter.concept_nlp import get_concept
from icd_generator.icd_naive_generator import generate_relevant_codes
from mapping_refinement.hypothesis_generator import generate_hypotheses
from time_series_evaluator.create_time_series import (
    create_timeseries_function,
    flag_dataframe,
    clean_data,
    get_input,
)
from time_series_evaluator.smoothness_evaluator import calculate_smoothness_score
from ts_results.plot_timeseries import plot_ts


def run_pipeline(user_desc):
    """Run the ICD code mapping pipeline"""
    print(f"Analyzing: '{user_desc}'")
    config = get_input(user_desc)

    # Load and prepare data
    print("Loading synthetic claims data...")
    claims_df = pd.read_csv(config["data_filepath"])
    claims_df = clean_data(claims_df, config["target_colnames"])

    # Phase 1: Extract medical concepts
    print("Phase 1: Extracting medical concepts...")
    extracted_concepts = get_concept(user_desc)
    print(f"Extracted concepts: {extracted_concepts}")

    # Phase 2: Generate ICD codes
    print("Phase 2: Generating ICD codes...")
    codes = generate_relevant_codes(extracted_concepts)
    total_codes = len(codes["icd9"]) + len(codes["icd10"])
    print(f"Found {total_codes} ICD codes")

    # Phase 3: Generate hypotheses
    print("Phase 3: Generating hypotheses...")
    hypotheses = generate_hypotheses(codes)
    print(f"Generated {len(hypotheses)} hypotheses to test.")

    # Phase 4: Evaluate hypotheses
    print("Phase 4: Evaluating hypotheses...")
    results = []
    for h in hypotheses:
        print(f"Testing hypothesis: '{h['name']}'...")

        # Flag, then create time series, then score
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

        # Dynamically find the rolling sum column name created by create_timeseries
        rolling_col_name = [
            col
            for col in ts.columns
            if col.startswith(f"{target_flag_col.split('_')[0]}_count")
        ][0]

        score = calculate_smoothness_score(ts, config["date_colname"], rolling_col_name)

        results.append(
            {
                "hypothesis": h,
                "score": score,
                "timeseries": ts,
                "rolling_col": rolling_col_name,
            }
        )
        print(f"  Smoothness Score: {score:.4f}")

    # Phase 5: Select best result
    print("Phase 5: Selecting best result...")
    best_result = min(results, key=lambda x: x["score"])
    best_hypothesis = best_result["hypothesis"]

    print(
        f"Best hypothesis: '{best_hypothesis['name']}' with score {best_result['score']:.4f}"
    )

    ts_to_plot = best_result["timeseries"]
    rolling_col_name = best_result["rolling_col"]

    plot_ts(
        ts_to_plot, date_col=config["date_colname"], target_rolling_col=rolling_col_name
    )

    return best_result["timeseries"], best_result["score"]


if __name__ == "__main__":
    print("ICD Code Mapping Pipeline")
    print(
        "Example: 'I want to find all codes related to cardiomyopathy and atherosclerosis.'"
    )
    print()

    USER_INPUT_DESC = input("Your description: ").strip()

    if not USER_INPUT_DESC:
        print("No input provided, using default example...")
        USER_INPUT_DESC = (
            "I want to find all codes related to cardiomyopathy and atherosclerosis."
        )

    run_pipeline(USER_INPUT_DESC)
