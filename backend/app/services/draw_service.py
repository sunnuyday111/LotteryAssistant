"""抽奖服务（核心业务）。

抽奖结果由后端随机生成并持久化，前端仅负责动画展示。
"""

import random
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Checkin, DrawRecord, Event, Participant, Prize
from ..schemas.draw import DrawRequest, DrawResult, DrawWinner


def _eligible_participants(
    db: Session, event: Event, allow_repeat_winner: bool
) -> list[Participant]:
    """获取有资格参与抽奖的候选人。

    默认仅已签到者可参与；若不允许重复中奖，则排除已中奖者。
    """

    # 已签到参与者 ID
    checked_ids = {
        c.participant_id
        for c in db.scalars(
            select(Checkin).where(Checkin.event_id == event.id)
        ).all()
    }

    stmt = select(Participant).where(Participant.event_id == event.id)
    participants = list(db.scalars(stmt).all())

    # 仅保留已签到者
    candidates = [p for p in participants if p.id in checked_ids]

    if not allow_repeat_winner:
        won_ids = {
            r.participant_id
            for r in db.scalars(
                select(DrawRecord).where(DrawRecord.event_id == event.id)
            ).all()
        }
        candidates = [p for p in candidates if p.id not in won_ids]

    return candidates


def draw(db: Session, event: Event, data: DrawRequest) -> DrawResult:
    """执行抽奖。

    - 校验奖项归属与剩余名额；
    - 从已签到且未中奖的候选人中随机抽取；
    - 写入中奖记录并返回结果。
    """

    prize = db.get(Prize, data.prize_id)
    if prize is None or prize.event_id != event.id:
        return DrawResult(
            success=False,
            message="奖项不存在或不属于当前活动",
            prize_id=data.prize_id,
            prize_name="",
        )

    # 剩余名额
    drawn_count = len(
        db.scalars(
            select(DrawRecord).where(DrawRecord.prize_id == prize.id)
        ).all()
    )
    remaining = prize.quantity - drawn_count
    if remaining <= 0:
        return DrawResult(
            success=False,
            message=f"奖项「{prize.name}」名额已抽完",
            prize_id=prize.id,
            prize_name=prize.name,
        )

    count = min(data.count, remaining)

    candidates = _eligible_participants(db, event, data.allow_repeat_winner)
    if not candidates:
        return DrawResult(
            success=False,
            message="没有符合条件的候选人（需已签到且未中奖）",
            prize_id=prize.id,
            prize_name=prize.name,
        )

    count = min(count, len(candidates))
    winners = random.sample(candidates, count)

    now = datetime.now()
    records: list[DrawRecord] = []
    for participant in winners:
        record = DrawRecord(
            event_id=event.id,
            prize_id=prize.id,
            participant_id=participant.id,
            drawn_at=now,
        )
        db.add(record)
        records.append(record)

    db.commit()

    winner_list = [
        DrawWinner(
            participant_id=p.id,
            name=p.name,
            phone=p.phone,
            department=p.department,
        )
        for p in winners
    ]

    return DrawResult(
        success=True,
        message=f"成功抽取 {len(winner_list)} 位中奖者",
        prize_id=prize.id,
        prize_name=prize.name,
        winners=winner_list,
    )


def list_draw_records(db: Session, event_id: int) -> list[DrawRecord]:
    """获取活动所有中奖记录。"""

    stmt = (
        select(DrawRecord)
        .where(DrawRecord.event_id == event_id)
        .order_by(DrawRecord.drawn_at.asc())
    )
    return list(db.scalars(stmt).all())


def reset_draws(db: Session, event_id: int, prize_id: int | None = None) -> int:
    """重置抽奖记录（可指定奖项）。返回删除数量。"""

    stmt = select(DrawRecord).where(DrawRecord.event_id == event_id)
    if prize_id is not None:
        stmt = stmt.where(DrawRecord.prize_id == prize_id)

    records = list(db.scalars(stmt).all())
    for record in records:
        db.delete(record)
    db.commit()
    return len(records)
