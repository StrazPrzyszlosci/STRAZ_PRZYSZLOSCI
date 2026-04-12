import json
import threading
import time
import unittest
from http.client import HTTPConnection

from api.server import create_server
from adapters.utils import load_sample_json


class APIServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_server("127.0.0.1", 18080)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=1)

    def post_json(self, path: str, payload: dict) -> tuple[int, dict]:
        connection = HTTPConnection("127.0.0.1", 18080, timeout=5)
        connection.request(
            "POST",
            path,
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def get_json(self, path: str) -> tuple[int, dict]:
        connection = HTTPConnection("127.0.0.1", 18080, timeout=5)
        connection.request("GET", path)
        response = connection.getresponse()
        data = json.loads(response.read().decode("utf-8"))
        connection.close()
        return response.status, data

    def test_provider_registration_and_status(self) -> None:
        payload = {
            "provider_id": "community-node-test",
            "provider_kind": "community",
            "provider_label": "Test Community Node",
            "node_class": "old_smartphone",
            "supports_water_quality": True,
            "supports_flow_monitoring": True,
            "supports_edge_vision_summary": True,
        }
        status, data = self.post_json("/v1/providers/register", payload)
        self.assertEqual(status, 201)
        self.assertEqual(data["registration_status"], "registered")

        status, data = self.get_json("/v1/providers/community-node-test/status")
        self.assertEqual(status, 200)
        self.assertEqual(data["provider_id"], "community-node-test")

    def test_recommendation_endpoint(self) -> None:
        observation = load_sample_json("fish_pond_observation.json")
        event = load_sample_json("fish_behavior_event.json")
        status, data = self.post_json(
            "/v1/recommendations/fish-pond",
            {"observation": observation, "last_behavior_event": event},
        )
        self.assertEqual(status, 200)
        self.assertEqual(data["schema_version"], "v1")
        self.assertIn("recommendation", data)
        self.assertIn("reason_codes", data)


if __name__ == "__main__":
    unittest.main()
