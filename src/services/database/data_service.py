from typing import Any, Literal
from uuid import UUID

from sqlalchemy import select, func, cast, Integer, Numeric
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.schemas import (
    AggregatedNumericData,
    DataResult,
)
from src.models import TrackerDataOrm


AggregateType = Literal["min", "max", "avg", "sum"]


class DataService:

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def get_field_by_name(self, tracker_id: UUID, name: str) -> list[Any]:
        async with self.session_factory() as session:
            stmt = (
                select(
                    func.row_number()
                    .over(order_by=TrackerDataOrm.created_at)
                    .label("id"),
                    TrackerDataOrm.data[name].label("value"),
                    TrackerDataOrm.created_at.label("date"),
                )
                .where(TrackerDataOrm.tracker_id == tracker_id)
                .order_by(TrackerDataOrm.created_at.asc())
            )
            res = await session.execute(stmt)
            return [
                DataResult(
                    id=row.id,
                    date=row.date,
                    value=row.value,
                )
                for row in res.all()
            ]

    async def get_sum_field(
        self,
        tracker_id: UUID,
        field: str,
        aggregates: list[AggregateType],
        interval: int,
    ) -> list[AggregatedNumericData]:
        async with self.session_factory() as session:
            field_value = cast(TrackerDataOrm.data[field].astext, Numeric).label(
                "field_value"
            )

            subquery = (
                select(
                    func.row_number()
                    .over(order_by=TrackerDataOrm.created_at)
                    .label("row_num"),
                    cast(
                        (func.row_number().over(order_by=TrackerDataOrm.created_at) - 1)
                        / interval,
                        Integer,
                    ).label("group_id"),
                    field_value,
                )
                .filter_by(tracker_id=tracker_id)
                .subquery()
            )

            selections = []
            if "sum" in aggregates:
                selections.append(func.sum(field_value).label("sum"))
            if "avg" in aggregates:
                selections.append(func.avg(field_value).label("avg"))
            if "min" in aggregates:
                selections.append(func.min(field_value).label("min"))
            if "max" in aggregates:
                selections.append(func.max(field_value).label("max"))

            query = (
                select(
                    subquery.c.group_id.label("id"),
                    func.min(TrackerDataOrm.created_at).label("interval_start"),
                    func.max(TrackerDataOrm.created_at).label("interval_end"),
                    func.count().label("record_count"),
                    *selections,
                )
                .group_by(subquery.c.group_id.cast(Integer))
                .order_by(subquery.c.group_id)
            )
            res = await session.execute(query)
            return [
                AggregatedNumericData.model_validate(row, from_attributes=True)
                for row in res.all()
            ]

    async def get_field_aggregation_days(
        self,
        tracker_id: UUID,
        field: str,
        aggregates: list[AggregateType],
        interval: str = "day",
        custom_days: int | None = None,
    ) -> list[AggregatedNumericData]:
        async with self.session_factory() as session:
            field_value = cast(TrackerDataOrm.data[field].astext, Numeric).label(
                "field_value"
            )
            group_expr = TrackerDataOrm.created_at

            if interval == "day":
                group_expr = func.date_trunc("day", TrackerDataOrm.created_at)
            elif interval == "week":
                group_expr = func.date_trunc("week", TrackerDataOrm.created_at)
            elif interval == "month":
                group_expr = func.date_trunc("month", TrackerDataOrm.created_at)
            elif interval == "custom" and custom_days:
                days_interval = custom_days * 86400
                group_expr = func.to_timestamp(
                    func.floor(
                        func.extract("epoch", TrackerDataOrm.created_at) / days_interval
                    )
                    * days_interval
                )

            selections = []
            if "sum" in aggregates:
                selections.append(func.sum(field_value).label("sum"))
            if "avg" in aggregates:
                selections.append(func.avg(field_value).label("avg"))
            if "min" in aggregates:
                selections.append(func.min(field_value).label("min"))
            if "max" in aggregates:
                selections.append(func.max(field_value).label("max"))

            query = (
                select(
                    func.row_number().over(order_by=group_expr).label("id"),
                    func.min(TrackerDataOrm.created_at).label("interval_start"),
                    func.max(TrackerDataOrm.created_at).label("interval_end"),
                    func.count().label("record_count"),
                    *selections,
                )
                .filter_by(tracker_id=tracker_id)
                .group_by(group_expr)
                .order_by(group_expr)
            )

            res = await session.execute(query)

            return [
                AggregatedNumericData.model_validate(row, from_attributes=True)
                for row in res.all()
            ]
