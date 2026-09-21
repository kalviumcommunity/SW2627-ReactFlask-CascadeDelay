import json
import os

import pandas as pd


def create_ratio_features(df):
    """
    Create business ratio features.

    - Transactions per month
    - Average spend per transaction
    - Lifetime value per month
    """

    days_per_month = df["days_as_customer"] / 30

    df["transactions_per_month"] = (
        df["total_transactions"] / days_per_month
    )

    df["avg_spend_per_transaction"] = (
        df["total_spent"] / df["total_transactions"]
    )

    df["lifetime_value_per_month"] = (
        df["total_spent"] / days_per_month
    )

    return df


def create_engagement_tier(df):
    """
    Create equal-width engagement tiers.

    0-2     = low
    2-10    = medium
    10+     = high
    """

    df["engagement_tier"] = pd.cut(
        df["transactions_per_month"],
        bins=[0, 2, 10, float("inf")],
        labels=["low", "medium", "high"]
    )

    return df


def create_spend_quartile(df):
    """
    Divide customers into four spend quartiles.
    """

    df["spend_quartile"] = pd.qcut(
        df["total_spent"],
        q=4,
        labels=["Q1", "Q2", "Q3", "Q4"]
    )

    return df


def create_rfm_scores(df):
    """
    Create recency, frequency, monetary scores
    and combine them into an RFM score.
    """

    df["recency_score"] = pd.qcut(
        df["days_since_last_purchase"],
        q=5,
        labels=[5, 4, 3, 2, 1]
    )

    df["frequency_score"] = pd.qcut(
        df["purchase_count"],
        q=5,
        labels=[1, 2, 3, 4, 5]
    )

    df["monetary_score"] = pd.qcut(
        df["total_spent"],
        q=5,
        labels=[1, 2, 3, 4, 5]
    )

    df["rfm_score"] = (
        df["recency_score"].astype(int)
        + df["frequency_score"].astype(int)
        + df["monetary_score"].astype(int)
    )

    return df


def validate_features(df):
    """
    Validate feature ranges and check for missing values.
    """

    validation = {}

    # Engagement distribution
    engagement_distribution = (
        df["engagement_tier"]
        .value_counts()
        .to_dict()
    )

    print("\nENGAGEMENT TIER DISTRIBUTION")
    print("=" * 60)
    print(
        df["engagement_tier"]
        .value_counts()
    )

    validation["engagement_tier_distribution"] = {
        str(key): int(value)
        for key, value in engagement_distribution.items()
    }

    # RFM range
    rfm_min = int(df["rfm_score"].min())
    rfm_max = int(df["rfm_score"].max())

    print("\nRFM SCORE RANGE")
    print("=" * 60)
    print(f"RFM score range: {rfm_min}-{rfm_max}")

    validation["rfm_score_range"] = {
        "min": rfm_min,
        "max": rfm_max
    }

    # Missing values
    feature_columns = [
        "engagement_tier",
        "spend_quartile",
        "rfm_score"
    ]

    missing_values = (
        df[feature_columns]
        .isna()
        .sum()
    )

    print("\nMISSING VALUES")
    print("=" * 60)
    print(missing_values)

    validation["missing_values"] = {
        column: int(value)
        for column, value in missing_values.items()
    }

    validation["validation_passed"] = (
        missing_values.sum() == 0
        and 3 <= rfm_min <= 15
        and 3 <= rfm_max <= 15
    )

    return validation


def save_summary(
    validation,
    input_path,
    output_path
):
    """
    Save feature engineering validation summary.
    """

    os.makedirs("output", exist_ok=True)

    summary = {
        "input_file": input_path,
        "output_file": output_path,
        "validation": validation,
        "features_created": [
            "transactions_per_month",
            "avg_spend_per_transaction",
            "lifetime_value_per_month",
            "engagement_tier",
            "spend_quartile",
            "recency_score",
            "frequency_score",
            "monetary_score",
            "rfm_score"
        ],
        "status": (
            "passed"
            if validation["validation_passed"]
            else "failed"
        )
    }

    with open(
        "output/feature_engineering_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            summary,
            file,
            indent=2
        )


if __name__ == "__main__":

    input_path = (
        "data/raw/customer_data.csv"
    )

    output_path = (
        "data/processed/"
        "customer_features.csv"
    )

    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    print("\n" + "=" * 70)
    print("STARTING FEATURE ENGINEERING")
    print("=" * 70)

    # Load raw dataset
    df = pd.read_csv(input_path)

    print(
        f"Initial records: {len(df)}"
    )

    # Task 1: Ratio features
    print("\n[Task 1] Creating ratio features...")

    df = create_ratio_features(df)

    print(
        df[
            [
                "transactions_per_month",
                "avg_spend_per_transaction",
                "lifetime_value_per_month"
            ]
        ].describe()
    )

    # Task 2: Equal-width engagement bins
    print(
        "\n[Task 2] Creating engagement tiers..."
    )

    df = create_engagement_tier(df)

    print(
        df["engagement_tier"]
        .value_counts()
    )

    # Task 3: Spend quartiles
    print(
        "\n[Task 3] Creating spend quartiles..."
    )

    df = create_spend_quartile(df)

    print(
        df["spend_quartile"]
        .value_counts()
    )

    # Task 4: RFM composite score
    print(
        "\n[Task 4] Creating RFM scores..."
    )

    df = create_rfm_scores(df)

    print(
        df[
            [
                "customer_id",
                "recency_score",
                "frequency_score",
                "monetary_score",
                "rfm_score"
            ]
        ].head(10)
    )

    # Task 5: Validate features
    print(
        "\n[Task 5] Validating engineered features..."
    )

    validation = validate_features(df)

    # Save processed dataset
    df.to_csv(
        output_path,
        index=False
    )

    # Save validation summary
    save_summary(
        validation,
        input_path,
        output_path
    )

    print("\n" + "=" * 70)
    print("FEATURE ENGINEERING COMPLETE")
    print("=" * 70)

    print(
        f"Processed dataset: {output_path}"
    )

    print(
        "Summary: "
        "output/feature_engineering_summary.json"
    )

    print(
        f"Validation status: "
        f"{'PASSED' if validation['validation_passed'] else 'FAILED'}"
    )
