import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats


INPUT_FILE = "data/raw/customer_revenue.csv"
OUTPUT_DIR = "output"


def load_data():
    """Load customer revenue data."""

    df = pd.read_csv(INPUT_FILE)

    print("=" * 70)
    print("DATASET")
    print("=" * 70)

    print(f"Rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")

    print("\nFirst 5 rows:")
    print(df.head())

    return df


def analyze_basic_statistics(df):
    """Calculate descriptive statistics."""

    revenue = df["revenue"]

    print("\n" + "=" * 70)
    print("BASIC REVENUE STATISTICS")
    print("=" * 70)

    print(revenue.describe())

    print(f"\nMean: ${revenue.mean():.2f}")
    print(f"Median: ${revenue.median():.2f}")
    print(f"Minimum: ${revenue.min():.2f}")
    print(f"Maximum: ${revenue.max():.2f}")

    print("\nPercentiles:")
    percentiles = revenue.quantile(
        [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    )

    print(percentiles)

    return percentiles


def calculate_skewness_kurtosis(df):
    """Calculate skewness and kurtosis."""

    revenue = df["revenue"]

    skewness = stats.skew(
        revenue,
        bias=False
    )

    kurtosis = stats.kurtosis(
        revenue,
        bias=False
    )

    print("\n" + "=" * 70)
    print("SKEWNESS AND KURTOSIS")
    print("=" * 70)

    print(f"Skewness: {skewness:.2f}")
    print(f"Excess Kurtosis: {kurtosis:.2f}")

    if abs(skewness) > 1:
        print(
            "→ Highly skewed distribution: "
            "median is more representative than mean."
        )
    elif abs(skewness) > 0.5:
        print(
            "→ Moderately skewed distribution."
        )
    else:
        print(
            "→ Approximately symmetric distribution."
        )

    if kurtosis > 3:
        print(
            "→ Heavy tails and potential extreme outliers."
        )
    else:
        print(
            "→ No extreme excess kurtosis detected."
        )

    return skewness, kurtosis


def create_distribution_plots(df):
    """Create histogram and KDE plots."""

    revenue = df["revenue"]

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(14, 5)
    )

    # Histogram
    axes[0].hist(
        revenue,
        bins=50,
        edgecolor="black"
    )

    axes[0].set_title(
        "Revenue Distribution (Histogram)"
    )
    axes[0].set_xlabel("Revenue")
    axes[0].set_ylabel("Number of Customers")

    # KDE
    revenue.plot(
        kind="density",
        ax=axes[1]
    )

    axes[1].set_title(
        "Revenue Distribution (KDE)"
    )
    axes[1].set_xlabel("Revenue")
    axes[1].set_ylabel("Density")

    plt.tight_layout()

    output_file = (
        f"{OUTPUT_DIR}/revenue_distribution.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"\n✓ Distribution plot saved: {output_file}"
    )


def analyze_abnormal_patterns(df):
    """Identify potential segments and abnormal patterns."""

    revenue = df["revenue"]

    print("\n" + "=" * 70)
    print("ABNORMAL PATTERN ANALYSIS")
    print("=" * 70)

    percentiles = revenue.quantile(
        [0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    )

    print("\nPercentile distribution:")
    print(percentiles)

    q75 = percentiles.loc[0.75]
    q90 = percentiles.loc[0.90]

    gap = q90 - q75

    print(
        f"\n75th percentile: ${q75:.2f}"
    )
    print(
        f"90th percentile: ${q90:.2f}"
    )
    print(
        f"75th → 90th percentile gap: ${gap:.2f}"
    )

    if gap > q75:
        print(
            "→ Large upper-tail gap suggests a "
            "small high-value customer segment."
        )
    else:
        print(
            "→ Upper tail does not show an extremely "
            "large percentile gap."
        )

    # IQR outlier detection
    q1 = revenue.quantile(0.25)
    q3 = revenue.quantile(0.75)

    iqr = q3 - q1

    upper_bound = q3 + 1.5 * iqr

    outliers = df[
        df["revenue"] > upper_bound
    ]

    print(
        f"\nIQR upper bound: ${upper_bound:.2f}"
    )

    print(
        f"Potential outliers: {len(outliers)}"
    )

    print(
        f"Outlier percentage: "
        f"{len(outliers) / len(df) * 100:.2f}%"
    )

    return outliers


def compare_segments(df):
    """Compare high-value and low-value customer groups."""

    revenue = df["revenue"]

    q25 = revenue.quantile(0.25)
    q75 = revenue.quantile(0.75)

    low_value = df[
        df["revenue"] <= q25
    ]

    high_value = df[
        df["revenue"] >= q75
    ]

    print("\n" + "=" * 70)
    print("SEGMENT COMPARISON")
    print("=" * 70)

    print(
        f"Low-value customers: {len(low_value)}"
    )

    print(
        f"High-value customers: {len(high_value)}"
    )

    print(
        f"\nLow-value mean: "
        f"${low_value['revenue'].mean():.2f}"
    )

    print(
        f"Low-value median: "
        f"${low_value['revenue'].median():.2f}"
    )

    print(
        f"\nHigh-value mean: "
        f"${high_value['revenue'].mean():.2f}"
    )

    print(
        f"High-value median: "
        f"${high_value['revenue'].median():.2f}"
    )

    # Segment visualization
    plt.figure(figsize=(10, 6))

    plt.hist(
        low_value["revenue"],
        bins=30,
        alpha=0.7,
        label="Low-Value Customers"
    )

    plt.hist(
        high_value["revenue"],
        bins=30,
        alpha=0.7,
        label="High-Value Customers"
    )

    plt.xlabel("Revenue")
    plt.ylabel("Number of Customers")
    plt.title(
        "Revenue: High vs Low Value Customers"
    )
    plt.legend()

    plt.tight_layout()

    output_file = (
        f"{OUTPUT_DIR}/high_low_segments.png"
    )

    plt.savefig(
        output_file,
        dpi=150
    )

    plt.close()

    print(
        f"\n✓ Segment plot saved: {output_file}"
    )

    return low_value, high_value


def statistical_test(df):
    """
    Test whether high-value and low-value
    customer revenue distributions differ.

    Mann-Whitney U is used because revenue is
    strongly skewed and does not require normality.
    """

    revenue = df["revenue"]

    q25 = revenue.quantile(0.25)
    q75 = revenue.quantile(0.75)

    low_value = df[
        df["revenue"] <= q25
    ]["revenue"]

    high_value = df[
        df["revenue"] >= q75
    ]["revenue"]

    statistic, p_value = stats.mannwhitneyu(
        low_value,
        high_value,
        alternative="two-sided"
    )

    print("\n" + "=" * 70)
    print("STATISTICAL TEST")
    print("=" * 70)

    print("Test: Mann-Whitney U test")
    print(
        f"U statistic: {statistic:.2f}"
    )
    print(
        f"p-value: {p_value:.6f}"
    )

    if p_value < 0.05:
        print(
            "→ Statistically significant difference "
            "between the two customer segments."
        )
    else:
        print(
            "→ No statistically significant difference "
            "detected."
        )

    return statistic, p_value


def business_interpretation(
    df,
    skewness,
    kurtosis
):
    """Generate business interpretation."""

    revenue = df["revenue"]

    mean = revenue.mean()
    median = revenue.median()
    top_1 = revenue.quantile(0.99)

    if skewness > 1:
        distribution_description = (
            "Highly right-skewed"
        )
        statistic_recommendation = (
            "The median should be preferred over "
            "the mean when describing the typical customer."
        )
        action = (
            "Segment customers into lower-value and "
            "enterprise/high-value groups and use "
            "different retention, pricing, and marketing strategies."
        )
    else:
        distribution_description = (
            "Approximately balanced"
        )
        statistic_recommendation = (
            "Mean and median provide relatively similar "
            "descriptions of the typical customer."
        )
        action = (
            "A relatively uniform customer strategy "
            "may be appropriate."
        )

    if kurtosis > 3:
        tail_description = (
            "Heavy tails indicate extreme revenue observations."
        )
    else:
        tail_description = (
            "Tail behavior is not unusually extreme."
        )

    interpretation = f"""
Revenue Distribution Analysis
=============================

Skewness: {skewness:.2f}
Interpretation: {distribution_description}

Mean revenue: ${mean:.2f}
Median revenue: ${median:.2f}

{statistic_recommendation}

Kurtosis: {kurtosis:.2f}
{tail_description}

99th percentile: ${top_1:.2f}
Maximum revenue: ${revenue.max():.2f}

Business Interpretation:
The right-skewed distribution indicates that most customers
generate relatively modest revenue while a smaller group of
customers generates disproportionately large revenue.

Therefore, the mean can overstate what a typical customer
is worth. The median provides a better representation of
the typical customer.

The high-value segment may represent enterprise or
strategically important accounts. These customers may
require dedicated account management, retention programs,
and customized pricing or service.

Business Action:
{action}
"""

    print("\n" + "=" * 70)
    print("BUSINESS INTERPRETATION")
    print("=" * 70)
    print(interpretation)

    with open(
        f"{OUTPUT_DIR}/business_interpretation.txt",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(interpretation)

    print(
        "✓ Business interpretation saved"
    )


def main():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # Load
    df = load_data()

    # Task 1
    create_distribution_plots(df)

    # Task 2
    skewness, kurtosis = (
        calculate_skewness_kurtosis(df)
    )

    # Task 3
    analyze_basic_statistics(df)
    analyze_abnormal_patterns(df)

    # Task 4
    compare_segments(df)

    # Statistical testing
    statistical_test(df)

    # Task 5
    business_interpretation(
        df,
        skewness,
        kurtosis
    )

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()