"""导出 API。"""

from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event
from ..services import export_service
from .deps import get_event_or_404

router = APIRouter(prefix="/api/events/{event_id}/export", tags=["数据导出"])

XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


def _excel_response(content: bytes, filename: str) -> Response:
    """构造 Excel 下载响应。"""

    encoded = quote(filename)
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={
            "Content-Disposition": (
                f"attachment; filename*=UTF-8''{encoded}"
            )
        },
    )


@router.get("/checkins", summary="导出签到明细")
def export_checkins(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> Response:
    content = export_service.export_checkin_list(db, event)
    return _excel_response(content, f"{event.name}_签到明细.xlsx")


@router.get("/draws", summary="导出中奖名单")
def export_draws(
    event: Event = Depends(get_event_or_404), db: Session = Depends(get_db)
) -> Response:
    content = export_service.export_draw_list(db, event)
    return _excel_response(content, f"{event.name}_中奖名单.xlsx")
