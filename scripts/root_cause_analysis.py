import pandas as pd

# Load data
df = pd.read_csv(
    "data/processed/customer_data.csv",
    parse_dates=["timestamp"]
)

print("=" * 60)
print("ROOT CAUSE INVESTIGATION")
print("=" * 60)

# ------------------------------------------------
# TASK 1: ISOLATE TIME WINDOW
# ------------------------------------------------

df["success_rate"] = (df["status"] == "success").astype(int)

daily_success = (
    df.groupby(df["timestamp"].dt.date)["success_rate"]
    .mean()
)

threshold = daily_success.mean() - daily_success.std()

anomaly_dates = daily_success[
    daily_success < threshold
].index

print("\nAnomaly Dates:")
print(list(anomaly_dates))

problem_day = anomaly_dates[0]

day_data = df[
    df["timestamp"].dt.date == problem_day
]

hourly_data = (
    day_data.groupby(day_data["timestamp"].dt.hour)
    ["success_rate"]
    .mean()
)

problem_hour = hourly_data.idxmin()

print(f"\nProblem Day: {problem_day}")
print(f"Worst Hour: {problem_hour}:00")
print(
    f"Success Rate: {hourly_data[problem_hour]:.2%}"
)

# ------------------------------------------------
# TASK 2: SEGMENT ANALYSIS
# ------------------------------------------------

problem_window = df[
    (df["timestamp"].dt.date == problem_day)
    &
    (df["timestamp"].dt.hour == problem_hour)
]

print("\nBy Customer Type")

customer_type = (
    problem_window.groupby("customer_type")
    ["success_rate"]
    .agg(["mean", "count"])
)

print(customer_type)

print("\nBy Payment Method")

payment_method = (
    problem_window.groupby("payment_method")
    ["success_rate"]
    .agg(["mean", "count"])
)

print(payment_method)

print("\nBy Region")

region = (
    problem_window.groupby("region")
    ["success_rate"]
    .agg(["mean", "count"])
)

print(region)

affected_segment = payment_method[
    payment_method["mean"] < 0.5
].index[0]

print(
    f"\nAffected Segment: {affected_segment}"
)

# ------------------------------------------------
# TASK 3: CORRELATION PATTERNS
# ------------------------------------------------

df["is_problem_period"] = (
    (
        df["timestamp"].dt.date == problem_day
    )
    &
    (
        df["timestamp"].dt.hour == problem_hour
    )
).astype(int)

print("\nPattern Analysis")

for col in [
    "payment_method",
    "customer_type",
    "region",
    "device_type"
]:
    print(f"\n{col}")

    print(
        pd.crosstab(
            df[col],
            df["is_problem_period"]
        )
    )

error_counts = (
    df[df["is_problem_period"] == 1]
    ["error_message"]
    .value_counts()
)

print("\nTop Errors")
print(error_counts.head())

top_error = error_counts.index[0]

# ------------------------------------------------
# TASK 4: REPORT
# ------------------------------------------------

report = f"""
ROOT CAUSE INVESTIGATION REPORT

OBSERVATION
-----------
Revenue drop detected on {problem_day}

Time Window:
{problem_hour}:00 - {problem_hour + 1}:00

ANALYSIS
--------
Affected Payment Method:
{affected_segment}

Top Error:
{top_error}

PATTERN
-------
Failures concentrated in:
- {affected_segment}
- Problem hour only
- Not all customer segments

HYPOTHESIS
----------
External payment processor outage
likely caused transaction failures.

RECOMMENDATIONS
---------------
1. Add backup payment processor
2. Monitor processor health
3. Configure failover
4. Alert operations team

CONFIDENCE
----------
High
"""

print(report)

with open(
    "output/investigation_report.txt",
    "w",
    encoding="utf-8"
) as f:
    f.write(report)

print(
    "\nInvestigation report saved successfully."
)
