import datetime
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey, DateTime, text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship


class Base(DeclarativeBase):
    pass


class UserOrm(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    chat_id: Mapped[str] = mapped_column(unique=True)

    trackers: Mapped[list["TrackerOrm"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __init__(self, chat_id: str):
        self.chat_id = chat_id


class TrackerStructureOrm(Base):
    __tablename__ = "tracker_structure"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    data: Mapped[dict] = mapped_column(JSONB)

    def __init__(self, data: dict):
        self.data = data


class TrackerOrm(Base):
    __tablename__ = "trackers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str]
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(UserOrm.id, ondelete="CASCADE"), index=True
    )
    structure_id: Mapped[UUID] = mapped_column(
        ForeignKey(TrackerStructureOrm.id, ondelete="RESTRICT")
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', now())")
    )
    user: Mapped["UserOrm"] = relationship(back_populates="trackers", lazy="selectin")
    structure: Mapped["TrackerStructureOrm"] = relationship(lazy="joined")
    data: Mapped[list["TrackerDataOrm"]] = relationship(
        back_populates="tracker",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __init__(self, user_id: UUID, structure_id: UUID, name: str):
        self.user_id = user_id
        self.structure_id = structure_id
        self.name = name


class TrackerDataOrm(Base):
    __tablename__ = "tracker_data"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tracker_id: Mapped[UUID] = mapped_column(
        ForeignKey(TrackerOrm.id, ondelete="CASCADE"), index=True
    )
    data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("TIMEZONE('utc', now())")
    )
    tracker: Mapped["TrackerOrm"] = relationship(back_populates="data", lazy="selectin")

    def __init__(self, tracker_id: UUID, data: dict):
        self.tracker_id = tracker_id
        self.data = data
