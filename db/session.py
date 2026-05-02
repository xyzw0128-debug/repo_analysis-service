from dataclasses import dataclass, field
from typing import List

from db.models import Job


def get_settings():
    class _S:
        database_url = "sqlite:///./repoforge.db"

    return _S()


def get_engine():
    return {"url": get_settings().database_url}


@dataclass
class InMemorySession:
    jobs: List[Job] = field(default_factory=list)

    def add(self, job: Job):
        self.jobs.append(job)

    def commit(self):
        return None


def get_session_factory():
    return InMemorySession
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import get_settings
from db.models.job import Base, Job

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        db.query(Job).filter(Job.status == "running").update(
            {
                Job.status: "failed",
                Job.error_message: "Server restarted during execution.",
            },
            synchronize_session=False,
        )
        db.commit()
