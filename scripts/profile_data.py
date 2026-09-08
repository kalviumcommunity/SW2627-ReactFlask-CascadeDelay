"""Profile a CSV dataset and save a structured data-quality report."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def profile_nulls_and_duplicates(df):
    """Compute null counts, null percentages, and exact duplicate metrics.

    Input: Pandas DataFrame containing raw data.
    Output: Dictionary of null and duplicate statistics.
    Assumptions: The DataFrame contains at least one row.
    """
    profile = {
        "null_counts": {},
        "null_percentages": {},
        "exact_duplicate_count": int(df.duplicated().sum()),
    }

    # Calculate missing values separately for every column.
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        null_percentage = (null_count / len(df)) * 100 if len(df) else 0

        profile["null_counts"][col] = null_count
        profile["null_percentages"][col] = round(null_percentage, 2)

    profile["duplicate_percentage"] = round(
        (profile["exact_duplicate_count"] / len(df)) * 100 if len(df) else 0,
        2,
    )

    return profile


def profile_numerical_columns(df):
    """Summarise numerical columns with descriptive statistics.

    Input: Pandas DataFrame with zero or more numeric columns.
    Output: DataFrame containing min, max, mean, median, std, and null count.
    Assumptions: Non-numeric columns are excluded.
    """
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    stats = {}

    # Calculate statistics for every numeric column.
    for col in numerical_cols:
        stats[col] = {
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
            "mean": round(float(df[col].mean()), 2),
            "median": round(float(df[col].median()), 2),
            "std": round(float(df[col].std()), 2),
            "null_count": int(df[col].isnull().sum()),
        }

    return pd.DataFrame(stats).T


def profile_categorical_columns(df, top_n=5):
    """Summarise categorical columns using unique counts and common values.

    Input: Pandas DataFrame and number of frequent values to retain.
    Output: Dictionary containing categorical distributions.
    Assumptions: Categorical fields are stored as object/text columns.
    """
    categorical_cols = df.select_dtypes(include=["object"]).columns
    profile = {}

    # Count unique and frequently occurring text values for each column.
    for col in categorical_cols:
        profile[col] = {
            "unique_count": int(df[col].nunique()),
            "top_values": {
                str(value): int(count)
                for value, count in df[col].value_counts().head(top_n).items()
            },
            "null_count": int(df[col].isnull().sum()),
        }

    return profile


def identify_quality_issues(df, null_threshold=30, duplicate_threshold=5):
    """Flag high null rates, duplicate rows, and negative amount values.

    Input: Pandas DataFrame plus percentage thresholds.
    Output: List of issue dictionaries with severity and recommendations.
    Assumptions: Columns containing 'amount' should not contain negatives.
    """
    issues = []
    null_percentages = (df.isnull().sum() / len(df)) * 100 if len(df) else pd.Series()

    # Flag columns exceeding the allowed missing-data threshold.
    for col, percentage in null_percentages.items():
        if percentage > null_threshold:
            issues.append({
                "type": "High nulls",
                "column": col,
                "severity": "HIGH",
                "value": f"{percentage:.1f}% missing",
                "recommendation": "Consider imputation or column exclusion",
            })

    duplicate_count = int(df.duplicated().sum())
    duplicate_percentage = (duplicate_count / len(df)) * 100 if len(df) else 0

    # Flag datasets containing too many exact duplicate rows.
    if duplicate_percentage > duplicate_threshold:
        issues.append({
            "type": "High duplicates",
            "column": "Full row",
            "severity": "HIGH",
            "value": f"{duplicate_percentage:.1f}% duplicated",
            "recommendation": "Deduplication required before analysis",
        })

    # Check numeric amount fields for values that should be non-negative.
    for col in df.select_dtypes(include=[np.number]).columns:
        if "amount" in col.lower() and (df[col] < 0).any():
            issues.append({
                "type": "Invalid range",
                "column": col,
                "severity": "MEDIUM",
                "value": "Contains negative values",
                "recommendation": "Investigate negative entries",
            })

    return issues


def generate_profile_report(df, filepath):
    """Build, save, and print a complete data-quality report.

    Input: Raw DataFrame and source-file label.
    Output: Dictionary containing all profiling results; also saves JSON.
    Assumptions: The output directory can be created by the script.
    """
    report = {
        "dataset": str(filepath),
        "record_count": len(df),
        "column_count": len(df.columns),
        "nulls_and_duplicates": profile_nulls_and_duplicates(df),
        "numerical_stats": profile_numerical_columns(df).to_dict(),
        "categorical_stats": profile_categorical_columns(df),
        "quality_issues": identify_quality_issues(df),
    }

    # Save an indented JSON report for downstream cleaning decisions.
    output_path = Path(__file__).resolve().parents[1] / "output/profile_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print(f"\n{'=' * 60}")
    print(f"DATA QUALITY PROFILE: {filepath}")
    print(f"{'=' * 60}")
    print(f"Records: {report['record_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"\nQuality Issues Found: {len(report['quality_issues'])}")

    for issue in report["quality_issues"]:
        print(f"  [{issue['severity']}] {issue['type']} in {issue['column']}")
        print(f"    Value: {issue['value']} → {issue['recommendation']}")

    print(f"{'=' * 60}\n")
    return report


def main():
    """Load the test CSV and generate its data-quality report."""
    project_root = Path(__file__).resolve().parents[1]
    source_path = project_root / "data/raw/quality_test.csv"

    # Ingest the raw test dataset before profiling its quality.
    dataset = pd.read_csv(source_path)
    generate_profile_report(dataset, source_path)


if __name__ == "__main__":
    main()