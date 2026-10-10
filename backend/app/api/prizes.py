"""奖项配置 API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, Prize
from ..schemas.prize import PrizeCreate, PrizeOut, PrizeUpdate
from ..services import prize_service
from .deps import get_event_or_404

router = APIRouter(prefix="/api/events/{event_id}/prizes", tags=["奖项配置"])


def _to_out(db: Session, prize: Prize) -> PrizeOut:
    out = PrizeOut.model_validate(prize)
    out.drawn_count = prize_service.count_drawn(db, prize.id)
    return out


@router.get("", response_model=list[PrizeOut], summary="获取奖项列表")
def list_prizes(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> list[PrizeOut]:
    return [_to_out(db, p) for p in prize_service.list_prizes(db, event.id)]


@router.post(
    "",
    response_model=PrizeOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建奖项",
)
def create_prize(
    data: PrizeCreate,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> PrizeOut:
    prize = prize_service.create_prize(db, event.id, data)
    return _to_out(db, prize)


@router.put("/{prize_id}", response_model=PrizeOut, summary="更新奖项")
def update_prize(
    prize_id: int,
    data: PrizeUpdate,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> PrizeOut:
    prize = prize_service.get_prize(db, prize_id)
    if prize is None or prize.event_id != event.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="奖项不存在"
        )
    prize = prize_service.update_prize(db, prize, data)
    return _to_out(db, prize)


@router.delete(
    "/{prize_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除奖项",
)
def delete_prize(
    prize_id: int,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> None:
    prize = prize_service.get_prize(db, prize_id)
    if prize is None or prize.event_id != event.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="奖项不存在"
        )
    prize_service.delete_prize(db, prize)
