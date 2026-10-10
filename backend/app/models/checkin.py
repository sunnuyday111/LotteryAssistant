"""签到记录模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Checkin(Base):
    """签到记录表。

    每个参与者最多一条签到记录（participant_id 唯一）。
    """

    __tablename__ = "checkins"
    __table_args__ = (
        UniqueConstraint("participant_id", name="uq_checkin_participant"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    participant_id: Mapped[int] = mapped_column(
        ForeignKey("participants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    # 签到方式：qrcode(扫码) / manual(手动)
    method: Mapped[str] = mapped_column(String(20), default="qrcode", nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 关系
    event: Mapped["Event"] = relationship(back_populates="checkins")  # noqa: F821
    participant: Mapped["Participant"] = relationship(back_populates="checkin")  # noqa: F821
