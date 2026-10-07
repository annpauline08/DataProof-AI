# DataProof AI — Data Cleaning Rules

## Rule 1 — Never modify raw data

Files inside:

data/raw/

are read-only source data.

Never overwrite them.

---

## Rule 2 — Normalize column names

Convert column names to a consistent form:

- lowercase
- trim spaces
- replace spaces with underscores

Example:

Order Total

becomes:

order_total

---

## Rule 3 — Monetary values

Values such as:

$1,250.50

must be converted to:

1250.50

But currency must remain known separately.

Never combine USD, EUR and INR without a valid conversion rate.

---

## Rule 4 — Currency conversion

Only convert a currency when:

1. a conversion rate exists
2. the correct month is known
3. the currency matches the rate

If a rate is missing:

REFUSE THE CALCULATION.

Do not guess a rate.

---

## Rule 5 — Dates

ISO dates such as:

2025-03-04

can be parsed safely.

Slash dates such as:

04/03/2025

are treated as ambiguous unless the dataset's convention is known.

Do not silently guess whether this means March 4 or April 3.

---

## Rule 6 — Duplicate orders

Duplicate order IDs must be reported.

Do not silently delete a duplicate.

The audit should preserve evidence that the duplicate existed.

---

## Rule 7 — Missing values

Missing values must be reported.

Do not replace missing values with zero unless the question or documented business rule explicitly justifies that action.

---

## Rule 8 — Foreign-key problems

An order referencing an unknown customer or product must be flagged.

Do not invent the missing customer/product.

---

## Rule 9 — Contradictory totals

If:

quantity × product price

does not equal:

order_total

the discrepancy must be reported.

Do not overwrite either value.

---

## Rule 10 — Units

Different units such as:

kg
lb

must not be treated as equal.

Conversion is allowed only when the conversion rule is explicitly known.

---

## Rule 11 — Missing concepts

If the required field does not exist, the system must refuse the question.

Example:

User asks:

"What was the profit?"

If there is no profit or cost information:

"I cannot determine profit from the available data."

---

## Rule 12 — Trust over guessing

When the data is insufficient, contradictory or ambiguous:

REFUSE rather than invent an answer.