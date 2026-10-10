"""抽奖相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DrawRequest(BaseModel):
    """抽奖请求。"""

    prize_id: int = Field(..., description="奖项 ID")
    count: int = Field(1, ge=1, le=100, description="本次抽取人数")
    # 是否允许已中奖者再次参与（默认不允许）
    allow_repeat_winner: bool = Field(False, description="是否允许重复中奖")


class DrawWinner(BaseModel):
    """单个中奖者信息。"""

    participant_id: int
    name: str
    phone: str
    department: str | None = None


class DrawResult(BaseModel):
    """抽奖结果。"""

    success: bool
    message: str
    prize_id: int
    prize_name: str
    winners: list[DrawWinner] = Field(default_factory=list)


class DrawRecordOut(BaseModel):
    """中奖记录输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    prize_id: int
    participant_id: int
    drawn_at: datetime
    prize_name: str | None = None
    participant_name: str | None = None
    participant_phone: str | None = None
