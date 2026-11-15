"""Only registered when DEMO_ENABLED=true."""

from flask_openapi3 import APIBlueprint, Tag

from fluxo.auth.current import auth_service
from fluxo.auth.schemas import SessionResponse, UserResponse
from fluxo.categorization.service import CategorizationService
from fluxo.components import components
from fluxo.database import db_session
from fluxo.demo.service import DemoService

blueprint = APIBlueprint(
    "demo",
    __name__,
    url_prefix="/api/demo",
    abp_tags=[Tag(name="Demo", description="A private account with six months of sample data")],
)


@blueprint.post("/session", responses={201: SessionResponse})
def start_demo() -> tuple[dict[str, object], int]:
    session = db_session()
    service = DemoService(
        session,
        components().clock,
        auth_service(),
        CategorizationService(session, components().classifier_cache),
    )
    issued = service.start()

    user = UserResponse(id=issued.user.id, name=issued.user.name, email=issued.user.email)
    response = SessionResponse(token=issued.token, expires_at=issued.expires_at, user=user)
    return response.model_dump(mode="json"), 201
