"""API 公共依赖。"""

from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..services import event_service


def get_event_or_404(
    event_id: int = Path(..., description="活动 ID"),
    db: Session = Depends(get_db),
) -> Event:
    """依赖：获取活动，不存在则返回 404。"""

    event = event_service.get_event(db, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在"
        )
    return event
