"""签到相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckinRequest(BaseModel):
    """签到请求。"""

    phone: str = Field(..., min_length=1, max_length=30, description="手机号")
    name: str | None = Field(None, max_length=100, description="姓名（可选，用于校验）")


class CheckinOut(BaseModel):
    """签到记录输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    participant_id: int
    checked_in_at: datetime
    method: str


class CheckinResult(BaseModel):
    """签到结果。"""

    success: bool
    message: str
    participant_name: str | None = None
    checked_in_at: datetime | None = None
    already_checked_in: bool = False
