"""参与者模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Participant(Base):
    """参与者名单表。"""

    __tablename__ = "participants"
    __table_args__ = (
        # 同一活动内手机号唯一，防止重复导入
        UniqueConstraint("event_id", "phone", name="uq_participant_event_phone"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # 关系
    event: Mapped["Event"] = relationship(back_populates="participants")  # noqa: F821
    checkin: Mapped["Checkin | None"] = relationship(  # noqa: F821
        back_populates="participant", cascade="all, delete-orphan", uselist=False
    )
    draw_records: Mapped[list["DrawRecord"]] = relationship(  # noqa: F821
        back_populates="participant", cascade="all, delete-orphan"
    )
