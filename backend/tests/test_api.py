import unittest

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
                "ADMIN_API_KEY": "test-admin-key",
            }
        )
        self.client = self.app.test_client()
        self.headers = {"X-DEV-OPENID": "test-openid"}

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

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

    def test_account_deletion_anonymizes_registration(self):
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
        self.assertEqual(recreated.status_code, 200)
        self.assertEqual(recreated.json["data"], [])


if __name__ == "__main__":
    unittest.main()
