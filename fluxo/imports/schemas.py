from datetime import datetime

from flask_openapi3 import FileStorage
from pydantic import BaseModel, Field

from fluxo.imports.models import FileFormat


class ImportForm(BaseModel):
    file: FileStorage = Field(description="A CSV or OFX statement exported from the bank")
    account_id: int
    invert_amounts: bool = Field(
        default=False,
        description="Credit card CSVs often list purchases as positive numbers; this flips them.",
    )


class ImportResponse(BaseModel):
    id: int
    account_id: int
    filename: str
    file_format: FileFormat
    imported_count: int
    duplicate_count: int
    categorized_count: int
    created_at: datetime


class ImportListResponse(BaseModel):
    items: list[ImportResponse]
