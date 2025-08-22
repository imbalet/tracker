from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import Integer, Numeric, cast, func, select
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, array
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.models import TrackerDataOrm
from src.schemas import AggregatedNumericData, DataResult, StaticticsTrackerData
from src.schemas.result import FieldResult

AggregateType = Literal["min", "max", "avg", "sum"]


class DataService:

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def get_field_by_name(self, tracker_id: UUID, name: str) -> list[FieldResult]:
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
                FieldResult(
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
                    TrackerDataOrm.created_at,
                )
                .filter_by(tracker_id=tracker_id)
                .subquery()
            )

            selections = []
            if "sum" in aggregates:
                selections.append(func.sum(subquery.c.field_value).label("sum"))
            if "avg" in aggregates:
                selections.append(func.avg(subquery.c.field_value).label("avg"))
            if "min" in aggregates:
                selections.append(func.min(subquery.c.field_value).label("min"))
            if "max" in aggregates:
                selections.append(func.max(subquery.c.field_value).label("max"))

            query = (
                select(
                    subquery.c.group_id.label("id"),
                    func.min(subquery.c.created_at).label("interval_start"),
                    func.max(subquery.c.created_at).label("interval_end"),
                    func.count(subquery.c.group_id).label("record_count"),
                    *selections,
                )
                .group_by(subquery.c.group_id)
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

    async def get_all_data(
        self,
        tracker_id: UUID,
        from_date: datetime | None = None,
        exclude_fields: list[str] | None = None,
    ) -> list[DataResult]:
        exclude_fields = exclude_fields or []

        async with self.session_factory() as session:
            if exclude_fields:
                data_expr = TrackerDataOrm.data.op("-")(array(exclude_fields))
            else:
                data_expr = TrackerDataOrm.data

            conditions = [TrackerDataOrm.tracker_id == tracker_id]
            if from_date is not None:
                conditions.append(TrackerDataOrm.created_at >= from_date)
            query = (
                select(
                    TrackerDataOrm.created_at.label("date"),
                    data_expr.label("data"),
                )
                .where(*conditions)
                .order_by(TrackerDataOrm.created_at)
            )

            res = await session.execute(query)
            rows = res.all()

            return [DataResult(date=row.date, value=row.data) for row in rows]

    async def get_statistics(
        self,
        tracker_id: UUID,
        numeric_fields: list[str] | None,
        categorial_fields: list[str] | None,
        from_date: datetime | None = None,
    ) -> list[StaticticsTrackerData]:
        async with self.session_factory() as session:
            selects = []
            if numeric_fields:
                for field in numeric_fields:
                    field_expr = cast(
                        TrackerDataOrm.data[field].astext, DOUBLE_PRECISION
                    )
                    selects.extend(
                        [
                            func.min(field_expr).label(f"{field}_min"),
                            func.max(field_expr).label(f"{field}_max"),
                            func.avg(field_expr).label(f"{field}_avg"),
                            func.sum(field_expr).label(f"{field}_sum"),
                            func.count(field_expr).label(f"{field}_count"),
                        ]
                    )
            if categorial_fields:
                for field in categorial_fields:
                    field_expr = TrackerDataOrm.data[field].astext
                    selects.extend(
                        [
                            func.mode().within_group(field_expr).label(f"{field}_mode"),
                            func.count(field_expr).label(f"{field}_count"),
                        ]
                    )
            conditions = [TrackerDataOrm.tracker_id == tracker_id]
            if from_date is not None:
                conditions.append(TrackerDataOrm.created_at >= from_date)

            stmt = select(*selects).where(*conditions)

            count_stmt = select(func.count()).where(*conditions)
            count_res = await session.execute(count_stmt)
            total_count = count_res.scalar_one()
            if total_count == 0:
                return []

            res = await session.execute(stmt)
            row = res.one()
            if not row:
                return []
            result = []
            if numeric_fields:
                result.extend(
                    [
                        StaticticsTrackerData(
                            field_name=field,
                            type="numeric",
                            min=getattr(row, f"{field}_min", -1),
                            max=getattr(row, f"{field}_max", -1),
                            avg=getattr(row, f"{field}_avg", -1),
                            sum=getattr(row, f"{field}_sum", -1),
                            count=getattr(row, f"{field}_count", 0),
                        )
                        for field in numeric_fields
                    ]
                )
            if categorial_fields:
                result.extend(
                    [
                        StaticticsTrackerData(
                            field_name=field,
                            type="categorial",
                            mode=getattr(row, f"{field}_mode", ""),
                            count=getattr(row, f"{field}_count", 0),
                        )
                        for field in categorial_fields
                    ]
                )

            return result
