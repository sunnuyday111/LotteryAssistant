"""奖项服务。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import DrawRecord, Prize
from ..schemas.prize import PrizeCreate, PrizeUpdate


def list_prizes(db: Session, event_id: int) -> list[Prize]:
    """获取活动下所有奖项，按排序权重升序。"""

    stmt = (
        select(Prize)
        .where(Prize.event_id == event_id)
        .order_by(Prize.sort_order.asc(), Prize.id.asc())
    )
    return list(db.scalars(stmt).all())


def get_prize(db: Session, prize_id: int) -> Prize | None:
    """按 ID 获取奖项。"""

    return db.get(Prize, prize_id)


def create_prize(db: Session, event_id: int, data: PrizeCreate) -> Prize:
    """创建奖项。"""

    prize = Prize(
        event_id=event_id,
        name=data.name,
        quantity=data.quantity,
        sort_order=data.sort_order,
        description=data.description,
        claim_required=data.claim_required,
        draw_mode=data.draw_mode,
    )
    db.add(prize)
    db.commit()
    db.refresh(prize)
    return prize


def update_prize(db: Session, prize: Prize, data: PrizeUpdate) -> Prize:
    """更新奖项。"""

    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(prize, key, value)
    db.commit()
    db.refresh(prize)
    return prize


def delete_prize(db: Session, prize: Prize) -> None:
    """删除奖项。"""

    db.delete(prize)
    db.commit()


def count_drawn(db: Session, prize_id: int) -> int:
    """统计某奖项已中奖人数。"""

    return db.scalar(
        select(func.count(DrawRecord.id)).where(DrawRecord.prize_id == prize_id)
    ) or 0
