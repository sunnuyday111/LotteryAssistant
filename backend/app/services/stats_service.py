"""统计服务。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Checkin, DrawRecord, Event, Participant, Prize
from ..schemas.stats import EventStats, PrizeStat


def get_event_stats(db: Session, event: Event) -> EventStats:
    """获取活动数据看板统计。"""

    total = db.scalar(
        select(func.count(Participant.id)).where(Participant.event_id == event.id)
    ) or 0
    checked = db.scalar(
        select(func.count(Checkin.id)).where(Checkin.event_id == event.id)
    ) or 0

    prizes = list(
        db.scalars(
            select(Prize)
            .where(Prize.event_id == event.id)
            .order_by(Prize.sort_order.asc(), Prize.id.asc())
        ).all()
    )

    prize_stats: list[PrizeStat] = []
    for prize in prizes:
        drawn = db.scalar(
            select(func.count(DrawRecord.id)).where(DrawRecord.prize_id == prize.id)
        ) or 0
        pending = db.scalar(
            select(func.count(DrawRecord.id)).where(
                DrawRecord.prize_id == prize.id,
                DrawRecord.claim_status == "pending",
            )
        ) or 0
        claimed = db.scalar(
            select(func.count(DrawRecord.id)).where(
                DrawRecord.prize_id == prize.id,
                DrawRecord.claim_status == "claimed",
            )
        ) or 0
        prize_stats.append(
            PrizeStat(
                prize_id=prize.id,
                prize_name=prize.name,
                quantity=prize.quantity,
                drawn_count=drawn,
                claim_required=prize.claim_required,
                pending_count=pending,
                claimed_count=claimed,
            )
        )

    claim_pending = sum(p.pending_count for p in prize_stats)
    # 免领奖项的记录会被自动置为已领取，这里只统计真正需要现场核销的
    claim_claimed = sum(
        p.claimed_count for p in prize_stats if p.claim_required
    )
    claim_exempt = sum(p.drawn_count for p in prize_stats if not p.claim_required)

    return EventStats(
        event_id=event.id,
        event_name=event.name,
        total_participants=total,
        checked_in=checked,
        not_checked_in=max(total - checked, 0),
        checkin_rate=round(checked / total, 4) if total else 0.0,
        prize_stats=prize_stats,
        claim_pending=claim_pending,
        claim_claimed=claim_claimed,
        claim_exempt=claim_exempt,
    )
