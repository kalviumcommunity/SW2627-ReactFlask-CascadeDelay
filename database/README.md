# Database Single Source of Truth

## Purpose

The database provides a centralized source of truth for cleaned customer data.
Instead of keeping different cleaned datasets in notebooks or sharing CSV files,
analyses can query the same database table.

## Database Connection

This project uses SQLite because it is file-based and requires zero server setup.

Connection string:

    sqlite:///analytics.db

No credentials are hardcoded.

For production or multi-user environments, PostgreSQL would be more appropriate:

    postgresql://username:password@localhost:5432/analytics

Credentials should be supplied through environment variables or a secure
configuration system rather than committed to source control.

## SQLite vs PostgreSQL

### SQLite

- File-based database
- No server required
- Easy to set up
- Suitable for local analysis, prototypes, and small applications
- Limited concurrent write capabilities

### PostgreSQL

- Server-based relational database
- Supports multiple concurrent users and applications
- Better suited to production systems and larger datasets
- Provides stronger production database features and access control

## SQLAlchemy

SQLAlchemy provides a database abstraction layer between Python and the
database.

The `create_engine()` function creates the database connection interface:

    engine = create_engine("sqlite:///analytics.db")

This allows Python code to work with the database without directly managing
low-level database connections.

## pandas Database Functions

### pd.to_sql()

`DataFrame.to_sql()` loads a pandas DataFrame into a database table.

Example:

    df.to_sql(
        "customers_cleaned",
        engine,
        if_exists="replace",
        index=False
    )

Important parameters:

- Table name: destination database table
- `engine`: SQLAlchemy database engine
- `if_exists="replace"`: replaces the existing table during the initial load
- `index=False`: prevents the pandas index from becoming a database column

### pd.read_sql()

`pd.read_sql()` executes a SQL query and returns the results as a pandas
DataFrame.

Example:

    results = pd.read_sql(
        "SELECT * FROM customers_cleaned",
        engine
    )

This allows existing Python analyses to query the centralized database.

## Schema Validation

Schema validation checks that:

- Required columns exist
- Column data types are correct
- Nullability is understood
- The database table exists
- The number of loaded rows matches the source DataFrame

This matters because analyses depend on consistent column names and data
types. Unexpected schema changes can cause incorrect calculations or failed
queries.

The project uses SQLAlchemy's `inspect()` function to inspect the database
schema.

## Schema Evolution

When the data structure changes, the database schema should be updated in a
controlled way.

Examples include:

- Adding a new column
- Renaming an existing column
- Changing a data type
- Removing an obsolete column

Schema changes should be documented and tested before being used by
downstream analyses.

For a simple SQLite workflow, the table can be recreated during controlled
initial loads. For production PostgreSQL systems, schema migrations should
normally be used so changes can be tracked and applied consistently.

## Repeatable Loading

The `load_cleaned_data_to_database()` function in
`database_setup.py` provides a reusable loading process.

It:

1. Creates the database engine
2. Loads the DataFrame into the requested table
3. Validates the number of rows loaded
4. Returns the SQLAlchemy engine for further queries

This makes database loading repeatable instead of requiring manual notebook
steps.
