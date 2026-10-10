"""中奖记录模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class DrawRecord(Base):
    """中奖记录表。"""

    __tablename__ = "draw_records"
    __table_args__ = (
        # 同一活动内同一参与者只能中奖一次（默认规则，可在业务层放宽）
        UniqueConstraint("event_id", "participant_id", name="uq_draw_event_participant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    prize_id: Mapped[int] = mapped_column(
        ForeignKey("prizes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    drawn_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # 关系
    event: Mapped["Event"] = relationship(back_populates="draw_records")  # noqa: F821
    prize: Mapped["Prize"] = relationship(back_populates="draw_records")  # noqa: F821
    participant: Mapped["Participant"] = relationship(back_populates="draw_records")  # noqa: F821
