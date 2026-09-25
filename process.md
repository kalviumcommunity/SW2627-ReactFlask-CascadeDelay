# DataLens Process Guide

## 1. What This Project Is

DataLens is a small, local analytics application. It turns a CSV file into useful business information without requiring a cloud database or a complicated setup.

The project helps answer questions such as:

- How much revenue is in the dataset?
- How many orders and customers are present?
- Which customer segment or product appears most often?
- Are there duplicate rows or missing values?
- How does revenue change over time?
- Do the Python and SQL calculations agree?
- What important findings can be reported from the data?

The project is designed to make the journey from raw data to understandable insights visible and easy to explain.

## 2. The One Bundled Demo Dataset

The repository has one official demo dataset:

- File: `data/raw/transactions.csv`
- Purpose: Gives the application a small, repeatable dataset to show when it first opens.
- Subject: Example transaction and sales activity.
- Important columns include:
  - `transaction_id`: identifies a transaction.
  - `customer_id`: identifies the customer.
  - `transaction_date`: records when the transaction happened.
  - `amount`: records the transaction value.
  - `customer_type`: describes the customer segment.
  - `product`: describes the product.
  - `payment_status`: records whether payment succeeded or failed.

This is demonstration data, not real customer data. It lets somebody open the project and understand the complete workflow immediately.

There is no need to create several demo files. To demonstrate the application, start with this one dataset. Any other CSV can be uploaded when you want to show how the application handles a different source.

## 3. How the Project Works

The main flow is:

1. Start the Streamlit application.
2. Load the bundled demo CSV or upload another CSV.
3. Keep a copy of the raw input unchanged.
4. Profile the dataset and inspect its quality.
5. Clean the analysis copy.
6. Detect useful columns such as dates, amounts, customers, segments, and status.
7. Add date and revenue features where the required columns exist.
8. Calculate KPIs.
9. Explore distributions, trends, correlations, and segments.
10. Recalculate revenue with an in-memory SQLite query.
11. Compare the Python and SQL results.
12. Create insights, alerts, and a Markdown report.

The central implementation is in `datalens/core.py`. The Streamlit interface is in `app.py`. The command-line entry point is `run_pipeline.py`.

## 4. Step-by-Step Pipeline

### Step 1: Ingest the file

- The application reads the selected file into a Pandas DataFrame.
- CSV and JSON files are supported by the shared loader.
- The uploaded source is not edited in place.
- An empty file is rejected because there is nothing to analyse.
- Unsupported file types produce a clear error.

### Step 2: Profile the raw data

DataLens records a first view of the original input:

- Number of rows.
- Number of columns.
- Column names and data types.
- Missing values in each column.
- Number of unique values.
- Exact duplicate rows.
- Numeric summaries such as minimum, maximum, average, and median.
- Date-like columns.

This profile is important because it describes what actually arrived before any cleaning happens.

### Step 3: Clean a separate copy

The raw DataFrame is preserved. A separate analysis copy is cleaned by:

- Trimming spaces from column names.
- Converting column names to lowercase.
- Replacing spaces in column names with underscores.
- Removing exact duplicate rows.
- Trimming whitespace from text values.
- Treating blank text values as missing values.
- Filling missing numeric values with the median of that column.
- Converting columns containing date or time names when most values can be parsed as dates.

The cleaning summary reports how many rows were present before and after cleaning and how many duplicates were removed.

### Step 4: Detect useful columns

DataLens is schema-flexible. It looks for common names and aliases instead of requiring one exact schema.

Examples of recognised roles are:

- ID: `transaction_id`, `order_id`, `event_id`, or `id`.
- Customer: `customer_id`, `user_id`, or `account_id`.
- Date: `transaction_date`, `order_date`, `purchase_date`, `date`, or `timestamp`.
- Amount: `amount`, `purchase_amount`, `order_amount`, `revenue`, `total_spent`, or `lifetime_value`.
- Segment: `customer_segment`, `customer_type`, `segment`, `tier`, or `category`.
- Status: `payment_status`, `order_status`, or `status`.
- Location: `location`, `city`, `region`, or `country`.

If a column has a different name, the application also tries to recognise date-like and amount-like columns from their values and names.

### Step 5: Enrich the data

When a usable date column exists, DataLens adds:

- Year.
- Month.
- Quarter.
- Day of the week.

When a usable amount column exists, it adds a standard `revenue` value for analysis.

If a required field is not present, DataLens does not invent it. The related metric is shown as unavailable instead.

### Step 6: Calculate KPIs

The overview can calculate:

- Total revenue: the sum of the detected amount column.
- Orders: the number of analysis rows.
- Customers: the number of unique customer IDs, when available.
- Average order value: revenue divided by the number of orders.
- Payment success rate: successful statuses divided by all recognised statuses.

These values describe the uploaded file only. They are not estimates of a wider business unless the uploaded file represents the full business period.

### Step 7: Explore the data

The application provides separate workspace pages for:

- **Overview:** headline KPIs, revenue trend, and quality signal.
- **Dataset:** a preview and column data dictionary.
- **Data Quality:** missing values, duplicate rates, invalid amount checks, and cleaning results.
- **Analysis:** numeric distributions and correlations.
- **Segmentation:** record counts and revenue by a detected segment column.
- **SQL Validation:** comparison of Python revenue with SQLite revenue.
- **Insights:** findings generated from the available evidence.
- **Reports:** a Markdown report generated from the current result.
- **Alerts:** threshold and quality warnings where applicable.

Pages that require a field show an unavailable message when that field is not in the source file.

### Step 8: Validate with SQL

- The cleaned analysis data is copied into an in-memory SQLite table.
- SQL calculates the total amount again.
- The SQL result is compared with the Python result.
- A status is shown:
  - `MATCH`: the values agree within the allowed rounding tolerance.
  - `REVIEW`: the values differ and should be investigated.
  - `UNAVAILABLE`: the dataset does not contain a usable amount column.

This is a trust check. It helps catch calculation or transformation mistakes before results are presented.

### Step 9: Report the result

The report contains:

- A generated timestamp.
- Number of analysed records.
- Data quality score and status.
- Available KPIs.
- Evidence-based insights.
- Limitations caused by missing fields or limited source data.

The command-line run writes the report to `output/datalens_report.md`.

## 5. How to Accept and Process a CSV File

### What the user does in the application

1. Open the project folder in a terminal.
2. Activate the virtual environment if one exists.
3. Install the dependencies.
4. Start Streamlit.
5. Open the local URL shown in the terminal.
6. Use **Upload CSV or JSON** in the sidebar.
7. Select a CSV file from the computer.
8. Click **Process dataset**.
9. Review the pages from **Overview** through **Reports**.
10. Use **Restore demo dataset** to return to `data/raw/transactions.csv`.

### Commands

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### What makes a CSV suitable

A CSV should:

- Have a header row.
- Have at least one data row.
- Use a consistent delimiter, normally a comma.
- Use readable text encoding, preferably UTF-8.
- Keep one record per row.
- Use consistent values within each column.
- Store dates in a recognisable format such as `2025-01-31`.
- Store money or numeric values as numbers, without mixed text where possible.

For the richest demonstration, include:

- A date column.
- An amount, revenue, or value column.
- A customer or user ID column.
- A segment, customer type, product, or category column.
- A payment or order status column.

The file does not have to use the exact demo column names because the pipeline recognises common aliases. However, clearer names make the results easier to explain.

### What happens when a CSV is uploaded

- The file is read in memory.
- The original input is retained as the raw dataset.
- A separate copy is cleaned.
- Duplicate and missing-value checks are performed.
- Dates, amounts, customers, segments, and statuses are detected.
- Available metrics are calculated.
- Missing capabilities are reported instead of guessed.
- The uploaded file is not permanently changed by the application.

### Common CSV problems

- **The file is empty:** add at least one data row.
- **The file cannot be parsed:** check delimiters, quotes, and broken rows.
- **The date is not recognised:** use a consistent date format.
- **Revenue is unavailable:** add a numeric column named `amount`, `revenue`, `order_amount`, or a similar name.
- **Customer counts are unavailable:** add a customer identifier such as `customer_id`.
- **Segmentation is unavailable:** add a column such as `customer_type`, `segment`, `product`, or `category`.
- **Payment success is unavailable:** add a status column such as `payment_status` or `order_status`.

## 6. Running Without the Interface

To run the bundled demo through the same core pipeline:

```bash
python run_pipeline.py
```

This command:

- Reads `data/raw/transactions.csv`.
- Runs the complete pipeline.
- Prints the row count, quality result, and SQL validation status.
- Writes `output/datalens_report.md`.

## 7. Testing the Project

Run the automated tests with:

```bash
python -m pytest -q
```

The tests check that:

- Raw data is preserved.
- Exact duplicates are removed from the analysis copy.
- KPI calculations are correct.
- Python and SQL revenue calculations reconcile.
- Unsupported schemas report unavailable capabilities clearly.

A quick demonstration check is:

```bash
python -c "from pathlib import Path; from datalens.core import load_dataset, run_pipeline; r=run_pipeline(load_dataset(Path('data/raw/transactions.csv'))); assert r['sql']['status']=='MATCH'; print(r['kpis'])"
```

## 8. How to Explain the Project in One Minute

- DataLens accepts one CSV file at a time.
- It keeps the original data safe and creates a cleaned analysis copy.
- It automatically profiles quality and detects common business columns.
- It calculates KPIs and creates useful charts and segments when the data supports them.
- It checks the main revenue calculation with SQLite.
- It turns the result into insights and a report.
- The bundled `transactions.csv` is only a repeatable demonstration file; real users can upload their own CSV.

## 9. Important Limitations

- The quality score is a review signal, not a guarantee that the data is correct.
- Results are limited to the rows and time period in the uploaded file.
- The application does not infer missing business facts.
- A dataset without the relevant columns cannot produce every KPI.
- Uploads are processed locally and in memory by the main Streamlit workflow.
- The demo data should not be presented as real customer or financial data.
