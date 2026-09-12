# CascadeDelay

A simple logistics analytics system designed to identify operational routes that are likely to cause cascading delivery delays.

## Problem

A logistics company maintains shipment scans, delay reports, and warehouse transfer records separately. Because this information is disconnected, it is difficult to identify routes and warehouse operations that repeatedly contribute to downstream delivery delays.

## Objective

Build a simple system that combines logistics data and helps identify:

* Delayed shipments
* Frequently delayed routes
* Warehouse transfer issues
* Routes with a higher risk of cascading delays

## Tech Stack

* **Frontend:** React
* **Backend:** Flask
* **Database:** SQLite

## Project Status

🚧 **Milestone 1 — Initial Setup**

The project is currently in the initial setup stage. Features and implementation details will be added as development progresses.

## Planned Features

* Shipment and route data management
* Delay tracking
* Warehouse transfer tracking
* Route delay analysis
* Cascading delay risk identification
* Simple dashboard for viewing logistics insights

## Project Structure

```text
CascadeDelay/
├── frontend/
├── backend/
├── database/
└── README.md
```

## Getting Started

Setup instructions will be added as the project development progresses.

## CSV & JSON Data Ingestion

### Overview

Hey Data Engineer!

Welcome. Your data is validated. Now comes ingestion: loading business data from multiple formats into analysis-ready Pandas DataFrames. Datasets arrive as CSVs with varying delimiters, JSON with nested structures, and Excel sheets with multiple tabs. Each format requires different handling. 

**Key Principle:** Be explicit with parameters, never rely on defaults. Defaults hide problems until data format changes unexpectedly.

Every data project that broke unexpectedly on new data, that loaded silently wrong data, or that crashed with cryptic errors had one thing in common: ingestion made assumptions about format and trusted defaults. Ingestion must be precise across multiple formats with explicit parameters and clear documentation of what was loaded.

---

### The Real Scenario

#### The Problem
* **Unexpected Delimiters:** A CSV from a European partner uses semicolon delimiters. If a script uses default comma separation, you get one giant column instead of separated fields.
* **Nested Structures:** A JSON file has nested customer objects. Attempting direct access fails because columns are buried in nested structures.
* **Worksheet Defaults:** An Excel file has data on sheet `"Sales"`, but the script reads default `"Sheet1"` and encounters empty cells.
* **Hours Wasted:** Debugging silent failures takes hours when all these issues are preventable by specifying formats explicitly.

#### The Solution
* Write ingestion functions that accept explicit parameters for delimiter, encoding, sheet name, etc.
* Specify parameters explicitly even when using default values.
* Load, validate shape and column types, and print sample outputs.
* Document everything so stakeholders know what was loaded, turning ingestion from magic into predictable operations.

---

### Be Explicit With Every Parameter

#### Why Defaults Are Dangerous

* **Using Defaults:**
  * Assume file is comma-delimited $\rightarrow$ semicolon-delimited file loads incorrectly.
  * Assume `utf-8` $\rightarrow$ `latin-1` file loads corrupted.
  * Assume file exists $\rightarrow$ moved or missing file crashes cryptically.
  * *Silent failures are the worst of all.*

* **Being Explicit:**
  * Specify every parameter explicitly.
  * If the data format changes $\rightarrow$ immediate error with a clear message.
  * If the encoding is wrong $\rightarrow$ caught immediately at load time.
  * *Explicit is safer because failures are loud and clear.*

#### CSV Ingestion Pattern

```python
import pandas as pd

def ingest_csv(filepath, delimiter=',', encoding='utf-8'):
    """Load CSV with explicit parameters."""
    try:
        df = pd.read_csv(filepath, delimiter=delimiter, encoding=encoding)
        return df
    except UnicodeDecodeError:
        print(f"Cannot decode with {encoding}. Try: latin-1, iso-8859-1, cp1252")
        raise
```

> **Rule:** Specify the delimiter (even if comma). Specify encoding (even if utf-8). Comment why you chose those values. Explicit parameters prevent silent failures.

---

### Multi-Format Ingestion

Handling CSV, JSON, and encoding variants reliably.

#### JSON Ingestion & Nested Flattening

JSON is hierarchical, while Pandas DataFrames are tabular. Nested structures cannot become columns directly. 
**Solution:** Flatten with `pd.json_normalize()` to expand nested objects into separate columns.

```python
import pandas as pd

def ingest_json(filepath, is_nested=False):
    """Load JSON file and flatten nested objects if required."""
    df = pd.read_json(filepath)
    if is_nested:
        df = pd.json_normalize(df)
        print("✓ Flattened nested JSON")
    return df

# Example Nested Structure:
# {'customer': {'name': 'Alice'}} -> customer.name
# Becomes column 'customer.name', accessible as df['customer.name']
```

#### Encoding Fallback Strategy

Try multiple common encodings if the primary fails. This prevents pipelines from crashing on encoding mismatches.

```python
import pandas as pd

def ingest_csv_with_fallback(filepath):
    """Attempt loading CSV across multiple common encodings."""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    for enc in encodings:
        try:
            return pd.read_csv(filepath, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not load file with any encoding")
```

---

### Documenting Ingestion Output

*Creating an Audit Trail of What Was Loaded*

Always document ingestion results to create a permanent record for downstream analysts:

```python
def document_ingestion(df, source):
    """Log an audit report for ingested datasets."""
    print(f"\nINGESTION REPORT: {source}")
    print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
    print(f"\nColumn Types:")
    print(df.dtypes)
    print(f"\nFirst 3 rows:")
    print(df.head(3))
```

#### What to Check:
* **Shape:** Row and column counts verify if the dataset is of expected size (e.g., discovering 1M rows instead of 1K indicates an upstream schema/export change).
* **Dtypes:** Verifies column types match expectations (e.g., a column loaded as `string` / `object` instead of `numeric` indicates dirty data or delimiter/encoding issues).

## Future Updates

This README will be updated after each milestone to reflect the actual features, implementation, screenshots, setup instructions, and project progress.
