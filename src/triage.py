import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def load_audit():
    with open(ROOT / "data" / "audit_report.json", "r", encoding="utf-8") as f:
        return json.load(f)


def load_schema():
    schema = {}

    for file in (ROOT / "data" / "raw").glob("*.csv"):
        df = pd.read_csv(file)
        schema[file.stem] = list(df.columns)

    return schema


def triage_question(question):
    audit = load_audit()
    schema = load_schema()
    q = question.lower()

    # Missing information
    for field in audit.get("unavailable_fields", []):
        if re.search(rf"\b{re.escape(field.lower())}\b", q):
            return {
                "decision": "refuse",
                "reason": f"'{field}' is not available in the dataset.",
                "tables": [],
                "risk_flags": ["missing_required_field"]
            }

    # Currency danger
    if any(word in q for word in ["revenue", "sales", "money", "amount"]):
        if len(audit["currency"]["order_currencies"]) > 1:
            if "total" in q:
                return {
                    "decision": "refuse",
                    "reason": "The data contains USD, EUR and INR, so a combined total is unsafe without complete conversion information.",
                    "tables": ["orders", "fx_rates"],
                    "risk_flags": ["currency_mismatch"]
                }

    # Date danger
    if any(word in q for word in
           ["march", "april", "may", "june", "july", "august", "september"]):
        if audit.get("ambiguous_dates"):
            return {
                "decision": "clarify",
                "reason": "Some dates use ambiguous formats such as DD/MM/YYYY and MM/DD/YYYY.",
                "tables": ["orders"],
                "risk_flags": ["ambiguous_dates"]
            }

    tables = []

    if any(x in q for x in ["customer", "user", "region"]):
        tables.append("customers")

    if any(x in q for x in ["order", "revenue", "sales", "total", "amount"]):
        tables.append("orders")

    if any(x in q for x in ["product", "price", "weight", "category"]):
        tables.append("products")

    if any(x in q for x in ["currency", "exchange", "usd", "eur", "inr"]):
        tables.append("fx_rates")

    return {
        "decision": "answer",
        "reason": "The question can be analyzed using the available data.",
        "tables": list(dict.fromkeys(tables)),
        "risk_flags": [
            "duplicates_present",
            "data_contradictions_present"
        ]
    }