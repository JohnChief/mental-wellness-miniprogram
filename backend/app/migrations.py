from sqlalchemy import inspect, text

from .extensions import db


def ensure_runtime_schema():
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "avatar_url" not in user_columns:
        db.session.execute(
            text(
                "ALTER TABLE users "
                "ADD COLUMN avatar_url VARCHAR(500) NOT NULL DEFAULT '' "
                "AFTER nickname"
            )
        )
        db.session.commit()
