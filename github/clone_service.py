import shutil
import subprocess
from pathlib import Path


class CloneError(Exception):
    pass


def _auth_url(repo_url: str, token: str) -> str:
    return repo_url.replace('https://', f'https://x-access-token:{token}@')


def clone_repo(repo_url: str, branch: str, token: str, job_id: str) -> Path:
    clone_path = Path(f'/tmp/repoforge/{job_id}')
    if clone_path.exists():
        shutil.rmtree(clone_path, ignore_errors=True)
    clone_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(['git','clone','--depth','1','--branch',branch,_auth_url(repo_url, token), str(clone_path)], check=True, capture_output=True)
        return clone_path
    except Exception as exc:
        shutil.rmtree(clone_path, ignore_errors=True)
        raise CloneError(f'Clone failed for {repo_url}') from exc


def get_commit_sha(clone_path: str) -> str:
    result = subprocess.run(['git','-C',clone_path,'rev-parse','HEAD'], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def cleanup(clone_path: str) -> None:
    shutil.rmtree(clone_path, ignore_errors=True)
