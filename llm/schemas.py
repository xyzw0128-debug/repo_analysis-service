from typing import Literal
from pydantic import BaseModel, field_validator


class RepoAnalysisOutput(BaseModel):
    project_type: Literal[
        "web-api",
        "cli-tool",
        "library",
        "monorepo",
        "mobile-app",
        "unknown",
    ]
    languages: list[str]
    frameworks: list[str]
    key_files: list[str]
    summary: str
    risks: list[str]

    @field_validator("risks")
    @classmethod
    def max_five_risks(cls, v: list[str]) -> list[str]:
        return v[:5]

    @field_validator("summary")
    @classmethod
    def summary_word_limit(cls, v: str) -> str:
        words = v.split()
        if len(words) > 120:
            raise ValueError(
                f"Summary exceeds 120 words ({len(words)} found). "
                "Must be 2-3 sentences under 120 words."
            )
        return v
