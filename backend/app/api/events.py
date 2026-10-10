"""活动管理 API。"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..schemas.event import EventCreate, EventDetailOut, EventOut, EventUpdate
from ..services import event_service
from .deps import get_event_or_404

router = APIRouter(prefix="/api/events", tags=["活动管理"])


@router.get("", response_model=list[EventOut], summary="获取活动列表")
def list_events(db: Session = Depends(get_db)) -> list[Event]:
    return event_service.list_events(db)


@router.post(
    "",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
    summary="创建活动",
)
def create_event(data: EventCreate, db: Session = Depends(get_db)) -> Event:
    return event_service.create_event(db, data)


@router.get("/{event_id}", response_model=EventDetailOut, summary="获取活动详情")
def get_event(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> EventDetailOut:
    return event_service.get_event_detail(db, event)


@router.put("/{event_id}", response_model=EventOut, summary="更新活动")
def update_event(
    data: EventUpdate,
    event: Event = Depends(get_event_or_404),
    db: Session = Depends(get_db),
) -> Event:
    return event_service.update_event(db, event, data)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除活动",
)
def delete_event(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> None:
    event_service.delete_event(db, event)
