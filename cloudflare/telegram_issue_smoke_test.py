from __future__ import annotations

import argparse
import json
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def normalize_base_url(base_url: str) -> str:
    normalized = base_url.strip()
    if not normalized:
        raise ValueError("Base URL nie może być pusty.")
    if not normalized.startswith(("http://", "https://")):
        normalized = f"https://{normalized}"
    return normalized.rstrip("/")


def build_webhook_url(base_url: str, path_segment: str | None = None) -> str:
    normalized = normalize_base_url(base_url)
    if path_segment:
        return f"{normalized}/integrations/telegram/webhook/{path_segment}"
    return f"{normalized}/integrations/telegram/webhook"


def build_text_update(chat_id: str, message: str, user_id: str = "500100200") -> dict[str, Any]:
    return {
        "update_id": 10001,
        "message": {
            "message_id": 7,
            "from": {
                "id": int(user_id),
                "is_bot": False,
                "first_name": "Test",
                "username": "test_sender",
            },
            "chat": {
                "id": int(chat_id),
                "type": "private",
            },
            "date": 1712908800,
            "text": message,
        },
    }


def http_request(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 30000,
) -> tuple[int, str]:
    final_headers = headers.copy() if headers else {}
    final_headers.setdefault("Accept", "application/json")
    final_headers.setdefault("User-Agent", "curl/8.7.1 telegram-issue-smoke-test/1.0")
    body: bytes | None = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        final_headers.setdefault("Content-Type", "application/json")

    request = Request(url, data=body, headers=final_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8")


def run_smoke_test(
    base_url: str,
    chat_id: str,
    message: str,
    secret_token: str | None = None,
    path_segment: str | None = None,
    timeout: int = 30000,
) -> dict[str, Any]:
    webhook_url = build_webhook_url(base_url, path_segment=path_segment)
    payload = build_text_update(chat_id, message)
    headers: dict[str, str] = {}
    if secret_token:
        headers["X-Telegram-Bot-Api-Secret-Token"] = secret_token

    status, body = http_request(
        "POST",
        webhook_url,
        payload=payload,
        headers=headers,
        timeout=timeout,
    )

    try:
        parsed_body: Any = json.loads(body)
    except json.JSONDecodeError:
        parsed_body = body

    return {
        "webhook_url": webhook_url,
        "post": {
            "status": status,
            "body": parsed_body,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke test dla mostu Telegram -> GitHub Issues."
    )
    parser.add_argument(
        "base_url",
        help="Bazowy adres wdrożonego Worker'a, np. https://fish-pond-api-v1.<subdomain>.workers.dev",
    )
    parser.add_argument(
        "--chat-id",
        default="500100200",
        help="Id czatu testowego Telegram.",
    )
    parser.add_argument(
        "--message",
        default="Pomysl: test webhooka Telegram do Issues",
        help="Treść wiadomości testowej.",
    )
    parser.add_argument(
        "--secret-token",
        default=None,
        help="Opcjonalny TELEGRAM_WEBHOOK_SECRET_TOKEN do testu nagłówka webhooka.",
    )
    parser.add_argument(
        "--path-segment",
        default=None,
        help="Opcjonalny segment ścieżki webhooka Telegram.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout pojedynczego żądania w sekundach.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = run_smoke_test(
            args.base_url,
            chat_id=args.chat_id,
            message=args.message,
            secret_token=args.secret_token,
            path_segment=args.path_segment,
            timeout=args.timeout,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
