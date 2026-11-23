import logging
from collections import deque
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, status
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("notifications-service")

app = FastAPI(title="notifications-service", version="1.0.0")

# Keep only the latest 100 events in memory
events = deque(maxlen=100)


class NoteEvent(BaseModel):
    event_type: Literal["note.created", "note.updated", "note.deleted"]
    user_id: int
    note_id: int
    title: str = ""


@app.get("/health")
def health():
    return {"status": "ok", "service": "notifications-service"}


@app.post("/events", status_code=status.HTTP_202_ACCEPTED)
def receive_event(event: NoteEvent):
    record = event.model_dump()
    record["received_at"] = datetime.now(timezone.utc).isoformat()
    events.appendleft(record)
    logger.info(
        "NOTIFY user=%s %s note_id=%s title=%r",
        event.user_id, event.event_type, event.note_id, event.title,
    )
    return {"accepted": True}


@app.get("/events")
def list_events():
    return list(events)
