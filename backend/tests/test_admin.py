import os
import unittest
from datetime import datetime
from io import BytesIO
from tempfile import TemporaryDirectory

from app import create_app
from app.admin import LOGIN_FAILURES
from app.extensions import db
from app.models import AdminAudit, Event, Registration, User

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00"
)


class AdminTestCase(unittest.TestCase):
    def setUp(self):
        self.uploads = TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "AUTO_INIT_DB": True,
                "SEED_SAMPLE_DATA": True,
                "SECRET_KEY": "test-secret",
                "ADMIN_USERNAME": "operator",
                "ADMIN_PASSWORD": "safe-password",
                "ADMIN_TEST_TOOLS_ENABLED": True,
                "EVENT_IMAGE_UPLOAD_FOLDER": self.uploads.name,
            }
        )
        self.client = self.app.test_client()
        LOGIN_FAILURES.clear()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.uploads.cleanup()

    def csrf_token(self):
        self.client.get("/admin/login")
        with self.client.session_transaction() as session:
            return session["csrf_token"]

    def login(self):
        return self.client.post(
            "/admin/login",
            data={
                "csrf_token": self.csrf_token(),
                "username": "operator",
                "password": "safe-password",
            },
        )

    def test_admin_requires_login_and_accepts_valid_credentials(self):
        protected = self.client.get("/admin/")
        self.assertEqual(protected.status_code, 302)
        self.assertIn("/admin/login", protected.location)

        invalid = self.client.post(
            "/admin/login",
            data={
                "csrf_token": self.csrf_token(),
                "username": "operator",
                "password": "wrong",
            },
        )
        self.assertEqual(invalid.status_code, 401)

        logged_in = self.login()
        self.assertEqual(logged_in.status_code, 302)
        dashboard = self.client.get("/admin/")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("数据概览".encode(), dashboard.data)

    def test_admin_can_create_and_toggle_event_with_audit(self):
        self.login()
        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]
        created = self.client.post(
            "/admin/events/new",
            data={
                "csrf_token": csrf,
                "title": "管理员新建活动",
                "subtitle": "测试",
                "category": "本周",
                "price_text": "免费",
                "event_time": "2026-08-01T14:00",
                "location": "活动空间",
                "capacity": "12",
                "description": "活动介绍",
                "target_audience": "适合人群",
                "flow": "活动流程",
                "notice": "注意事项",
                "cover_color": "#d8d1ff",
                "status": "offline",
            },
        )
        self.assertEqual(created.status_code, 302)

        with self.app.app_context():
            event = Event.query.filter_by(title="管理员新建活动").one()
            event_id = event.id
            self.assertEqual(event.capacity, 12)
            self.assertEqual(event.status, "offline")
            self.assertEqual(event.event_time_text, "8月1日 周六 14:00")
            self.assertIsNotNone(
                AdminAudit.query.filter_by(
                    action="create_event", target_id=str(event.id)
                ).first()
            )

        toggled = self.client.post(
            f"/admin/events/{event_id}/toggle",
            data={"csrf_token": csrf},
        )
        self.assertEqual(toggled.status_code, 302)
        with self.app.app_context():
            self.assertEqual(db.session.get(Event, event_id).status, "online")

    def test_admin_can_upload_event_cover_image(self):
        self.login()
        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]
        created = self.client.post(
            "/admin/events/new",
            data={
                "csrf_token": csrf,
                "title": "Event With Cover",
                "subtitle": "Cover upload",
                "category": "This Week",
                "price_text": "Free",
                "event_time": "2026-08-01T14:00",
                "location": "Activity Space",
                "description": "Intro",
                "target_audience": "Audience",
                "flow": "Flow",
                "notice": "Notice",
                "cover_color": "#d8d1ff",
                "status": "offline",
                "cover_image_file": (BytesIO(PNG_BYTES), "cover.png"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(created.status_code, 302)

        with self.app.app_context():
            event = Event.query.filter_by(title="Event With Cover").one()
            cover_image = event.cover_image
            self.assertEqual(event.event_time_text, "8月1日 周六 14:00")
            self.assertTrue(event.cover_image.startswith("/admin/uploads/events/"))
            self.assertTrue(event.cover_image.endswith(".png"))

        saved_files = os.listdir(self.uploads.name)
        self.assertEqual(len(saved_files), 1)
        self.assertTrue(saved_files[0].endswith(".png"))
        image_response = self.client.get(cover_image)
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response.data, PNG_BYTES)
        image_response.close()

    def test_admin_rejects_disguised_event_cover_image(self):
        self.login()
        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]
        response = self.client.post(
            "/admin/events/new",
            data={
                "csrf_token": csrf,
                "title": "Bad Cover",
                "category": "This Week",
                "price_text": "Free",
                "event_time": "2026-08-01T14:00",
                "location": "Activity Space",
                "description": "Intro",
                "target_audience": "Audience",
                "flow": "Flow",
                "notice": "Notice",
                "cover_color": "#d8d1ff",
                "status": "offline",
                "cover_image_file": (BytesIO(b"<script>alert(1)</script>"), "cover.png"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        with self.app.app_context():
            self.assertIsNone(Event.query.filter_by(title="Bad Cover").first())

    def test_admin_event_edit_rejects_stale_version(self):
        self.login()
        with self.app.app_context():
            event = Event.query.order_by(Event.id.asc()).first()
            event_id = event.id
            stale_version = event.updated_at.isoformat(timespec="microseconds")
            event.title = "Concurrent Update"
            db.session.commit()

        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]
        response = self.client.post(
            f"/admin/events/{event_id}/edit",
            data={
                "csrf_token": csrf,
                "updated_at": stale_version,
                "title": "Stale Update",
                "category": "This Week",
                "price_text": "Free",
                "event_time": "2026-08-01T14:00",
                "location": "Activity Space",
                "description": "Intro",
                "target_audience": "Audience",
                "flow": "Flow",
                "notice": "Notice",
                "cover_color": "#d8d1ff",
                "status": "offline",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn(f'name="updated_at" value="{stale_version}"'.encode(), response.data)

        repeated = self.client.post(
            f"/admin/events/{event_id}/edit",
            data={
                "csrf_token": csrf,
                "updated_at": stale_version,
                "title": "Repeated Stale Update",
                "category": "This Week",
                "price_text": "Free",
                "event_time": "2026-08-01T14:00",
                "location": "Activity Space",
                "description": "Intro",
                "target_audience": "Audience",
                "flow": "Flow",
                "notice": "Notice",
                "cover_color": "#d8d1ff",
                "status": "offline",
            },
        )
        self.assertEqual(repeated.status_code, 409)

        with self.app.app_context():
            event = db.session.get(Event, event_id)
            self.assertEqual(event.title, "Concurrent Update")

    def test_admin_event_edit_accepts_current_version(self):
        self.login()
        with self.app.app_context():
            event = Event.query.order_by(Event.id.asc()).first()
            event_id = event.id
            current_version = event.updated_at.isoformat(timespec="microseconds")

        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]
        response = self.client.post(
            f"/admin/events/{event_id}/edit",
            data={
                "csrf_token": csrf,
                "updated_at": current_version,
                "title": "Fresh Update",
                "category": "This Week",
                "price_text": "Free",
                "event_time": "2026-08-01T14:00",
                "location": "Activity Space",
                "description": "Intro",
                "target_audience": "Audience",
                "flow": "Flow",
                "notice": "Notice",
                "cover_color": "#d8d1ff",
                "status": "offline",
            },
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            event = db.session.get(Event, event_id)
            self.assertEqual(event.title, "Fresh Update")

    def test_admin_rejects_post_without_csrf(self):
        self.login()
        response = self.client.post("/admin/logout", data={})
        self.assertEqual(response.status_code, 400)

    def test_admin_login_rate_limits_repeated_failures(self):
        csrf = self.csrf_token()
        for _ in range(5):
            response = self.client.post(
                "/admin/login",
                data={
                    "csrf_token": csrf,
                    "username": "operator",
                    "password": "wrong",
                },
            )
            self.assertEqual(response.status_code, 401)

        response = self.client.post(
            "/admin/login",
            data={
                "csrf_token": csrf,
                "username": "operator",
                "password": "wrong",
            },
        )
        self.assertEqual(response.status_code, 429)

    def test_admin_can_toggle_vip(self):
        self.login()
        with self.app.app_context():
            user = User(openid="admin-test-user", nickname="后台测试用户")
            db.session.add(user)
            db.session.commit()
            user_id = user.id
        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]
        response = self.client.post(
            f"/admin/users/{user_id}/vip", data={"csrf_token": csrf}
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            self.assertTrue(db.session.get(User, user_id).is_vip)

    def test_admin_users_support_search_filter_and_sort(self):
        self.login()
        with self.app.app_context():
            db.session.add_all(
                [
                    User(
                        openid="user-alpha",
                        nickname="Alpha",
                        phone="13800138001",
                        is_vip=False,
                    ),
                    User(
                        openid="user-beta",
                        nickname="Beta",
                        phone="13800138002",
                        is_vip=True,
                    ),
                ]
            )
            db.session.commit()

        searched = self.client.get("/admin/users?keyword=13800138002")
        self.assertEqual(searched.status_code, 200)
        self.assertIn(b"Beta", searched.data)
        self.assertNotIn(b"Alpha", searched.data)

        vip_only = self.client.get("/admin/users?vip=yes&sort=vip_first")
        self.assertEqual(vip_only.status_code, 200)
        self.assertIn(b"Beta", vip_only.data)
        self.assertNotIn(b"Alpha", vip_only.data)

        sorted_users = self.client.get("/admin/users?sort=nickname_desc")
        self.assertLess(
            sorted_users.data.find(b"Beta"),
            sorted_users.data.find(b"Alpha"),
        )

    def test_admin_can_bulk_set_users_as_vip(self):
        self.login()
        with self.app.app_context():
            users = [
                User(openid="bulk-user-1", nickname="Bulk One"),
                User(openid="bulk-user-2", nickname="Bulk Two"),
            ]
            db.session.add_all(users)
            db.session.commit()
            user_ids = [user.id for user in users]
        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]

        response = self.client.post(
            "/admin/users/bulk-vip",
            data={"csrf_token": csrf, "user_ids": user_ids},
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            updated = User.query.filter(User.id.in_(user_ids)).all()
            self.assertTrue(all(user.is_vip for user in updated))
            self.assertEqual(
                AdminAudit.query.filter_by(action="bulk_set_vip").count(), 2
            )

    def test_registration_page_marks_checkin_as_confirmed_action(self):
        self.login()
        response = self.client.get("/admin/registrations")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"data-checkin-dialog", response.data)
        self.assertIn("签到后不可撤销".encode(), response.data)

    def test_admin_can_create_and_reset_test_data(self):
        self.login()
        with self.client.session_transaction() as session:
            csrf = session["csrf_token"]
        created = self.client.post(
            "/admin/test-data",
            data={"csrf_token": csrf},
        )
        self.assertEqual(created.status_code, 302)
        with self.app.app_context():
            self.assertEqual(
                User.query.filter(User.openid.like("admin-test-user-%")).count(),
                8,
            )
            registration = (
                Registration.query.join(User)
                .filter(User.openid.like("admin-test-user-%"))
                .first()
            )
            registration_id = registration.id
            registration.status = "checked_in"
            registration.checked_in_at = datetime.now()
            db.session.commit()

        reset = self.client.post(
            f"/admin/registrations/{registration_id}/test-status",
            data={"csrf_token": csrf, "status": "registered"},
        )
        self.assertEqual(reset.status_code, 302)
        with self.app.app_context():
            registration = db.session.get(Registration, registration_id)
            self.assertEqual(registration.status, "registered")
            self.assertIsNone(registration.checked_in_at)


if __name__ == "__main__":
    unittest.main()
