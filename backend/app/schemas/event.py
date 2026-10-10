"""活动相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventBase(BaseModel):
    """活动基础字段。"""

    name: str = Field(..., min_length=1, max_length=200, description="活动名称")
    description: str | None = Field(None, description="活动说明")
    location: str | None = Field(None, max_length=200, description="活动地点")
    start_time: datetime | None = Field(None, description="开始时间")
    end_time: datetime | None = Field(None, description="结束时间")


class EventCreate(EventBase):
    """创建活动请求。"""


class EventUpdate(BaseModel):
    """更新活动请求（所有字段可选）。"""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    location: str | None = Field(None, max_length=200)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = Field(None, pattern="^(draft|ongoing|finished)$")


class EventOut(EventBase):
    """活动输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    checkin_token: str
    created_at: datetime
    updated_at: datetime


class EventDetailOut(EventOut):
    """活动详情输出（含统计）。"""

    participant_count: int = 0
    checkin_count: int = 0
    prize_count: int = 0
