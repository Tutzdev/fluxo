# 1. Fingerprints, and the database decides what is a duplicate

Status: accepted

## Context

People export overlapping periods all the time: October, then "the last 90 days", then the card's current bill. Importing must be safe to repeat, or every overlap doubles the spending.

The obvious check, "does a transaction with this date, amount and description already exist?", fails twice:

- **Real twins.** Two coffees of R$ 6,50 at the same café on the same day are two transactions. A "same date, amount and description" check throws the second one away.
- **Races.** Two uploads of the same file at the same moment both run the `SELECT`, both see nothing, and both insert.

## Decision

Every statement line gets a **fingerprint**, stored with a unique constraint on `(account_id, fingerprint)`:

- When the bank sends its own id (OFX `FITID`, Nubank's `Identificador`), the fingerprint is `id:` + SHA-256 of that id. The bank knows best.
- Otherwise it is `ln:` + SHA-256 of `date | amount | normalized description | occurrence`, where `occurrence` counts identical lines within the file: the first coffee is 0, the second is 1, in every file that contains them.

The import is a single `INSERT ... ON CONFLICT (account_id, fingerprint) DO NOTHING RETURNING id`. The ids that come back are the new transactions, and only those go through categorization. The database decides; there is no `SELECT` beforehand.

The description is normalized first (uppercase, no accents, no tokens without letters), so `Uber *Trip 05/11` and `UBER TRIP 05/11` are the same line.

## Consequences

- Importing the same file twice, or overlapping files, or the same file from two tabs at once, leaves every transaction there exactly once. Tests prove each case.
- The same line in two different accounts is two transactions, as it should be (the constraint includes the account).
- If a bank changes the description of a line between exports without sending an id, the line is imported twice. That is the trade-off for keeping real twins; the user can delete the extra one.
- Manual transactions get a random `manual:` fingerprint and can never collide.
- The fingerprint depends on the sign convention, so importing a card statement once flipped and once not would create duplicates. The import screen pre-selects the flip for card accounts to make that unlikely.
