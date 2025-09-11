import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.dates as mdates

def plot_ts(
    df_timeseries: pd.DataFrame,
    date_col: str,
    target_rolling_col: str
):
    df = df_timeseries.sort_values(by=[date_col]).copy()

    # --- Create the Plots ---
    plt.clf()
    fig, ax1 = plt.subplots(figsize=(15, 3.5))  # Create figure and primary axis

    # Plot target_col1
    color1 = "tab:blue"
    ax1.set_xlabel("Date")
    ax1.set_ylabel(target_rolling_col, color=color1)
    line1 = ax1.plot(
        df[date_col],
        df[target_rolling_col],
        color=color1,
        marker=".",
        linestyle="-",
        markersize=2,
        label=target_rolling_col,
    )
    ax1.tick_params(axis="y", labelcolor=color1)

    lines = line1  # For combined legend
    labels = [line.get_label() for line in lines]

    ax1.grid(True, which="both", linestyle="--", linewidth=0.5)
    ax1.legend(lines, labels, loc="upper left")

    # Improve date formatting on x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=8, maxticks=15))
    plt.xticks(rotation=30, ha="right")

    # Save plot
    plt.tight_layout()
    plt.show()

    return plt