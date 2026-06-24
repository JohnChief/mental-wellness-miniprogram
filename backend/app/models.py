from datetime import datetime

from .extensions import db

PRIMARY_KEY = db.BigInteger().with_variant(db.Integer, "sqlite")


def now():
    return datetime.now()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(PRIMARY_KEY, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    nickname = db.Column(db.String(80), nullable=False, default="微信用户")
    phone = db.Column(db.String(32))
    is_vip = db.Column(db.Boolean, nullable=False, default=False)
    privacy_version = db.Column(db.String(32))
    privacy_consent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)
    deleted_at = db.Column(db.DateTime)


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(PRIMARY_KEY, primary_key=True, autoincrement=True)
    title = db.Column(db.String(160), nullable=False)
    subtitle = db.Column(db.String(255), nullable=False, default="")
    cover_image = db.Column(db.String(500), nullable=False, default="")
    cover_color = db.Column(db.String(32), nullable=False, default="#d8d1ff")
    event_time = db.Column(db.DateTime, nullable=False)
    event_time_text = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    price_text = db.Column(db.String(80), nullable=False, default="免费")
    description = db.Column(db.Text, nullable=False)
    target_audience = db.Column(db.Text, nullable=False)
    flow = db.Column(db.Text, nullable=False)
    notice = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(40), nullable=False, default="本周", index=True)
    capacity = db.Column(db.Integer)
    registration_deadline = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default="online", index=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)


class Registration(db.Model):
    __tablename__ = "registrations"
    __table_args__ = (
        db.UniqueConstraint("event_id", "user_id", name="uq_registration_event_user"),
    )

    id = db.Column(PRIMARY_KEY, primary_key=True, autoincrement=True)
    event_id = db.Column(
        PRIMARY_KEY,
        db.ForeignKey("events.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        PRIMARY_KEY,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(32), nullable=False)
    remark = db.Column(db.String(500), nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="registered", index=True)
    checked_in_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=now)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)

    event = db.relationship("Event", lazy="joined")
    user = db.relationship("User", lazy="joined")


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=now, onupdate=now)


class AdminAudit(db.Model):
    __tablename__ = "admin_audits"

    id = db.Column(PRIMARY_KEY, primary_key=True, autoincrement=True)
    action = db.Column(db.String(120), nullable=False)
    target_type = db.Column(db.String(80), nullable=False)
    target_id = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=now)
