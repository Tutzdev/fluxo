"""Gives each statement line an identity that survives being imported again.

People export overlapping periods all the time (October, then "last 90 days").
The same bank line must land on the same fingerprint every time, so the
unique (account_id, fingerprint) constraint can drop it as a duplicate.

- The bank's own id (OFX FITID, Nubank 'Identificador') is used when present.
- Otherwise: date + amount + normalized description + occurrence. The
  occurrence counter keeps two real, identical coffees on the same day apart,
  and numbers them the same way in every file that contains them.
"""

import hashlib
import uuid
from collections import Counter
from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from fluxo.imports.parsers.base import StatementLine
from fluxo.text import normalize_description


def fingerprint_lines(lines: Sequence[StatementLine]) -> list[str]:
    seen: Counter[tuple[date, Decimal, str]] = Counter()
    fingerprints = []

    for line in lines:
        if line.external_id:
            fingerprints.append(f"id:{_sha256(line.external_id)}")
            continue

        key = (line.occurred_on, line.amount, normalize_description(line.description))
        occurrence = seen[key]
        seen[key] += 1

        fingerprints.append(f"ln:{_sha256(f'{key[0]}|{key[1]}|{key[2]}|{occurrence}')}")

    return fingerprints


def manual_fingerprint() -> str:
    """A transaction typed by hand is always new, so it gets a fingerprint nothing can collide with."""
    return f"manual:{uuid.uuid4().hex}"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
