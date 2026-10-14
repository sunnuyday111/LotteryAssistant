"""应用配置。

通过环境变量或 .env 文件覆盖默认值。
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置项。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用信息
    app_name: str = "活动签到抽奖助手"
    debug: bool = True

    # 数据库：默认使用 SQLite 单机版，可切换为 PostgreSQL
    # 例如：postgresql+psycopg://user:pass@localhost:5432/lottery
    database_url: str = "sqlite:///./lottery.db"

    # 跨域配置（前端开发服务器地址）
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "tauri://localhost",
        "http://tauri.localhost",
    ]

    # 签到二维码指向的前端地址（手机扫码后打开的页面）
    checkin_base_url: str = "http://172.31.20.69:5173/checkin"

    # 领奖二维码指向的前端地址（留空则由 checkin_base_url 推导）
    claim_base_url: str = ""

    # 领奖码签名密钥（留空则用 app_name 派生，正式环境建议显式配置随机值）
    claim_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    """获取配置单例。"""

    return Settings()


settings = get_settings()
