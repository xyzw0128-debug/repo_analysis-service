from core.logging import get_logger
from github.clone_service import clone_repo, get_commit_sha, cleanup, CloneError
from github.file_scanner import scan_repository
from llm.client import analyze_with_llm, InputTooLargeError, AnalysisFailedError
from services.prompt_loader import PromptLoader
from services.cache import make_cache_key, cache_lookup, store_cache_key

logger = get_logger(__name__)


def run_analysis_job(session, job, settings, api_client):
    clone_path = None
    try:
        job.status = 'running'; session.commit()
        prelim_key = make_cache_key(job.prompt_name, job.prompt_version, job.repo_url, job.branch, job.commit_sha or '')
        hit = cache_lookup(session, prelim_key)
        if hit:
            job.result_json = hit
            job.status = 'completed'
            session.commit()
            return
        try:
            clone_path = clone_repo(job.repo_url, job.branch, settings.github_token, str(job.id))
        except CloneError:
            job.status = 'failed'; job.error_code = 'CLONE_FAILED'; session.commit(); return

        job.commit_sha = get_commit_sha(str(clone_path)); session.commit()
        scan = scan_repository(str(clone_path))
        rendered = PromptLoader(settings.prompts_root).render(job.prompt_name, int(job.prompt_version), scan.repo_tree, scan.selected_files)
        try:
            result, usage = analyze_with_llm(settings.llm_provider, settings.llm_model, rendered['system'], rendered['user'], settings.max_input_tokens, api_client)
        except InputTooLargeError:
            job.status = 'failed'; job.error_code = 'INPUT_TOO_LARGE'; session.commit(); return
        except AnalysisFailedError:
            job.status = 'failed'; job.error_code = 'LLM_FAILED'; session.commit(); return

        key = make_cache_key(job.prompt_name, job.prompt_version, job.repo_url, job.branch, job.commit_sha)
        job.result_json = result.model_dump_json()
        job.status = 'completed'
        job.model = usage['model']; job.tokens_in = usage['tokens_in']; job.tokens_out = usage['tokens_out']; job.latency_ms = usage['latency_ms']; job.retry_count = usage['retry_count']
        store_cache_key(job, key)
        session.commit()
        logger.info('analysis_completed', extra={'prompt_name': job.prompt_name, 'prompt_version': job.prompt_version, 'model': job.model, 'tokens_in': job.tokens_in, 'tokens_out': job.tokens_out, 'cache_hit': False, 'latency_ms': job.latency_ms, 'retry_count': job.retry_count})
    except Exception:
        job.status = 'failed'; job.error_code = job.error_code or 'INTERNAL_ERROR'; session.commit()
    finally:
        if clone_path is not None:
            cleanup(str(clone_path))
