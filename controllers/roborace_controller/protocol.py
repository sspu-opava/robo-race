"""Small JSON protocol validation helpers for Webots WWI messages."""
import json


CLIENT_TYPES = {"hello", "restore_view", "set_level", "validate", "start", "reset", "new_competitor", "admin_reset"}


def decode_message(raw: str | None) -> tuple[dict | None, str | None]:
    if not raw:
        return None, None
    try:
        message = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, "Zpráva z panelu není platný JSON."
    if not isinstance(message, dict) or message.get("type") not in CLIENT_TYPES:
        return None, "Zpráva z panelu nemá známý typ."
    request_id = message.get("request_id")
    if request_id is not None and (not isinstance(request_id, str) or len(request_id) > 80):
        return None, "Neplatné ID požadavku."
    return message, None


def encode_message(payload: dict) -> str:
    # Webots R2025a's Python wwiSendText uses character count as byte count.
    # Escape Unicode so Czech text cannot truncate the UTF-8 JSON payload.
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
