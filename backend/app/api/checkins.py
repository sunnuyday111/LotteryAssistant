"""签到 API。"""

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..schemas.checkin import CheckinRequest, CheckinResult
from ..services import checkin_service, event_service, participant_service, ws_manager
from .deps import get_event_or_404

router = APIRouter(prefix="/api/checkin", tags=["签到"])


@router.get("/{token}", summary="获取签到活动信息（扫码后）")
def get_checkin_event(token: str, db: Session = Depends(get_db)) -> dict:
    event = event_service.get_event_by_token(db, token)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="签到链接无效或已失效"
        )
    return {
        "event_id": event.id,
        "name": event.name,
        "location": event.location,
        "start_time": event.start_time,
        "status": event.status,
    }


@router.post("/{token}", response_model=CheckinResult, summary="提交签到")
async def submit_checkin(
    token: str,
    data: CheckinRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> CheckinResult:
    event = event_service.get_event_by_token(db, token)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="签到链接无效或已失效"
        )

    ip_address = request.client.host if request.client else None
    result = checkin_service.check_in(
        db, event, data.phone, data.name, ip_address=ip_address
    )

    # 签到成功后实时推送最新签到人数到大屏
    if result.success and not result.already_checked_in:
        count = checkin_service.count_checkins(db, event.id)
        await ws_manager.manager.broadcast(
            event.id,
            {
                "type": "checkin",
                "event_id": event.id,
                "participant_name": result.participant_name,
                "checked_in_count": count,
            },
        )

    return result


@router.post(
    "/{event_id}/manual/{participant_id}",
    response_model=CheckinResult,
    summary="主办方手动签到",
)
async def manual_checkin(
    participant_id: int = Path(..., description="参与者 ID"),
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> CheckinResult:
    participant = participant_service.get_participant(db, participant_id)
    if participant is None or participant.event_id != event.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="参与者不存在"
        )

    result = checkin_service.manual_check_in(db, event, participant)
    if result.success and not result.already_checked_in:
        count = checkin_service.count_checkins(db, event.id)
        await ws_manager.manager.broadcast(
            event.id,
            {
                "type": "checkin",
                "event_id": event.id,
                "participant_name": result.participant_name,
                "checked_in_count": count,
            },
        )
    return result


@router.delete(
    "/{event_id}/manual/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="取消签到",
)
def cancel_checkin(
    participant_id: int = Path(..., description="参与者 ID"),
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> None:
    participant = participant_service.get_participant(db, participant_id)
    if participant is None or participant.event_id != event.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="参与者不存在"
        )
    checkin_service.cancel_check_in(db, participant)
