from pydantic import BaseModel


class RepoAnalysisOutput(BaseModel):
    summary: str
    findings: list[str] = []
