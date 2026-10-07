def generate_code(question):

    q = question.lower()

    # -----------------------------------------
    # HIGHEST CUSTOMER ORDER TOTAL
    # -----------------------------------------

    if "highest" in q and "customer" in q:

        code = """import pandas as pd

orders = pd.read_csv("data/raw/orders.csv")
customers = pd.read_csv("data/raw/customers.csv")

orders["order_total"] = (
    orders["order_total"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

orders["order_total"] = pd.to_numeric(
    orders["order_total"],
    errors="coerce"
)

orders = orders.drop_duplicates(
    subset=["order_id"]
)

df = orders.merge(
    customers[["customer_id", "name"]],
    on="customer_id",
    how="left"
)

totals = df.groupby("name")["order_total"].sum()

result = totals.max()
winner = totals.idxmax()

print("Customer:", winner)
print("Total:", result)
"""

        return {
            "summary": "Find the customer with the highest total order value.",
            "code": code
        }


    # -----------------------------------------
    # ORDER COUNT
    # -----------------------------------------

    if (
        ("how many" in q or "number of" in q)
        and "order" in q
    ):

        code = """import pandas as pd

orders = pd.read_csv("data/raw/orders.csv")

orders = orders.drop_duplicates(
    subset=["order_id"]
)

result = len(orders)

print("Number of orders:", result)
"""

        return {
            "summary": "Count unique orders.",
            "code": code
        }


    # -----------------------------------------
    # HIGHEST REGION
    # -----------------------------------------

    # IMPORTANT:
    # This comes BEFORE the generic "total order"
    # condition so region questions are handled correctly.

    if "region" in q and "highest" in q:

        code = """import pandas as pd

orders = pd.read_csv("data/raw/orders.csv")
customers = pd.read_csv("data/raw/customers.csv")

orders["order_total"] = (
    orders["order_total"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

orders["order_total"] = pd.to_numeric(
    orders["order_total"],
    errors="coerce"
)

orders = orders.drop_duplicates(
    subset=["order_id"]
)

df = orders.merge(
    customers[["customer_id", "region"]],
    on="customer_id",
    how="left"
)

totals = df.groupby("region")["order_total"].sum()

result = totals.max()
winner = totals.idxmax()

print("Region:", winner)
print("Total:", result)
"""

        return {
            "summary": "Find the region with the highest order value.",
            "code": code
        }


    # -----------------------------------------
    # TOTAL ORDER VALUE
    # -----------------------------------------

    # Do NOT use this branch for region questions.

    if (
        "total" in q
        and "order" in q
        and "region" not in q
    ):

        code = """import pandas as pd

orders = pd.read_csv("data/raw/orders.csv")

orders["order_total"] = (
    orders["order_total"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

orders["order_total"] = pd.to_numeric(
    orders["order_total"],
    errors="coerce"
)

orders = orders.drop_duplicates(
    subset=["order_id"]
)

result = orders["order_total"].sum()

print("Total order value:", result)
"""

        return {
            "summary": "Calculate total order value after removing duplicate order rows.",
            "code": code
        }


    # -----------------------------------------
    # UNSUPPORTED QUESTION
    # -----------------------------------------

    return {
        "summary": "Question not supported by the current MVP planner.",
        "code": None
    }