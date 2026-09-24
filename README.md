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

## Duplicate Detection & Record Deduplication

### Overview

Hey Data Engineer!

Welcome. Your data is validated, ingested, profiled, documented, nulls handled, and types enforced. One final problem blocks analysis: duplicates. A customer appears twice in the database. A transaction is imported twice from different sources. A row is accidentally duplicated during a merge. These exact and near-duplicates distort every metric — customer count inflates, revenue doubles, and analysis conclusions become unreliable. You must detect them, decide which version to keep, and log all removals for audit and compliance.

Every analysis broken by duplicate records, every count that did not match reality, and every KPI that stakeholders questioned had one thing in common: duplicates entered the pipeline and were never caught before analysis began. This lesson teaches you to detect and remove duplicates defensibly. You will identify exact duplicates using `.duplicated()`, find near-duplicates by key columns, implement deduplication logic preserving the best record, log all removals for audit purposes, and compare before/after metrics.

---

### The Real Scenario

#### The Problem
* **Unexpected Duplications:** A customer database contains 10,000 records. An analyst runs analysis and gets 10,500 unique customers. Where did the 500 extra come from?
* **Exact Duplicates:** Investigation reveals 250 exact duplicates where every field matches (data imported twice by mistake).
* **Near Duplicates:** Another 250 near-duplicates where the same customer is recorded under slightly different names (e.g., `JOHN` vs `JOHN SMITH`).
* **Lost Trust & Untracked Removals:** Nobody tracked which duplicates were removed. Analysis completed before duplicates were noticed. Conclusions about customer count, revenue per customer, and churn rates are all wrong. Trust erodes, and fixing requires redoing analysis without knowing what was previously removed.

#### The Solution
* A deduplication workflow that detects exact duplicates using `.duplicated()`.
* Identifies near-duplicates by matching on key columns (e.g., `customer_id` + `date`).
* Removes duplicates keeping the most complete or most recent record.
* Logs all removals to an audit file for compliance (`output/removed_duplicates_audit.csv`).
* Documents the impact with before/after row counts.
* Everything is traceable: when someone asks *"Where did that record go?"*, you can answer with certainty: *"It was a duplicate of record X, removed on date Y."*

---

### Exact vs Near Duplicates

*Identifying What to Remove and How*

* **Exact Duplicates:**
  * Every field is identical. Same `customer_id`, same transaction amount, same date.
  * Accidental import from a source system that sends data twice.
  * **Action:** Remove all but first (or most recent, or most complete depending on strategy).

* **Near Duplicates:**
  * Same key columns (`customer_id`, `transaction_date`) but different other values.
  * Same transaction recorded with slightly different amounts or descriptions.
  * **Action:** Merge into a single record or keep the most complete version based on business logic.

#### Detection and Removal Pattern

```python
import pandas as pd

# Exact duplicates
exact_dup_count = df.duplicated().sum()
df = df.drop_duplicates(keep='first')  # Keep 'first', 'last', or False to remove all

# Near-duplicates on key
dup_keys = df[df.duplicated(subset=['customer_id'], keep=False)]
df = df.drop_duplicates(subset=['customer_id'], keep='first')
```

---

### Deduplication Strategy and Audit Trail

*Keeping the Best Record and Documenting Removals*

#### Deduplication Strategies
* **Keep First:** Preserve original record. Use when the first entry is the most reliable.
* **Keep Last:** Preserve most recent record. Use when later updates are corrections.
* **Keep Most Complete:** Preserve record with fewest nulls. Use for merging incomplete data from multiple sources.
* **Decision:** Choose based on business logic. Document your choice so downstream analysts know what was kept and why.

#### Audit Trail Logging

```python
# Save every removed record
removed = df_original[~df_original.index.isin(df_dedup.index)]
removed.to_csv('output/removed_duplicates_audit.csv', index=False)

# Document impact
pct = (len(removed) / len(df_original)) * 100
print(f"Before: {len(df_original):,} rows")
print(f"After: {len(df_dedup):,} rows")
print(f"Removed: {len(removed):,} ({pct:.1f}%)")
```

> **Audit Trail Principle:** Answers *"Where is that record?"* $\rightarrow$ *"Duplicate of X, removed date Y."*

#### Before / After Comparison

Log metrics showing deduplication impact so results are traceable:

```python
comparison = {
    'rows_before': len(df_original),
    'rows_after': len(df_dedup),
    'rows_removed': len(df_original) - len(df_dedup),
    'removal_pct': round((len(df_original) - len(df_dedup)) / len(df_original) * 100, 2)
}
```

---

### Bonus Resources

* [Pandas Duplicated Documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.duplicated.html) - Complete reference for `.duplicated()` with all `keep` parameter options.
* [Record Linkage Library](https://recordlinkage.readthedocs.io/) - Probabilistic matching for detecting near-duplicates with fuzzy matching.
* [Data Quality Assessment Guide](https://www.gartner.com/en/information-technology/glossary/data-quality) - Frameworks for measuring and monitoring data quality over time.

---

## String Cleaning & Text Normalisation

### Overview

Hey Data Cleaner!

Welcome. Your data is validated and types enforced. Now comes the meticulous work of string cleaning: the spaces before names that break groupby, the inconsistent casing (`"JOHN"`, `"john"`, `"John"`) that creates three categories instead of one, and the special characters hiding in text fields. Real-world text is messy. You must clean it deliberately.

Every analyst who skipped string cleaning, who thought "close enough" was good enough, or who ran groupby aggregations on uncleaned text and got wrong segment counts had the same problem: text diversity masqueraded as data volume. This guide covers building transformation pipelines that strip whitespace, normalize casing, remove special characters with regex, standardize categorical labels using mapping dictionaries, and build reusable functions that clean any text column consistently.

---

### The Real Scenario

#### The Problem
* **Inconsistent Categorical Values:** A dataset has a `product_category` column with values like `" Electronics "`, `"electronics"`, `"ELECTRONICS"`, and `"electro nics"`. An analyst runs `.value_counts()` and expects 3 categories, but gets 7 instead, artificially inflating category counts.
* **Hidden Whitespace:** A `customer_name` column has trailing spaces (`" John "`) that break exact string matching.
* **Special Characters & Encoding Artifacts:** A city field contains characters like `"São Paulo"` or `"Montréal"` that can disappear or corrupt in certain export formats.
* **Spelling Inconsistencies:** The marketing team uses `"B2B"`, `"b2b"`, and `"B 2 B"` interchangeably.
* **Impact:** Groupby aggregations produce inaccurate results, skewing downstream analysis and business reporting.

#### The Solution
* A string cleaning pipeline that applies transformations consistently:
  * `.str.strip()` removes leading/trailing whitespace.
  * `.str.lower()` normalizes casing.
  * Regular expressions remove special characters.
  * Mapping dictionaries standardize spelling variations.
* Wrap all operations into reusable functions so the pipeline can clean future datasets reliably. Groupby operations now produce accurate, dependable counts.

---

### Why String Cleaning Matters

*Text Consistency as Data Quality Foundation*

* **Dirty Text:**
  * Whitespace variation, mixed casing, special characters, and spelling inconsistencies.
  * Groupby operations treat each variation as a separate unique category.
  * Results in inflated segment counts, unreliable aggregations, and incorrect business metrics.

* **Clean Text:**
  * Whitespace stripped, casing normalized, special characters handled, and spelling standardized.
  * Groupby operations produce accurate counts and trustworthy metrics.

#### Four String Cleaning Fundamentals

1. **Strip Whitespace:** Eliminates invisible leading/trailing noise that breaks equality and joins.
2. **Normalize Casing:** Makes text matching case-insensitive and standard across categories.
3. **Remove Special Characters:** Prevents encoding corruption and parsing discrepancies.
4. **Canonical Mapping:** Converts multiple historical spelling variants into a single standard label.

---

### Building the String Cleaning Pipeline

*Transformation Step by Step*

#### 1. Strip Whitespace
Leading and trailing spaces are invisible but break exact matching. Always remove them:

```python
df['category'] = df['category'].str.strip()
# " Electronics " -> "Electronics"
```

#### 2. Normalize Casing
Make casing consistent. Lowercase is standard for categorical comparisons:

```python
df['name'] = df['name'].str.lower()
# "John", "JOHN", "john" -> all become "john"
```

#### 3. Remove Special Characters with Regex
The regex pattern `[^a-zA-Z0-9 ]` removes anything that is not a letter, number, or space (the caret `^` inside brackets denotes negation):

```python
df['city'] = df['city'].str.replace('[^a-zA-Z0-9 ]', '', regex=True)
# "São Paulo" -> "So Paulo"
# "Montréal" -> "Montreal"
```

#### 4. Map Spelling Variations to Canonical Form
Standardize disparate variants to a single agreed-upon value:

```python
segment_map = {
    'b2b': 'B2B',
    'b 2 b': 'B2B',
    'b2 b': 'B2B',
    'business-to-business': 'B2B'
}
df['segment'] = df['segment'].map(segment_map)
```

---

### Creating a Reusable Pipeline

*Function-Based String Cleaning*

Wrap transformations in reusable functions rather than hardcoding them inline.

#### Template Pipeline Function

```python
def clean_text_column(series, 
                      lowercase=True, 
                      strip=True, 
                      remove_special=False,
                      mapping=None):
    """Reusable text cleaning function for pandas Series."""
    result = series.copy()
    
    if strip:
        result = result.str.strip()
    
    if lowercase:
        result = result.str.lower()
    
    if remove_special:
        result = result.str.replace('[^a-zA-Z0-9 ]', '', regex=True)
    
    if mapping:
        result = result.map(mapping)
    
    return result
```

#### Applying to Multiple Columns

```python
# Clean customer name with whitespace stripping and lowercasing
df['name'] = clean_text_column(df['name'], lowercase=True, strip=True)

# Standardize product categories via canonical mapping
df['category'] = clean_text_column(df['category'], mapping=category_map)
```

## Future Updates

This README will be updated after each milestone to reflect the actual features, implementation, screenshots, setup instructions, and project progress.
