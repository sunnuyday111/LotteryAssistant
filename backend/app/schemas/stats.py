"""统计相关 Schema。"""

from pydantic import BaseModel, Field


class PrizeStat(BaseModel):
    """单个奖项统计。"""

    prize_id: int
    prize_name: str
    quantity: int
    drawn_count: int
    claim_required: bool = True
    pending_count: int = Field(0, description="待领取人数")
    claimed_count: int = Field(0, description="已领取人数")


class EventStats(BaseModel):
    """活动数据看板统计。"""

    event_id: int
    event_name: str
    total_participants: int = Field(0, description="总人数")
    checked_in: int = Field(0, description="已签到人数")
    not_checked_in: int = Field(0, description="未签到人数")
    checkin_rate: float = Field(0.0, description="签到率（0-1）")
    prize_stats: list[PrizeStat] = Field(default_factory=list)
    claim_pending: int = Field(0, description="待领取总数")
    claim_claimed: int = Field(0, description="已领取总数")
    claim_exempt: int = Field(0, description="无需领奖总数")
