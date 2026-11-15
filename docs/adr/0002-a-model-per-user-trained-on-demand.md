# 2. A model per user, trained on demand and never stored

Status: accepted

## Context

Keyword rules catch famous merchants (IFOOD, UBER, NETFLIX) but not the bakery around the corner, the local supermarket chain or `PAG*JOAOPAULOSOUZA`. Those are different for every person, so one global model trained on everyone's data would be both a privacy problem and wrong for most people.

What a person needs: "I told you once that PREZUNIC is groceries; stop asking."

## Decision

- **One classifier per user**, trained only on that user's transactions whose category was decided by a person: set by hand (`manual`) or by one of their rules (`rule`). Never on the model's own guesses (`model`): training on them would turn every mistake into a stronger one.
- **Character n-grams (3 to 5) with TF-IDF, then logistic regression.** Bank text is abbreviated and inconsistent (`IFD*BURGUER`, `DROGASIL 1123`), so pieces of words carry more than whole words. Logistic regression gives a calibrated-enough probability to compare against a threshold.
- **A prediction is kept only at 55% or more.** Below that the transaction waits in "needs review". Asking costs one click; a confident wrong category hides money from the person.
- **Rules come first, the model second, the person always wins.** A manual category is never overwritten.
- **No model is persisted.** Training on a personal history (hundreds to a few thousand lines) takes milliseconds. Models live in an LRU cache in each process, keyed by `users.labels_version`, which is bumped on every correction, rule change or category deletion. The next categorization notices the version changed and trains again.
- **No model below 8 examples or 2 categories.** There is nothing meaningful to learn yet; the starter rules cover the first import.

## Consequences

- No model files, no storage, no migrations for models, and no `pickle.load` of anything (unpickling is code execution).
- Each gunicorn worker trains its own copy the first time it needs it: a few milliseconds per worker per change, which is cheaper than coordinating a shared store.
- A restart or deploy empties the caches; the first request per user after that pays the training time. Warming the cache for active users is on the roadmap.
- The approach stops being cheap at hundreds of thousands of lines per user. That is far beyond a personal statement history; if it happens, training moves to a background job and the model is stored (in a safe format, not pickle).
