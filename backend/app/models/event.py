"""活动模型。"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Event(Base):
    """活动信息表。"""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 活动状态：draft(草稿) / ongoing(进行中) / finished(已结束)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)

    # 签到令牌：用于生成签到二维码，避免直接暴露活动 ID
    checkin_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # 关系
    participants: Mapped[list["Participant"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    checkins: Mapped[list["Checkin"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    prizes: Mapped[list["Prize"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
    draw_records: Mapped[list["DrawRecord"]] = relationship(  # noqa: F821
        back_populates="event", cascade="all, delete-orphan"
    )
