from flask_openapi3 import APIBlueprint, Tag

from fluxo.auth.current import current_user_id, require_user
from fluxo.categorization.service import CategorizationService
from fluxo.components import components
from fluxo.database import db_session
from fluxo.imports.models import StatementImport
from fluxo.imports.schemas import ImportForm, ImportListResponse, ImportResponse
from fluxo.imports.service import ImportService
from fluxo.openapi import BEARER_SECURITY

blueprint = APIBlueprint(
    "imports",
    __name__,
    url_prefix="/api/imports",
    abp_tags=[Tag(name="Imports", description="Upload bank statements (CSV or OFX)")],
    abp_security=BEARER_SECURITY,
)
blueprint.before_request(require_user)


def _service() -> ImportService:
    session = db_session()
    return ImportService(session, CategorizationService(session, components().classifier_cache))


@blueprint.post("", responses={201: ImportResponse})
def import_statement(form: ImportForm) -> tuple[dict[str, object], int]:
    statement_import = _service().import_statement(
        user_id=current_user_id(),
        account_id=form.account_id,
        filename=form.file.filename or "statement",
        content=form.file.read(),
        invert_amounts=form.invert_amounts,
    )
    return _to_response(statement_import).model_dump(mode="json"), 201


@blueprint.get("", responses={200: ImportListResponse})
def list_imports() -> dict[str, object]:
    imports = _service().recent(current_user_id())
    return ImportListResponse(items=[_to_response(item) for item in imports]).model_dump(mode="json")


def _to_response(statement_import: StatementImport) -> ImportResponse:
    return ImportResponse(
        id=statement_import.id,
        account_id=statement_import.account_id,
        filename=statement_import.filename,
        file_format=statement_import.file_format,
        imported_count=statement_import.imported_count,
        duplicate_count=statement_import.duplicate_count,
        categorized_count=statement_import.categorized_count,
        created_at=statement_import.created_at,
    )
