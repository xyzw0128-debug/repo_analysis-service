import json

from core.logging import get_logger
from github.clone_service import CloneError, cleanup, clone_repository, get_commit_sha
from github.file_scanner import scan_repository
from llm.client import AnalysisFailedError, InputTooLargeError
from services.cache import get_cached_result, make_cache_key, set_cache_key
from services.prompt_loader import PromptLoader

logger = get_logger(__name__)


def run_analysis_job(session, job, llm_client, github_token: str):
    clone_path = None
    try:
        job.status = "running"
        session.commit()
        cache_key = make_cache_key(job.prompt_name, str(job.prompt_version), job.repo_url, job.branch or "", job.commit_sha or "")
        cached = get_cached_result(session, cache_key)
        if cached:
            job.result = cached
            job.status = "completed"
            session.commit()
            return
        try:
            clone_path = clone_repository(str(job.id), job.repo_url, github_token, job.branch)
        except CloneError:
            job.status = "failed"; job.error_code = "CLONE_FAILED"; session.commit(); return
        job.commit_sha = get_commit_sha(clone_path)
        session.commit()
        scan = scan_repository(str(clone_path))
        prompt = PromptLoader().render(job.prompt_name, job.prompt_version, scan.repo_tree, scan.selected_files)
        try:
            response = llm_client.analyze(prompt["system"], prompt["user"])
        except InputTooLargeError:
            job.status = "failed"; job.error_code = "INPUT_TOO_LARGE"; session.commit(); return
        except AnalysisFailedError:
            job.status = "failed"; job.error_code = "LLM_FAILED"; session.commit(); return
        job.result = json.dumps(response["result"])
        usage = response["usage"]
        job.model = usage["model"]; job.tokens_in = usage["tokens_in"]; job.tokens_out = usage["tokens_out"]; job.latency_ms = usage["latency_ms"]; job.retry_count = usage["retry_count"]
        set_cache_key(job, make_cache_key(job.prompt_name, str(job.prompt_version), job.repo_url, job.branch or "", job.commit_sha or ""))
        job.status = "completed"
        session.commit()
        logger.info("analysis_complete", extra={"prompt_name": job.prompt_name, "prompt_version": job.prompt_version, "model": job.model, "tokens_in": job.tokens_in, "tokens_out": job.tokens_out, "cache_hit": False, "latency_ms": job.latency_ms, "retry_count": job.retry_count})
    except Exception:
        job.status = "failed"; job.error_code = job.error_code or "INTERNAL_ERROR"; session.commit()
    finally:
        if clone_path:
            cleanup(clone_path)
