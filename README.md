# Fluxo

Personal finance that sorts itself: import the statement your bank gives you, and Fluxo files every line under a category, learns from each correction you make, and tells you how the month is going to end.

[![CI](https://github.com/Tutzdev/fluxo/actions/workflows/ci.yml/badge.svg)](https://github.com/Tutzdev/fluxo/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-12343b?style=flat-square&logo=python&logoColor=white)
![Flask 3](https://img.shields.io/badge/Flask-3-12343b?style=flat-square&logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-12343b?style=flat-square&logo=postgresql&logoColor=white)
![SQLAlchemy 2](https://img.shields.io/badge/SQLAlchemy-2-12343b?style=flat-square&logo=sqlalchemy&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-migrations-12343b?style=flat-square)
![scikit-learn](https://img.shields.io/badge/scikit--learn-classifier-12343b?style=flat-square&logo=scikitlearn&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-OpenAPI-12343b?style=flat-square&logo=pydantic&logoColor=white)
![mypy strict](https://img.shields.io/badge/mypy-strict-12343b?style=flat-square)
![React](https://img.shields.io/badge/React-19-12343b?style=flat-square&logo=react&logoColor=white)

<p>
  <img src="docs/screenshots/overview.png" alt="The month at a glance: R$ 3.300 out, R$ 6.800 in, spending by category and how November ends" width="49%">
  <img src="docs/screenshots/review.png" alt="The review queue after one correction, offering to sort the rest with what was taught" width="49%">
</p>

## The problem

Every finance app asks you to categorize your spending. Almost nobody keeps doing it after the second week, because:

- **Bank descriptions are noise.** `IFD*BURGUER DO ZE`, `PAG*JOAOPAULOSOUZA`, `UBER *TRIP 12/11 HELP.UBER.COM`. A keyword list catches the famous merchants and nothing else.
- **Statements overlap.** You export October, then "the last 90 days". Import both and every purchase counts twice, unless the app knows they are the same lines.
- **Money moves between your own accounts.** Paying the credit card bill from checking is not spending: the purchases on the card were. Count both and the month looks twice as expensive.
- **"Where did my money go" is the past.** The useful question is where the balance will be on the 30th.

Fluxo is built around those four problems.

## Backend highlights

- **A categorization chain with a clear order of trust.** Your own choice wins, then a keyword rule you wrote, then a classifier trained on *your* history, and only when it is sure. Everything else waits in a review queue. [How it works](#how-a-transaction-gets-its-category).
- **The model learns from you, never from itself.** It trains only on categories a person decided (by hand or through their rule). Training on its own guesses would turn every mistake into a stronger one.
- **Idempotent imports.** Each statement line gets a fingerprint; a unique constraint and one `INSERT ... ON CONFLICT DO NOTHING RETURNING id` decide what is new. Import the same file ten times, or two overlapping exports at the same moment, and every purchase is there once. [How](#how-an-import-stays-idempotent).
- **Real bank formats.** Nubank CSVs (account and card), generic CSVs with columns in Portuguese or English, comma or semicolon, `1.234,56` or `1,234.56`, and OFX 1.x, which is SGML without closing tags and breaks XML parsers.
- **A forecast, not just a report.** Recurring bills and incomes are detected from your history; the end-of-month balance is today's balance plus what is still to come plus your usual day-to-day pace. [How](#how-the-forecast-works).
- **Money is `Decimal`, never `float`**, end to end: `NUMERIC(14,2)` in PostgreSQL, `Decimal` in Python, strings in JSON.
- **Security without ceremony.** Opaque bearer tokens stored as SHA-256 (a leaked database leaks no sessions), scrypt passwords, login throttling without storing IP addresses, a wrong e-mail indistinguishable from a wrong password, and rows of other users answering 404, never 403.
- **Errors you can program against.** RFC 9457 Problem Details with a stable `code` (`EMAIL_TAKEN`, `ACCOUNT_NOT_FOUND`, `UNREADABLE_STATEMENT`...) and the failing fields on validation errors.
- **Typed all the way.** `mypy --strict` on the whole package, Pydantic request and response models, and an OpenAPI document with Swagger UI generated from them.

## How a transaction gets its category

```text
 new or re-run transaction
          │
          ├─ categorized by hand? ───────────────► keep it, always
          │
          ├─ a rule matches the description? ────► category = rule's          (source: rule)
          │     whole words only: MERCADO does not catch MERCADOPAGO
          │     the most specific rule wins: AMAZON PRIME beats AMAZON
          │
          ├─ the user's classifier is ≥ 55% sure? ► category = prediction     (source: model)
          │
          └─ otherwise ──────────────────────────► no category, "needs review"
```

- **Cold start.** A new account comes with 15 categories and 94 rules for common Brazilian merchants (IFOOD, UBER, NETFLIX, DROGASIL, SABESP...). The model has nothing to learn from on day one; the rules carry it.
- **The classifier** is character n-grams (3 to 5) with TF-IDF and logistic regression, one per user. Character n-grams because bank text is abbreviated and inconsistent; logistic regression because it gives a real probability to compare with the threshold. In the demo, one correction for `PREZUNIC TIJUCA` is enough: the other nine purchases there come in as Groceries at 82%.
- **No model files.** Training on a personal history takes milliseconds, so models live in a small LRU cache per process, keyed by the user's `labels_version`. Every correction or rule change bumps the version; the next categorization trains again. Nothing to migrate, no pickles to trust. ([ADR 0002](docs/adr/0002-a-model-per-user-trained-on-demand.md))
- **Review, then "sort the rest".** In the review queue the person picks categories for a few lines, then asks Fluxo to go through everything not categorized by hand again with what it just learned.

## How an import stays idempotent

```text
 file ──► read (CSV / OFX, any encoding) ──► lines ──► fingerprint each line
                                                             │
     bank id present (OFX FITID, Nubank "Identificador") ────┤──► "id:" + sha256(bank id)
     otherwise ──────────────────────────────────────────────┘──► "ln:" + sha256(date | amount | normalized description | occurrence)

 INSERT INTO transactions ... ON CONFLICT (account_id, fingerprint) DO NOTHING RETURNING id
     └─► only the returned ids are new; only they go through categorization
```

The **occurrence** counter is what keeps two real, identical coffees on the same day as two transactions while still recognizing them in the next export: the first `CAFE -6.50` of the day is occurrence 0 and the second is occurrence 1, in every file that contains them. Normalizing the description first (uppercase, no accents, no tokens without letters) means `Uber *Trip 05/11` and `UBER TRIP 05/11` are the same line.

The database decides, not a `SELECT` before the `INSERT`: two uploads of the same file at the same moment cannot both see "not there yet". ([ADR 0001](docs/adr/0001-fingerprints-and-the-database-decide-duplicates.md))

## How the forecast works

```text
 end-of-month balance = balance today (all accounts)
                      + recurring incomes and bills not seen yet this month
                      + usual day-to-day spending per day × days left
```

A series of transactions is **recurring** when it appears in at least three different months of the last six, **at most once a month**, always within 20% of its median amount. "At most once a month" is the rule that matters: ten Uber rides a month are a habit, not a bill with a due date. Day-to-day spending is the average of the last 90 days (or since the first transaction) without the recurring bills, so rent is not counted twice.

## Business rules

| Rule | Where |
| --- | --- |
| Amounts are signed: negative is money going out, positive is money coming in | everywhere |
| Credit card exports that list purchases as positive numbers can be flipped on import | `imports/service.py` |
| Transfers between your own accounts (category kind `transfer`) are left out of income, expenses, budgets and the forecast | `reports/service.py` |
| A category set by hand is never overwritten by a rule or the model | `categorization/service.py` |
| A new rule applies right away to everything not categorized by hand | `categories/service.py` |
| Deleting a category sends its transactions back to review | `ON DELETE SET NULL` |
| Account and category names are unique per user, ignoring case | `lower(name)` unique indexes |
| A budget belongs to an expense category; refunds count as income and do not lower spending | `budgets/service.py` |
| Budget status: warning from 80% of the limit, exceeded above 100% | `budgets/status.py` |
| Balances are never stored: opening balance plus the sum of the transactions | `accounts/service.py` |
| Five failed sign-ins lock an e-mail for 15 minutes | `auth/throttle.py` |

## Web front end

[`web/`](web) is a React 19 + TypeScript app (Vite, Tailwind v4, TanStack Query, react-hook-form + zod, Radix) built around the review queue:

- **Overview**: the month in one sentence, spending by category, how the month ends, budgets and six months of income against expenses.
- **Review**: what no rule knew and the model was not sure about, with "Sort the rest with what I taught".
- **Transactions**: filters, accent-insensitive search, inline category changes and who decided each one: *Rule*, *Learned 82%* or *You*.
- **Import**, **Budgets**, **Categories & rules**, **Accounts**.

Spending is not painted red; red is kept for a budget that went over. Fonts are bundled, never loaded from Google. The layout works from 390 px up.

<p>
  <img src="docs/screenshots/transactions.png" alt="Transactions with their category and who decided it" width="49%">
  <img src="docs/screenshots/welcome.png" alt="The welcome page with a sample statement and the demo button" width="49%">
</p>

## API

Interactive docs (Swagger UI) at **`/api/docs/swagger`**, the OpenAPI document at `/api/docs/openapi.json`.

| Method | Path | What it does |
| --- | --- | --- |
| `POST` | `/api/auth/register` · `/api/auth/login` | Create an account (with the starter categories) or sign in; returns a bearer token |
| `POST` `GET` | `/api/auth/logout` · `/api/auth/me` | End the session; who is signed in |
| `GET` `POST` `PATCH` `DELETE` | `/api/accounts[/{id}]` | Accounts with their live balance |
| `POST` `GET` | `/api/imports` | Upload a CSV or OFX statement (multipart); recent imports |
| `GET` `POST` | `/api/transactions` | Search with filters and totals; add one by hand |
| `PUT` | `/api/transactions/{id}/category` | Set or clear a category (teaches the model) |
| `POST` | `/api/transactions/recategorize` | Run rules and the model again on everything not set by hand |
| `GET` `POST` `PATCH` `DELETE` | `/api/categories[/{id}]` | Categories with their rules |
| `POST` `DELETE` | `/api/categories/{id}/rules` · `/api/categories/rules/{id}` | Add a rule (applied at once) or remove it |
| `GET` `PUT` `DELETE` | `/api/budgets[/{category_id}]` | Monthly limits with what was spent |
| `GET` | `/api/reports/summary` · `/trend` · `/forecast` | The month, the last months, the end of the month |
| `POST` | `/api/demo/session` | A private demo account with six months of data (when `DEMO_ENABLED=true`) |

```bash
# A demo account with six months of statements, already imported and categorized
TOKEN=$(curl -s -X POST localhost:5000/api/demo/session | jq -r .token)

curl -s localhost:5000/api/reports/forecast -H "Authorization: Bearer $TOKEN"

# Import a statement; the second time, every line is reported as a duplicate
curl -s localhost:5000/api/imports -H "Authorization: Bearer $TOKEN" \
  -F account_id=1 -F file=@tests/fixtures/nubank-checking.csv
```

## Technical decisions

| Decision | Why |
| --- | --- |
| Flask + flask-openapi3 + Pydantic | A small, explicit stack where validation and the OpenAPI document come from the same typed models |
| Package by feature, thin routes, services own the transaction | `routes.py` translates HTTP, `service.py` holds the rules and commits, `models.py` maps tables. Pure rules (`fingerprint`, `recurring`, `forecast`, `budgets/status`) have no I/O and are unit-tested alone |
| Plain SQLAlchemy 2 (no Flask-SQLAlchemy), one session per request | Services and tests do not depend on Flask to reach the database |
| Hand-written Alembic migrations, checked against the models by a test | Read like SQL scripts, and cannot drift from the code |
| Enums as `VARCHAR` + `CHECK` | Adding a value is a plain migration; altering a native Postgres enum is not |
| A `Clock` dependency | "Today" is the user's day in `America/Sao_Paulo`, and every rule that depends on it is testable |
| Opaque tokens over JWT | Signing out actually ends the session, and nothing secret sits in the browser beyond a random string |
| No IP addresses stored, fonts bundled | Privacy by default (LGPD) |

The longer reasoning is in [`docs/adr`](docs/adr).

## Tests

**118 tests**: 66 unit tests for the pure rules (parsers, fingerprints, rule matching, classifier, recurring detection, forecast, money, months, budget status, throttling) and 52 integration tests that drive the HTTP API against a **real PostgreSQL** migrated by Alembic, exactly like production.

Some of what they prove:

- `test_importing_the_same_file_twice_imports_nothing_the_second_time`
- `test_overlapping_exports_only_add_what_is_new_and_keep_real_twin_purchases`
- `test_one_correction_teaches_the_model_the_rest`
- `test_a_manual_category_is_never_overwritten`
- `test_paying_the_card_bill_is_not_counted_as_income_or_spending`
- `test_somewhere_you_go_often_is_a_habit_not_a_bill`
- `test_a_wrong_email_and_a_wrong_password_look_the_same`
- `test_someone_elses_account_does_not_exist_for_you`
- `test_the_migrations_create_exactly_what_the_models_describe`

CI runs `ruff check`, `ruff format --check`, `mypy --strict`, the whole suite on PostgreSQL 17, and the front end's type-check and build.

## Running locally

**Everything with Docker** (PostgreSQL, the API with the demo on, and the web app):

```bash
docker compose up --build
# open http://localhost:8080 and press "Try it with six months of sample data"
```

**Without Docker** (Python 3.12, Node 24, a PostgreSQL you can reach):

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

export DATABASE_URL=postgresql+psycopg://fluxo:fluxo@localhost:5432/fluxo
export DEMO_ENABLED=true
alembic upgrade head
flask --app fluxo.wsgi run                            # API on :5000, Swagger on /api/docs/swagger

cd web && npm install && npm run dev                    # web on :5173, /api proxied to :5000
```

Tests need an empty database they can own:

```bash
export TEST_DATABASE_URL=postgresql+psycopg://fluxo:fluxo@localhost:5432/fluxo_test
pytest && ruff check . && mypy
```

All settings and their defaults are in [`.env.example`](.env.example).

## Project layout

```text
fluxo/
  auth/            sign up, sign in, tokens, login throttle
  accounts/        accounts and live balances
  categories/      categories, keyword rules, the starter kit
  categorization/  rule matcher, classifier, model cache, the decision chain
  imports/         CSV and OFX parsers, fingerprints, idempotent import
  transactions/    search, manual entries, corrections
  budgets/         monthly limits and their status
  reports/         summary, trend, recurring detection, forecast
  demo/            the sample data generator and demo accounts
  app.py           application factory
migrations/        Alembic
tests/unit/        pure rules, no database
tests/integration/ the HTTP API against PostgreSQL
web/               React front end
```

## Roadmap

- [x] Accounts, categories, rules, idempotent CSV and OFX import
- [x] Per-user classifier with a review queue
- [x] Budgets, month summary, trend and end-of-month forecast
- [x] Web front end and a one-click demo
- [ ] Split a transaction across categories (the supermarket receipt that is also the pharmacy)
- [ ] Explain a prediction: the past transactions that made the model choose a category
- [ ] Import Open Finance data instead of files
- [ ] A scheduled job that retrains and warms the cache for active users after deploys
