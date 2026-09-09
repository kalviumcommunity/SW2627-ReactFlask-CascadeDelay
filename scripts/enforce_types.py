import os

import pandas as pd
import numpy as np


def cast_columns_to_types(df, type_mapping):
    """
    Explicitly cast columns to correct dtypes.

    Args:
        df: Input DataFrame
        type_mapping: Dict of {column: target_dtype}

    Returns:
        Tuple of (DataFrame with corrected types, conversion log)
    """
    df_typed = df.copy()
    conversion_log = {}

    for col, target_dtype in type_mapping.items():
        if col not in df.columns:
            print(f"Warning: Column {col} not found in DataFrame")
            continue

        original_dtype = df[col].dtype

        try:
            df_typed[col] = df_typed[col].astype(target_dtype)
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "success",
            }
            print(f"✓ {col}: {original_dtype} → {target_dtype}")
        except Exception as e:
            conversion_log[col] = {
                "from": str(original_dtype),
                "to": str(target_dtype),
                "status": "failed",
                "error": str(e),
            }
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed, conversion_log


def convert_string_dates_to_datetime(df, date_columns, date_format=None):
    """
    Convert string columns to datetime with explicit format.

    Args:
        df: Input DataFrame
        date_columns: List of column names containing dates
        date_format: Datetime format string, e.g. '%Y-%m-%d'

    Returns:
        DataFrame with datetime columns converted.
    """
    df_typed = df.copy()

    for col in date_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            if not date_format:
                raise ValueError(
                    "date_format must be explicitly specified for date conversion"
                )

            df_typed[col] = pd.to_datetime(
                df_typed[col],
                format=date_format,
            )

            print(f"✓ {col}: Converted to datetime")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            print(f"  Sample values: {df[col].head(3).tolist()}")
            print(f"  Expected format: {date_format}")
            raise

    return df_typed


def convert_currency_to_float(df, currency_columns):
    """
    Strip currency symbols and convert values to float.

    Example: '$150.50' → 150.50

    Args:
        df: Input DataFrame
        currency_columns: List of column names with currency.

    Returns:
        DataFrame with clean numeric columns.
    """
    df_typed = df.copy()

    for col in currency_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            original_nulls = df[col].isnull().sum()

            cleaned = (
                df_typed[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .str.strip()
            )

            df_typed[col] = pd.to_numeric(cleaned, errors="coerce").astype(float)

            failed_conversions = (
                df_typed[col].isnull().sum() - original_nulls
            )

            if failed_conversions > 0:
                print(
                    f"⚠ {col}: {failed_conversions} values "
                    "could not be converted to numeric"
                )

            print(f"✓ {col}: Stripped symbols, converted to float")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed


def convert_integers_to_boolean(df, boolean_columns):
    """
    Convert 0/1 or yes/no columns to proper boolean type.

    Args:
        df: Input DataFrame
        boolean_columns: List of column names with binary values.

    Returns:
        DataFrame with bool columns.
    """
    df_typed = df.copy()

    for col in boolean_columns:
        if col not in df.columns:
            print(f"Warning: Column {col} not found")
            continue

        try:
            unique_vals = df[col].dropna().unique()
            print(f"  {col} unique values: {unique_vals}")

            if df[col].dtype == "object":
                mapping = {
                    "yes": True,
                    "no": False,
                    "y": True,
                    "n": False,
                    "true": True,
                    "false": False,
                    "1": True,
                    "0": False,
                    1: True,
                    0: False,
                    True: True,
                    False: False,
                }

                normalized = df_typed[col].map(mapping)

                unknown_values = (
                    df_typed.loc[
                        df_typed[col].notna() & normalized.isna(),
                        col,
                    ]
                    .unique()
                    .tolist()
                )

                if unknown_values:
                    raise ValueError(
                        f"Unknown boolean values in {col}: {unknown_values}"
                    )

                df_typed[col] = normalized.astype(bool)

            else:
                invalid_values = set(unique_vals) - {0, 1}

                if invalid_values:
                    raise ValueError(
                        f"Expected only 0/1 values in {col}, "
                        f"found {invalid_values}"
                    )

                df_typed[col] = df_typed[col].astype(bool)

            print(f"✓ {col}: Converted to boolean")

        except Exception as e:
            print(f"✗ {col}: Conversion failed - {e}")
            raise

    return df_typed


def compare_dtypes(df_original, df_typed):
    """
    Compare dtypes before and after conversion.

    Returns:
        DataFrame summarizing dtype changes.
    """
    comparison = pd.DataFrame(
        {
            "column": df_original.columns,
            "dtype_before": df_original.dtypes.values,
            "dtype_after": df_typed.dtypes.values,
            "changed": (
                df_original.dtypes != df_typed.dtypes
            ).values,
        }
    )

    print("\n" + "=" * 70)
    print("DTYPE CONVERSION SUMMARY")
    print("=" * 70)
    print(comparison.to_string(index=False))

    os.makedirs("output", exist_ok=True)
    comparison.to_csv(
        "output/dtype_conversion_report.csv",
        index=False,
    )

    print("\nReport saved to output/dtype_conversion_report.csv")
    print("=" * 70)

    return comparison


if __name__ == "__main__":
    # Load data
    df = pd.read_csv("data/raw/untyped_data.csv")

    print("=" * 70)
    print("BEFORE TYPE CONVERSION")
    print("=" * 70)
    print(df.dtypes)
    print("\nSample data:")
    print(df.head(3))

    df_typed = df.copy()

    # Convert dates
    print("\n1. Converting date columns...")
    df_typed = convert_string_dates_to_datetime(
        df_typed,
        ["transaction_date", "signup_date"],
        date_format="%Y-%m-%d",
    )

    # Convert currency
    print("\n2. Converting currency columns...")
    df_typed = convert_currency_to_float(
        df_typed,
        ["amount", "revenue"],
    )

    # Convert booleans
    print("\n3. Converting boolean columns...")
    df_typed = convert_integers_to_boolean(
        df_typed,
        ["is_active", "is_premium"],
    )

    # Compare
    print("\n4. Comparing before/after types...")
    print("=" * 70)
    print("AFTER TYPE CONVERSION")
    print("=" * 70)
    print(df_typed.dtypes)
    print("\nSample data:")
    print(df_typed.head(3))

    compare_dtypes(df, df_typed)

    # Save typed data
    os.makedirs("data/processed", exist_ok=True)

    df_typed.to_csv(
        "data/processed/typed_data.csv",
        index=False,
    )

    print(
        "\n✓ Typed data saved to "
        "data/processed/typed_data.csv"
    )