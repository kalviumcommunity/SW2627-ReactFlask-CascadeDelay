import pandas as pd


def calculate_mau(df, days=30, reference_date=None):
    """
    Calculate Monthly Active Users.

    MAU = distinct customers with at least one transaction
    during the last N days.
    """

    if reference_date is None:
        reference_date = pd.Timestamp.now()

    reference_date = pd.Timestamp(reference_date)

    cutoff = reference_date - pd.Timedelta(days=days)

    active_customers = df[
        df["transaction_date"] >= cutoff
    ]["customer_id"].nunique()

    return active_customers


def calculate_revenue_per_customer(df):
    """
    Calculate average revenue per unique customer.

    Revenue per Customer = Total Revenue / Unique Customers
    """

    unique_customers = df["customer_id"].nunique()

    if unique_customers == 0:
        return 0.0

    return (
        df["amount"].sum()
        / unique_customers
    )


def calculate_churn_rate(
    df,
    period_days=30,
    reference_date=None
):
    """
    Calculate customer churn between two consecutive periods.

    Period 1:
        60 to 30 days before reference date

    Period 2:
        Last 30 days
    """

    if reference_date is None:
        reference_date = pd.Timestamp.now()

    reference_date = pd.Timestamp(reference_date)

    period_2_start = (
        reference_date
        - pd.Timedelta(days=period_days)
    )

    period_1_end = period_2_start

    period_1_start = (
        period_1_end
        - pd.Timedelta(days=period_days)
    )

    active_p1 = set(
        df[
            (df["transaction_date"] >= period_1_start)
            & (df["transaction_date"] < period_1_end)
        ]["customer_id"]
    )

    active_p2 = set(
        df[
            (df["transaction_date"] >= period_2_start)
            & (df["transaction_date"] <= reference_date)
        ]["customer_id"]
    )

    if len(active_p1) == 0:
        return 0.0

    churned = active_p1 - active_p2

    return len(churned) / len(active_p1)


def calculate_payment_success_rate(df):
    """
    Calculate percentage of successful payment attempts.
    """

    total_payments = len(df)

    if total_payments == 0:
        return 0.0

    successful_payments = (
        df["payment_status"]
        .eq("success")
        .sum()
    )

    return successful_payments / total_payments


def calculate_customer_acquisition_cost(
    marketing_spend,
    new_customers
):
    """
    Calculate Customer Acquisition Cost.

    CAC = Marketing Spend / New Customers
    """

    if new_customers == 0:
        return 0.0

    return marketing_spend / new_customers


def calculate_total_revenue(df):
    """
    Calculate total revenue.
    """

    return df["amount"].sum()


def calculate_unique_customers(df):
    """
    Calculate number of unique customers.
    """

    return df["customer_id"].nunique()


def calculate_revenue_by_segment(df):
    """
    Break total revenue down by customer segment.
    """

    return (
        df.groupby("customer_type")["amount"]
        .sum()
        .sort_values(ascending=False)
    )


def calculate_revenue_by_product(df):
    """
    Break total revenue down by product.
    """

    return (
        df.groupby("product")["amount"]
        .sum()
        .sort_values(ascending=False)
    )