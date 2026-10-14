"""抽奖相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# 抽奖玩法：roll(滚动名单) / wheel(轮盘) / egg(砸金蛋) / grid(九宫格)
DrawMode = str  # Literal["roll", "wheel", "egg", "grid"]

# 领奖状态：pending(待领取) / claimed(已领取)
ClaimStatus = str  # Literal["pending", "claimed"]


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
    # 中奖记录 ID（用于生成领奖二维码）
    record_id: int | None = None
    # 领奖二维码 URL（需现场领奖时才有值）
    claim_url: str | None = None


class DrawResult(BaseModel):
    """抽奖结果。"""

    success: bool
    message: str
    prize_id: int
    prize_name: str
    draw_mode: str = "roll"
    claim_required: bool = True
    winners: list[DrawWinner] = Field(default_factory=list)


class DrawRecordOut(BaseModel):
    """中奖记录输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    prize_id: int
    participant_id: int
    drawn_at: datetime
    claim_status: str = "pending"
    claimed_at: datetime | None = None
    prize_name: str | None = None
    participant_name: str | None = None
    participant_phone: str | None = None
    claim_required: bool = True
    # 领奖二维码 URL（仅 claim_required 且待领取时有值）
    claim_url: str | None = None


class ClaimInfo(BaseModel):
    """领奖凭证信息（扫码后展示）。"""

    record_id: int
    participant_name: str
    prize_name: str
    drawn_at: datetime
    claim_status: str
    claimed_at: datetime | None = None


class ClaimResult(BaseModel):
    """领奖提交结果。"""

    success: bool
    message: str
    info: ClaimInfo | None = None
    already_claimed: bool = False


class ClaimStats(BaseModel):
    """领奖统计。"""

    pending: int = 0
    claimed: int = 0
    exempt: int = 0
    total: int = 0


class ManualClaimRequest(BaseModel):
    """主办方手动核销领奖（手机号可选二次确认）。"""

    phone: str | None = Field(
        None, max_length=30, description="手机号或后 4 位（可选，用于二次确认）"
    )


class ClaimRequest(BaseModel):
    """领奖请求（扫码后提交）。"""

    code: str = Field(..., min_length=4, max_length=64, description="领奖码")
    phone: str | None = Field(None, max_length=30, description="手机号二次确认（可选）")
