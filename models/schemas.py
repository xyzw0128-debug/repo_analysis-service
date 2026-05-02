from pydantic import BaseModel


class RepoAnalysisOutput(BaseModel):
    summary: str
    risks: list[str] = []
    recommendations: list[str] = []
