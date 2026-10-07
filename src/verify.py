import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def load_orders():

    return pd.read_csv(
        ROOT / "data" / "raw" / "orders.csv"
    )


def clean_order_totals(df):

    df = df.copy()

    df["order_total"] = (
        df["order_total"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )

    df["order_total"] = pd.to_numeric(
        df["order_total"],
        errors="coerce"
    )

    return df


def independent_customer_answer():

    orders = clean_order_totals(
        load_orders()
    )

    customers = pd.read_csv(
        ROOT / "data" / "raw" / "customers.csv"
    )

    # Remove duplicate order IDs independently.
    orders = orders.drop_duplicates(
        subset=["order_id"]
    )

    df = orders.merge(
        customers[
            ["customer_id", "name"]
        ],
        on="customer_id",
        how="left"
    )

    totals = (
        df.groupby("name")["order_total"]
        .sum()
    )

    customer = totals.idxmax()
    total = float(totals.max())

    return customer, total


def independent_region_answer():

    orders = clean_order_totals(
        load_orders()
    )

    customers = pd.read_csv(
        ROOT / "data" / "raw" / "customers.csv"
    )

    orders = orders.drop_duplicates(
        subset=["order_id"]
    )

    df = orders.merge(
        customers[
            ["customer_id", "region"]
        ],
        on="customer_id",
        how="left"
    )

    totals = (
        df.groupby("region")["order_total"]
        .sum()
    )

    region = totals.idxmax()
    total = float(totals.max())

    return region, total


def independent_order_count():

    orders = load_orders()

    return int(
        orders["order_id"].nunique()
    )


def independent_order_total():

    orders = clean_order_totals(
        load_orders()
    )

    orders = orders.drop_duplicates(
        subset=["order_id"]
    )

    return float(
        orders["order_total"].sum()
    )


def verify_customer(output):

    expected_customer, expected_total = (
        independent_customer_answer()
    )

    customer_match = re.search(
        r"Customer:\s*(.+)",
        output
    )

    total_match = re.search(
        r"Total:\s*([\d,.]+)",
        output
    )

    if not customer_match or not total_match:
        return {
            "verified": False,
            "reason": "Could not read the proof output."
        }

    actual_customer = (
        customer_match.group(1).strip()
    )

    actual_total = float(
        total_match.group(1).replace(",", "")
    )

    correct_customer = (
        actual_customer == expected_customer
    )

    correct_total = (
        abs(actual_total - expected_total)
        < 0.01
    )

    return {
        "verified": (
            correct_customer
            and correct_total
        ),
        "expected_customer":
            expected_customer,
        "actual_customer":
            actual_customer,
        "expected_total":
            expected_total,
        "actual_total":
            actual_total
    }


def verify_region(output):

    expected_region, expected_total = (
        independent_region_answer()
    )

    region_match = re.search(
        r"Region:\s*(.+)",
        output
    )

    total_match = re.search(
        r"Total:\s*([\d,.]+)",
        output
    )

    if not region_match or not total_match:
        return {
            "verified": False,
            "reason": "Could not read proof output."
        }

    actual_region = (
        region_match.group(1).strip()
    )

    actual_total = float(
        total_match.group(1).replace(",", "")
    )

    return {
        "verified": (
            actual_region == expected_region
            and abs(
                actual_total - expected_total
            ) < 0.01
        ),
        "expected_region":
            expected_region,
        "actual_region":
            actual_region,
        "expected_total":
            expected_total,
        "actual_total":
            actual_total
    }


def verify_count(output):

    expected = independent_order_count()

    match = re.search(
        r"Number of orders:\s*(\d+)",
        output
    )

    if not match:

        return {
            "verified": False,
            "reason": "Could not read order count."
        }

    actual = int(match.group(1))

    return {
        "verified": actual == expected,
        "expected": expected,
        "actual": actual
    }


def verify_total(output):

    expected = independent_order_total()

    match = re.search(
        r"Total order value:\s*([\d,.]+)",
        output
    )

    if not match:

        return {
            "verified": False,
            "reason": "Could not read total."
        }

    actual = float(
        match.group(1).replace(",", "")
    )

    return {
        "verified": abs(
            actual - expected
        ) < 0.01,

        "expected": expected,
        "actual": actual
    }


def verify(question, output):

    q = question.lower()

    if (
        "highest" in q
        and "customer" in q
    ):
        return verify_customer(output)

    if (
        "highest" in q
        and "region" in q
    ):
        return verify_region(output)

    if (
    ("how many" in q or "number of" in q)
    and "order" in q
):
        return verify_count(output)

    if (
        "total" in q
        and "order" in q
    ):
        return verify_total(output)

    return {
        "verified": False,
        "reason":
            "No verifier is implemented for this question type."
    }