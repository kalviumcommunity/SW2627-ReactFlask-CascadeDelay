import os

import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "data/raw/daily_revenue.csv"
OUTPUT_DIR = "output"
PROCESSED_FILE = "data/processed/rolling_metrics.csv"


def load_data():
    """Load and prepare daily revenue data."""

    df = pd.read_csv(INPUT_FILE)

    df["date"] = pd.to_datetime(
        df["date"],
        format="%Y-%m-%d"
    )

    df = df.sort_values("date").reset_index(drop=True)

    print("=" * 70)
    print("DATASET")
    print("=" * 70)

    print(f"Rows: {len(df)}")
    print(f"Start date: {df['date'].min()}")
    print(f"End date: {df['date'].max()}")

    return df


def resample_data(df):
    """
    Resample daily data into weekly and monthly periods.
    """

    df_ts = df.set_index("date")

    # Weekly metrics
    weekly = df_ts.resample("W").agg({
        "revenue": ["sum", "mean"],
        "orders": ["count", "sum"]
    })

    weekly.columns = [
        "revenue_sum",
        "revenue_mean",
        "orders_count",
        "orders_sum"
    ]

    # Monthly metrics
    monthly = df_ts.resample("ME").agg({
        "revenue": ["sum", "mean"],
        "orders": ["count", "sum"]
    })

    monthly.columns = [
        "revenue_sum",
        "revenue_mean",
        "orders_count",
        "orders_sum"
    ]

    print("\n" + "=" * 70)
    print("TASK 1: TIME PERIOD RESAMPLING")
    print("=" * 70)

    print("\nWeekly revenue:")
    print(weekly["revenue_sum"])

    print("\nMonthly revenue:")
    print(monthly["revenue_sum"])

    highest_week = weekly["revenue_sum"].idxmax()
    highest_week_revenue = weekly["revenue_sum"].max()

    highest_month = monthly["revenue_sum"].idxmax()
    highest_month_revenue = monthly["revenue_sum"].max()

    print(
        f"\nHighest revenue week: "
        f"{highest_week.date()} "
        f"→ ${highest_week_revenue:,.2f}"
    )

    print(
        f"Highest revenue month: "
        f"{highest_month.strftime('%Y-%m')} "
        f"→ ${highest_month_revenue:,.2f}"
    )

    return weekly, monthly


def calculate_rolling_averages(df):
    """
    Calculate 7-day and 30-day rolling revenue averages.
    """

    df = df.copy()

    df["revenue_ma7"] = (
        df["revenue"]
        .rolling(window=7)
        .mean()
    )

    df["revenue_ma30"] = (
        df["revenue"]
        .rolling(window=30)
        .mean()
    )

    print("\n" + "=" * 70)
    print("TASK 2: ROLLING AVERAGES")
    print("=" * 70)

    print(
        "\n7-day MA latest value: "
        f"${df['revenue_ma7'].iloc[-1]:,.2f}"
    )

    print(
        "30-day MA latest value: "
        f"${df['revenue_ma30'].iloc[-1]:,.2f}"
    )

    return df


def calculate_mom_change(monthly):
    """
    Calculate month-over-month revenue percentage change.
    """

    monthly_revenue = monthly["revenue_sum"]

    mom_change = (
        monthly_revenue
        .pct_change()
        * 100
    )

    print("\n" + "=" * 70)
    print("TASK 3: MONTH-OVER-MONTH CHANGE")
    print("=" * 70)

    print("\nMonthly revenue:")
    print(monthly_revenue)

    print("\nMoM percentage change:")
    print(mom_change)

    growth_months = mom_change[
        mom_change > 0
    ]

    decline_months = mom_change[
        mom_change < 0
    ]

    print("\nMonths with growth:")
    print(growth_months)

    print("\nMonths with decline:")
    print(decline_months)

    return mom_change


def calculate_cumulative_revenue(df):
    """
    Calculate cumulative revenue.
    """

    df = df.copy()

    df["cumulative_revenue"] = (
        df["revenue"].cumsum()
    )

    total_revenue = (
        df["cumulative_revenue"].iloc[-1]
    )

    print("\n" + "=" * 70)
    print("TASK 4: CUMULATIVE REVENUE")
    print("=" * 70)

    print(
        f"Total accumulated revenue: "
        f"${total_revenue:,.2f}"
    )

    return df


def create_rolling_plot(df):
    """
    Plot raw revenue with 7-day and 30-day rolling averages.
    """

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["revenue"],
        label="Raw Daily Revenue",
        alpha=0.3
    )

    plt.plot(
        df["date"],
        df["revenue_ma7"],
        label="7-Day Moving Average"
    )

    plt.plot(
        df["date"],
        df["revenue_ma30"],
        label="30-Day Moving Average"
    )

    plt.title(
        "Daily Revenue vs Rolling Averages"
    )

    plt.xlabel("Date")
    plt.ylabel("Revenue ($)")
    plt.legend()

    plt.tight_layout()

    output_file = (
        f"{OUTPUT_DIR}/rolling_avg.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"\n✓ Rolling average plot saved: "
        f"{output_file}"
    )


def create_cumulative_plot(df):
    """
    Plot cumulative revenue.
    """

    plt.figure(figsize=(12, 6))

    plt.plot(
        df["date"],
        df["cumulative_revenue"]
    )

    plt.title(
        "Cumulative Revenue Over Time"
    )

    plt.xlabel("Date")
    plt.ylabel("Cumulative Revenue ($)")

    plt.tight_layout()

    output_file = (
        f"{OUTPUT_DIR}/cumulative.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"✓ Cumulative plot saved: "
        f"{output_file}"
    )


def analyze_trend(df, mom_change):
    """
    Determine whether the underlying revenue trend
    is increasing, decreasing, or flat.
    """

    # Compare the beginning and end of the
    # latest 30-day rolling average period.
    recent_ma30 = (
        df["revenue_ma30"]
        .dropna()
        .iloc[-30:]
    )

    start_value = recent_ma30.iloc[0]
    end_value = recent_ma30.iloc[-1]

    trend_magnitude = (
        (end_value - start_value)
        / start_value
        * 100
    )

    if abs(trend_magnitude) < 2:
        trend_direction = "flat"
    elif trend_magnitude > 0:
        trend_direction = "up"
    else:
        trend_direction = "down"

    latest_mom = (
        mom_change.dropna().iloc[-1]
    )

    volatility = df["revenue"].std()

    print("\n" + "=" * 70)
    print("TASK 5: TREND ANALYSIS")
    print("=" * 70)

    print(
        f"Rolling Average Trend: "
        f"{trend_direction.upper()}"
    )

    print(
        f"30-day rolling average change: "
        f"{trend_magnitude:.2f}%"
    )

    print(
        f"Latest month-over-month change: "
        f"{latest_mom:.2f}%"
    )

    print(
        f"Daily revenue standard deviation: "
        f"${volatility:,.2f}"
    )

    if trend_direction == "up":
        implication = (
            "The smoothed revenue trend is increasing, "
            "suggesting positive underlying momentum "
            "despite daily fluctuations."
        )

        action = (
            "Investigate which products, customers, "
            "or channels are contributing to growth "
            "and evaluate whether successful strategies "
            "can be sustained."
        )

    elif trend_direction == "down":
        implication = (
            "The smoothed revenue trend is declining, "
            "suggesting weakening underlying momentum."
        )

        action = (
            "Investigate changes in customer demand, "
            "product performance, pricing, and acquisition "
            "channels before making strategic changes."
        )

    else:
        implication = (
            "The smoothed revenue trend is relatively "
            "stable, despite daily fluctuations."
        )

        action = (
            "Continue monitoring the rolling metrics and "
            "investigate whether specific customer or "
            "product segments show different trends."
        )

    analysis = f"""
TREND ANALYSIS
==============

Rolling Average Trend: {trend_direction.upper()}
Change over latest 30-day rolling period: {trend_magnitude:.2f}%
Latest month-over-month growth: {latest_mom:.2f}%

Daily Revenue Volatility:
${volatility:,.2f} standard deviation

Business Interpretation:
{implication}

Business Action:
{action}

Important:
Daily revenue contains short-term noise. The 7-day and
30-day rolling averages provide a smoother view of the
underlying business trend. The 30-day average is less
sensitive to individual daily spikes or drops.
"""

    print(analysis)

    with open(
        f"{OUTPUT_DIR}/trend_analysis.txt",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(analysis)

    print(
        "✓ Trend analysis saved to "
        "output/trend_analysis.txt"
    )


def validate_data(df):
    """
    Validate time-series data.
    """

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        f"Date range: "
        f"{df['date'].min()} → "
        f"{df['date'].max()}"
    )

    print(
        f"Missing dates: "
        f"{df['date'].isna().sum()}"
    )

    print(
        f"Missing revenue: "
        f"{df['revenue'].isna().sum()}"
    )

    print(
        f"Missing orders: "
        f"{df['orders'].isna().sum()}"
    )

    assert pd.api.types.is_datetime64_any_dtype(
        df["date"]
    )

    assert df["date"].is_monotonic_increasing

    assert df["revenue"].notna().all()

    print("\n✓ Validation passed")


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    # Load
    df = load_data()

    # Task 1
    weekly, monthly = resample_data(df)

    # Task 2
    df = calculate_rolling_averages(df)

    # Task 3
    mom_change = calculate_mom_change(
        monthly
    )

    # Task 4
    df = calculate_cumulative_revenue(df)

    # Plots
    create_rolling_plot(df)
    create_cumulative_plot(df)

    # Task 5
    analyze_trend(
        df,
        mom_change
    )

    # Validation
    validate_data(df)

    # Save processed dataset
    df.to_csv(
        PROCESSED_FILE,
        index=False
    )

    print(
        f"\n✓ Processed data saved to "
        f"{PROCESSED_FILE}"
    )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()