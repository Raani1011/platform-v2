from typing import List

from fastapi import BackgroundTasks, FastAPI, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from schemas import NoteCreate, NoteUpdate, NoteOut
from auth import get_current_user_id
from notifier import send_event

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="notes-service", version="1.1.0")


def get_owned_note(note_id: int, user_id: int, db: Session) -> models.Note:
    note = (
        db.query(models.Note)
        .filter(models.Note.id == note_id, models.Note.owner_id == user_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.get("/health")
def health():
    return {"status": "ok", "service": "notes-service"}


@app.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    note: NoteCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    new_note = models.Note(owner_id=user_id, **note.model_dump())
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    background_tasks.add_task(send_event, "note.created", user_id, new_note.id, new_note.title)
    return new_note


@app.get("/notes", response_model=List[NoteOut])
def list_notes(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Note)
        .filter(models.Note.owner_id == user_id)
        .order_by(models.Note.created_at.desc())
        .all()
    )


@app.get("/notes/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_owned_note(note_id, user_id, db)


@app.put("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    updates: NoteUpdate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    note = get_owned_note(note_id, user_id, db)
    for field, value in updates.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    background_tasks.add_task(send_event, "note.updated", user_id, note.id, note.title)
    return note


@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    note = get_owned_note(note_id, user_id, db)
    title = note.title
    db.delete(note)
    db.commit()
    background_tasks.add_task(send_event, "note.deleted", user_id, note_id, title)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
