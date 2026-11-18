from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from schemas import UserCreate, UserLogin, UserOut, Token
from auth import hash_password, verify_password, create_access_token

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="users-service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "users-service"}


@app.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    new_user = models.User(email=user.email, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=Token)
def login(creds: UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return Token(access_token=create_access_token(user.id, user.email))
