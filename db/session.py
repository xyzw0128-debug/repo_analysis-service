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
