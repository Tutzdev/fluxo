"""Every row belongs to one user. Someone else's row looks exactly like a missing one."""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from fluxo.database import Base
from fluxo.errors import NotFoundError

_WORD_START = re.compile(r"(?<!^)(?=[A-Z])")


def get_owned[T: Base](session: Session, model: type[T], entity_id: int, user_id: int) -> T:
    """Loads a row only if it belongs to the user; 404 otherwise (a 403 would confirm it exists)."""
    entity = session.scalars(select(model).filter_by(id=entity_id, user_id=user_id)).one_or_none()

    if entity is None:
        words = _WORD_START.split(model.__name__)  # "CategoryRule" -> ["Category", "Rule"]
        code = "_".join(words).upper()
        name = " ".join(words).lower()
        raise NotFoundError(f"{code}_NOT_FOUND", f"No {name} with id {entity_id}.")

    return entity
