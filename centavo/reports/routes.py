from flask_openapi3 import APIBlueprint, Tag

from centavo.auth.current import current_user_id, require_user
from centavo.components import components
from centavo.database import db_session
from centavo.month import Month
from centavo.openapi import BEARER_SECURITY
from centavo.reports.schemas import (
    CategorySpendingResponse,
    ForecastResponse,
    MonthQuery,
    MonthTotalsResponse,
    SummaryResponse,
    TrendQuery,
    TrendResponse,
    UpcomingResponse,
)
from centavo.reports.service import ReportService

blueprint = APIBlueprint(
    "reports",
    __name__,
    url_prefix="/api/reports",
    abp_tags=[Tag(name="Reports", description="The month at a glance, the trend and the forecast")],
    abp_security=BEARER_SECURITY,
)
blueprint.before_request(require_user)


def _requested_month(text: str | None) -> Month:
    return Month.parse(text) if text else Month.of(components().clock.today())


@blueprint.get("/summary", responses={200: SummaryResponse})
def summary(query: MonthQuery) -> dict[str, object]:
    result = ReportService(db_session()).summary(current_user_id(), _requested_month(query.month))

    response = SummaryResponse(
        month=str(result.month),
        income=result.income,
        expenses=result.expenses,
        net=result.net,
        needs_review=result.needs_review,
        by_category=[
            CategorySpendingResponse(
                category_id=item.category_id,
                name=item.name,
                color=item.color,
                amount=item.amount,
            )
            for item in result.by_category
        ],
    )
    return response.model_dump(mode="json")


@blueprint.get("/trend", responses={200: TrendResponse})
def trend(query: TrendQuery) -> dict[str, object]:
    months = ReportService(db_session()).trend(current_user_id(), _requested_month(query.month), query.months)

    items = [
        MonthTotalsResponse(
            month=str(item.month),
            income=item.income,
            expenses=item.expenses,
            net=item.income - item.expenses,
        )
        for item in months
    ]
    return TrendResponse(items=items).model_dump(mode="json")


@blueprint.get("/forecast", responses={200: ForecastResponse})
def forecast() -> dict[str, object]:
    result = ReportService(db_session()).forecast(current_user_id(), components().clock.today())

    response = ForecastResponse(
        today=result.today,
        days_left=result.days_left,
        balance_now=result.balance_now,
        expected_income=result.expected_income,
        expected_bills=result.expected_bills,
        projected_day_to_day=result.projected_day_to_day,
        projected_end_balance=result.projected_end_balance,
        upcoming=[
            UpcomingResponse(
                description=series.description,
                amount=series.typical_amount,
                expected_day=series.typical_day,
                category_id=series.category_id,
                months_seen=series.months_seen,
            )
            for series in result.upcoming
        ],
    )
    return response.model_dump(mode="json")
