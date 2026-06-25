import os
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv()


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


class Config:
    MYSQL_ADDRESS = os.getenv("MYSQL_ADDRESS", "127.0.0.1:3306")
    MYSQL_USERNAME = os.getenv("MYSQL_USERNAME", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "flask_demo")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or (
        f"mysql+pymysql://{quote_plus(MYSQL_USERNAME)}:{quote_plus(MYSQL_PASSWORD)}"
        f"@{MYSQL_ADDRESS}/{MYSQL_DATABASE}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    SECRET_KEY = os.getenv("SECRET_KEY", "")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
    WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
    WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
    AUTO_INIT_DB = env_bool("AUTO_INIT_DB", True)
    SEED_SAMPLE_DATA = env_bool("SEED_SAMPLE_DATA", True)
    ALLOW_DEV_OPENID = env_bool("ALLOW_DEV_OPENID", False)
    ADMIN_TEST_TOOLS_ENABLED = env_bool("ADMIN_TEST_TOOLS_ENABLED", False)
    JSON_AS_ASCII = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
