import logging
import os

import httpx

logger = logging.getLogger("notes-service")

NOTIFICATIONS_URL = os.getenv("NOTIFICATIONS_URL", "http://localhost:8003")


def send_event(event_type: str, user_id: int, note_id: int, title: str = "") -> None:
    payload = {
        "event_type": event_type,
        "user_id": user_id,
        "note_id": note_id,
        "title": title,
    }
    try:
        response = httpx.post(f"{NOTIFICATIONS_URL}/events", json=payload, timeout=2.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # Notifications failing must never break notes
        logger.warning("Could not reach notifications-service: %s", exc)
