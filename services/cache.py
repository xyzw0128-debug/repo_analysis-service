import hashlib


def make_cache_key(prompt_name: str, prompt_version: str, repo_url: str, branch: str, commit_sha: str) -> str:
    payload = f'{prompt_name}|{prompt_version}|{repo_url}|{branch}|{commit_sha}'
    return hashlib.sha256(payload.encode()).hexdigest()


def cache_lookup(session, cache_key: str):
    for job in session.jobs:
        if job.cache_key == cache_key and job.status == 'completed':
            return job.result_json
    return None


def store_cache_key(job, cache_key: str):
    return hashlib.sha256(f"{prompt_name}{prompt_version}{repo_url}{branch}{commit_sha}".encode()).hexdigest()


def get_cached_result(session, cache_key: str):
    for j in getattr(session, "jobs", []):
        if j.cache_key == cache_key and j.status == "completed":
            return j.result
    return None


def set_cache_key(job, cache_key: str):
    job.cache_key = cache_key
