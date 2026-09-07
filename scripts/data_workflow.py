"""Run a reusable CSV data-processing workflow from the command line."""

from pathlib import Path

import pandas as pd


def ingest_data(filepath: str | Path) -> pd.DataFrame:
    """Load CSV data into a Pandas DataFrame.

    Input: A path to a readable CSV file with a header row.
    Output: A Pandas DataFrame containing the source data.
    Assumptions/constraints: The file must exist and be valid CSV.
    """
    # Read raw data without modifying it during ingestion.
    return pd.read_csv(filepath)


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw data and return an analysis-ready DataFrame.

    Input: A Pandas DataFrame with possible duplicates or missing numeric values.
    Output: A new DataFrame with duplicates removed and numeric nulls filled.
    Assumptions/constraints: Missing text values remain unchanged.
    """
    # Copy the cleaned data so the original DataFrame is not modified.
    cleaned = df.drop_duplicates().copy()

    # Fill missing numeric values with each column's median.
    for column in cleaned.select_dtypes(include="number").columns:
        cleaned[column] = cleaned[column].fillna(cleaned[column].median())

    return cleaned


def output_results(df: pd.DataFrame, output_path: str | Path) -> None:
    """Save processed data to CSV and print a success summary.

    Input: A processed DataFrame and an output CSV path.
    Output: None; writes a CSV file and prints confirmation.
    Assumptions/constraints: The script must have permission to write the file.
    """
    destination = Path(output_path)

    # Create the output directory automatically if it does not exist.
    destination.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(destination, index=False)

    print("✓ Data successfully processed")
    print(f"✓ Rows processed: {len(df)}")
    print(f"✓ Output saved to {destination}")


def main() -> None:
    """Run ingestion, processing, and output using project-relative paths.

    Input: None.
    Output: None; creates output/processed.csv.
    Assumptions/constraints: data/raw/sample.csv must exist.
    """
    # Resolve paths from this file so the script works from either directory.
    project_root = Path(__file__).resolve().parents[1]

    raw_data = ingest_data(project_root / "data/raw/sample.csv")
    processed_data = process_data(raw_data)
    output_results(processed_data, project_root / "output/processed.csv")


if __name__ == "__main__":
    main()