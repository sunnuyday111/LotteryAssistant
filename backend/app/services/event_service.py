"""活动服务。"""

import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Checkin, Event, Participant, Prize
from ..schemas.event import EventCreate, EventDetailOut, EventUpdate


def _generate_token() -> str:
    """生成签到令牌。"""

    return secrets.token_urlsafe(24)


def list_events(db: Session) -> list[Event]:
    """获取所有活动，按创建时间倒序。"""

    stmt = select(Event).order_by(Event.created_at.desc())
    return list(db.scalars(stmt).all())


def get_event(db: Session, event_id: int) -> Event | None:
    """按 ID 获取活动。"""

    return db.get(Event, event_id)


def get_event_by_token(db: Session, token: str) -> Event | None:
    """按签到令牌获取活动。"""

    stmt = select(Event).where(Event.checkin_token == token)
    return db.scalars(stmt).first()


def create_event(db: Session, data: EventCreate) -> Event:
    """创建活动。"""

    event = Event(
        name=data.name,
        description=data.description,
        location=data.location,
        start_time=data.start_time,
        end_time=data.end_time,
        status="draft",
        checkin_token=_generate_token(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, event: Event, data: EventUpdate) -> Event:
    """更新活动。"""

    payload = data.model_dump(exclude_unset=True)
    for key, value in payload.items():
        setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: Event) -> None:
    """删除活动（级联删除关联数据）。"""

    db.delete(event)
    db.commit()


def get_event_detail(db: Session, event: Event) -> EventDetailOut:
    """获取活动详情（含统计）。"""

    participant_count = db.scalar(
        select(func.count(Participant.id)).where(Participant.event_id == event.id)
    )
    checkin_count = db.scalar(
        select(func.count(Checkin.id)).where(Checkin.event_id == event.id)
    )
    prize_count = db.scalar(
        select(func.count(Prize.id)).where(Prize.event_id == event.id)
    )

    detail = EventDetailOut.model_validate(event)
    detail.participant_count = participant_count or 0
    detail.checkin_count = checkin_count or 0
    detail.prize_count = prize_count or 0
    return detail
