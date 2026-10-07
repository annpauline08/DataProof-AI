import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


# Things proof code is NOT allowed to use.
FORBIDDEN_IMPORTS = {
    "os",
    "subprocess",
    "socket",
    "shutil",
    "requests",
    "urllib",
    "http",
    "ftplib",
    "pathlib",
}

FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "input",
}


def validate_code(code):
    """
    Check the generated proof code before executing it.
    """

    tree = ast.parse(code)

    for node in ast.walk(tree):

        # Check imports
        if isinstance(node, ast.Import):

            for alias in node.names:

                name = alias.name.split(".")[0]

                if name in FORBIDDEN_IMPORTS:
                    raise ValueError(
                        f"Blocked import: {name}"
                    )

        if isinstance(node, ast.ImportFrom):

            module = (node.module or "").split(".")[0]

            if module in FORBIDDEN_IMPORTS:
                raise ValueError(
                    f"Blocked import: {module}"
                )

        # Check dangerous function calls
        if isinstance(node, ast.Call):

            if isinstance(node.func, ast.Name):

                if node.func.id in FORBIDDEN_CALLS:
                    raise ValueError(
                        f"Blocked function: {node.func.id}"
                    )

        # Block dangerous dunder access
        if isinstance(node, ast.Attribute):

            if node.attr.startswith("__"):
                raise ValueError(
                    f"Blocked attribute: {node.attr}"
                )

        # Make sure pandas file reads stay inside our data folder
        if isinstance(node, ast.Call):

            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "pd"
                and node.func.attr in {"read_csv", "read_excel"}
            ):

                if not node.args:
                    raise ValueError(
                        "Data file path is required."
                    )

                first_arg = node.args[0]

                if isinstance(first_arg, ast.Constant):

                    path = str(first_arg.value).replace("\\", "/")

                    if not path.startswith("data/raw/"):
                        raise ValueError(
                            "Proof code may only read files from data/raw/."
                        )

                else:
                    raise ValueError(
                        "Data file path must be a fixed local path."
                    )

    return True


def run_code(code, timeout=5):
    """
    Run proof code with a time limit.
    """

    validate_code(code)

    with tempfile.TemporaryDirectory() as temp_dir:

        script = Path(temp_dir) / "proof.py"

        script.write_text(
            code,
            encoding="utf-8"
        )

        # Do not give proof code our API secret.
        safe_env = {
            "PATH": os.environ.get("PATH", "")
        }

        result = subprocess.run(
            [
                sys.executable,
                str(script)
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=safe_env
        )

        if result.returncode != 0:

            return {
                "status": "error",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        return {
            "status": "success",
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }


if __name__ == "__main__":

    example = """
import pandas as pd

df = pd.read_csv("data/raw/orders.csv")

result = len(df)

print(result)
"""

    result = run_code(example)

    print(result)