"""签到服务。"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Checkin, Event, Participant
from ..schemas.checkin import CheckinResult


def get_checkin_by_participant(
    db: Session, participant_id: int
) -> Checkin | None:
    """获取参与者的签到记录。"""

    stmt = select(Checkin).where(Checkin.participant_id == participant_id)
    return db.scalars(stmt).first()


def check_in(
    db: Session,
    event: Event,
    phone: str,
    name: str | None = None,
    ip_address: str | None = None,
) -> CheckinResult:
    """执行签到。

    规则：
    - 手机号必须在活动名单中；
    - 同一参与者不能重复签到；
    - 若提供姓名，则需与名单一致。
    """

    phone = phone.strip()
    stmt = select(Participant).where(
        Participant.event_id == event.id, Participant.phone == phone
    )
    participant = db.scalars(stmt).first()

    if participant is None:
        return CheckinResult(
            success=False,
            message="未在活动名单中找到该手机号，请联系主办方",
        )

    if name and name.strip() and name.strip() != participant.name:
        return CheckinResult(
            success=False,
            message="姓名与名单不一致，请核对后重试",
        )

    existing = get_checkin_by_participant(db, participant.id)
    if existing is not None:
        return CheckinResult(
            success=True,
            message="您已签到，无需重复签到",
            participant_name=participant.name,
            checked_in_at=existing.checked_in_at,
            already_checked_in=True,
        )

    checkin = Checkin(
        event_id=event.id,
        participant_id=participant.id,
        checked_in_at=datetime.now(),
        method="qrcode",
        ip_address=ip_address,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return CheckinResult(
        success=True,
        message="签到成功，欢迎参加活动！",
        participant_name=participant.name,
        checked_in_at=checkin.checked_in_at,
        already_checked_in=False,
    )


def manual_check_in(
    db: Session, event: Event, participant: Participant
) -> CheckinResult:
    """主办方手动签到。"""

    existing = get_checkin_by_participant(db, participant.id)
    if existing is not None:
        return CheckinResult(
            success=True,
            message="该参与者已签到",
            participant_name=participant.name,
            checked_in_at=existing.checked_in_at,
            already_checked_in=True,
        )

    checkin = Checkin(
        event_id=event.id,
        participant_id=participant.id,
        checked_in_at=datetime.now(),
        method="manual",
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return CheckinResult(
        success=True,
        message="手动签到成功",
        participant_name=participant.name,
        checked_in_at=checkin.checked_in_at,
        already_checked_in=False,
    )


def cancel_check_in(db: Session, participant: Participant) -> bool:
    """取消签到。"""

    existing = get_checkin_by_participant(db, participant.id)
    if existing is None:
        return False
    db.delete(existing)
    db.commit()
    return True


def count_checkins(db: Session, event_id: int) -> int:
    """统计签到人数。"""

    return len(
        db.scalars(select(Checkin).where(Checkin.event_id == event_id)).all()
    )
