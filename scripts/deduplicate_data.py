import json
import os
from datetime import datetime

import pandas as pd


def detect_exact_duplicates(df):
    """
    Find rows where all values are identical.

    Returns:
        Tuple of (count, duplicate_rows_dataframe)
    """

    exact_dups = df.duplicated().sum()

    dup_rows = (
        df[df.duplicated(keep=False)]
        .sort_values(by=df.columns.tolist())
    )

    print("\nEXACT DUPLICATE DETECTION")
    print("=" * 60)
    print(f"Exact duplicates found: {exact_dups}")
    print(
        f"Total duplicate rows (including originals): "
        f"{len(dup_rows)}"
    )

    if len(dup_rows) > 0:
        print("\nSample duplicate rows:")
        print(dup_rows.head(10).to_string())

    return exact_dups, dup_rows


def detect_near_duplicates(df, key_columns):
    """
    Find rows with the same key values.

    Args:
        df: Input DataFrame
        key_columns: Columns defining uniqueness

    Returns:
        DataFrame containing records with duplicate keys.
    """

    duplicate_keys = df[
        df.duplicated(subset=key_columns, keep=False)
    ]

    print("\nNEAR-DUPLICATE DETECTION")
    print("=" * 60)
    print(
        f"Records with duplicate keys: "
        f"{len(duplicate_keys)}"
    )

    unique_key_count = len(
        duplicate_keys.groupby(key_columns)
    )

    print(
        f"Unique key combinations with duplicates: "
        f"{unique_key_count}"
    )

    if len(duplicate_keys) > 0:
        print("\nSample groups with duplicate keys:")

        for keys, group in list(
            duplicate_keys.groupby(key_columns)
        )[:3]:

            print(f"\n  Key: {keys}")
            print(f"  Records in group: {len(group)}")
            print(group.to_string())

    return duplicate_keys


def remove_exact_duplicates(df, keep="first"):
    """
    Remove exact duplicates.

    keep:
        first = keep first record
        last = keep last record
        False = remove all duplicate copies
    """

    rows_before = len(df)

    df_dedup = df.drop_duplicates(keep=keep)

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after

    if rows_before > 0:
        removal_pct = (
            rows_removed / rows_before
        ) * 100
    else:
        removal_pct = 0

    print("\nEXACT DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(
        f"Rows removed: {rows_removed:,} "
        f"({removal_pct:.2f}%)"
    )

    return df_dedup


def remove_near_duplicates(
    df,
    key_columns,
    keep_strategy="most_complete"
):
    """
    Remove near-duplicates using the selected strategy.

    Strategies:
        most_complete = keep row with fewest nulls
        first = keep first row
        last = keep last row
    """

    rows_before = len(df)

    if keep_strategy == "most_complete":

        def keep_most_complete(group):
            null_counts = group.isnull().sum(axis=1)
            best_idx = null_counts.idxmin()
            return group.loc[[best_idx]]

        df_dedup = (
            df.groupby(
                key_columns,
                as_index=False,
                group_keys=False
            )
            .apply(keep_most_complete)
            .reset_index(drop=True)
        )

    elif keep_strategy == "last":

        df_dedup = df.drop_duplicates(
            subset=key_columns,
            keep="last"
        )

    else:

        df_dedup = df.drop_duplicates(
            subset=key_columns,
            keep="first"
        )

    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after

    if rows_before > 0:
        removal_pct = (
            rows_removed / rows_before
        ) * 100
    else:
        removal_pct = 0

    print("\nNEAR-DUPLICATE REMOVAL")
    print("=" * 60)
    print(f"Keep strategy: {keep_strategy}")
    print(f"Key columns: {key_columns}")
    print(f"Rows before: {rows_before:,}")
    print(f"Rows after:  {rows_after:,}")
    print(
        f"Rows removed: {rows_removed:,} "
        f"({removal_pct:.2f}%)"
    )

    return df_dedup


def log_removed_duplicates(
    df_original,
    df_dedup
):
    """
    Save every removed record to the audit file.
    """

    removed_mask = ~df_original.index.isin(
        df_dedup.index
    )

    removed_records = df_original[removed_mask]

    print("\nAUDIT LOGGING")
    print("=" * 60)
    print(
        f"Total records removed: "
        f"{len(removed_records)}"
    )

    os.makedirs("output", exist_ok=True)

    removed_records.to_csv(
        "output/removed_duplicates_audit.csv",
        index=False
    )

    print(
        "Removed records saved to "
        "output/removed_duplicates_audit.csv"
    )

    audit_summary = {
        "removal_timestamp": datetime.now().isoformat(),
        "total_removed": int(len(removed_records)),
        "reason": "Duplicate detection and deduplication",
        "audit_file": (
            "output/removed_duplicates_audit.csv"
        ),
        "audit_note": (
            "All removed records logged for "
            "compliance and recovery if needed"
        )
    }

    with open(
        "output/dedup_audit_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            audit_summary,
            file,
            indent=2
        )

    print(
        "Audit summary saved to "
        "output/dedup_audit_summary.json"
    )

    return removed_records, audit_summary


def compare_before_after(
    df_original,
    df_dedup
):
    """
    Compare dataset before and after deduplication.
    """

    rows_before = len(df_original)
    rows_after = len(df_dedup)
    rows_removed = rows_before - rows_after

    if rows_before > 0:
        removal_percentage = round(
            (rows_removed / rows_before) * 100,
            2
        )
    else:
        removal_percentage = 0

    comparison = {
        "rows_before": rows_before,
        "rows_after": rows_after,
        "rows_removed": rows_removed,
        "removal_percentage": removal_percentage,
        "columns": len(df_original.columns),
        "nulls_before": int(
            df_original.isnull().sum().sum()
        ),
        "nulls_after": int(
            df_dedup.isnull().sum().sum()
        ),
        "timestamp": datetime.now().isoformat()
    }

    print("\n" + "=" * 70)
    print("DEDUPLICATION FINAL SUMMARY")
    print("=" * 70)
    print(
        f"Rows before: {comparison['rows_before']:,}"
    )
    print(
        f"Rows after:  {comparison['rows_after']:,}"
    )
    print(
        f"Removed:     {comparison['rows_removed']:,} "
        f"({comparison['removal_percentage']}%)"
    )
    print(
        f"\nNulls before: {comparison['nulls_before']:,}"
    )
    print(
        f"Nulls after:  {comparison['nulls_after']:,}"
    )
    print(
        f"Null change:  "
        f"{comparison['nulls_before'] - comparison['nulls_after']:,}"
    )
    print("=" * 70)

    os.makedirs("output", exist_ok=True)

    with open(
        "output/dedup_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            comparison,
            file,
            indent=2
        )

    return comparison


if __name__ == "__main__":

    input_path = "data/raw/data_with_dupes.csv"

    output_path = (
        "data/processed/deduplicated_data.csv"
    )

    os.makedirs("data/processed", exist_ok=True)

    print("\n" + "=" * 70)
    print("STARTING DEDUPLICATION WORKFLOW")
    print("=" * 70)

    # Load original dataset
    df_original = pd.read_csv(input_path)

    print(
        f"Initial record count: "
        f"{len(df_original):,}"
    )

    # Keep a working copy
    df = df_original.copy()

    # Step 1: Detect exact duplicates
    print(
        "\n[Step 1/4] "
        "Detecting exact duplicates..."
    )

    exact_count, exact_rows = (
        detect_exact_duplicates(df)
    )

    # Step 2: Detect near-duplicates
    print(
        "\n[Step 2/4] "
        "Detecting near-duplicates by key..."
    )

    near_dups = detect_near_duplicates(
        df,
        key_columns=[
            "customer_id",
            "transaction_date"
        ]
    )

    # Step 3: Remove exact duplicates
    print(
        "\n[Step 3/4] "
        "Removing exact duplicates..."
    )

    df = remove_exact_duplicates(
        df,
        keep="first"
    )

    # Step 4: Remove near-duplicates
    print(
        "\n[Step 4/4] "
        "Removing near-duplicates..."
    )

    df = remove_near_duplicates(
        df,
        key_columns=[
            "customer_id",
            "transaction_date"
        ],
        keep_strategy="most_complete"
    )

    # Audit removed records
    print(
        "\n[Audit] "
        "Logging removed records..."
    )

    log_removed_duplicates(
        df_original,
        df
    )

    # Compare original and final datasets
    compare_before_after(
        df_original,
        df
    )

    # Save final deduplicated dataset
    df.to_csv(
        output_path,
        index=False
    )

    print(
        "\nDeduplicated data saved to "
        f"{output_path}"
    )
