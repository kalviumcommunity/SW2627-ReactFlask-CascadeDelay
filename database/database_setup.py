import pandas as pd
from sqlalchemy import create_engine, inspect, text


DATABASE_PATH = "analytics.db"
TABLE_NAME = "customers_cleaned"
INPUT_FILE = "data/processed/customers_cleaned.csv"


def load_cleaned_data_to_database(
    df,
    table_name,
    database_path=DATABASE_PATH
):
    """
    Load a cleaned DataFrame into a SQLite database.

    Parameters
    ----------
    df : pandas.DataFrame
        Cleaned customer data to load.
    table_name : str
        Name of the database table.
    database_path : str
        Path to the SQLite database file.

    Returns
    -------
    sqlalchemy.Engine
        Database engine that can be reused for queries.
    """

    engine = create_engine(f"sqlite:///{database_path}")

    # Load DataFrame into database
    df.to_sql(
        table_name,
        engine,
        if_exists="replace",
        index=False
    )

    # Validate row count
    count_query = text(
        f"SELECT COUNT(*) AS row_count FROM {table_name}"
    )

    count = pd.read_sql(count_query, engine)
    rows_loaded = int(count.iloc[0]["row_count"])

    if rows_loaded != len(df):
        raise ValueError(
            f"Row count mismatch: expected {len(df)}, "
            f"got {rows_loaded}"
        )

    print(f"✓ Loaded {rows_loaded} rows to {table_name}")

    return engine


def validate_schema(engine, table_name):
    """Inspect and validate the database table schema."""

    inspector = inspect(engine)

    if table_name not in inspector.get_table_names():
        raise ValueError(f"Table '{table_name}' does not exist.")

    columns = inspector.get_columns(table_name)

    print("\nTABLE SCHEMA:")

    for column in columns:
        nullable = "NULLABLE" if column["nullable"] else "NOT NULL"

        print(
            f"  {column['name']:20} "
            f"{str(column['type']):15} "
            f"{nullable}"
        )

    expected_types = {
        "customer_id": "INTEGER",
        "email": "VARCHAR",
        "signup_date": "DATE",
        "customer_type": "VARCHAR",
        "lifetime_value": "FLOAT",
    }

    print("\nDATATYPE VALIDATION:")

    actual_columns = {
        column["name"]: str(column["type"]).upper()
        for column in columns
    }

    for column_name, expected_type in expected_types.items():

        if column_name not in actual_columns:
            print(f"✗ {column_name}: MISSING")
            continue

        actual_type = actual_columns[column_name]

        # SQLite may represent DATE as DATETIME and FLOAT as FLOAT/REAL.
        if expected_type == "DATE":
            valid = "DATE" in actual_type or "DATETIME" in actual_type
        elif expected_type == "FLOAT":
            valid = (
                "FLOAT" in actual_type
                or "REAL" in actual_type
                or "NUMERIC" in actual_type
            )
        else:
            valid = expected_type in actual_type

        status = "✓" if valid else "✗"

        print(
            f"{status} {column_name}: "
            f"{actual_type} (expected {expected_type})"
        )


def run_queries(engine):
    """Run simple and aggregation queries."""

    # Simple SELECT query
    query = text(
        """
        SELECT *
        FROM customers_cleaned
        WHERE customer_type = 'Enterprise'
        """
    )

    results = pd.read_sql(query, engine)

    print(
        f"\nEnterprise customers retrieved: {len(results)}"
    )

    print(results.head().to_string(index=False))

    # Aggregation query
    query_agg = text(
        """
        SELECT
            customer_type,
            COUNT(*) AS count,
            AVG(lifetime_value) AS avg_ltv
        FROM customers_cleaned
        GROUP BY customer_type
        ORDER BY avg_ltv DESC
        """
    )

    summary = pd.read_sql(query_agg, engine)

    print("\nSUMMARY BY SEGMENT:")
    print(summary.to_string(index=False))


def main():

    print("=" * 60)
    print("DATABASE SINGLE SOURCE OF TRUTH")
    print("=" * 60)

    # ---------------------------------------
    # TASK 1: Load cleaned data
    # ---------------------------------------

    df_clean = pd.read_csv(INPUT_FILE)

    df_clean["signup_date"] = pd.to_datetime(
        df_clean["signup_date"]
    )

    print(f"\n✓ Cleaned data loaded: {len(df_clean)} rows")

    # ---------------------------------------
    # TASK 1: Setup database connection
    # ---------------------------------------

    engine = create_engine(
        f"sqlite:///{DATABASE_PATH}"
    )

    with engine.connect():
        print("✓ Database connection successful")

    print(
        f"✓ Connection string: "
        f"sqlite:///{DATABASE_PATH}"
    )

    # ---------------------------------------
    # TASK 2: Load DataFrame
    # ---------------------------------------

    engine = load_cleaned_data_to_database(
        df_clean,
        TABLE_NAME,
        DATABASE_PATH
    )

    inspector = inspect(engine)

    print("\nDATABASE TABLES:")
    print(inspector.get_table_names())

    # ---------------------------------------
    # TASK 3: Validate schema
    # ---------------------------------------

    validate_schema(
        engine,
        TABLE_NAME
    )

    # ---------------------------------------
    # TASK 4: Query database
    # ---------------------------------------

    run_queries(engine)

    # ---------------------------------------
    # Final verification
    # ---------------------------------------

    final_count = pd.read_sql(
        text(
            "SELECT COUNT(*) AS count "
            "FROM customers_cleaned"
        ),
        engine
    )

    print(
        f"\n✓ Final database row count: "
        f"{final_count.iloc[0]['count']}"
    )

    print("\n✓ ALL DATABASE TASKS COMPLETED")


if __name__ == "__main__":
    main()
