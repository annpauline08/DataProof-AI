from pathlib import Path
import json
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


# -----------------------------------
# LOAD TABLES
# -----------------------------------

def load_tables():

    tables = {}

    for file in RAW.glob("*.csv"):

        tables[file.stem] = pd.read_csv(
            file
        )

    return tables


# -----------------------------------
# BASIC PROFILE
# -----------------------------------

def profile_table(df):

    return {
        "rows": int(len(df)),
        "columns": list(df.columns),

        "missing_cells": int(
            df.isna().sum().sum()
        ),

        "duplicate_rows": int(
            df.duplicated().sum()
        ),

        "data_types": {
            column: str(df[column].dtype)
            for column in df.columns
        }
    }


# -----------------------------------
# DUPLICATE ORDERS
# -----------------------------------

def audit_duplicate_orders(orders):

    duplicated = (
        orders["order_id"]
        .astype(str)
        .duplicated(keep=False)
    )

    ids = sorted(
        orders.loc[duplicated, "order_id"]
        .astype(str)
        .unique()
        .tolist()
    )

    return ids


# -----------------------------------
# GHOST CUSTOMERS
# -----------------------------------

def audit_customers(customers, orders):

    known_customers = set(
        customers["customer_id"]
        .astype(str)
        .str.strip()
    )

    order_customers = set(
        orders["customer_id"]
        .astype(str)
        .str.strip()
    )

    return sorted(
        order_customers - known_customers
    )


# -----------------------------------
# GHOST PRODUCTS
# -----------------------------------

def audit_products(products, orders):

    known_products = set(
        products["product_id"]
        .astype(str)
        .str.strip()
    )

    order_products = set(
        orders["product_id"]
        .astype(str)
        .str.strip()
    )

    return sorted(
        order_products - known_products
    )


# -----------------------------------
# DUPLICATE CUSTOMER IDENTITIES
# -----------------------------------

def audit_customer_identity(customers):

    normalized = (
        customers["email"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    duplicates = normalized[
        normalized.duplicated(keep=False)
    ].unique()

    return sorted(
        duplicates.tolist()
    )


# -----------------------------------
# CURRENCY AUDIT
# -----------------------------------

def audit_currency(orders, fx_rates):

    order_currencies = sorted(
        orders["currency"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
        .tolist()
    )

    fx_currencies = sorted(
        fx_rates["currency"]
        .dropna()
        .astype(str)
        .str.upper()
        .unique()
        .tolist()
    )

    return {
        "order_currencies": order_currencies,
        "fx_currencies": fx_currencies,

       "missing_fx_currencies": sorted(
    (set(order_currencies) - {"USD"})
    - set(fx_currencies)
)
    }


# -----------------------------------
# DATE AUDIT
# -----------------------------------

def audit_dates(orders):

    ambiguous_rows = []

    for index, value in orders["order_date"].items():

        value = str(value).strip()

        # Slash dates can be ambiguous.
        if re.match(
            r"^\d{1,2}/\d{1,2}/\d{4}$",
            value
        ):

            ambiguous_rows.append({
                "row": int(index),
                "value": value
            })

    return ambiguous_rows


# -----------------------------------
# UNIT AUDIT
# -----------------------------------

def audit_units(products):

    units = sorted(
        products["weight_unit"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .unique()
        .tolist()
    )

    return units


# -----------------------------------
# ORDER TOTAL CONTRADICTIONS
# -----------------------------------

def audit_order_totals(orders, products):

    merged = orders.merge(
        products[
            [
                "product_id",
                "price"
            ]
        ],
        on="product_id",
        how="left"
    )

    quantities = pd.to_numeric(
        merged["quantity"],
        errors="coerce"
    )

    totals = (
        merged["order_total"]
        .astype(str)
        .str.replace(
            "$",
            "",
            regex=False
        )
        .str.replace(
            ",",
            "",
            regex=False
        )
    )

    totals = pd.to_numeric(
        totals,
        errors="coerce"
    )

    expected = (
        quantities
        * pd.to_numeric(
            merged["price"],
            errors="coerce"
        )
    )

    mismatch = (
        expected.notna()
        & totals.notna()
        & (
            (expected - totals).abs()
            > 0.01
        )
    )

    return {
        "mismatch_count": int(
    merged.loc[mismatch, "order_id"]
    .astype(str)
    .nunique()
),

        "examples": [
            {
                "order_id": str(
                    merged.loc[i, "order_id"]
                ),
                "expected": float(
                    expected.loc[i]
                ),
                "reported": float(
                    totals.loc[i]
                )
            }

            for i in merged.index[mismatch][:5]
        ]
    }


# -----------------------------------
# FX COVERAGE
# -----------------------------------

def audit_fx_coverage(orders, fx_rates):

    parsed_dates = pd.to_datetime(
        orders["order_date"],
        errors="coerce",
        dayfirst=False
    )

    orders_months = set(
        parsed_dates
        .dropna()
        .dt.strftime("%Y-%m")
    )

    fx_months = set(
        fx_rates["month"]
        .astype(str)
    )

    return sorted(
        orders_months - fx_months
    )


# -----------------------------------
# MAIN AUDIT
# -----------------------------------

def run_audit():

    tables = load_tables()

    customers = tables["customers"]
    orders = tables["orders"]
    products = tables["products"]
    fx_rates = tables["fx_rates"]

    report = {

        "tables": {},

        "duplicate_orders":
            audit_duplicate_orders(orders),

        "ghost_customers":
            audit_customers(
                customers,
                orders
            ),

        "ghost_products":
            audit_products(
                products,
                orders
            ),

        "duplicate_customer_identities":
            audit_customer_identity(
                customers
            ),

        "currency":
            audit_currency(
                orders,
                fx_rates
            ),

        "ambiguous_dates":
            audit_dates(
                orders
            ),

        "weight_units":
            audit_units(
                products
            ),

        "order_total_contradictions":
            audit_order_totals(
                orders,
                products
            ),

        "months_without_fx_rates":
            audit_fx_coverage(
                orders,
                fx_rates
            ),

        "unavailable_fields": [
            "profit",
            "cost"
        ]
    }


    for name, df in tables.items():

        report["tables"][name] = (
            profile_table(df)
        )


    output = ROOT / "data" / "audit_report.json"

    with open(
        output,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=2
        )


    print(
        json.dumps(
            report,
            indent=2
        )
    )

    print(
        f"\nAudit saved to {output}"
    )


if __name__ == "__main__":
    run_audit()