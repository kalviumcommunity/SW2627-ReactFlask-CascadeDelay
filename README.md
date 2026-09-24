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

---

## Outlier Detection with Statistical Methods

### Overview

Hey Statistical Analyst!

Welcome. Time features are extracted. Now comes outlier detection: the $10,000 transaction when typical is $50, the 99-hour work week when normal is 40, or the product return rate of 95% when others are 5%. These anomalies distort averages and break statistical assumptions. You must detect them statistically, decide whether to cap, remove, or flag, and log every decision for audit and reproducibility.

Every analyst who ignored outliers and got skewed statistics, who silently removed anomalies without documentation, or who capped values incorrectly had the same problem: they treated outlier detection as optional cleanup instead of intentional decision-making. This guide covers statistical detection: implementing Z-score and IQR methods, applying distinct handling strategies per column, flagging anomalies with binary columns, and documenting decisions in an audit log.

---

### The Real Scenario

#### The Problem
* **Skewed Summary Statistics:** A salary dataset has one executive earning $2M when the company average is $65k. An employee has 150 vacation days when the company max is 30. A customer spent $50,000 on a website where the average order is $500.
* **Distorted Downstream Metrics:** Mean salary becomes severely inflated and median metrics become misleading; average customer spend fails to represent typical behavior.
* **Undocumented Decisions:** When anomalies are dropped or modified without record, downstream analysts cannot reproduce the results or understand if extreme values were dropped, capped, or ignored.

#### The Solution
* Detect outliers using statistical rigor:
  * **Z-Score:** Measuring how many standard deviations a value lies from the mean.
  * **Interquartile Range (IQR):** Identifying values falling 1.5 times beyond the IQR boundaries ($Q1 - 1.5 \times IQR$ and $Q3 + 1.5 \times IQR$).
* Choose an intentional strategy per column:
  * **Cap:** Preserves rows while bounding extreme influence.
  * **Remove:** Eliminates invalid rows or collection errors.
  * **Flag:** Retains all data while marking anomalies for segmented downstream analysis.
* Document every decision in an audit log (`output/cleaning_log.csv`) detailing the column, method, action taken, and row count.

---

### Outlier Detection Methods

*Z-Score vs Interquartile Range*

| Method | Definition / Formula | Distribution Assumption | Sensitivity & Best Use |
| :--- | :--- | :--- | :--- |
| **Z-Score** | $Z = \frac{x - \mu}{\sigma}$ (Values where $|Z| > 3$) | Assumes normal distribution | Sensitive to extreme outliers that pull the mean; best on normally distributed, scaled data |
| **IQR** | Boundaries: $[Q1 - 1.5 \times IQR, Q3 + 1.5 \times IQR]$ | Distribution-free | Robust and resistant to extreme values; best for skewed data |

#### Detection & Decision Making Code

```python
import numpy as np
import pandas as pd
from scipy import stats

# 1. Z-Score Detection
z_scores = np.abs(stats.zscore(df['salary']))
df['outlier_zscore'] = z_scores > 3

# 2. IQR Detection
Q1 = df['salary'].quantile(0.25)
Q3 = df['salary'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

df['outlier_iqr'] = (df['salary'] < lower_bound) | (df['salary'] > upper_bound)
```

---

### Handling Outliers: Three Strategies

*Cap, Remove, or Flag*

#### Strategy 1: Cap at Boundaries (Winsorizing)
Extreme values are replaced with boundary limits. This preserves row count while restricting undue leverage on summary statistics:

```python
# Values below lower_bound become lower_bound; values above upper_bound become upper_bound
df['salary_capped'] = df['salary'].clip(lower=lower_bound, upper=upper_bound)
```

#### Strategy 2: Remove Rows
Eliminate the entire row if an outlier is identified. Use only when rows represent verified errors, faulty instrumentation, or invalid records:

```python
# Keep only rows where outlier_iqr is False
df_clean = df[~df['outlier_iqr']]
```

#### Strategy 3: Flag with Binary Column
Preserve raw data intact, adding a boolean indicator so downstream models or dashboards can segment or treat anomalies separately:

```python
# Keep all data, mark anomalies separately
df['is_salary_outlier'] = df['outlier_iqr'].astype(int)
```

---

### Documenting Decisions: The Cleaning Log

Create an audit log (`output/cleaning_log.csv`) capturing column name, method, action taken, threshold values, affected row count, and timestamp:

```python
cleaning_log = [
    {
        "column": "salary",
        "method": "IQR",
        "action": "cap",
        "threshold_lower": lower_bound,
        "threshold_upper": upper_bound,
        "affected_rows": int(df['outlier_iqr'].sum()),
        "timestamp": pd.Timestamp.now().isoformat()
    }
]

log_df = pd.DataFrame(cleaning_log)
log_df.to_csv("output/cleaning_log.csv", index=False)
```

---

### Bonus Resources

* [SciPy Stats zscore Documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.zscore.html) - Documentation for computing standard scores.
* [Pandas DataFrame.clip Documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.clip.html) - Reference for capping numerical values at lower/upper thresholds.
* [NIST Engineering Statistics: Detection of Outliers](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm) - Foundational statistical guide on outlier detection rules and strategies.

## Future Updates

This README will be updated after each milestone to reflect the actual features, implementation, screenshots, setup instructions, and project progress.
