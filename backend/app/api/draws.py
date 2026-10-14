"""抽奖 API。"""

import io

import qrcode
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, Prize
from ..schemas.draw import (
    ClaimRequest,
    ClaimResult,
    ClaimStats,
    DrawRecordOut,
    DrawRequest,
    DrawResult,
    ManualClaimRequest,
)
from ..services import claim_service, draw_service, ws_manager
from .deps import get_event_or_404

router = APIRouter(prefix="/api/events/{event_id}/draws", tags=["抽奖"])


@router.post("", response_model=DrawResult, summary="执行抽奖")
async def draw(
    data: DrawRequest,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> DrawResult:
    result = draw_service.draw(db, event, data)

    # 抽奖成功后实时推送结果到大屏
    if result.success:
        await ws_manager.manager.broadcast(
            event.id,
            {
                "type": "draw",
                "event_id": event.id,
                "prize_id": result.prize_id,
                "prize_name": result.prize_name,
                "winners": [w.model_dump() for w in result.winners],
            },
        )

    return result


@router.get("", response_model=list[DrawRecordOut], summary="获取中奖记录")
def list_draw_records(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> list[DrawRecordOut]:
    return claim_service.list_records(db, event)


@router.get("/claim-stats", response_model=ClaimStats, summary="领奖统计")
def get_claim_stats(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> ClaimStats:
    return ClaimStats(**claim_service.claim_stats(db, event))


@router.get(
    "/records/{record_id}/claim-qrcode",
    summary="生成领奖二维码 PNG",
    response_class=Response,
)
def get_claim_qrcode(
    record_id: int,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> Response:
    record = claim_service.get_record(db, event, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="中奖记录不存在")
    url = claim_service.build_claim_url(event, record_id)
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="image/png")


@router.get(
    "/records/{record_id}/claim-preview",
    response_model=ClaimResult,
    summary="预览领奖凭证（不核销）",
)
def preview_claim(
    record_id: int,
    code: str,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> ClaimResult:
    info = claim_service.preview(db, event, record_id, code)
    if info is None:
        return ClaimResult(success=False, message="领奖码无效")
    if info.claim_status == "claimed":
        return ClaimResult(
            success=False,
            message="该奖品已被领取",
            already_claimed=True,
            info=info,
        )
    return ClaimResult(success=True, message="领奖凭证有效", info=info)


@router.post(
    "/records/{record_id}/claim",
    response_model=ClaimResult,
    summary="核销领奖",
)
async def claim_prize(
    record_id: int,
    data: ClaimRequest,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> ClaimResult:
    result = claim_service.claim(db, event, record_id, data.code, phone=data.phone)
    if result.success:
        await ws_manager.manager.broadcast(
            event.id,
            {
                "type": "claim",
                "event_id": event.id,
                "record_id": record_id,
                "stats": claim_service.claim_stats(db, event),
            },
        )
    return result


@router.post(
    "/records/{record_id}/manual-claim",
    response_model=ClaimResult,
    summary="主办方手动核销领奖",
)
async def manual_claim_prize(
    record_id: int,
    data: ManualClaimRequest | None = None,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> ClaimResult:
    """无需领奖码，由主办方在后台直接核销（手机号可选二次确认）。"""

    result = claim_service.manual_claim(
        db, event, record_id, phone=data.phone if data else None
    )
    if result.success:
        await ws_manager.manager.broadcast(
            event.id,
            {
                "type": "claim",
                "event_id": event.id,
                "record_id": record_id,
                "stats": claim_service.claim_stats(db, event),
            },
        )
    return result


@router.delete(
    "/records/{record_id}/claim",
    response_model=DrawRecordOut,
    summary="撤销领奖",
)
async def revoke_claim(
    record_id: int,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> DrawRecordOut:
    out = claim_service.revoke_claim(db, event, record_id)
    if out is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="中奖记录不存在")
    await ws_manager.manager.broadcast(
        event.id,
        {
            "type": "claim",
            "event_id": event.id,
            "record_id": record_id,
            "stats": claim_service.claim_stats(db, event),
        },
    )
    return out


@router.delete("", summary="重置抽奖记录")
async def reset_draws(
    prize_id: int | None = None,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> dict:
    if prize_id is not None:
        prize = db.get(Prize, prize_id)
        if prize is None or prize.event_id != event.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="奖项不存在"
            )

    deleted = draw_service.reset_draws(db, event.id, prize_id)

    await ws_manager.manager.broadcast(
        event.id,
        {"type": "draw_reset", "event_id": event.id, "prize_id": prize_id},
    )

    return {"deleted": deleted}
