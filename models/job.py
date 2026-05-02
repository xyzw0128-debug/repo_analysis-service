from dataclasses import dataclass


@dataclass
class Job:
    id: int | None = None
    status: str = 'pending'
    result_json: str | None = None
    cache_key: str | None = None
    error_code: str | None = None
    prompt_name: str | None = None
    prompt_version: str | None = None
    repo_url: str | None = None
    branch: str | None = None
    commit_sha: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    latency_ms: int | None = None
    retry_count: int | None = None
