import pandas as pd
import typing
import statsmodels.api as sm


def calculate_smoothness_score(
    time_series: pd.DataFrame,
    date_col: str,
    target_rolling_col: str,
    transition_date: str = "2015-10-01"
) -> float:
    """
    Performs an Interrupted Time Series Analysis (ITSA) to score discontinuity.
    The score is the p-value of the interaction term, which represents the
    significance of the change in slope after the transition.
    A higher score (p-value closer to 1.0) is better, indicating a smoother transition.
    """
    if target_rolling_col not in time_series.columns:
        raise ValueError(f"Target column '{target_rolling_col}' not found in time_series DataFrame.")
    if date_col not in time_series.columns:
         raise ValueError(f"Date column '{date_col}' not found in time_series DataFrame.")

    df_itsa = time_series.copy()
    transition_date_dt = pd.to_datetime(transition_date)
    df_itsa[date_col] = pd.to_datetime(df_itsa[date_col])

    # --- Prepare variables for ITSA ---
    # 1. Create a continuous time counter from the start
    df_itsa['time'] = (df_itsa[date_col] - df_itsa[date_col].min()).dt.days

    # 2. Create a dummy variable for the period after the transition
    df_itsa['post_transition'] = (df_itsa[date_col] > transition_date_dt).astype(int)

    # 3. Create an interaction term to test for a change in slope
    # This term is zero before the transition and counts days after
    df_itsa['time_after_transition'] = (df_itsa[date_col] - transition_date_dt).dt.days.clip(lower=0)
    
    # --- Setup and run the OLS model ---
    y = df_itsa[target_rolling_col]
    X = df_itsa[["time", "post_transition", "time_after_transition"]]
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()
    
    # The significance metric is the p-value for the interaction term.
    # This p-value tells us the probability that the observed change in slope
    # is just due to random chance. A high p-value means the change is not
    # statistically significant, indicating a "smooth" transition.
    significance_metric = model.pvalues.get('time_after_transition', 1.0) # Default to 1.0 (perfectly smooth) if term is dropped

    # Since the main loop will likely look for the MINIMUM score, we return
    # 1.0 - p_value. This way, a high p-value (good) results in a low score.
    # A p-value of 0.95 (very smooth) becomes a score of 0.05.
    # A p-value of 0.01 (very abrupt) becomes a score of 0.99.
    return 1.0 - significance_metric