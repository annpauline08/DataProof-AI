from pathlib import Path
import csv
import json
import random
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

RAW.mkdir(parents=True, exist_ok=True)

rng = random.Random(42)

# -------------------------
# CUSTOMERS
# -------------------------

customers = []

for i in range(1, 31):
    customers.append({
        "customer_id": f"C{i:04d}",
        "name": f"Customer {i}",
        "email": f"user{i}@example.com",
        "region": ["North", "South", "East", "West"][(i - 1) % 4]
    })

# Duplicate identity trap
customers[4]["email"] = "USER5@EXAMPLE.COM"

customers.append({
    "customer_id": "C0031",
    "name": "Customer 5 Duplicate",
    "email": "user5@example.com",
    "region": "North"
})

# -------------------------
# PRODUCTS
# -------------------------

products = []

for i in range(1, 11):
    products.append({
        "product_id": f"P{i:03d}",
        "name": f"Product {i}",
        "category": ["Tech", "Office", "Home"][i % 3],
        "price": [25, 40, 75, 120, 250][i % 5],
        "weight": [0.5, 1, 2, 4, 6][i % 5],
        "weight_unit": "kg" if i % 2 else "lb"
    })

# -------------------------
# ORDERS
# -------------------------

orders = []

start_date = date(2025, 1, 5)

for i in range(1, 121):

    order_id = f"O{i:05d}"

    customer = customers[rng.randrange(0, 30)]
    product = products[rng.randrange(len(products))]

    order_date = start_date + timedelta(
        days=rng.randrange(0, 270)
    )

    quantity = rng.randint(1, 4)

    true_total = round(
        quantity * product["price"],
        2
    )

    currency = ["USD", "EUR", "INR"][i % 3]

    # Date-format traps
    date_text = order_date.isoformat()

    if i in {12, 13, 14}:
        date_text = order_date.strftime("%d/%m/%Y")

    elif i in {15, 16}:
        date_text = order_date.strftime("%m/%d/%Y")

    # Wrong totals in first 60 orders
    if i <= 60:
        shown_total = round(true_total * 1.05, 2)
    else:
        shown_total = true_total

    # Currency formatting trap
    if i % 4 == 0:
        total_text = f"${shown_total:,.2f}"
    else:
        total_text = f"{shown_total:,.2f}"

    # Ghost customer
    customer_id = customer["customer_id"]

    if i == 77:
        customer_id = "C9999"

    orders.append({
        "order_id": order_id,
        "customer_id": customer_id,
        "product_id": product["product_id"],
        "order_date": date_text,
        "quantity": quantity,
        "currency": currency,
        "order_total": total_text
    })

# Duplicate order
orders.append(orders[20].copy())

# Ghost product
orders[88]["product_id"] = "P9999"

# Missing quantity
orders[99]["quantity"] = ""

# -------------------------
# FX RATES
# -------------------------

fx_rates = []

# Rates only available January to June
for month in range(1, 7):

    fx_rates.append({
        "month": f"2025-{month:02d}",
        "currency": "EUR",
        "rate_to_usd": 1.08
    })

    fx_rates.append({
        "month": f"2025-{month:02d}",
        "currency": "INR",
        "rate_to_usd": 0.012
    })

# -------------------------
# SAVE CSV FILES
# -------------------------

def write_csv(filename, rows):

    path = RAW / filename

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)


write_csv("customers.csv", customers)
write_csv("products.csv", products)
write_csv("orders.csv", orders)
write_csv("fx_rates.csv", fx_rates)

# -------------------------
# GROUND TRUTH
# -------------------------

ground_truth = {

    "seed": 42,

    "wrong_order_totals": 60,

    "duplicate_order_count": 1,

    "ghost_customer_ids": [
        "C9999"
    ],

    "ghost_product_ids": [
        "P9999"
    ],

    "duplicate_identity_emails": [
        "user5@example.com"
    ],

    "weight_units": [
        "kg",
        "lb"
    ],

    "fx_available_until": "2025-06",

    "missing_fields": [
        "profit",
        "cost"
    ]
}

with open(
    ROOT / "data" / "ground_truth.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        ground_truth,
        file,
        indent=2
    )

print(
    "Wrote ['customers.csv', 'fx_rates.csv', "
    "'orders.csv', 'products.csv'] + ground_truth.json"
)