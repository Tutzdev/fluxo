# 3. Transfers between your own accounts are neither income nor spending

Status: accepted

## Context

Paying the credit card bill shows up twice: `PAGAMENTO DE FATURA -2.828,20` in checking and `PAGAMENTO RECEBIDO +2.828,20` on the card. The purchases on the card were already counted as spending when they happened. Counting the payment as well makes the month look twice as expensive; counting the card's side as income makes it look richer than it was. Moving money to savings or an investment has the same shape.

## Decision

Categories have a kind: `expense`, `income` or `transfer`. Every transaction in a `transfer` category is left out of the month's income and expenses, the spending by category, budgets, the trend and the forecast's recurring and day-to-day figures. The starter kit has a *Transfers* category with rules for the usual descriptions (`PAGAMENTO DE FATURA`, `PAGAMENTO RECEBIDO`, `APLICACAO`, `RESGATE`).

Balances are not affected: the money really left checking and really reached the card.

## Consequences

- The overview answers "what did I spend" correctly even with a credit card paid from checking, which is how most Brazilians pay.
- A Pix to another person is *not* a transfer; it is spending or income, and the person categorizes it.
- If a payment is mis-categorized, the month is off until it is fixed; the review queue and the "Between my accounts" section on the categories page make that visible.
