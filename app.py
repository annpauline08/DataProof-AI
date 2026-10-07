from flask import Flask, request, render_template_string

from src.triage import triage_question
from src.codegen import generate_code
from src.sandbox import run_code
from src.verify import verify


app = Flask(__name__)


HTML = """
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>DataProof AI</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, sans-serif;
    background: #0b1020;
    color: white;
}

.container {
    max-width: 1100px;
    margin: auto;
    padding: 30px 20px;
}

.hero {
    background: linear-gradient(135deg, #18244a, #11182f);
    padding: 30px;
    border-radius: 20px;
    margin-bottom: 20px;
}

.hero h1 {
    margin: 0;
    font-size: 42px;
}

.hero p {
    color: #b8c3e0;
    font-size: 17px;
}

.card {
    background: #111932;
    border: 1px solid #2a385e;
    border-radius: 18px;
    padding: 22px;
    margin-bottom: 18px;
}

textarea {
    width: 100%;
    min-height: 110px;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #394b79;
    background: #080e20;
    color: white;
    resize: vertical;
    font-size: 16px;
}

button {
    margin-top: 14px;
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 12px;
    background: #5b7cff;
    color: white;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.answer {
    font-size: 25px;
    line-height: 1.5;
}

.success {
    background: #153c2a;
    border: 1px solid #2f8a5b;
    padding: 14px;
    border-radius: 10px;
}

.warning {
    background: #423218;
    border: 1px solid #8f702f;
    padding: 14px;
    border-radius: 10px;
}

.error {
    background: #411d25;
    border: 1px solid #9b3c4c;
    padding: 14px;
    border-radius: 10px;
}

pre {
    background: #070b15;
    padding: 18px;
    border-radius: 12px;
    overflow-x: auto;
    line-height: 1.5;
}

.label {
    color: #9caed8;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.demo {
    color: #aebad8;
    font-size: 14px;
}

</style>

</head>

<body>

<div class="container">

    <div class="hero">

        <h1>🛡️ DataProof AI</h1>

        <p>
            An AI data analyst that doesn't just give an answer —
            it shows the executable proof behind the answer.
        </p>

    </div>


    <div class="card">

        <div class="label">
            Ask your data question
        </div>

        <form method="POST">

            <textarea
                name="question"
                placeholder="Example: Which customer had the highest order total?"
                required
            >{{ question }}</textarea>

            <button type="submit">
                Analyze → Verify → Prove
            </button>

        </form>

        <p class="demo">
            Try:
            "Which customer had the highest order total?"
            <br>
            or:
            "What was the profit?"
        </p>

    </div>


    {% if error %}

    <div class="card">

        <div class="error">

            <b>System Error</b>

            <p>{{ error }}</p>

        </div>

    </div>

    {% endif %}


    {% if refusal %}

    <div class="card">

        <h2>🛑 Cannot answer reliably</h2>

        <div class="warning">

            {{ refusal }}

        </div>

    </div>

    {% endif %}


    {% if clarification %}

    <div class="card">

        <h2>❓ Clarification needed</h2>

        <div class="warning">

            {{ clarification }}

        </div>

    </div>

    {% endif %}


    {% if result %}

    <div class="card">

        <h2>✅ Verified Answer</h2>

        <div class="answer">

            {{ result.answer }}

        </div>

        <br>

        <div class="success">

            ✅ Verification PASS

            <br><br>

            The proof code executed successfully and the result
            matched an independent calculation.

        </div>

    </div>


    <div class="card">

        <h2>🧠 Agent Decision</h2>

        <pre>{{ result.triage }}</pre>

    </div>


    <div class="card">

        <h2>🐍 Executable Proof Code</h2>

        <pre>{{ result.code }}</pre>

    </div>


    <div class="card">

        <h2>🔎 Proof Output</h2>

        <pre>{{ result.output }}</pre>

    </div>

    {% endif %}


</div>

</body>

</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():

    question = ""

    result = None
    refusal = None
    clarification = None
    error = None

    if request.method == "POST":

        question = request.form.get(
            "question",
            ""
        ).strip()

        try:

            # ---------------------------
            # 1. TRIAGE
            # ---------------------------

            triage = triage_question(
                question
            )


            # ---------------------------
            # 2. REFUSAL
            # ---------------------------

            if triage["decision"] == "refuse":

                refusal = triage["reason"]


            # ---------------------------
            # 3. CLARIFICATION
            # ---------------------------

            elif triage["decision"] == "clarify":

                clarification = triage["reason"]


            # ---------------------------
            # 4. ANSWER
            # ---------------------------

            else:

                generated = generate_code(
                    question
                )

                if not generated["code"]:

                    refusal = (
                        "The current MVP cannot reliably "
                        "answer this question."
                    )

                else:

                    # ---------------------------
                    # 5. RUN PROOF CODE
                    # ---------------------------

                    execution = run_code(
                        generated["code"]
                    )

                    if execution["status"] != "success":

                        error = (
                            "The generated proof code "
                            "failed to execute.\n\n"
                            + execution["stderr"]
                        )

                    else:

                        # ---------------------------
                        # 6. VERIFY
                        # ---------------------------

                        verification = verify(
                            question,
                            execution["stdout"]
                        )

                        if not verification["verified"]:

                            error = (
                                "Verification failed. "
                                "The system refused to show "
                                "an unverified answer."
                            )

                        else:

                            result = {

                                "answer":
                                    execution["stdout"].strip(),

                                "triage":
                                    str(triage),

                                "code":
                                    generated["code"],

                                "output":
                                    execution["stdout"]
                            }

        except Exception as exc:

            error = str(exc)


    return render_template_string(
        HTML,
        question=question,
        result=result,
        refusal=refusal,
        clarification=clarification,
        error=error
    )


if __name__ == "__main__":

    app.run(
        debug=True
    )