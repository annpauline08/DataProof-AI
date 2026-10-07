# Messy-Data Question-Answering Agent

An AI agent that answers questions about messy, real-world data spread across several tables. **Every number it reports comes with a standalone Python script that anyone can re-run to check the math.** When a question cannot be answered reliably, the agent says so and explains why instead of guessing.

> Built by a team of 3 for HackNex 2026 (internal qualifier).
> Team: `<NAME 1 (Person A)>`, `<NAME 2 (Person B)>`, `<NAME 3 (Person C)>`

---

## 1. The problem we solved

Real data is dirty. The agent must handle:

| Trap | Example in our data |
|---|---|
| Units / currency don't match | Orders in USD and EUR; weights in kg and lb |
| Ambiguous dates | `2025-03-04` and `04/03/2025` in the same column |
| Duplicated rows | Same order appearing twice; same customer under two IDs |
| Tables contradict each other | An order's total differs from the sum of its line items |
| Missing data | Blank currency, customer, total; no EUR rate after June |
| Question has no valid answer | "What was the profit margin?" when no cost data exists |
| Trick questions | "Why did sales drop in March?" (a cause the data cannot prove) |

**The rules we built around:**
1. Every number must have re-runnable code. A verifier runs the code and must get the same number.
2. A wrong, confident answer is worse than "I can't determine this from the data" with a good reason.

---

## 2. How it works (big picture)

```
question
   |
   v
[1] Hard rules (no LLM)  --> refuse: topic has no data, or date outside coverage
   |
   v
[2] LLM triage           --> ANSWERABLE / AMBIGUOUS / UNANSWERABLE / TRAP
   |
   v
[3] LLM writes ONE standalone pandas script (uses only the cleaned tables)
   |
   v
[4] Sandbox runs the script (up to 3 attempts; errors are fed back to the LLM)
   |
   v
[5] Answer sentence is built BY CODE from the script's output (never by the LLM)
   |
   v
[6] Verifier re-runs the script and checks the result before it is trusted
```

**Key design decision:** the LLM never produces a number itself. It only writes code, and the code produces the number. The final sentence is assembled from the script's output so the text can never disagree with the code.

---

## 3. Team roles

| Person | Owns | Files |
|---|---|---|
| **A: Data and audit** | Messy dataset, data audit, cleaning rules | `data/generate_messy_data.py`, `src/audit.py`, `src/cleaning.py`, `tests/test_audit.py` |
| **B: Agent** | Triage, prompts, code generation, orchestration | `src/llm.py`, `src/triage.py`, `src/codegen.py`, `src/agent.py`, `tests/test_agent_offline.py` |
| **C: Sandbox, verifier, eval** | Safe execution, independent checking, scoring | `src/sandbox.py`, `src/verify.py`, `eval/`, `tests/test_sandbox_verify.py` |

---

## 4. Tech stack

- Python 3.11 or newer
- pandas 3.0.2 and numpy 2.4.4 (pinned in `requirements.txt`)
- An LLM provider through one file (`src/llm.py`): `<YOUR PROVIDER, e.g. Anthropic or OpenAI>`, model `<YOUR MODEL NAME>`
- Git and VS Code for collaboration
- No database and no web server. Data lives in CSV files.

---

## 5. Repository structure

```
your-repo/
├── data/
│   ├── generate_messy_data.py   builds the messy dataset (seeded, repeatable)
│   ├── raw/                     the 5 messy CSVs (never edited by hand)
│   │   ├── customers.csv
│   │   ├── products.csv
│   │   ├── orders.csv
│   │   ├── order_items.csv
│   │   └── fx_rates.csv
│   ├── ground_truth.json        the answer key (tests and eval ONLY, never the agent)
│   └── processed/issues.json    audit report (generated, git-ignored)
├── src/
│   ├── cleaning.py              explicit cleaning rules
│   ├── audit.py                 finds the data problems
│   ├── llm.py                   the only file that talks to an LLM
│   ├── triage.py                decides answer / ambiguous / refuse
│   ├── codegen.py               asks the LLM for a re-runnable script
│   ├── agent.py                 runs the whole pipeline (CLI entry point)
│   ├── sandbox.py               runs generated scripts safely
│   └── verify.py                independent answer checker
├── answers/                     generated answer_<id>.py scripts + results.json
├── eval/
│   ├── questions.json           15 test questions with known right outcomes
│   ├── run_eval.py              scores the whole agent
│   └── report.json              last eval report (generated)
├── tests/
│   ├── test_audit.py
│   ├── test_agent_offline.py
│   └── test_sandbox_verify.py
├── requirements.txt
├── .env.example                 template for your API key (copy to .env)
├── .gitignore
└── README.md
```

---

## 6. Setup, step by step

### 6.1 Get the code
```bash
git clone <YOUR REPO URL>
cd <YOUR REPO FOLDER>
```
Run every later command from this folder (the repo root).

### 6.2 Check Python
```bash
python --version        # needs 3.11+  (try py or python3 if "not found")
```

### 6.3 Create and activate a virtual environment
```bash
python -m venv .venv
# Windows (PowerShell):   .venv\Scripts\activate
# Mac / Linux:            source .venv/bin/activate
```
You should now see `(.venv)` at the start of your terminal line.
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope Process Bypass`.
In VS Code: `Ctrl+Shift+P`, then *Python: Select Interpreter*, then pick the `.venv` one.

### 6.4 Install libraries
```bash
pip install -r requirements.txt
pip install anthropic        # or: pip install openai   (only if you use a real LLM)
```

### 6.5 Configure the LLM
```bash
cp .env.example .env         # Windows: copy .env.example .env
```
Edit `.env`:
```
LLM_PROVIDER=anthropic       # anthropic | openai | mock
ANTHROPIC_API_KEY=your-key-here
# LLM_MODEL=claude-sonnet-4-6
```
- `LLM_PROVIDER=mock` runs offline with canned answers. It is for testing the plumbing only.
- `.env` is git-ignored. **Never commit it.**

### 6.6 Build the data
```bash
python data/generate_messy_data.py
```
Expected output (one line):
```
Wrote ['customers.csv', 'fx_rates.csv', 'order_items.csv', 'orders.csv', 'products.csv'] + ground_truth.json
```
The generator uses a fixed seed (`42`), so every teammate (and every judge) gets byte-identical files.

---

## 7. The dataset and its planted traps

| Table | Rows | What is wrong with it |
|---|---|---|
| `customers.csv` | 213 | 5 exact duplicate rows; 8 people stored under 2 IDs (email in different case), giving 208 IDs but only **200 real customers**; 14 blank regions |
| `products.csv` | 30 | `weight_unit` is a mix of `kg` and `lb` |
| `orders.csv` | 1,520 | 20 duplicate rows (**1,500 unique orders**); dates in both `YYYY-MM-DD` and `DD/MM/YYYY`; 150 totals stored as text like `$1,234.50` or `€88.20`; 45 blank currencies; 15 blank totals; 30 blank customers; 15 orders pointing to non-existent customer `C9999`; 60 totals that contradict their line items |
| `order_items.csv` | about 3,700 | Source of truth for per-order totals (amounts in the order's own currency) |
| `fx_rates.csv` | 6 | EUR to USD rates only for Jan to Jun 2025 |

Structural gaps (no file shows them, but questions probe them):
- **No cost or profit column anywhere.**
- **No orders after 30 Sep 2025.**

`data/ground_truth.json` records the exact planted counts and one true revenue figure. Only the tests and the eval read it. The sandbox actively blocks generated code that mentions it.

---

## 8. Audit and cleaning rules (`src/audit.py`, `src/cleaning.py`)

**Principle: never guess.** Anything unreadable becomes `NaN`/`NaT` and gets a flag. Nothing is silently filled in.

| Area | Rule |
|---|---|
| Loading | All CSVs are read as text (`dtype=str`) so pandas never silently converts values |
| Duplicates | Exact duplicate rows are dropped. If one `order_id` repeats with different contents, the code raises an error instead of choosing |
| Dates | ISO dates parse directly. For `xx/xx/yyyy`, the code infers DD/MM vs MM/DD from the data itself: a first field above 12 can only be a day. If the evidence is mixed or absent, the date stays `NaT` |
| Ambiguous dates | A slash date valid both ways (e.g. `04/03/2025`) is flagged `date_ambiguous` even after inference |
| Money | `$1,234.50` is parsed to a number plus a symbol. A symbol that contradicts the currency column is flagged |
| Currency | Never filled in. Blank currency is flagged `currency_missing` |
| Customers | Same normalised (trimmed, lower-case) email means same person. The lowest ID becomes the canonical ID |
| Totals vs items | Compared with a 0.01 tolerance. A difference sets `total_mismatch` |
| FX | USD stays as is. EUR converts to USD only if that month has a rate, otherwise `revenue_usd` is `NaN` and `fx_missing` is set |
| Units | Product weights converted to kg (1 lb = 0.45359237 kg) |
| Revenue | `revenue_usd` is built from the sum of line items, in USD |

Run the audit:
```bash
python -m src.audit          # writes data/processed/issues.json
```
The audit report lists duplicates, date formats and the inferred date order, currency counts, nulls, orphan keys, total mismatches, FX coverage, the date range, and **`topics_with_no_data`** (used to refuse questions about profit, cost, margin).

---

## 9. The agent in detail

### 9.1 Hard-rule triage (`src/triage.py`, no LLM)
Refuses immediately, with a reason, when:
- the question mentions a topic with no data (`profit`, `cost`, `margin`)
- the question names a quarter (e.g. `Q4 2025`) or a year (e.g. `2026`) outside the data's date range

A quarter written without a year (like "Q4") is assumed to be in the last year of the data. A partly covered quarter (Q3 2025) adds a warning instead of a refusal.

### 9.2 LLM triage
The LLM sees the question plus the audit report and returns JSON with `status`, `reason`, `interpretations`, `assumptions`:

| Status | Meaning | Agent behaviour |
|---|---|---|
| `ANSWERABLE` | Data exists, issues handled with stated assumptions | Writes and runs code |
| `AMBIGUOUS` | 2 or more readings give different numbers | Computes each reading |
| `UNANSWERABLE` | Data missing or too contradictory | Refuses with reason |
| `TRAP` | False premise, or causation the data can't prove | Refuses with reason |

If the triage reply cannot be parsed after 2 tries, the agent proceeds as answerable (the script must still run and pass the checks).

### 9.3 Code generation (`src/codegen.py`)
The prompt contains the column guide and **hard rules**:
1. Load data only via `from src.cleaning import clean_all`. Never read raw files or `ground_truth.json`. No network, no randomness.
2. Never guess. Exclude rows with missing currency, dates, amounts, or FX rates, and **count** the exclusions.
3. Never add EUR and USD together; use `revenue_usd`.
4. "Revenue" means `status == 'completed'` unless the question says otherwise, and the assumption must be stated.
5. Unique customers means `canonical_id.nunique()`, not the number of IDs.
6. If there are several interpretations, compute each and return a dict.
7. The last line printed must be one JSON object: `value`, `unit`, `assumptions`, `rows_used`, `excluded`.

The agent prepends a small header so each script finds the `src` package no matter where it is run from.

### 9.4 Run and retry (`src/agent.py`)
Up to 3 attempts. On an error, the traceback and the failed code go back to the LLM. A result counts only if it has a `value` that is not `None` or `NaN`.

### 9.5 Answer text
Built by code from the script's output. Numbers are formatted with thousands separators (e.g. `294,885.30 USD`).

### 9.6 Output of every question
```json
{
  "qid": "a1b2c3d4",
  "question": "What was total revenue in USD from completed orders in Q1 2025?",
  "status": "ANSWERED",
  "answer": "294,885.30 USD",
  "assumptions": ["Only status == completed orders", "..."],
  "data_issues_hit": ["orders_with_unknown_currency"],
  "code_path": "answers/answer_a1b2c3d4.py",
  "result": {"value": 294885.3, "unit": "USD", "rows_used": 0, "excluded": {}},
  "triage": {"status": "ANSWERABLE", "...": "..."},
  "attempts": 1
}
```
`status` is one of `ANSWERED`, `AMBIGUOUS`, `REFUSED`, `CANNOT_DETERMINE`. All results are saved to `answers/results.json`.

---

## 10. Sandbox and verifier

### 10.1 Sandbox (`src/sandbox.py`)
Before running any generated script it scans for forbidden things: reading `ground_truth` or `data/raw`, network libraries, `subprocess`, `os.system`, `anthropic`/`openai`, `eval`/`exec`, and randomness. Then it runs the script with API keys removed from the environment, a fixed hash seed, and a 60-second timeout. It returns `{"ok", "stdout", "stderr", "result"}`.

### 10.2 Verifier (`src/verify.py`)
For every answer it checks:
1. `no_forbidden_access`: the code did not cheat
2. `runs_ok`: the script runs
3. `same_result_twice`: two runs give the same result
4. `runs_from_other_folder`: works when started from a different folder
5. `matches_reported_result`: the code's output equals the reported result
6. `answer_text_contains_the_numbers`: the sentence contains the real numbers
7. `sane_numbers`: counts are not negative or fractional, percentages are 0 to 100
8. `states_assumptions`: assumptions are listed

Refusals are checked separately: they must give a clear reason and contain no number and no code.

---

## 11. How to run it

**One question:**
```bash
python -m src.agent "What was total revenue in USD from completed orders in Q1 2025?"
```

**Many questions** (one per line in a text file):
```bash
python -m src.agent --batch questions.txt
```

**Check an answer yourself** (this is exactly what a judge does):
```bash
python answers/answer_<id>.py
```
The last printed JSON line must match `result` in `answers/results.json`.

---

## 12. Testing and evaluation

```bash
python tests/test_audit.py            # 4 tests: audit finds every planted trap
python tests/test_agent_offline.py    # 5 tests: refusals, end-to-end, re-run (mock LLM)
python tests/test_sandbox_verify.py   # 9 tests: sandbox and verifier
python eval/run_eval.py               # mock mode: 5 questions that need no real LLM
python eval/run_eval.py --all         # real LLM: all 15 questions
```
If you have pytest installed, `python -m pytest -q` also works.

`eval/questions.json` has 15 questions:

| Group | Examples | Expected |
|---|---|---|
| Exact numbers | unique customers (200), unique orders (1,500), orders with no customer (30), orphan-customer orders (15), mismatching totals (60), EUR orders without a rate, ambiguous-date orders | Number matches `ground_truth.json` |
| Must refuse | profit margin, cost of goods, Q4 2025, orders in 2026, "What is the CEO's salary?" | `REFUSED` with a reason |
| Judgement | "Why did sales drop in March 2025?"; Q3 2025 revenue (no EUR rates) | Refuse, or flag what was left out |

### Results
> Paste your latest output of `python eval/run_eval.py --all` here:
```
<PASTE YOUR SCORE AND ANY NOTES>
```

---

## 13. Design decisions and assumptions

- **Code first, words second.** The LLM writes code; code produces numbers; code composes the answer text.
- **Never guess.** Missing values are excluded and counted, not filled in.
- **Refusal beats a confident wrong answer.** Deterministic rules refuse certain questions before any LLM is involved.
- **Date order is inferred from evidence** (a first field above 12), not assumed.
- **"Revenue" excludes cancelled and returned orders** by default, and says so.
- **Customers are merged by normalised email.** Two accounts with the same email are one person.
- **Line items are the source of truth** when an order total contradicts them. The disagreement is flagged, never hidden.
- **Reproducibility everywhere:** fixed seed (42), pinned library versions, fixed hash seed in the sandbox, no randomness allowed in generated code.

---

## 14. Known limitations

- The refusal rules only know what `audit.py` reports. With a different dataset, check `topics_with_no_data` and `date_coverage`.
- Only the first wave of hard rules (topics and dates) is deterministic. Everything else relies on the LLM's triage.
- The sandbox's static scan catches an LLM's mistakes. It is not a security boundary for untrusted code.
- Revenue conversion supports USD and EUR only. EUR needs a monthly rate and only Jan to Jun 2025 exist.
- Mock mode (`LLM_PROVIDER=mock`) always returns one canned calculation and is for plumbing tests only.
- `<ADD ANY OTHER LIMITATIONS YOU FOUND WHILE TESTING>`

---

## 15. Troubleshooting

| Problem | Fix |
|---|---|
| `python` not recognised | Use `py` (Windows) or `python3`, or reinstall Python with "Add to PATH" ticked |
| `ModuleNotFoundError: pandas` | The virtual environment isn't active. Activate it and run `pip install -r requirements.txt` |
| `can't open file ... generate_messy_data.py` | You are in the wrong folder. `cd` to the repo root |
| `FileNotFoundError: data/raw/...` | Run `python data/generate_messy_data.py` first |
| Files appear inside `repo/repo/` | Copy the contents of the folder, not the folder itself |
| Warning "LLM_PROVIDER=mock" | Set `LLM_PROVIDER` and your key in `.env` |
| Authentication error from the LLM | Check the key in `.env`, with no quotes or spaces around it |
| A script is "Blocked by sandbox" | It used something forbidden (see section 10.1). Ask the agent again or tighten the prompt |

---

## 16. Git workflow we used

- `main` holds merged, working code.
- Each person works on a feature branch: `feat/data-audit` (A), `feat/agent` (B), `feat/verify-eval` (C).
- Work is merged through pull requests on GitHub. Run `python eval/run_eval.py --all` before merging into `main`.
- Never commit `.env` (API keys). `data/raw/` and `data/ground_truth.json` **are** committed so all three work on identical files.

Typical cycle:
```bash
git checkout -b feat/<name>
git add .
git commit -m "Short description"
git push -u origin feat/<name>
```
