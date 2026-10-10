"""参与者名单 API。"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, Participant
from ..schemas.participant import (
    ParticipantCreate,
    ParticipantImportResult,
    ParticipantOut,
)
from ..services import participant_service
from .deps import get_event_or_404

router = APIRouter(prefix="/api/events/{event_id}/participants", tags=["参与者名单"])


@router.get("", response_model=list[ParticipantOut], summary="获取参与者列表")
def list_participants(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> list[ParticipantOut]:
    pairs = participant_service.list_participants_with_checkin(db, event.id)
    result: list[ParticipantOut] = []
    for participant, checked_in in pairs:
        item = ParticipantOut.model_validate(participant)
        item.checked_in = checked_in
        result.append(item)
    return result


@router.post(
    "",
    response_model=ParticipantOut,
    status_code=status.HTTP_201_CREATED,
    summary="添加单个参与者",
)
def create_participant(
    data: ParticipantCreate,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> Participant:
    existing = participant_service.get_participant_by_phone(db, event.id, data.phone)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="该手机号已存在"
        )
    return participant_service.create_participant(db, event.id, data)


@router.post(
    "/import",
    response_model=ParticipantImportResult,
    summary="从 Excel/CSV 导入名单",
)
async def import_participants(
    event: Event = Depends(get_event_or_404),
    file: UploadFile = File(..., description="Excel(.xlsx/.xls) 或 CSV 文件"),
    db: Session = Depends(get_db),
) -> ParticipantImportResult:
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="上传文件为空"
        )
    return participant_service.import_from_excel(
        db, event.id, content, file.filename or "upload.xlsx"
    )


@router.delete(
    "/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除参与者",
)
def delete_participant(
    participant_id: int,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> None:
    participant = participant_service.get_participant(db, participant_id)
    if participant is None or participant.event_id != event.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="参与者不存在"
        )
    participant_service.delete_participant(db, participant)
