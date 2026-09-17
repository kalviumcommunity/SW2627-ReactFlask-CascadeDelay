# KPI Reference Document

This document is the single source of truth for business KPI definitions.
All teams should use these definitions and computation functions when
reporting performance.

---

## KPI 1: Monthly Active Users (MAU)

**Definition:**  
Distinct customers who completed at least one transaction during the
last 30 days.

**Formula:**  
COUNT(DISTINCT customer_id) WHERE transaction_date >= reference_date - 30 days

**Data Source:**  
transactions table

**Required Columns:**  
customer_id, transaction_date

**Target Range:**  
5,000 - 6,000

**Owner:**  
Product Manager

**Update Frequency:**  
Daily

**Notes:**  
Measures customer activity and engagement. The same customer is counted
only once during the measurement window.

---

## KPI 2: Revenue per Customer

**Definition:**  
Average transaction revenue generated per unique customer during the
measurement period.

**Formula:**  
Total Revenue / Number of Unique Customers

**Data Source:**  
transactions table

**Required Columns:**  
customer_id, amount

**Target Range:**  
$90 - $110

**Owner:**  
Finance Manager

**Update Frequency:**  
Daily

**Notes:**  
Useful for understanding customer monetization. Should be interpreted
alongside customer mix because enterprise customers can generate
disproportionately high revenue.

---

## KPI 3: Churn Rate

**Definition:**  
Percentage of customers who were active during the previous 30-day
period but had no activity during the most recent 30-day period.

**Formula:**  
Customers Active in Previous Period but Inactive in Current Period
/ Customers Active in Previous Period

**Data Source:**  
transactions table

**Required Columns:**  
customer_id, transaction_date

**Target Range:**  
0% - 5%

**Owner:**  
Customer Success Manager

**Update Frequency:**  
Weekly

**Notes:**  
Lower churn indicates stronger customer retention. The measurement
window must remain consistent when comparing periods.

---

## KPI 4: Payment Success Rate

**Definition:**  
Percentage of payment attempts that completed successfully.

**Formula:**  
Successful Payments / Total Payment Attempts

**Data Source:**  
transactions table

**Required Columns:**  
payment_status

**Target Range:**  
95% - 100%

**Owner:**  
Payments/Product Manager

**Update Frequency:**  
Daily

**Notes:**  
A decline may indicate payment-provider problems, checkout issues,
or customer payment failures.

---

## KPI 5: Customer Acquisition Cost (CAC)

**Definition:**  
Average sales and marketing spend required to acquire one new customer.

**Formula:**  
Sales and Marketing Spend / Number of New Customers Acquired

**Data Source:**  
marketing and customer acquisition data

**Required Columns:**  
marketing_spend, new_customers

**Target Range:**  
$0 - $50

**Owner:**  
Growth Manager

**Update Frequency:**  
Monthly

**Notes:**  
CAC should be evaluated together with customer lifetime value and
revenue per customer.

---

## KPI Governance

These KPI definitions are the standard definitions used across Finance,
Sales, Product, and other teams.

Changes to definitions should be documented, reviewed, and version
controlled before being used in official reporting.

If the underlying data schema changes, the KPI implementation must be
updated and validated before the KPI is published.