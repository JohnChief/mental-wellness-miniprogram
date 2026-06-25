import unittest

from app import create_app
from app.extensions import db
from app.models import AdminAudit, Event, User


class AdminTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "AUTO_INIT_DB": True,
                "SEED_SAMPLE_DATA": True,
                "SECRET_KEY": "test-secret",
                "ADMIN_USERNAME": "operator",
                "ADMIN_PASSWORD": "safe-password",
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

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
                "event_time_text": "周六 14:00",
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

    def test_admin_rejects_post_without_csrf(self):
        self.login()
        response = self.client.post("/admin/logout", data={})
        self.assertEqual(response.status_code, 400)

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


if __name__ == "__main__":
    unittest.main()
