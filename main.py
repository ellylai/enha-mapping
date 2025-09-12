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


def create_mock_data():
    """Creates a mock dataset with multiple diagnosis columns."""
    N_CLAIMS = 25000
    START_DATE = "2014-01-01"
    END_DATE = "2020-12-31"
    TRANSITION_DATE = "2015-10-01"

    pre_transition_codes = {"425.4": 0.4, "440.9": 0.4, "A01": 0.2}
    post_transition_codes = {"I42.9": 0.45, "I70.9": 0.35, "B02": 0.2}

    dates = pd.to_datetime(pd.date_range(start=START_DATE, end=END_DATE, freq="D"))
    transition_date_dt = pd.to_datetime(TRANSITION_DATE)

    pre_dates = dates[dates < transition_date_dt]
    post_dates = dates[dates >= transition_date_dt]

    n_pre = int(N_CLAIMS * (len(pre_dates) / len(dates)))
    n_post = N_CLAIMS - n_pre

    pre_claims_dates = np.random.choice(pre_dates, size=n_pre, replace=True)
    pre_claims_codes = np.random.choice(
        list(pre_transition_codes.keys()),
        size=n_pre,
        replace=True,
        p=list(pre_transition_codes.values()),
    )
    post_claims_dates = np.random.choice(post_dates, size=n_post, replace=True)
    post_claims_codes = np.random.choice(
        list(post_transition_codes.keys()),
        size=n_post,
        replace=True,
        p=list(post_transition_codes.values()),
    )

    # Create a single column first
    single_diag_df = pd.DataFrame(
        {
            "date": np.concatenate([pre_claims_dates, post_claims_dates]),
            "diag_1": np.concatenate([pre_claims_codes, post_claims_codes]),
        }
    )

    # Distribute into three diagnosis columns, adding some NaNs
    claims_df = single_diag_df.copy()
    claims_df["diag_2"] = claims_df["diag_1"].where(
        np.random.rand(len(claims_df)) < 0.3, np.nan
    )
    claims_df["diag_3"] = claims_df["diag_1"].where(
        np.random.rand(len(claims_df)) < 0.1, np.nan
    )
    claims_df["diag_1"] = claims_df["diag_1"].where(
        np.random.rand(len(claims_df)) < 0.8, np.nan
    )

    return claims_df.sample(frac=1).reset_index(drop=True)


def run_pipeline():
    """
    Executes the full agentic pipeline.
    """
    # --- User Input & Config ---
    print("=== ICD Code Mapping Pipeline ===")
    print("Enter a description of the medical conditions you want to analyze:")
    print("Example: 'I want to find all claims related to cardiomyopathy and atherosclerosis.'")
    print()
    
    USER_INPUT_DESC = input("Your description: ").strip()
    
    if not USER_INPUT_DESC:
        print("No input provided, using default example...")
        USER_INPUT_DESC = "I want to find all claims related to cardiomyopathy and atherosclerosis."
    
    print(f"\nAnalyzing: '{USER_INPUT_DESC}'")
    config = get_input(USER_INPUT_DESC)

    # --- Load and Prepare Data ---
    print("Loading and preparing mock claims data...")
    claims_df = create_mock_data()
    claims_df = clean_data(claims_df, config["target_colnames"])
    print(f"Loaded {len(claims_df)} mock claims.")

    # --- Phase 1: Interpret Concept ---
    print("\n--- Phase 1: Interpreting Concept ---")
    keywords = get_concept(USER_INPUT_DESC)
    print(f"Generated Keywords: {keywords}")

    # --- Phase 2: Generate Naive Code List ---
    print("\n--- Phase 2: Generating Naive Code List ---")
    naive_codes = generate_relevant_codes(keywords)
    print(
        f"Found {len(naive_codes['icd9'])} naive ICD-9 codes and {len(naive_codes['icd10'])} naive ICD-10 codes."
    )

    # --- Phase 3: Generate Hypotheses ---
    print("\n--- Phase 3: Generating Hypotheses ---")
    hypotheses = generate_hypotheses(naive_codes)
    print(f"Generated {len(hypotheses)} hypotheses to test.")

    # --- Phase 4: Evaluate Hypotheses ---
    print("\n--- Phase 4: Evaluating Hypotheses ---")
    results = []
    for h in hypotheses:
        print(f"Testing hypothesis: '{h['name']}'...")

        # Corrected Logic: Flag, then create time series, then score
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

        # Dynamically find the rolling sum column name created by `create_timeseries`
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
        print(f"  Smoothness Score (1.0 - p_value): {score:.4f}")

    # --- Phase 5: Select and Output Best Result ---
    print("\n--- Phase 5: Selecting Best Result ---")
    # A lower score is better (p-value closer to 1.0)
    best_result = min(results, key=lambda x: x["score"])
    best_hypothesis = best_result["hypothesis"]

    print(
        f"\nBest hypothesis found: '{best_hypothesis['name']}' with a score of {best_result['score']:.4f}"
    )
    print(f"\nICD-9 Codes ({len(best_hypothesis['icd9_codes'])}):")
    print(sorted(list(best_hypothesis["icd9_codes"])))
    print(f"\nICD-10 Codes ({len(best_hypothesis['icd10_codes'])}):")
    print(sorted(list(best_hypothesis["icd10_codes"])))

    # Plot the best time series
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))

    ts_to_plot = best_result["timeseries"]

    plot_ts(
        ts_to_plot, date_col=config["date_colname"], target_rolling_col=rolling_col_name
    )


if __name__ == "__main__":
    run_pipeline()
