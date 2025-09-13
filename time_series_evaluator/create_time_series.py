import pandas as pd
import numpy as np


def get_input(user_input: str) -> dict:
    """
    Parses user input to get parameters for the analysis.
    MOCK FUNCTION: NEEDS TO GET UI
    """
    print(f"Parsing mock user input from: '{user_input}'")
    result_dict = {
        "target_category": user_input,
        "date_colname": "date",
        "target_colnames": ["diag_p"]
        + [f"odiag{n}" for n in range(1, 11)],  # columns from synthetic dataset
        "cap_year": None,
        "data_filepath": "synthetic_claims.csv",
    }
    return result_dict


def clean_data(df: pd.DataFrame, target_colnames: list[str]) -> pd.DataFrame:
    """
    Cleans the target ICD code columns by ensuring they are strings and stripped of whitespace and periods.
    """
    print("Cleaning target columns...")
    for col in target_colnames:
        if col in df.columns:
            # Convert to string, strip whitespace, and replace 'nan' strings with actual NaN
            df[col] = (
                df[col].astype(str).str.strip().str.strip(".").replace("nan", np.nan)
            )
    return df


def flag_dataframe(
    df: pd.DataFrame,
    codes: list[str],
    target_colnames: list[str],
    target_category_colname: str,
):
    """
    Takes in a dataframe (df) and adds a flagged column (target_category_colname)
    for the user's target 'category'
    """
    # Flag the category columns
    df[target_category_colname] = (
        (df[target_colnames].isin(codes)).any(axis=1).fillna(False)
    )
    flagged_count = df[target_category_colname].sum()
    print(
        f"    Flagged {flagged_count} claims out of {len(df[target_category_colname])}."
    )
    return df


def create_timeseries_function(
    df_original: pd.DataFrame,
    date_col: str,
    target_col: str,
    cap_year: int = 2020,
):
    # THIS CODE WORKS ALREADY --- DON'T CHANGE
    df_original[date_col] = pd.to_datetime(df_original[date_col])
    df = df_original.sort_values(by=[date_col]).copy()
    window_size = 364  # let's start with doing a yearly rolling sum for smoothness... this can later be a tuneable parameter

    # print(f"target columns for the end: {target_cols}")
    # print(f"initial shape: {df.shape}")
    daily_sums = {}
    target_cols = [target_col] + [
        "all_claims"
    ]  # make sure to create an all_claims column for comparison
    for col in target_cols:
        if col == "all_claims":
            df[col] = 1
        df[col] = pd.to_numeric(df[col])
        daily_sums[col] = df.groupby(date_col)[col].sum()

    min_date = min(s.index.min() for s in daily_sums.values())
    max_date = max(s.index.max() for s in daily_sums.values())
    all_dates = pd.date_range(start=min_date, end=max_date, freq="D")

    print(f"len(all_dates) = {len(all_dates)}")

    rolling_results = {}
    for col in target_cols:
        reindexed = daily_sums[col].reindex(all_dates, fill_value=0)
        rolled = reindexed.rolling(window=window_size, min_periods=1).sum()
        rolled_trimmed = rolled[window_size - 1 :]
        ts = rolled_trimmed.reset_index()
        ts.columns = [date_col, "rolling_sum"]
        rolling_results[col] = ts

    df_return = rolling_results[target_cols[0]][[date_col]].copy()
    for col in target_cols:
        col_name = f"{col.split('_')[0]}_count{window_size}"
        df_return[col_name] = rolling_results[col]["rolling_sum"]

    df_return["year"] = df_return[date_col].dt.year
    if cap_year:
        df_return = df_return[df_return["year"] < cap_year]

    # possible future integration with cloud-based database to track progression of hypothesis testing
    # df_return.to_csv(output_file, index=False)
    # print(f"saved to {output_file}")
    # print(f"final shape: {df_return.shape}")
    # print(f"final cols: {df_return.columns.tolist()}")

    return df_return
