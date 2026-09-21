import json
import os

import numpy as np
import pandas as pd
from scipy import stats


def detect_zscore_outliers(df, column):
    """
    Detect outliers using the Z-score method.

    Values beyond +/- 3 standard deviations
    are considered outliers.
    """

    z_scores = np.abs(stats.zscore(df[column]))

    df["revenue_zscore"] = z_scores

    df["is_outlier_zscore"] = (
        df["revenue_zscore"] > 3
    )

    z_outliers = df[
        df["is_outlier_zscore"]
    ]

    print("\nZ-SCORE OUTLIER DETECTION")
    print("=" * 60)
    print(
        f"Z-score outliers: "
        f"{len(z_outliers)}"
    )

    return df, z_outliers


def detect_iqr_outliers(df, column):
    """
    Detect outliers using the IQR method.

    Outliers are values below:
        Q1 - 1.5 * IQR

    or above:
        Q3 + 1.5 * IQR
    """

    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)

    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    df["is_outlier_iqr"] = (
        (df[column] < lower)
        | (df[column] > upper)
    )

    print("\nIQR OUTLIER DETECTION")
    print("=" * 60)
    print(f"Q1: {q1}")
    print(f"Q3: {q3}")
    print(f"IQR: {iqr}")
    print(f"Lower bound: {lower}")
    print(f"Upper bound: {upper}")
    print(
        f"IQR outliers: "
        f"{df['is_outlier_iqr'].sum()}"
    )

    return df, lower, upper


def cap_outliers(df, column, lower, upper):
    """
    Cap values at the IQR boundaries.
    """

    df[f"{column}_capped"] = df[column].clip(
        lower=lower,
        upper=upper
    )

    print("\nOUTLIER CAPPING")
    print("=" * 60)

    print(
        f"Before: min={df[column].min()}, "
        f"max={df[column].max()}"
    )

    print(
        f"After:  min={df[f'{column}_capped'].min()}, "
        f"max={df[f'{column}_capped'].max()}"
    )

    return df


def flag_outliers(df, column):
    """
    Combine Z-score and IQR detection
    into a single binary outlier flag.
    """

    df["is_outlier"] = (
        df["is_outlier_iqr"]
        | (df["revenue_zscore"] > 3)
    )

    normal = df[
        ~df["is_outlier"]
    ]

    anomalies = df[
        df["is_outlier"]
    ]

    print("\nOUTLIER FLAGGING")
    print("=" * 60)
    print(
        f"Normal records: "
        f"{len(normal)}"
    )
    print(
        f"Anomalies: "
        f"{len(anomalies)}"
    )

    return df, normal, anomalies


def create_cleaning_log(
    df,
    lower,
    upper
):
    """
    Create an audit log documenting
    the outlier handling decision.
    """

    affected_rows = int(
        df["is_outlier_iqr"].sum()
    )

    cleaning_log = [
        {
            "column": "revenue",
            "method": "IQR",
            "action": "cap",
            "threshold_lower": lower,
            "threshold_upper": upper,
            "affected_rows": affected_rows,
            "date": pd.Timestamp.now().isoformat()
        }
    ]

    log_df = pd.DataFrame(
        cleaning_log
    )

    os.makedirs("output", exist_ok=True)

    log_df.to_csv(
        "output/cleaning_log.csv",
        index=False
    )

    print("\nCLEANING LOG")
    print("=" * 60)
    print(log_df.to_string(index=False))

    return log_df


def create_summary(
    df,
    lower,
    upper,
    z_outlier_count,
    iqr_outlier_count
):
    """
    Create a summary of the outlier
    detection and handling process.
    """

    summary = {
        "column": "revenue",
        "zscore_threshold": 3,
        "zscore_outliers": int(
            z_outlier_count
        ),
        "iqr_lower_bound": float(lower),
        "iqr_upper_bound": float(upper),
        "iqr_outliers": int(
            iqr_outlier_count
        ),
        "combined_outliers": int(
            df["is_outlier"].sum()
        ),
        "handling_strategy": "cap",
        "timestamp": pd.Timestamp.now().isoformat()
    }

    with open(
        "output/outlier_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            summary,
            file,
            indent=2
        )

    return summary


if __name__ == "__main__":

    input_path = (
        "data/raw/revenue_data.csv"
    )

    output_path = (
        "data/processed/"
        "revenue_data_with_outliers_handled.csv"
    )

    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    print("\n" + "=" * 70)
    print("STARTING OUTLIER DETECTION WORKFLOW")
    print("=" * 70)

    # Load data
    df = pd.read_csv(input_path)

    print(
        f"Initial records: {len(df)}"
    )

    print(
        f"Revenue range: "
        f"{df['revenue'].min()} - "
        f"{df['revenue'].max()}"
    )

    # Task 1: Z-score detection
    df, z_outliers = detect_zscore_outliers(
        df,
        "revenue"
    )

    # Task 2: IQR detection
    (
        df,
        lower,
        upper
    ) = detect_iqr_outliers(
        df,
        "revenue"
    )

    # Task 3: Cap outliers
    df = cap_outliers(
        df,
        "revenue",
        lower,
        upper
    )

    # Task 4: Flag outliers
    (
        df,
        normal,
        anomalies
    ) = flag_outliers(
        df,
        "revenue"
    )

    # Task 5: Cleaning log
    create_cleaning_log(
        df,
        lower,
        upper
    )

    # Create summary
    summary = create_summary(
        df,
        lower,
        upper,
        len(z_outliers),
        int(df["is_outlier_iqr"].sum())
    )

    # Save processed dataset
    df.to_csv(
        output_path,
        index=False
    )

    print("\n" + "=" * 70)
    print("OUTLIER DETECTION COMPLETE")
    print("=" * 70)

    print(
        f"Z-score outliers: "
        f"{summary['zscore_outliers']}"
    )

    print(
        f"IQR outliers: "
        f"{summary['iqr_outliers']}"
    )

    print(
        f"Combined outliers: "
        f"{summary['combined_outliers']}"
    )

    print(
        f"\nProcessed dataset saved to: "
        f"{output_path}"
    )

    print(
        "Cleaning log saved to: "
        "output/cleaning_log.csv"
    )

    print(
        "Summary saved to: "
        "output/outlier_summary.json"
    )
