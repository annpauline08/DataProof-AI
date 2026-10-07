import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT / "src")
)

from triage import triage_question
from codegen import generate_code
from sandbox import run_code
from verify import verify


QUESTIONS_FILE = (
    ROOT
    / "tests"
    / "eval_questions.json"
)


with open(
    QUESTIONS_FILE,
    "r",
    encoding="utf-8"
) as file:

    questions = json.load(file)


passed = 0
failed = 0


print(
    "\n================================"
)

print(
    "     DATAPROOF EVALUATION"
)

print(
    "================================\n"
)


for index, item in enumerate(
    questions,
    start=1
):

    question = item["question"]
    expected = item["expected"]

    print(
        f"\n[{index}/{len(questions)}] {question}"
    )

    triage = triage_question(
        question
    )

    actual_decision = (
        triage["decision"]
    )

    # -----------------------------
    # REFUSE / CLARIFY TEST
    # -----------------------------

    if expected in {
        "refuse",
        "clarify"
    }:

        if actual_decision == expected:

            print(
                f"✅ PASS — expected {expected}"
            )

            passed += 1

        else:

            print(
                f"❌ FAIL — expected {expected}, got {actual_decision}"
            )

            failed += 1

        continue


    # -----------------------------
    # ANSWER TEST
    # -----------------------------

    if actual_decision != "answer":

        print(
            f"❌ FAIL — expected answer, got {actual_decision}"
        )

        failed += 1

        continue


    generated = generate_code(
        question
    )

    code = generated.get(
        "code"
    )

    if not code:

        print(
            "❌ FAIL — no proof code generated"
        )

        failed += 1

        continue


    execution = run_code(
        code
    )

    if execution["status"] != "success":

        print(
            "❌ FAIL — proof code did not run"
        )

        failed += 1

        continue


    verification = verify(
        question,
        execution["stdout"]
    )


    if verification["verified"]:

        print(
            "✅ PASS — executed and independently verified"
        )

        passed += 1

    else:

        print(
            "❌ FAIL — verification mismatch"
        )

        print(
            verification
        )

        failed += 1


print(
    "\n================================"
)

print(
    f"PASSED: {passed}"
)

print(
    f"FAILED: {failed}"
)

print(
    f"TOTAL : {len(questions)}"
)

print(
    "================================"
)