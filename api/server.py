from __future__ import annotations

import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.utils import (  # noqa: E402
    make_provider_status,
    utc_now_iso,
    validate_event_payload,
    validate_observation_payload,
)
from models.fish_pond.recommendation_engine import generate_recommendation  # noqa: E402


REGISTRY: Dict[str, Dict[str, Any]] = {}
OBSERVATIONS: list[Dict[str, Any]] = []
EVENTS: list[Dict[str, Any]] = []


def validate_provider_descriptor(payload: Dict[str, Any]) -> Dict[str, Any]:
    required = ["provider_id", "provider_kind", "provider_label"]
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"Brak wymaganych pól providera: {', '.join(missing)}")
    return payload


class FishPondAPIHandler(BaseHTTPRequestHandler):
    server_version = "FishPondAPIServer/0.1"

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Nieprawidłowy JSON.") from exc

    def _not_found(self) -> None:
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Nie znaleziono zasobu."})

    def _bad_request(self, message: str) -> None:
        self._send_json(HTTPStatus.BAD_REQUEST, {"error": message})

    def _handle_provider_register(self, payload: Dict[str, Any]) -> None:
        provider = validate_provider_descriptor(payload)
        provider_id = provider["provider_id"]
        REGISTRY[provider_id] = {
            "descriptor": provider,
            "status": make_provider_status(
                provider_id,
                supports_water_quality=provider.get("supports_water_quality", False),
                supports_flow_monitoring=provider.get("supports_flow_monitoring", False),
                supports_edge_vision_summary=provider.get("supports_edge_vision_summary", False),
            ),
        }
        self._send_json(
            HTTPStatus.CREATED,
            {
                "provider_id": provider_id,
                "registration_status": "registered",
                "schema_version": "v1",
                "message": "Provider został zarejestrowany.",
            },
        )

    def _handle_observation(self, payload: Dict[str, Any]) -> None:
        observation = validate_observation_payload(payload)
        provider_id = observation["provider"]["provider_id"]
        if provider_id not in REGISTRY:
            REGISTRY[provider_id] = {
                "descriptor": observation["provider"],
                "status": make_provider_status(
                    provider_id,
                    supports_water_quality=observation["provider"].get("supports_water_quality", True),
                    supports_flow_monitoring=observation["provider"].get("supports_flow_monitoring", True),
                    supports_edge_vision_summary=observation["provider"].get(
                        "supports_edge_vision_summary", False
                    ),
                ),
            }
        REGISTRY[provider_id]["status"]["last_seen_at"] = utc_now_iso()
        OBSERVATIONS.append(observation)
        self._send_json(
            HTTPStatus.ACCEPTED,
            {
                "status": "accepted",
                "provider_id": provider_id,
                "observation_count": len(OBSERVATIONS),
            },
        )

    def _handle_event(self, payload: Dict[str, Any]) -> None:
        event = validate_event_payload(payload)
        provider_id = event["provider"]["provider_id"]
        if provider_id not in REGISTRY:
            REGISTRY[provider_id] = {
                "descriptor": event["provider"],
                "status": make_provider_status(
                    provider_id,
                    supports_water_quality=event["provider"].get("supports_water_quality", False),
                    supports_flow_monitoring=event["provider"].get("supports_flow_monitoring", False),
                    supports_edge_vision_summary=event["provider"].get(
                        "supports_edge_vision_summary", True
                    ),
                ),
            }
        REGISTRY[provider_id]["status"]["last_seen_at"] = utc_now_iso()
        EVENTS.append(event)
        self._send_json(
            HTTPStatus.ACCEPTED,
            {
                "status": "accepted",
                "provider_id": provider_id,
                "event_count": len(EVENTS),
            },
        )

    def _handle_recommendation(self, payload: Dict[str, Any]) -> None:
        if "observation" not in payload:
            raise ValueError("Brak pola observation.")
        observation = validate_observation_payload(payload["observation"])
        last_event = payload.get("last_behavior_event")
        if last_event is not None:
            last_event = validate_event_payload(last_event)
        recommendation = generate_recommendation(
            observation,
            context=payload.get("context"),
            last_event=last_event,
        )
        self._send_json(HTTPStatus.OK, recommendation)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            payload = self._read_json()
            if parsed.path == "/v1/providers/register":
                self._handle_provider_register(payload)
                return
            if parsed.path == "/v1/observations":
                self._handle_observation(payload)
                return
            if parsed.path == "/v1/events":
                self._handle_event(payload)
                return
            if parsed.path == "/v1/recommendations/fish-pond":
                self._handle_recommendation(payload)
                return
            self._not_found()
        except ValueError as exc:
            self._bad_request(str(exc))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 4 and parts[:2] == ["v1", "providers"] and parts[3] == "status":
            provider_id = parts[2]
            provider = REGISTRY.get(provider_id)
            if provider is None:
                self._not_found()
                return
            self._send_json(HTTPStatus.OK, provider["status"])
            return
        self._not_found()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), FishPondAPIHandler)


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    if len(sys.argv) >= 2:
        port = int(sys.argv[1])
    server = create_server(host, port)
    print(f"Fish pond API server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
