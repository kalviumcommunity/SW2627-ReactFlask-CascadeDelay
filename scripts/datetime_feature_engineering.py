import os

import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "data/raw/transaction_data.csv"
OUTPUT_DIR = "output"
PROCESSED_DIR = "data/processed"

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_transaction_datetime(df):
    """
    Parse transaction timestamp strings using an explicit format.

    Expected format:
        YYYY-MM-DD HH:MM:SS

    Example:
        2025-01-15 14:30:45
    """
    df = df.copy()

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"],
        format=DATE_FORMAT,
    )

    print("\n1. DATETIME PARSING")
    print("=" * 70)
    print(f"Format used: {DATE_FORMAT}")
    print(f"transaction_date dtype: {df['transaction_date'].dtype}")
    print(f"Min date: {df['transaction_date'].min()}")
    print(f"Max date: {df['transaction_date'].max()}")

    return df


def extract_datetime_features(df):
    """
    Extract temporal features from transaction_date.
    """
    df = df.copy()

    df["day_of_week"] = df["transaction_date"].dt.day_name()
    df["hour"] = df["transaction_date"].dt.hour
    df["week_num"] = df["transaction_date"].dt.isocalendar().week
    df["month"] = df["transaction_date"].dt.month
    df["month_name"] = df["transaction_date"].dt.month_name()
    df["day_of_month"] = df["transaction_date"].dt.day

    print("\n2. DATETIME FEATURE EXTRACTION")
    print("=" * 70)
    print("Created features:")
    print("- day_of_week")
    print("- hour")
    print("- week_num")
    print("- month")
    print("- month_name")
    print("- day_of_month")

    print("\nHour distribution:")
    print(df.groupby("hour").size())

    print("\nDay-of-week distribution:")
    print(df.groupby("day_of_week").size())

    return df


def create_weekly_metrics(df):
    """
    Resample transactions into weekly buckets.
    """
    df_ts = df.set_index("transaction_date")

    weekly_metrics = df_ts["amount"].resample("W").agg(
        ["sum", "count", "mean"]
    )

    weekly_metrics.columns = [
        "revenue",
        "transaction_count",
        "average_transaction",
    ]

    print("\n3. WEEKLY AGGREGATION")
    print("=" * 70)
    print(weekly_metrics)

    return weekly_metrics


def calculate_customer_recency(df):
    """
    Calculate days since each customer's most recent purchase.

    For reproducible analysis, use the latest transaction date in the
    dataset as the reference date rather than the actual current date.
    """
    df = df.copy()

    reference_date = df["transaction_date"].max()

    customer_last_purchase = (
        df.groupby("customer_id")["transaction_date"]
        .max()
    )

    customer_recency = (
        reference_date - customer_last_purchase
    ).dt.days

    customer_recency = customer_recency.rename(
        "days_since_last_purchase"
    )

    df = df.merge(
        customer_recency,
        on="customer_id",
        how="left",
    )

    print("\n4. CUSTOMER RECENCY")
    print("=" * 70)
    print(f"Reference date: {reference_date}")

    print("\nCustomer last purchase:")
    print(customer_last_purchase)

    print("\nDays since last purchase:")
    print(customer_recency)

    print("\nRecency distribution:")
    print(df["days_since_last_purchase"].describe())

    return df, customer_recency


def create_time_based_aggregation(df):
    """
    Group transactions by day of week and hour.

    Calculates:
    - total amount
    - transaction count
    - average transaction amount
    """
    hourly_daily = (
        df.groupby(["day_of_week", "hour"])["amount"]
        .agg(["sum", "count", "mean"])
    )

    print("\n5. DAY × HOUR AGGREGATION")
    print("=" * 70)
    print(hourly_daily)

    pivot_table = pd.pivot_table(
        df,
        values="amount",
        index="hour",
        columns="day_of_week",
        aggfunc="sum",
    )

    day_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    pivot_table = pivot_table.reindex(
        columns=[
            day for day in day_order
            if day in pivot_table.columns
        ]
    )

    print("\nHour × Day-of-Week revenue:")
    print(pivot_table)

    return hourly_daily, pivot_table


def identify_peak_activity(df):
    """
    Identify the busiest hour and day/hour combination.
    """
    hourly_volume = df.groupby("hour").size()

    peak_hour = hourly_volume.idxmax()
    peak_hour_volume = hourly_volume.max()

    day_hour_volume = (
        df.groupby(["day_of_week", "hour"])
        .size()
        .sort_values(ascending=False)
    )

    peak_day_hour = day_hour_volume.index[0]
    peak_day_hour_volume = day_hour_volume.iloc[0]

    print("\n6. PEAK ACTIVITY")
    print("=" * 70)
    print(
        f"Peak hour: {peak_hour}:00 "
        f"({peak_hour_volume} transactions)"
    )
    print(
        f"Peak day/hour window: "
        f"{peak_day_hour[0]} at {peak_day_hour[1]}:00 "
        f"({peak_day_hour_volume} transactions)"
    )

    return peak_hour, peak_day_hour


def create_plots(df, weekly_metrics, pivot_table):
    """
    Create temporal distribution plots.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Hour distribution
    plt.figure(figsize=(10, 6))
    df["hour"].value_counts().sort_index().plot(kind="bar")
    plt.title("Transaction Volume by Hour")
    plt.xlabel("Hour of Day")
    plt.ylabel("Number of Transactions")
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/hour_distribution.png",
        dpi=150,
    )
    plt.close()

    # Weekly revenue
    plt.figure(figsize=(10, 6))
    weekly_metrics["revenue"].plot()
    plt.title("Weekly Revenue Trend")
    plt.xlabel("Week")
    plt.ylabel("Revenue")
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/weekly_revenue.png",
        dpi=150,
    )
    plt.close()

    # Day/hour heatmap
    plt.figure(figsize=(10, 6))
    plt.imshow(pivot_table.fillna(0), aspect="auto")
    plt.colorbar(label="Revenue")
    plt.title("Revenue by Hour and Day of Week")
    plt.xlabel("Day of Week")
    plt.ylabel("Hour")
    plt.xticks(
        range(len(pivot_table.columns)),
        pivot_table.columns,
        rotation=45,
    )
    plt.tight_layout()
    plt.savefig(
        f"{OUTPUT_DIR}/day_hour_heatmap.png",
        dpi=150,
    )
    plt.close()

    print("\nPlots saved:")
    print(f"- {OUTPUT_DIR}/hour_distribution.png")
    print(f"- {OUTPUT_DIR}/weekly_revenue.png")
    print(f"- {OUTPUT_DIR}/day_hour_heatmap.png")


def run_validation(df):
    """
    Run required validation checks.
    """
    print("\n7. VALIDATION")
    print("=" * 70)

    print(f"Min date: {df['transaction_date'].min()}")
    print(f"Max date: {df['transaction_date'].max()}")

    days = (
        df["transaction_date"].max()
        - df["transaction_date"].min()
    ).days

    print(f"Days in dataset: {days}")
    print(f"Hours with data: {sorted(df['hour'].unique())}")
    print(f"Weeks in dataset: {df['week_num'].nunique()}")
    print(
        "Min days since purchase: "
        f"{df['days_since_last_purchase'].min()}"
    )
    print(
        "Max days since purchase: "
        f"{df['days_since_last_purchase'].max()}"
    )

    assert pd.api.types.is_datetime64_any_dtype(
        df["transaction_date"]
    )

    assert "day_of_week" in df.columns
    assert "hour" in df.columns
    assert "week_num" in df.columns
    assert "days_since_last_purchase" in df.columns

    print("\n✓ All validation checks passed")


def main():
    print("=" * 70)
    print("DATETIME FEATURE ENGINEERING PIPELINE")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    # Load data
    df = pd.read_csv(INPUT_FILE)

    print("\nOriginal data:")
    print(df.head())
    print("\nOriginal dtypes:")
    print(df.dtypes)

    # Task 1
    df = parse_transaction_datetime(df)

    # Task 2
    df = extract_datetime_features(df)

    # Task 3
    weekly_metrics = create_weekly_metrics(df)

    # Task 4
    df, customer_recency = calculate_customer_recency(df)

    # Task 5
    hourly_daily, pivot_table = create_time_based_aggregation(df)

    # Peak analysis
    identify_peak_activity(df)

    # Plots
    create_plots(df, weekly_metrics, pivot_table)

    # Validation
    run_validation(df)

    # Save processed dataset
    output_file = f"{PROCESSED_DIR}/datetime_features.csv"
    df.to_csv(output_file, index=False)

    weekly_metrics.to_csv(
        f"{OUTPUT_DIR}/weekly_metrics.csv"
    )

    hourly_daily.to_csv(
        f"{OUTPUT_DIR}/hourly_daily_aggregation.csv"
    )

    pivot_table.to_csv(
        f"{OUTPUT_DIR}/day_hour_pivot.csv"
    )

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"✓ Processed data: {output_file}")
    print("✓ Weekly metrics saved")
    print("✓ Hour/day aggregation saved")
    print("✓ Pivot table saved")
    print("✓ Temporal plots saved")


if __name__ == "__main__":
    main()