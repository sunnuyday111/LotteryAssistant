"""数据库连接与会话管理。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

# SQLite 需要 check_same_thread=False 以支持多线程访问
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供数据库会话。"""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 轻量迁移表：为旧库补齐后续版本新增的列
# 结构：{表名: {列名: (SQLite 类型, 其他数据库类型)}}
_ADDED_COLUMNS: dict[str, dict[str, tuple[str, str]]] = {
    "prizes": {
        "claim_required": ("BOOLEAN NOT NULL DEFAULT 1", "BOOLEAN NOT NULL DEFAULT TRUE"),
        "draw_mode": ("VARCHAR(20) NOT NULL DEFAULT 'roll'", "VARCHAR(20) NOT NULL DEFAULT 'roll'"),
    },
    "draw_records": {
        "claim_status": ("VARCHAR(20) NOT NULL DEFAULT 'pending'", "VARCHAR(20) NOT NULL DEFAULT 'pending'"),
        "claimed_at": ("DATETIME", "TIMESTAMP"),
    },
}

# 需要补齐的索引：{表名: {索引名: 列名}}
_ADDED_INDEXES: dict[str, dict[str, str]] = {
    "draw_records": {"ix_draw_records_claim_status": "claim_status"},
}


def _migrate_schema() -> None:
    """为已存在的旧数据库补齐新增列与索引。

    ``create_all`` 只建新表、不会改旧表，因此升级后需要显式补列，
    否则旧库会因缺少 claim_status / draw_mode 等字段而报错。
    """

    from sqlalchemy import inspect, text

    is_sqlite = engine.dialect.name == "sqlite"
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table, columns in _ADDED_COLUMNS.items():
            if table not in tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table)}
            for name, types in columns.items():
                if name in present:
                    continue
                ddl = types[0] if is_sqlite else types[1]
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))

        for table, indexes in _ADDED_INDEXES.items():
            if table not in tables:
                continue
            present = {i["name"] for i in inspector.get_indexes(table)}
            for name, column in indexes.items():
                if name in present:
                    continue
                conn.execute(
                    text(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})")
                )


def init_db() -> None:
    """创建所有数据表，并补齐旧库缺失的列。"""

    # 导入模型以便注册到 Base.metadata
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _migrate_schema()
