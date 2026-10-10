"""抽奖 API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, Participant, Prize
from ..schemas.draw import DrawRecordOut, DrawRequest, DrawResult
from ..services import draw_service, ws_manager
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
    records = draw_service.list_draw_records(db, event.id)

    prize_map = {
        p.id: p.name
        for p in db.query(Prize).filter(Prize.event_id == event.id).all()
    }
    participant_map = {
        p.id: p
        for p in db.query(Participant).filter(Participant.event_id == event.id).all()
    }

    result: list[DrawRecordOut] = []
    for r in records:
        out = DrawRecordOut.model_validate(r)
        out.prize_name = prize_map.get(r.prize_id)
        p = participant_map.get(r.participant_id)
        if p is not None:
            out.participant_name = p.name
            out.participant_phone = p.phone
        result.append(out)
    return result


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
