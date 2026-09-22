from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# pool_pre_ping + pool_recycle: o Neon (plano gratuito) suspende o banco após
# 5 min sem uso e derruba as conexões abertas; assim elas são refeitas sem erro.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_recycle=240)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
