import sys

from sandbox import run_code
from verify import verify


def verify_proof(question, code):

    print("\n==============================")
    print("      PROOF VERIFICATION")
    print("==============================")

    print("\nQuestion:")
    print(question)

    print("\nRunning proof code...")

    execution = run_code(code)

    if execution["status"] != "success":

        print("\n❌ EXECUTION FAILED")

        print(
            execution["stderr"]
        )

        return {
            "verified": False,
            "reason": "Proof code failed to run."
        }

    print("\n✅ Code executed successfully.")

    output = execution["stdout"]

    print("\nProof output:")
    print(output)

    result = verify(
        question,
        output
    )

    print("\nVerification result:")

    print(result)

    if result["verified"]:

        print(
            "\n✅ VERIFIED: The proof result matches an independent calculation."
        )

    else:

        print(
            "\n❌ FAILED: The proof result does not match."
        )

    return result


if __name__ == "__main__":

    print(
        "This script expects proof code from Person B."
    )

    print(
        "For now, testing can be done through run_eval.py."
    )