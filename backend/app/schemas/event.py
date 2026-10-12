"""活动相关 Schema。

时间字段约定：
  - 内部存储一律是 **naive UTC**（数据库不存时区）
  - 输入（EventCreate / EventUpdate）自动识别是否带 tz：带 tz 转换到 UTC 再去 tz；
    naive 视为 UTC
  - 输出（EventOut / EventDetailOut）一律返回 **带 Z 后缀的 UTC ISO 字符串**，
    由前端 dayjs 按浏览器本地时区显示
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


def _to_naive_utc(value: datetime | None) -> datetime | None:
    """统一把 datetime 转为无时区的 UTC。"""

    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def derive_status(
    start_time: datetime | None,
    end_time: datetime | None,
    stored: str,
) -> str:
    """根据开始 / 结束时间自动推算状态（手动设置的 finished 不会被自动覆盖）。

    规则：
      - 用户手动设的 finished 保留
      - 有 end_time 且 <= now  → finished
      - 有 start_time 且 <= now → ongoing
      - 其余 → draft
    """

    if stored == "finished":
        return "finished"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if end_time and end_time <= now:
        return "finished"
    if start_time and start_time <= now:
        return "ongoing"
    return "draft"


class _UTCDateTime(BaseModel):
    """支持任意带 / 不带时区输入，输出统一带 Z 的 UTC ISO 字符串。"""

    @field_validator("*", mode="before", check_fields=False)
    @classmethod
    def _parse(cls, value):  # noqa: D401
        if isinstance(value, datetime):
            return _to_naive_utc(value)
        return value

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class EventBase(BaseModel):
    """活动基础字段。"""

    name: str = Field(..., min_length=1, max_length=200, description="活动名称")
    description: str | None = Field(None, description="活动说明")
    location: str | None = Field(None, max_length=200, description="活动地点")
    start_time: datetime | None = Field(None, description="开始时间（UTC）")
    end_time: datetime | None = Field(None, description="结束时间（UTC）")


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

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def _norm_time(cls, v):
        return _to_naive_utc(v)


class EventOut(EventBase):
    """活动输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    checkin_token: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("start_time", "end_time", "created_at", "updated_at")
    def _ser_dt(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @model_validator(mode="before")
    @classmethod
    def _auto_status(cls, data: Any) -> Any:
        """从 ORM 对象读出的 start/end 自动推算 status。"""

        if isinstance(data, dict):
            return data
        start = getattr(data, "start_time", None)
        end = getattr(data, "end_time", None)
        stored = getattr(data, "status", "draft")
        new_status = derive_status(start, end, stored)
        if new_status != stored:
            setattr(data, "status", new_status)
        return data


class EventDetailOut(EventOut):
    """活动详情输出（含统计）。"""

    participant_count: int = 0
    checkin_count: int = 0
    prize_count: int = 0