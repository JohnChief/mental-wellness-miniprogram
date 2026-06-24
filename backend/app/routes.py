import hmac
import json
import random
import re
from datetime import datetime
from functools import wraps

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import AdminAudit, Event, Registration, Setting, User
from .serializers import event_to_dict, registration_to_dict
from .wechat import WeChatApiError, resolve_phone_number

api = Blueprint("api", __name__)
PHONE_PATTERN = re.compile(r"^1\d{10}$")
DEFAULT_NICKNAMES = [
    "清风来客",
    "云间小憩",
    "自在行者",
    "暖心朋友",
    "松间听雨",
    "星河旅人",
]
DEFAULT_AVATARS = [
    "default:lotus",
    "default:moon",
    "default:cloud",
    "default:leaf",
    "default:star",
    "default:mountain",
]


def ok(data=None, status=200):
    return jsonify({"code": 0, "data": data}), status


def error(message, status=400, code=1):
    return jsonify({"code": code, "message": message}), status


def current_openid():
    openid = request.headers.get("X-WX-OPENID", "").strip()
    if not openid and current_app.config["ALLOW_DEV_OPENID"]:
        openid = request.headers.get("X-DEV-OPENID", "").strip()
    return openid


def user_to_dict(user):
    return {
        "id": user.id,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "phone": user.phone,
        "is_vip": user.is_vip,
        "registered": bool(user.phone and user.privacy_consent_at),
    }


def require_user(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        openid = current_openid()
        if not openid:
            return error("未获取到可信微信身份，请通过小程序云托管调用", 401)
        user = User.query.filter_by(openid=openid, deleted_at=None).first()
        if not user or not user.phone or not user.privacy_consent_at:
            return error("请先完成微信登录注册", 401)
        return view(user, *args, **kwargs)

    return wrapped


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        expected = current_app.config["ADMIN_API_KEY"]
        provided = request.headers.get("X-ADMIN-KEY", "")
        if not expected or not hmac.compare_digest(expected, provided):
            return error("管理员鉴权失败", 401)
        return view(*args, **kwargs)

    return wrapped


def audit(action, target_type, target_id, detail=""):
    db.session.add(
        AdminAudit(
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            detail=detail,
        )
    )


@api.get("/")
def index():
    return ok({"service": "mental-wellness-api", "status": "ok"})


@api.get("/health")
def health():
    db.session.execute(db.select(Setting.key).limit(1))
    return ok({"status": "healthy"})


@api.get("/api/home")
def home():
    settings = {item.key: item.value for item in Setting.query.all()}
    service_cards = json.loads(settings.get("service_cards", "[]"))
    events = (
        Event.query.filter_by(status="online")
        .order_by(Event.event_time.asc())
        .limit(2)
        .all()
    )
    featured = (
        Event.query.filter_by(status="online", is_featured=True)
        .order_by(Event.event_time.asc())
        .first()
        or (events[0] if events else None)
    )
    return ok(
        {
            "settings": {
                "platform_name": settings.get("platform_name", "心语轻疗愈"),
                "platform_slogan": settings.get(
                    "platform_slogan", "心理陪伴 · 活动体验 · 社群支持"
                ),
                "service_cards": service_cards,
            },
            "featured_event": event_to_dict(featured, True) if featured else None,
            "events": [event_to_dict(item) for item in events],
        }
    )


@api.get("/api/events")
def list_events():
    selected = request.args.get("filter", "全部")
    query = Event.query.filter_by(status="online")
    if selected == "线下":
        query = query.filter(Event.location.like("%线下%"))
    elif selected != "全部":
        query = query.filter_by(category=selected)
    events = query.order_by(Event.event_time.asc()).all()
    return ok([event_to_dict(item) for item in events])


@api.get("/api/events/<int:event_id>")
def event_detail(event_id):
    event = Event.query.filter_by(id=event_id, status="online").first()
    if not event:
        return error("活动不存在或已下架", 404)
    return ok(event_to_dict(event, include_detail=True))


@api.get("/api/auth/me")
def auth_me():
    openid = current_openid()
    if not openid:
        return error("未获取到可信微信身份，请通过小程序云托管调用", 401)
    user = User.query.filter_by(openid=openid, deleted_at=None).first()
    if not user:
        return ok({"registered": False})
    return ok(user_to_dict(user))


@api.post("/api/auth/register")
def auth_register():
    openid = current_openid()
    if not openid:
        return error("未获取到可信微信身份，请通过小程序云托管调用", 401)

    payload = request.get_json(silent=True) or {}
    nickname = str(payload.get("nickname", "")).strip()
    avatar_url = str(payload.get("avatar_url", "")).strip()
    phone_code = str(payload.get("phone_code", "")).strip()
    privacy_version = str(payload.get("privacy_version", "")).strip()

    if len(nickname) > 80:
        return error("昵称不能超过80字")
    if len(avatar_url) > 500:
        return error("头像地址过长")
    if not privacy_version:
        return error("请先同意隐私政策")

    try:
        phone = resolve_phone_number(phone_code)
    except WeChatApiError as exc:
        return error(str(exc), 400)

    user = User.query.filter_by(openid=openid, deleted_at=None).first()
    if not user:
        user = User(openid=openid)
        db.session.add(user)

    user.nickname = nickname or random.choice(DEFAULT_NICKNAMES)
    user.avatar_url = avatar_url or random.choice(DEFAULT_AVATARS)
    user.phone = phone
    user.privacy_version = privacy_version
    user.privacy_consent_at = datetime.now()
    db.session.commit()
    return ok(user_to_dict(user), 201)


@api.put("/api/auth/profile")
@require_user
def update_profile(user):
    payload = request.get_json(silent=True) or {}
    nickname = str(payload.get("nickname", "")).strip()
    avatar_url = str(payload.get("avatar_url", "")).strip()

    if nickname:
        if len(nickname) > 80:
            return error("昵称不能超过80字")
        user.nickname = nickname
    if avatar_url:
        if len(avatar_url) > 500:
            return error("头像地址过长")
        user.avatar_url = avatar_url

    if not nickname and not avatar_url:
        return error("没有需要更新的资料")

    db.session.commit()
    return ok(user_to_dict(user))


@api.post("/api/registrations")
@require_user
def create_registration(user):
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    remark = str(payload.get("remark", "")).strip()
    privacy_version = str(payload.get("privacy_version", "")).strip()

    if not name or len(name) > 80:
        return error("请填写正确姓名")
    if not PHONE_PATTERN.match(phone):
        return error("请填写正确手机号")
    if len(remark) > 500:
        return error("备注不能超过500字")
    if not privacy_version:
        return error("请先同意隐私政策")

    event = (
        db.session.execute(
            db.select(Event).where(
                Event.id == payload.get("event_id"),
                Event.status == "online",
            ).with_for_update()
        )
        .scalars()
        .first()
    )
    if not event:
        return error("活动不存在或已下架", 404)
    if event.registration_deadline and datetime.now() > event.registration_deadline:
        return error("活动报名已截止", 409)

    active_count = Registration.query.filter(
        Registration.event_id == event.id,
        Registration.status.in_(["registered", "checked_in"]),
    ).count()
    if event.capacity is not None and active_count >= event.capacity:
        return error("活动名额已满", 409)

    existing = Registration.query.filter_by(event_id=event.id, user_id=user.id).first()
    if existing and existing.status != "cancelled":
        return error("你已经报名过该活动", 409)

    user.phone = phone
    user.privacy_version = privacy_version
    user.privacy_consent_at = datetime.now()

    if existing:
        existing.name = name
        existing.phone = phone
        existing.remark = remark
        existing.status = "registered"
        existing.cancelled_at = None
        registration = existing
    else:
        registration = Registration(
            event_id=event.id,
            user_id=user.id,
            name=name,
            phone=phone,
            remark=remark,
        )
        db.session.add(registration)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("请勿重复提交报名", 409)
    return ok(registration_to_dict(registration), 201)


@api.get("/api/registrations/mine")
@require_user
def my_registrations(user):
    records = (
        Registration.query.filter_by(user_id=user.id)
        .order_by(Registration.created_at.desc())
        .all()
    )
    return ok([registration_to_dict(item) for item in records])


@api.put("/api/registrations/<int:registration_id>/cancel")
@require_user
def cancel_registration(user, registration_id):
    registration = Registration.query.filter_by(
        id=registration_id, user_id=user.id
    ).first()
    if not registration:
        return error("报名记录不存在", 404)
    if registration.status == "checked_in":
        return error("已签到活动不能取消", 409)
    registration.status = "cancelled"
    registration.cancelled_at = datetime.now()
    db.session.commit()
    return ok(registration_to_dict(registration))


@api.delete("/api/account")
@require_user
def delete_account(user):
    registrations = Registration.query.filter_by(user_id=user.id).all()
    for registration in registrations:
        registration.name = "已注销用户"
        registration.phone = ""
        registration.remark = ""
    user.phone = None
    user.nickname = "已注销用户"
    user.avatar_url = ""
    user.openid = f"deleted-{user.id}-{int(datetime.now().timestamp())}"
    user.deleted_at = datetime.now()
    db.session.commit()
    return ok({"deleted": True})


@api.get("/admin/api/events")
@require_admin
def admin_events():
    events = Event.query.order_by(Event.event_time.desc()).all()
    return ok([event_to_dict(item, True) | {"status": item.status} for item in events])


@api.post("/admin/api/events")
@require_admin
def admin_create_event():
    payload = request.get_json(silent=True) or {}
    required = [
        "title",
        "event_time",
        "event_time_text",
        "location",
        "description",
        "target_audience",
        "flow",
        "notice",
    ]
    if any(not payload.get(field) for field in required):
        return error("活动信息不完整")
    event = Event(
        title=payload["title"],
        subtitle=payload.get("subtitle", ""),
        cover_image=payload.get("cover_image", ""),
        cover_color=payload.get("cover_color", "#d8d1ff"),
        event_time=datetime.fromisoformat(payload["event_time"]),
        event_time_text=payload["event_time_text"],
        location=payload["location"],
        price_text=payload.get("price_text", "免费"),
        description=payload["description"],
        target_audience=payload["target_audience"],
        flow=payload["flow"],
        notice=payload["notice"],
        category=payload.get("category", "本周"),
        capacity=payload.get("capacity"),
        status=payload.get("status", "offline"),
        is_featured=bool(payload.get("is_featured", False)),
    )
    db.session.add(event)
    db.session.flush()
    audit("create_event", "event", event.id, event.title)
    db.session.commit()
    return ok(event_to_dict(event, True), 201)


@api.put("/admin/api/events/<int:event_id>")
@require_admin
def admin_update_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return error("活动不存在", 404)
    payload = request.get_json(silent=True) or {}
    editable = {
        "title",
        "subtitle",
        "cover_image",
        "cover_color",
        "event_time_text",
        "location",
        "price_text",
        "description",
        "target_audience",
        "flow",
        "notice",
        "category",
        "capacity",
        "status",
        "is_featured",
    }
    for field in editable:
        if field in payload:
            setattr(event, field, payload[field])
    if "event_time" in payload:
        event.event_time = datetime.fromisoformat(payload["event_time"])
    if "registration_deadline" in payload:
        value = payload["registration_deadline"]
        event.registration_deadline = datetime.fromisoformat(value) if value else None
    audit("update_event", "event", event.id, event.title)
    db.session.commit()
    return ok(event_to_dict(event, True) | {"status": event.status})


@api.put("/admin/api/events/<int:event_id>/toggle")
@require_admin
def admin_toggle_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return error("活动不存在", 404)
    event.status = "offline" if event.status == "online" else "online"
    audit("toggle_event", "event", event.id, event.status)
    db.session.commit()
    return ok({"id": event.id, "status": event.status})


@api.get("/admin/api/registrations")
@require_admin
def admin_registrations():
    query = Registration.query
    if request.args.get("event_id"):
        query = query.filter_by(event_id=request.args["event_id"])
    records = query.order_by(Registration.created_at.desc()).all()
    return ok([registration_to_dict(item) for item in records])


@api.post("/admin/api/registrations/<int:registration_id>/checkin")
@require_admin
def admin_checkin(registration_id):
    registration = Registration.query.get(registration_id)
    if not registration:
        return error("报名记录不存在", 404)
    if registration.status != "registered":
        return error("当前状态不能签到", 409)
    registration.status = "checked_in"
    registration.checked_in_at = datetime.now()
    audit("checkin", "registration", registration.id)
    db.session.commit()
    return ok(registration_to_dict(registration))


@api.get("/admin/api/users")
@require_admin
def admin_users():
    users = User.query.filter_by(deleted_at=None).order_by(User.created_at.desc()).all()
    return ok(
        [
            {
                "id": user.id,
                "nickname": user.nickname,
                "phone": user.phone,
                "is_vip": user.is_vip,
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ]
    )


@api.put("/admin/api/users/<int:user_id>/vip")
@require_admin
def admin_toggle_vip(user_id):
    user = User.query.filter_by(id=user_id, deleted_at=None).first()
    if not user:
        return error("用户不存在", 404)
    user.is_vip = not user.is_vip
    audit("toggle_vip", "user", user.id, str(user.is_vip))
    db.session.commit()
    return ok({"id": user.id, "is_vip": user.is_vip})
