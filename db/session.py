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
