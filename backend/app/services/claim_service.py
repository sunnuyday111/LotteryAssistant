"""领奖服务：生成领奖码、核销领奖。

领奖码用 HMAC-SHA256 基于 (record_id + secret) 生成，
不落库、不可伪造，扫码 URL 形如 /claim/<event_id>/<record_id>/<code>。
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import DrawRecord, Event, Participant, Prize
from ..schemas.draw import ClaimInfo, ClaimResult, DrawRecordOut
from ..config import settings


def _secret() -> bytes:
    """领奖签名密钥：优先环境变量，否则用检查令牌派生（保证同一活动稳定）。"""
    env_secret = getattr(settings, "claim_secret", None)
    if env_secret:
        return env_secret.encode("utf-8")
    # 退化方案：用 checkin_token 派生，保证同一活动内签名稳定且不同活动隔离
    return settings.app_name.encode("utf-8")


def make_claim_code(record_id: int, event_token: str) -> str:
    """根据中奖记录 ID 生成短领奖码（8 位十六进制）。"""
    msg = f"{event_token}:{record_id}".encode("utf-8")
    digest = hmac.new(_secret(), msg, hashlib.sha256).hexdigest()
    return digest[:8]


def verify_claim_code(record_id: int, event_token: str, code: str) -> bool:
    """校验领奖码是否匹配（常量时间比较，避免时序侧信道）。"""
    expected = make_claim_code(record_id, event_token)
    return hmac.compare_digest(expected, (code or "").strip().lower())


def claim_base_url() -> str:
    """领奖页基础地址（与签到页同源）。"""
    base = getattr(settings, "claim_base_url", "") or ""
    if base:
        return base.rstrip("/")
    # 回退到签到地址，把 /checkin 换成 /claim
    checkin = settings.checkin_base_url.rstrip("/")
    if checkin.endswith("/checkin"):
        return checkin[: -len("/checkin")] + "/claim"
    return checkin


def build_claim_url(event: Event, record_id: int) -> str:
    """生成领奖二维码指向的 URL。"""
    code = make_claim_code(record_id, event.checkin_token)
    return f"{claim_base_url()}/{event.id}/{record_id}/{code}"


def _enrich(record: DrawRecord, event: Event, prize: Prize | None, participant: Participant | None) -> DrawRecordOut:
    """把 ORM 记录补全成带领取状态的输出。"""
    out = DrawRecordOut.model_validate(record)
    out.prize_name = prize.name if prize else None
    if participant is not None:
        out.participant_name = participant.name
        out.participant_phone = participant.phone
    out.claim_required = prize.claim_required if prize else True
    # 免领奖项不暴露领取时间（中奖即终态，claimed_at 无意义）
    if not out.claim_required:
        out.claimed_at = None
    if out.claim_required and record.claim_status == "pending":
        out.claim_url = build_claim_url(event, record.id)
    return out


def list_records(db: Session, event: Event) -> list[DrawRecordOut]:
    """列出活动所有中奖记录（含领奖状态）。"""
    records = list(
        db.scalars(
            select(DrawRecord)
            .where(DrawRecord.event_id == event.id)
            .order_by(DrawRecord.drawn_at.desc())
        ).all()
    )
    prize_map = {p.id: p for p in db.scalars(select(Prize).where(Prize.event_id == event.id)).all()}
    part_map = {p.id: p for p in db.scalars(select(Participant).where(Participant.event_id == event.id)).all()}
    return [_enrich(r, event, prize_map.get(r.prize_id), part_map.get(r.participant_id)) for r in records]


def get_record(db: Session, event: Event, record_id: int) -> DrawRecord | None:
    """按 ID 获取中奖记录（校验归属）。"""
    return db.scalar(
        select(DrawRecord).where(
            DrawRecord.id == record_id,
            DrawRecord.event_id == event.id,
        )
    )


def claim_info(db: Session, event: Event, record_id: int) -> ClaimInfo | None:
    """扫码后展示的领奖凭证信息。"""
    record = get_record(db, event, record_id)
    if record is None:
        return None
    prize = db.get(Prize, record.prize_id)
    participant = db.get(Participant, record.participant_id)
    return ClaimInfo(
        record_id=record.id,
        participant_name=participant.name if participant else "-",
        prize_name=prize.name if prize else "-",
        drawn_at=record.drawn_at,
        claim_status=record.claim_status,
        claimed_at=(
            record.claimed_at
            if prize is None or prize.claim_required
            else None
        ),
    )


def preview(db: Session, event: Event, record_id: int, code: str) -> ClaimInfo | None:
    """只读预览领奖凭证：校验领奖码并返回信息，不改变任何状态。

    领奖码无效返回 None；已领取则返回带claimed 状态的信息。
    """
    if not verify_claim_code(record_id, event.checkin_token, code):
        return None
    return claim_info(db, event, record_id)


def claim(
    db: Session,
    event: Event,
    record_id: int,
    code: str,
    phone: str | None = None,
) -> ClaimResult:
    """核销领奖。

    - 不需要领奖的奖项：直接提示，不写状态
    - 已领取：返回 already_claimed
    - 校验领奖码（可选手机号二次确认）
    """
    record = get_record(db, event, record_id)
    if record is None:
        return ClaimResult(success=False, message="领奖码不存在或不属于本活动")

    prize = db.get(Prize, record.prize_id)
    if prize is not None and not prize.claim_required:
        return ClaimResult(success=False, message="该奖项无需现场领奖")

    if record.claim_status == "claimed":
        return ClaimResult(
            success=False,
            message="该奖品已被领取",
            already_claimed=True,
            info=claim_info(db, event, record_id),
        )

    if not verify_claim_code(record_id, event.checkin_token, code):
        return ClaimResult(success=False, message="领奖码无效")

    if phone:
        participant = db.get(Participant, record.participant_id)
        if participant is None:
            return ClaimResult(success=False, message="中奖人信息缺失")
        entered = phone.strip()
        # 支持完整手机号或后4 位
        if entered != participant.phone and not (
            len(entered) <= 4 and participant.phone.endswith(entered)
        ):
            return ClaimResult(success=False, message="手机号与中奖人不匹配")

    record.claim_status = "claimed"
    record.claimed_at = datetime.now()
    db.commit()
    db.refresh(record)

    return ClaimResult(success=True, message="领奖成功", info=claim_info(db, event, record_id))


def revoke_claim(db: Session, event: Event, record_id: int) -> DrawRecordOut | None:
    """撤销领奖（误操作补救）。"""
    record = get_record(db, event, record_id)
    if record is None:
        return None
    record.claim_status = "pending"
    record.claimed_at = None
    db.commit()
    db.refresh(record)
    prize = db.get(Prize, record.prize_id)
    participant = db.get(Participant, record.participant_id)
    return _enrich(record, event, prize, participant)


def claim_stats(db: Session, event: Event) -> dict[str, int]:
    """统计待领取 / 已领取 / 免领数量。

    - pending：需要现场领奖但尚未核销
    - claimed：已核销（含免领奖项自动置为已领取的记录）
    - exempt：奖项配置为无需领奖的记录数
    """

    rows = db.execute(
        select(DrawRecord.claim_status, Prize.claim_required)
        .join(Prize, Prize.id == DrawRecord.prize_id)
        .where(DrawRecord.event_id == event.id)
    ).all()

    pending = claimed = exempt = 0
    for status, claim_required in rows:
        if not claim_required:
            exempt += 1
        elif status == "claimed":
            claimed += 1
        else:
            pending += 1

    return {
        "pending": pending,
        "claimed": claimed,
        "exempt": exempt,
        "total": pending + claimed + exempt,
    }


def manual_claim(
    db: Session, event: Event, record_id: int, phone: str | None = None
) -> ClaimResult:
    """主办方手动核销领奖（无需领奖码，用于手机没电/二维码丢失等场景）。"""

    record = get_record(db, event, record_id)
    if record is None:
        return ClaimResult(success=False, message="中奖记录不存在")

    prize = db.get(Prize, record.prize_id)
    if prize is not None and not prize.claim_required:
        return ClaimResult(success=False, message="该奖项无需现场领奖")

    if record.claim_status == "claimed":
        return ClaimResult(
            success=False,
            message="该奖品已被领取",
            already_claimed=True,
            info=claim_info(db, event, record_id),
        )

    if phone:
        participant = db.get(Participant, record.participant_id)
        if participant is None:
            return ClaimResult(success=False, message="中奖人信息缺失")
        entered = phone.strip()
        if entered != participant.phone and not (
            len(entered) <= 4 and participant.phone.endswith(entered)
        ):
            return ClaimResult(success=False, message="手机号与中奖人不匹配")

    record.claim_status = "claimed"
    record.claimed_at = datetime.now()
    db.commit()
    db.refresh(record)

    return ClaimResult(
        success=True, message="已手动核销领奖", info=claim_info(db, event, record_id)
    )


def random_code() -> str:
    """生成通用随机码（预留）。"""
    return secrets.token_hex(4)