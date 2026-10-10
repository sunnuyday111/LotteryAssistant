"""参与者服务：名单管理、Excel 导入。"""

import io

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Checkin, Participant
from ..schemas.participant import ParticipantCreate, ParticipantImportResult

# Excel 列名映射（支持中英文表头）
COLUMN_ALIASES: dict[str, str] = {
    "姓名": "name",
    "名字": "name",
    "name": "name",
    "手机号": "phone",
    "手机": "phone",
    "电话": "phone",
    "联系方式": "phone",
    "phone": "phone",
    "mobile": "phone",
    "部门": "department",
    "单位": "department",
    "department": "department",
    "备注": "remark",
    "remark": "remark",
}


def list_participants(db: Session, event_id: int) -> list[Participant]:
    """获取活动下所有参与者。"""

    stmt = (
        select(Participant)
        .where(Participant.event_id == event_id)
        .order_by(Participant.created_at.asc())
    )
    return list(db.scalars(stmt).all())


def get_participant(db: Session, participant_id: int) -> Participant | None:
    """按 ID 获取参与者。"""

    return db.get(Participant, participant_id)


def get_participant_by_phone(
    db: Session, event_id: int, phone: str
) -> Participant | None:
    """按手机号获取活动内参与者。"""

    stmt = select(Participant).where(
        Participant.event_id == event_id, Participant.phone == phone
    )
    return db.scalars(stmt).first()


def create_participant(
    db: Session, event_id: int, data: ParticipantCreate
) -> Participant:
    """创建单个参与者。"""

    participant = Participant(
        event_id=event_id,
        name=data.name,
        phone=data.phone,
        department=data.department,
        remark=data.remark,
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def delete_participant(db: Session, participant: Participant) -> None:
    """删除参与者。"""

    db.delete(participant)
    db.commit()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """将表头标准化为内部字段名。"""

    rename_map: dict[str, str] = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[key]
    return df.rename(columns=rename_map)


def import_from_excel(
    db: Session, event_id: int, content: bytes, filename: str
) -> ParticipantImportResult:
    """从 Excel/CSV 文件导入参与者名单。

    支持 .xlsx / .xls / .csv，自动识别中英文表头。
    """

    result = ParticipantImportResult()

    # 解析文件
    try:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content), dtype=str)
        else:
            df = pd.read_excel(io.BytesIO(content), dtype=str)
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"文件解析失败：{exc}")
        return result

    df = _normalize_columns(df)

    if "name" not in df.columns or "phone" not in df.columns:
        result.errors.append("缺少必需列：姓名(name) 和 手机号(phone)")
        return result

    # 已存在的手机号集合
    existing_phones = {
        p.phone for p in list_participants(db, event_id)
    }
    seen_in_file: set[str] = set()

    for idx, row in df.iterrows():
        result.total += 1
        row_no = idx + 2  # Excel 行号（含表头）

        name = str(row.get("name") or "").strip()
        phone = str(row.get("phone") or "").strip()

        # 处理 pandas 读取的 NaN
        if name.lower() == "nan":
            name = ""
        if phone.lower() == "nan":
            phone = ""

        if not name or not phone:
            result.invalid += 1
            result.errors.append(f"第 {row_no} 行：姓名或手机号为空")
            continue

        if phone in existing_phones or phone in seen_in_file:
            result.duplicated += 1
            result.errors.append(f"第 {row_no} 行：手机号 {phone} 重复，已跳过")
            continue

        department = str(row.get("department") or "").strip()
        remark = str(row.get("remark") or "").strip()

        participant = Participant(
            event_id=event_id,
            name=name,
            phone=phone,
            department=None if department.lower() == "nan" or not department else department,
            remark=None if remark.lower() == "nan" or not remark else remark,
        )
        db.add(participant)
        seen_in_file.add(phone)
        result.imported += 1

    db.commit()
    return result


def list_participants_with_checkin(
    db: Session, event_id: int
) -> list[tuple[Participant, bool]]:
    """获取参与者及其签到状态。"""

    participants = list_participants(db, event_id)
    checked_ids = {
        c.participant_id
        for c in db.scalars(
            select(Checkin).where(Checkin.event_id == event_id)
        ).all()
    }
    return [(p, p.id in checked_ids) for p in participants]
