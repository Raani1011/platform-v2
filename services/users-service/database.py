import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base


def build_database_url():
    # 1. Full URL given (local dev, Docker Compose)
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # 2. Separate parts given (Kubernetes + RDS).
    #    URL.create escapes special characters in the generated password safely.
    host = os.getenv("DB_HOST")
    if host:
        return URL.create(
            drivername="postgresql+psycopg2",
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=host,
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME"),
            query={"sslmode": os.getenv("DB_SSLMODE", "require")},
        )

    # 3. Quick local fallback
    return "sqlite:///./users.db"


DATABASE_URL = build_database_url()

# SQLite needs this extra setting; Postgres doesn't
connect_args = {"check_same_thread": False} if str(DATABASE_URL).startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
