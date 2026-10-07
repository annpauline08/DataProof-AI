from triage import triage_question
from codegen import generate_code


def run_agent(question):

    print("\n==============================")
    print("       DATAPROOF AI")
    print("==============================")

    print("\nUser question:")
    print(question)

    # Step 1: Triage
    triage = triage_question(question)

    print("\n--- TRIAGE ---")
    print("Decision:", triage["decision"])
    print("Reason:", triage["reason"])

    # Stop if unsafe
    if triage["decision"] != "answer":

        print("\n❌ Agent response:")
        print(triage["reason"])

        return

    # Step 2: Code generation
    generated = generate_code(question)

    print("\n--- CODE GENERATION ---")
    print(generated["summary"])

    if generated["code"] is None:

        print("\n⚠️ I cannot reliably answer this question yet.")
        return

    print("\n--- PROOF CODE ---")
    print(generated["code"])

    print("\n--- NEXT STEP ---")
    print("Send this proof code to Person C's sandbox for execution and verification.")


if __name__ == "__main__":

    question = input("\nAsk DataProof AI: ")

    run_agent(question)