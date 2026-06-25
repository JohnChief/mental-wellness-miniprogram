import unittest
from unittest.mock import patch

from app import create_app
from app.extensions import db


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "AUTO_INIT_DB": True,
                "SEED_SAMPLE_DATA": True,
                "ALLOW_DEV_OPENID": True,
            }
        )
        self.client = self.app.test_client()
        self.headers = {"X-DEV-OPENID": "test-openid"}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def register_user(self, openid="test-openid"):
        return self.client.post(
            "/api/auth/register",
            json={
                "nickname": "微信测试用户",
                "avatar_url": "cloud://test-env/avatars/test.jpg",
                "privacy_version": "2026-06-24",
            },
            headers={"X-DEV-OPENID": openid},
        )

    def test_auth_registration_and_existing_login(self):
        guest = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(guest.status_code, 200)
        self.assertFalse(guest.json["data"]["registered"])

        registered = self.register_user()
        self.assertEqual(registered.status_code, 201)
        self.assertTrue(registered.json["data"]["registered"])
        self.assertIsNone(registered.json["data"]["phone"])

        existing = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(existing.status_code, 200)
        self.assertEqual(existing.json["data"]["nickname"], "微信测试用户")
        self.assertEqual(
            existing.json["data"]["avatar_url"],
            "cloud://test-env/avatars/test.jpg",
        )

    def test_auth_can_use_generated_profile_and_update_later(self):
        registered = self.client.post(
            "/api/auth/register",
            json={"privacy_version": "2026-06-24"},
            headers=self.headers,
        )
        self.assertEqual(registered.status_code, 201)
        self.assertTrue(registered.json["data"]["nickname"])
        self.assertTrue(
            registered.json["data"]["avatar_url"].startswith("default:")
        )

        updated = self.client.put(
            "/api/auth/profile",
            json={
                "nickname": "后来修改的昵称",
                "avatar_url": "cloud://test-env/avatars/new.jpg",
            },
            headers=self.headers,
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json["data"]["nickname"], "后来修改的昵称")

    def test_home_and_event_detail(self):
        home = self.client.get("/api/home")
        self.assertEqual(home.status_code, 200)
        self.assertEqual(home.json["code"], 0)
        self.assertGreaterEqual(len(home.json["data"]["events"]), 1)

        event_id = home.json["data"]["events"][0]["id"]
        detail = self.client.get(f"/api/events/{event_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertIn("notice", detail.json["data"])

    def test_registration_lifecycle_and_duplicate_protection(self):
        self.register_user()
        event_id = self.client.get("/api/events").json["data"][0]["id"]
        payload = {
            "event_id": event_id,
            "name": "测试用户",
            "phone": "13800138000",
            "remark": "",
            "privacy_version": "2026-06-24",
        }

        created = self.client.post(
            "/api/registrations", json=payload, headers=self.headers
        )
        self.assertEqual(created.status_code, 201)
        registration_id = created.json["data"]["id"]

        duplicate = self.client.post(
            "/api/registrations", json=payload, headers=self.headers
        )
        self.assertEqual(duplicate.status_code, 409)

        mine = self.client.get("/api/registrations/mine", headers=self.headers)
        self.assertEqual(len(mine.json["data"]), 1)

        cancelled = self.client.put(
            f"/api/registrations/{registration_id}/cancel", headers=self.headers
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json["data"]["status"], "cancelled")

    def test_user_route_rejects_untrusted_identity(self):
        response = self.client.get("/api/registrations/mine")
        self.assertEqual(response.status_code, 401)

    def test_legacy_admin_api_is_not_exposed(self):
        self.assertEqual(self.client.get("/admin/api/events").status_code, 404)
        self.assertEqual(self.client.get("/admin/api/users").status_code, 404)

    def test_account_deletion_anonymizes_registration(self):
        self.register_user()
        event_id = self.client.get("/api/events").json["data"][0]["id"]
        self.client.post(
            "/api/registrations",
            json={
                "event_id": event_id,
                "name": "待注销用户",
                "phone": "13800138000",
                "remark": "普通活动备注",
                "privacy_version": "2026-06-24",
            },
            headers=self.headers,
        )

        deleted = self.client.delete("/api/account", headers=self.headers)
        self.assertEqual(deleted.status_code, 200)

        recreated = self.client.get("/api/registrations/mine", headers=self.headers)
        self.assertEqual(recreated.status_code, 401)

        guest = self.client.get("/api/auth/me", headers=self.headers)
        self.assertEqual(guest.status_code, 200)
        self.assertFalse(guest.json["data"]["registered"])


if __name__ == "__main__":
    unittest.main()
