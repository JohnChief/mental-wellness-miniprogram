import hmac
import secrets
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_
from werkzeug.security import check_password_hash

from .extensions import db
from .models import AdminAudit, Event, Registration, User

admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin.login", next=request.full_path))
        return view(*args, **kwargs)

    return wrapped


def verify_csrf():
    expected = session.get("csrf_token", "")
    provided = request.form.get("csrf_token", "")
    if not expected or not hmac.compare_digest(expected, provided):
        abort(400, description="页面已过期，请刷新后重试")


def record_audit(action, target_type, target_id, detail=""):
    db.session.add(
        AdminAudit(
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            detail=detail,
        )
    )


def password_matches(password):
    password_hash = current_app.config.get("ADMIN_PASSWORD_HASH", "")
    if password_hash:
        return check_password_hash(password_hash, password)
    expected = current_app.config.get("ADMIN_PASSWORD", "")
    return bool(expected) and hmac.compare_digest(expected, password)


def safe_next_url(value):
    if value and value.startswith("/admin") and not value.startswith("//"):
        return value
    return url_for("admin.dashboard")


def parse_datetime(value, field_name, required=False):
    value = (value or "").strip()
    if not value:
        if required:
            raise ValueError(f"请填写{field_name}")
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name}格式不正确") from exc


def populate_event(event, form):
    required_text = {
        "title": "活动标题",
        "event_time_text": "展示时间",
        "location": "活动地点",
        "description": "活动介绍",
        "target_audience": "适合人群",
        "flow": "活动流程",
        "notice": "注意事项",
    }
    for field, label in required_text.items():
        value = (form.get(field) or "").strip()
        if not value:
            raise ValueError(f"请填写{label}")
        setattr(event, field, value)

    event.subtitle = (form.get("subtitle") or "").strip()
    event.cover_image = (form.get("cover_image") or "").strip()
    event.cover_color = (form.get("cover_color") or "#d8d1ff").strip()
    event.price_text = (form.get("price_text") or "免费").strip()
    event.category = (form.get("category") or "本周").strip()
    event.event_time = parse_datetime(form.get("event_time"), "活动时间", True)
    event.registration_deadline = parse_datetime(
        form.get("registration_deadline"), "报名截止时间"
    )
    event.status = form.get("status", "offline")
    if event.status not in {"online", "offline"}:
        event.status = "offline"
    event.is_featured = form.get("is_featured") == "on"

    capacity = (form.get("capacity") or "").strip()
    if capacity:
        try:
            event.capacity = int(capacity)
        except ValueError as exc:
            raise ValueError("活动名额必须是整数") from exc
        if event.capacity < 1:
            raise ValueError("活动名额必须大于 0")
    else:
        event.capacity = None


@admin.app_context_processor
def inject_admin_context():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(24)
    return {
        "csrf_token": session["csrf_token"],
        "current_admin": session.get("admin_username"),
        "admin_test_tools_enabled": current_app.config.get(
            "ADMIN_TEST_TOOLS_ENABLED", False
        ),
    }


@admin.get("/login")
def login():
    if session.get("admin_authenticated"):
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html")


@admin.post("/login")
def login_submit():
    verify_csrf()
    username = (request.form.get("username") or "").strip()
    password = request.form.get("password") or ""
    expected_username = current_app.config.get("ADMIN_USERNAME", "admin")

    valid_username = hmac.compare_digest(expected_username, username)
    if not valid_username or not password_matches(password):
        flash("账号或密码不正确", "error")
        return render_template("admin/login.html"), 401

    session.clear()
    session["admin_authenticated"] = True
    session["admin_username"] = username
    session["csrf_token"] = secrets.token_urlsafe(24)
    return redirect(safe_next_url(request.args.get("next")))


@admin.post("/logout")
@admin_required
def logout():
    verify_csrf()
    session.clear()
    return redirect(url_for("admin.login"))


@admin.get("/")
@admin_required
def dashboard():
    event_count = Event.query.count()
    online_count = Event.query.filter_by(status="online").count()
    registration_count = Registration.query.count()
    pending_count = Registration.query.filter_by(status="registered").count()
    user_count = User.query.filter_by(deleted_at=None).count()
    vip_count = User.query.filter_by(deleted_at=None, is_vip=True).count()
    recent_registrations = (
        Registration.query.order_by(Registration.created_at.desc()).limit(6).all()
    )
    upcoming_events = (
        Event.query.filter(Event.event_time >= datetime.now())
        .order_by(Event.event_time.asc())
        .limit(5)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        event_count=event_count,
        online_count=online_count,
        registration_count=registration_count,
        pending_count=pending_count,
        user_count=user_count,
        vip_count=vip_count,
        recent_registrations=recent_registrations,
        upcoming_events=upcoming_events,
    )


@admin.get("/events")
@admin_required
def events():
    status = request.args.get("status", "")
    query = Event.query
    if status in {"online", "offline"}:
        query = query.filter_by(status=status)
    items = query.order_by(Event.event_time.desc()).all()
    return render_template("admin/events.html", events=items, status=status)


@admin.route("/events/new", methods=["GET", "POST"])
@admin_required
def event_create():
    if request.method == "POST":
        verify_csrf()
        event = Event()
        try:
            populate_event(event, request.form)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "admin/event_form.html", event=None, form=request.form
            ), 400
        db.session.add(event)
        db.session.flush()
        record_audit("create_event", "event", event.id, event.title)
        db.session.commit()
        flash("活动已创建", "success")
        return redirect(url_for("admin.events"))
    return render_template("admin/event_form.html", event=None, form={})


@admin.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@admin_required
def event_edit(event_id):
    event = db.get_or_404(Event, event_id)
    if request.method == "POST":
        verify_csrf()
        try:
            populate_event(event, request.form)
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template(
                "admin/event_form.html", event=event, form=request.form
            ), 400
        record_audit("update_event", "event", event.id, event.title)
        db.session.commit()
        flash("活动已保存", "success")
        return redirect(url_for("admin.events"))
    return render_template("admin/event_form.html", event=event, form={})


@admin.post("/events/<int:event_id>/toggle")
@admin_required
def event_toggle(event_id):
    verify_csrf()
    event = db.get_or_404(Event, event_id)
    event.status = "offline" if event.status == "online" else "online"
    record_audit("toggle_event", "event", event.id, event.status)
    db.session.commit()
    flash(f"活动已{'上架' if event.status == 'online' else '下架'}", "success")
    return redirect(request.referrer or url_for("admin.events"))


@admin.get("/registrations")
@admin_required
def registrations():
    event_id = request.args.get("event_id", type=int)
    status = request.args.get("status", "")
    keyword = (request.args.get("keyword") or "").strip()
    query = Registration.query
    if event_id:
        query = query.filter_by(event_id=event_id)
    if status in {"registered", "checked_in", "cancelled"}:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            or_(
                Registration.name.contains(keyword),
                Registration.phone.contains(keyword),
            )
        )
    items = query.order_by(Registration.created_at.desc()).all()
    event_options = Event.query.order_by(Event.event_time.desc()).all()
    return render_template(
        "admin/registrations.html",
        registrations=items,
        event_options=event_options,
        event_id=event_id,
        status=status,
        keyword=keyword,
    )


@admin.post("/registrations/<int:registration_id>/checkin")
@admin_required
def registration_checkin(registration_id):
    verify_csrf()
    registration = db.get_or_404(Registration, registration_id)
    if registration.status != "registered":
        flash("只有待签到的报名可以签到", "error")
    else:
        registration.status = "checked_in"
        registration.checked_in_at = datetime.now()
        record_audit("checkin", "registration", registration.id)
        db.session.commit()
        flash("签到成功", "success")
    return redirect(request.referrer or url_for("admin.registrations"))


def require_test_tools():
    if not current_app.config.get("ADMIN_TEST_TOOLS_ENABLED", False):
        abort(404)


@admin.post("/registrations/<int:registration_id>/test-status")
@admin_required
def registration_test_status(registration_id):
    require_test_tools()
    verify_csrf()
    registration = db.get_or_404(Registration, registration_id)
    status = request.form.get("status", "")
    if status not in {"registered", "cancelled"}:
        abort(400, description="不支持的测试状态")

    registration.status = status
    if status == "registered":
        registration.checked_in_at = None
        registration.cancelled_at = None
    else:
        registration.checked_in_at = None
        registration.cancelled_at = datetime.now()
    record_audit(
        "test_reset_registration",
        "registration",
        registration.id,
        status,
    )
    db.session.commit()
    flash(
        "已恢复为待签到" if status == "registered" else "已取消测试报名",
        "success",
    )
    return redirect(request.referrer or url_for("admin.registrations"))


@admin.get("/users")
@admin_required
def users():
    keyword = (request.args.get("keyword") or "").strip()
    sort = request.args.get("sort", "newest")
    vip = request.args.get("vip", "")
    query = User.query.filter_by(deleted_at=None)
    if keyword:
        query = query.filter(
            or_(User.nickname.contains(keyword), User.phone.contains(keyword))
        )
    if vip in {"yes", "no"}:
        query = query.filter_by(is_vip=vip == "yes")

    order_options = {
        "newest": (User.created_at.desc(),),
        "oldest": (User.created_at.asc(),),
        "nickname_asc": (User.nickname.asc(), User.created_at.desc()),
        "nickname_desc": (User.nickname.desc(), User.created_at.desc()),
        "vip_first": (User.is_vip.desc(), User.created_at.desc()),
    }
    if sort not in order_options:
        sort = "newest"
    items = query.order_by(*order_options[sort]).all()
    return render_template(
        "admin/users.html",
        users=items,
        keyword=keyword,
        sort=sort,
        vip=vip,
    )


@admin.post("/users/<int:user_id>/vip")
@admin_required
def user_toggle_vip(user_id):
    verify_csrf()
    user = User.query.filter_by(id=user_id, deleted_at=None).first_or_404()
    user.is_vip = not user.is_vip
    record_audit("toggle_vip", "user", user.id, str(user.is_vip))
    db.session.commit()
    flash(f"已{'设为' if user.is_vip else '取消'} VIP", "success")
    return redirect(request.referrer or url_for("admin.users"))


@admin.post("/users/bulk-vip")
@admin_required
def users_bulk_vip():
    verify_csrf()
    user_ids = []
    for value in request.form.getlist("user_ids"):
        try:
            user_ids.append(int(value))
        except (TypeError, ValueError):
            continue
    user_ids = list(dict.fromkeys(user_ids))
    if not user_ids:
        flash("请至少选择一位用户", "error")
        return redirect(request.referrer or url_for("admin.users"))

    users = User.query.filter(
        User.id.in_(user_ids),
        User.deleted_at.is_(None),
    ).all()
    changed = 0
    for user in users:
        if user.is_vip:
            continue
        user.is_vip = True
        changed += 1
        record_audit("bulk_set_vip", "user", user.id, "True")
    db.session.commit()
    flash(f"已将 {changed} 位用户设为 VIP", "success")
    return redirect(request.referrer or url_for("admin.users"))


@admin.post("/test-data")
@admin_required
def create_test_data():
    require_test_tools()
    verify_csrf()
    events = Event.query.order_by(Event.event_time.asc()).all()
    if not events:
        flash("请先创建至少一个活动", "error")
        return redirect(request.referrer or url_for("admin.users"))

    test_profiles = [
        ("测试用户·春风", "13800001001", False),
        ("测试用户·夏雨", "13800001002", True),
        ("测试用户·秋叶", "13800001003", False),
        ("测试用户·冬雪", "13800001004", True),
        ("测试用户·星光", "13800001005", False),
        ("测试用户·月影", "13800001006", False),
        ("测试用户·云朵", "13800001007", True),
        ("测试用户·山岚", "13800001008", False),
    ]
    created_users = 0
    created_registrations = 0
    for index, (nickname, phone, is_vip) in enumerate(test_profiles, start=1):
        openid = f"admin-test-user-{index}"
        user = User.query.filter_by(openid=openid).first()
        if not user:
            user = User(
                openid=openid,
                nickname=nickname,
                avatar_url="default:cloud",
                phone=phone,
                is_vip=is_vip,
                privacy_version="test",
                privacy_consent_at=datetime.now(),
            )
            db.session.add(user)
            db.session.flush()
            created_users += 1

        if index <= 6:
            event = events[(index - 1) % len(events)]
            registration = Registration.query.filter_by(
                event_id=event.id,
                user_id=user.id,
            ).first()
            if not registration:
                registration = Registration(
                    event_id=event.id,
                    user_id=user.id,
                    name=nickname,
                    phone=phone,
                    remark="Admin 测试数据",
                    status="registered",
                )
                db.session.add(registration)
                created_registrations += 1

    record_audit(
        "create_test_data",
        "system",
        "admin",
        f"users={created_users}, registrations={created_registrations}",
    )
    db.session.commit()
    flash(
        f"已新增 {created_users} 位测试用户、{created_registrations} 条测试报名",
        "success",
    )
    return redirect(request.referrer or url_for("admin.users"))
