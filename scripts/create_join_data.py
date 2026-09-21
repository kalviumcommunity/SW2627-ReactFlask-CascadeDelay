import pandas as pd
import numpy as np

np.random.seed(42)

# Customers: 1000
customers = pd.DataFrame({
    "customer_id": range(1, 1001),
    "customer_type": np.random.choice(
        ["Enterprise", "SMB", "Startup"],
        1000,
        p=[0.2, 0.5, 0.3]
    ),
    "signup_date": pd.date_range(
        "2024-01-01",
        periods=1000,
        freq="D"
    )
})

# Orders: 5000
orders = pd.DataFrame({
    "order_id": range(1, 5001),
    "customer_id": np.random.randint(1, 1001, 5000),
    "order_date": pd.date_range(
        "2025-01-01",
        periods=5000,
        freq="h"
    ),
    "order_amount": np.round(
        np.random.uniform(20, 500, 5000),
        2
    )
})

# Deliberately create 50 orphaned orders
orders.loc[4950:, "customer_id"] = np.arange(1001, 1051)

# Products: 100
products = pd.DataFrame({
    "product_id": range(1, 101),
    "product_name": [
        f"Product_{i}"
        for i in range(1, 101)
    ]
})

# Order items: 8000
order_items = pd.DataFrame({
    "order_item_id": range(1, 8001),
    "order_id": np.random.randint(1, 5001, 8000),
    "product_id": np.random.randint(1, 101, 8000),
    "quantity": np.random.randint(1, 6, 8000),
    "unit_price": np.round(
        np.random.uniform(10, 250, 8000),
        2
    )
})

# Save datasets
customers.to_csv(
    "data/raw/join_customers.csv",
    index=False
)

orders.to_csv(
    "data/raw/join_orders.csv",
    index=False
)

order_items.to_csv(
    "data/raw/join_order_items.csv",
    index=False
)

products.to_csv(
    "data/raw/join_products.csv",
    index=False
)

print("✓ DATASETS CREATED")
print(f"Customers: {len(customers)}")
print(f"Orders: {len(orders)}")
print(f"Order items: {len(order_items)}")
print(f"Products: {len(products)}")
print(
    f"Orphaned orders: "
    f"{(orders['customer_id'] > 1000).sum()}"
)
