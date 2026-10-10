"""参与者相关 Schema。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ParticipantBase(BaseModel):
    """参与者基础字段。"""

    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    phone: str = Field(..., min_length=1, max_length=30, description="手机号")
    department: str | None = Field(None, max_length=100, description="部门")
    remark: str | None = Field(None, max_length=255, description="备注")


class ParticipantCreate(ParticipantBase):
    """创建参与者请求。"""


class ParticipantOut(ParticipantBase):
    """参与者输出。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    created_at: datetime
    checked_in: bool = False


class ParticipantImportResult(BaseModel):
    """Excel 导入结果。"""

    total: int = Field(0, description="解析到的总行数")
    imported: int = Field(0, description="成功导入数量")
    duplicated: int = Field(0, description="重复跳过数量")
    invalid: int = Field(0, description="格式错误数量")
    errors: list[str] = Field(default_factory=list, description="错误明细")
