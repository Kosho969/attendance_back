from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    # Reconnects instead of failing with "MySQL server has gone away" after
    # MySQL closes idle connections (wait_timeout); no-op for sqlite.
    pool_pre_ping=True,
    pool_recycle=280,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def sync_schema() -> None:
    """Add columns introduced after the table already existed.

    There's no migration tool in this project (just create_all at startup),
    which only creates missing tables, not missing columns. This patches the
    one gap that matters today: existing `users` rows predate
    `must_change_password`.
    """
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("users")}
    if "must_change_password" not in columns:
        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN must_change_password BOOLEAN NOT NULL DEFAULT 1")
            )
