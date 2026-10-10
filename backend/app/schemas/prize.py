"""奖项相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrizeBase(BaseModel):
    """奖项基础字段。"""

    name: str = Field(..., min_length=1, max_length=100, description="奖项名称")
    quantity: int = Field(1, ge=1, description="奖项数量")
    sort_order: int = Field(0, description="排序权重")
    description: str | None = Field(None, max_length=255, description="奖品描述")


class PrizeCreate(PrizeBase):
    """创建奖项请求。"""


class PrizeUpdate(BaseModel):
    """更新奖项请求。"""

    name: str | None = Field(None, min_length=1, max_length=100)
    quantity: int | None = Field(None, ge=1)
    sort_order: int | None = None
    description: str | None = Field(None, max_length=255)


class PrizeOut(PrizeBase):
    """奖项输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    created_at: datetime
    drawn_count: int = 0
