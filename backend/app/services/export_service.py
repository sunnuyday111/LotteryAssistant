"""导出服务：签到明细、中奖名单导出为 Excel。"""

import io

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Checkin, DrawRecord, Event, Participant, Prize


def export_checkin_list(db: Session, event: Event) -> bytes:
    """导出签到明细 Excel。

    列：姓名、手机号、部门、签到状态、签到时间、签到方式。
    """

    participants = list(
        db.scalars(
            select(Participant)
            .where(Participant.event_id == event.id)
            .order_by(Participant.created_at.asc())
        ).all()
    )
    checkins = {
        c.participant_id: c
        for c in db.scalars(
            select(Checkin).where(Checkin.event_id == event.id)
        ).all()
    }

    rows = []
    for p in participants:
        c = checkins.get(p.id)
        rows.append(
            {
                "姓名": p.name,
                "手机号": p.phone,
                "部门": p.department or "",
                "签到状态": "已签到" if c else "未签到",
                "签到时间": c.checked_in_at.strftime("%Y-%m-%d %H:%M:%S") if c else "",
                "签到方式": {"qrcode": "扫码", "manual": "手动"}.get(c.method, "")
                if c
                else "",
            }
        )

    df = pd.DataFrame(rows, columns=["姓名", "手机号", "部门", "签到状态", "签到时间", "签到方式"])
    return _to_excel_bytes(df, "签到明细")


def export_draw_list(db: Session, event: Event) -> bytes:
    """导出中奖名单 Excel。

    列：奖项、姓名、手机号、部门、中奖时间、领取状态、领取时间。
    """

    records = list(
        db.scalars(
            select(DrawRecord)
            .where(DrawRecord.event_id == event.id)
            .order_by(DrawRecord.drawn_at.asc())
        ).all()
    )

    prize_map = {
        p.id: p
        for p in db.scalars(select(Prize).where(Prize.event_id == event.id)).all()
    }
    participant_map = {
        p.id: p
        for p in db.scalars(
            select(Participant).where(Participant.event_id == event.id)
        ).all()
    }

    rows = []
    for r in records:
        p = participant_map.get(r.participant_id)
        prize = prize_map.get(r.prize_id)
        if prize is not None and not prize.claim_required:
            claim_status = "无需领奖"
        elif r.claim_status == "claimed":
            claim_status = "已领取"
        else:
            claim_status = "待领取"
        # 免领奖项不记录领取时间（中奖即终态）
        claimed_at = r.claimed_at if prize is None or prize.claim_required else None
        rows.append(
            {
                "奖项": prize.name if prize else "",
                "姓名": p.name if p else "",
                "手机号": p.phone if p else "",
                "部门": (p.department or "") if p else "",
                "中奖时间": r.drawn_at.strftime("%Y-%m-%d %H:%M:%S"),
                "领取状态": claim_status,
                "领取时间": claimed_at.strftime("%Y-%m-%d %H:%M:%S")
                if claimed_at
                else "",
            }
        )

    df = pd.DataFrame(
        rows,
        columns=["奖项", "姓名", "手机号", "部门", "中奖时间", "领取状态", "领取时间"],
    )
    return _to_excel_bytes(df, "中奖名单")


def _to_excel_bytes(df: pd.DataFrame, sheet_name: str) -> bytes:
    """将 DataFrame 转为 Excel 字节流。"""

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    buffer.seek(0)
    return buffer.getvalue()
