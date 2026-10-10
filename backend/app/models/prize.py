"""奖项模型。"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Prize(Base):
    """奖项配置表。"""

    __tablename__ = "prizes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # 奖项数量（可中奖名额）
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # 排序权重，数值越小越靠前
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # 奖品描述
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # 关系
    event: Mapped["Event"] = relationship(back_populates="prizes")  # noqa: F821
    draw_records: Mapped[list["DrawRecord"]] = relationship(  # noqa: F821
        back_populates="prize", cascade="all, delete-orphan"
    )
