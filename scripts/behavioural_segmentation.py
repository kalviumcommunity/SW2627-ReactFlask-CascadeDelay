import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


INPUT_FILE = Path("data/raw/customer_segmentation.csv")
OUTPUT_DIR = Path("output")
PROCESSED_DIR = Path("data/processed")


def load_data():
    """Load customer segmentation data."""
    df = pd.read_csv(INPUT_FILE)

    required_columns = [
        "customer_id",
        "customer_type",
        "lifetime_value",
        "churn",
        "support_tickets",
        "retention_days",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    return df


def compute_segment_metrics(df):
    """Compute behavioural metrics for each customer segment."""

    segment_metrics = df.groupby("customer_type").agg({
        "lifetime_value": "mean",
        "churn": "mean",
        "support_tickets": "mean",
        "retention_days": "mean",
        "customer_id": "count",
    })

    segment_metrics.columns = [
        "avg_ltv",
        "churn_rate",
        "avg_tickets",
        "avg_retention",
        "count",
    ]

    return segment_metrics


def create_summary_table(segment_metrics):
    """Create readable summary table with rankings."""

    summary = segment_metrics.copy()

    summary["ltv_rank"] = (
        summary["avg_ltv"]
        .rank(ascending=False, method="min")
        .astype(int)
    )

    summary["churn_rank"] = (
        summary["churn_rate"]
        .rank(ascending=True, method="min")
        .astype(int)
    )

    summary["avg_ltv_display"] = summary["avg_ltv"].apply(
        lambda x: f"${x:,.0f}"
    )

    summary["churn_rate_display"] = summary["churn_rate"].apply(
        lambda x: f"{x:.1%}"
    )

    summary["avg_tickets_display"] = summary["avg_tickets"].apply(
        lambda x: f"{x:.1f}"
    )

    summary["avg_retention_display"] = summary["avg_retention"].apply(
        lambda x: f"{x:.0f} days"
    )

    return summary


def create_heatmap(segment_metrics):
    """Create segment comparison heatmap."""

    heatmap_data = segment_metrics[
        [
            "avg_ltv",
            "churn_rate",
            "avg_tickets",
            "avg_retention",
        ]
    ].copy()

    # Normalize each metric so different units
    # do not dominate the heatmap.
    normalized = (
        heatmap_data - heatmap_data.min()
    ) / (
        heatmap_data.max() - heatmap_data.min()
    )

    plt.figure(figsize=(10, 6))

    sns.heatmap(
        normalized,
        annot=heatmap_data.round(2),
        fmt=".2f",
        cmap="RdYlGn_r",
        cbar_kws={"label": "Relative Value"},
    )

    plt.title("Segment Comparison Heatmap")
    plt.xlabel("Metrics")
    plt.ylabel("Customer Segment")
    plt.tight_layout()

    output_file = OUTPUT_DIR / "segment_heatmap.png"
    plt.savefig(output_file, dpi=150)
    plt.close()

    return output_file


def identify_performers(segment_metrics):
    """Identify highest value, highest churn and best retention segments."""

    top_value_segment = segment_metrics["avg_ltv"].idxmax()
    high_churn_segment = segment_metrics["churn_rate"].idxmax()
    best_retention_segment = segment_metrics["avg_retention"].idxmax()

    return {
        "highest_value": {
            "segment": top_value_segment,
            "avg_ltv": float(
                segment_metrics.loc[top_value_segment, "avg_ltv"]
            ),
        },
        "highest_churn": {
            "segment": high_churn_segment,
            "churn_rate": float(
                segment_metrics.loc[high_churn_segment, "churn_rate"]
            ),
        },
        "best_retention": {
            "segment": best_retention_segment,
            "avg_retention": float(
                segment_metrics.loc[
                    best_retention_segment,
                    "avg_retention"
                ]
            ),
        },
    }


def create_business_insights(segment_metrics):
    """Create business-facing insights based on observed metrics."""

    insights = {}

    for segment in segment_metrics.index:
        row = segment_metrics.loc[segment]

        if segment == "Enterprise":
            action = (
                "Maintain premium support and focus on retention "
                "because this segment has high lifetime value and "
                "low churn."
            )
        elif segment == "SMB":
            action = (
                "Improve onboarding and provide efficient support "
                "because this segment has moderate lifetime value "
                "and comparatively higher churn."
            )
        elif segment == "Startup":
            action = (
                "Emphasize self-service resources and education "
                "because this segment has lower lifetime value "
                "and shorter retention."
            )
        else:
            action = (
                "Review segment-specific retention, support and "
                "value metrics before defining a strategy."
            )

        insights[segment] = {
            "customer_count": int(row["count"]),
            "avg_ltv": float(row["avg_ltv"]),
            "churn_rate": float(row["churn_rate"]),
            "avg_tickets": float(row["avg_tickets"]),
            "avg_retention": float(row["avg_retention"]),
            "action": action,
        }

    return insights


def save_outputs(segment_metrics, summary, performers, insights):
    """Save all analysis outputs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Raw numeric segment metrics
    segment_metrics.to_csv(
        OUTPUT_DIR / "segment_metrics.csv"
    )

    # Summary with rankings and readable values
    summary.to_csv(
        OUTPUT_DIR / "segment_summary.csv"
    )

    # Performer analysis
    with open(
        OUTPUT_DIR / "segment_performers.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            performers,
            file,
            indent=4,
        )

    # Business-facing insights
    with open(
        OUTPUT_DIR / "business_segment_insights.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            insights,
            file,
            indent=4,
        )


def main():
    print("Loading customer data...")
    df = load_data()

    print(f"Loaded {len(df)} customer records.")
    print(
        f"Segments identified: "
        f"{df['customer_type'].nunique()}"
    )

    # Task 1
    print("\n=== SEGMENT METRICS ===")
    segment_metrics = compute_segment_metrics(df)
    print(segment_metrics)

    # Task 2
    print("\n=== SEGMENT SUMMARY ===")
    summary = create_summary_table(segment_metrics)

    display_columns = [
        "avg_ltv_display",
        "ltv_rank",
        "churn_rate_display",
        "churn_rank",
        "avg_tickets_display",
        "avg_retention_display",
        "count",
    ]

    print(summary[display_columns])

    # Task 3
    print("\nCreating heatmap...")
    heatmap_file = create_heatmap(segment_metrics)
    print(f"Heatmap saved to: {heatmap_file}")

    # Task 4
    print("\n=== PERFORMER ANALYSIS ===")
    performers = identify_performers(segment_metrics)

    print(
        f"Highest value: "
        f"{performers['highest_value']['segment']} "
        f"= ${performers['highest_value']['avg_ltv']:,.0f}"
    )

    print(
        f"Highest churn: "
        f"{performers['highest_churn']['segment']} "
        f"= {performers['highest_churn']['churn_rate']:.1%}"
    )

    print(
        f"Best retention: "
        f"{performers['best_retention']['segment']} "
        f"= {performers['best_retention']['avg_retention']:.0f} days"
    )

    # Task 5
    print("\n=== BUSINESS INSIGHTS ===")
    insights = create_business_insights(segment_metrics)

    for segment, data in insights.items():
        print(f"\n{segment}")
        print(
            f"Customers: {data['customer_count']}"
        )
        print(
            f"Average LTV: ${data['avg_ltv']:,.0f}"
        )
        print(
            f"Churn Rate: {data['churn_rate']:.1%}"
        )
        print(
            f"Average Tickets: {data['avg_tickets']:.1f}"
        )
        print(
            f"Average Retention: "
            f"{data['avg_retention']:.0f} days"
        )
        print(f"Action: {data['action']}")

    save_outputs(
        segment_metrics,
        summary,
        performers,
        insights,
    )

    print("\nAll outputs generated successfully.")


if __name__ == "__main__":
    main()
