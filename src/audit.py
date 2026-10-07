import pandas as pd
import json
from pathlib import Path


DATA_DIR = Path("data/raw")


def audit_csv(path):
    df = pd.read_csv(path)

    report = {
        "file": str(path),
        "rows": len(df),
        "columns": list(df.columns),
        "missing_values": {},
        "duplicate_rows": int(df.duplicated().sum()),
        "column_types": {},
        "currency_values": {},
    }

    # -------------------------
    # 1. Missing values
    # -------------------------
    for column in df.columns:
        missing = int(df[column].isna().sum())

        if missing > 0:
            report["missing_values"][column] = missing

        report["column_types"][column] = str(df[column].dtype)

    # -------------------------
    # 2. Currency detection
    # -------------------------
    for column in df.columns:
        if "currency" in column.lower():
            values = (
                df[column]
                .dropna()
                .astype(str)
                .str.upper()
                .unique()
                .tolist()
            )

            report["currency_values"][column] = values

    return report


def audit_all_data():
    reports = []

    for path in DATA_DIR.glob("*.csv"):
        try:
            reports.append(audit_csv(path))
        except Exception as e:
            reports.append({
                "file": str(path),
                "error": str(e)
            })

    return reports


if __name__ == "__main__":
    reports = audit_all_data()

    output_path = Path("data/audit_report.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)

    print(f"Audit complete.")
    print(f"Report saved to: {output_path}")
    print()
    print(json.dumps(reports, indent=2))