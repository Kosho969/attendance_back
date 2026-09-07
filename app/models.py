import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    hosted_activities: Mapped[list["Activity"]] = relationship(
        back_populates="host", foreign_keys="Activity.host_id"
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    host_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    qr_token: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    host: Mapped["User"] = relationship(foreign_keys=[host_id], back_populates="hosted_activities")
    creator: Mapped["User | None"] = relationship(foreign_keys=[created_by])
    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )

    @property
    def attendances_count(self) -> int:
        return len(self.attendances)


class Attendee(Base):
    __tablename__ = "attendees"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    attendances: Mapped[list["Attendance"]] = relationship(back_populates="attendee")


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint("activity_id", "attendee_id", name="uq_activity_attendee"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"))
    attendee_id: Mapped[int] = mapped_column(ForeignKey("attendees.id", ondelete="CASCADE"))
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    activity: Mapped["Activity"] = relationship(back_populates="attendances")
    attendee: Mapped["Attendee"] = relationship(back_populates="attendances")
