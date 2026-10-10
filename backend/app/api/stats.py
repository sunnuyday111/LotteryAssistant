"""统计 API。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..schemas.stats import EventStats
from ..services import stats_service
from .deps import get_event_or_404

router = APIRouter(prefix="/api/events/{event_id}/stats", tags=["数据看板"])


@router.get("", response_model=EventStats, summary="获取活动统计")
def get_stats(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> EventStats:
    return stats_service.get_event_stats(db, event)
