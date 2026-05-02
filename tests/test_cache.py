from models.job import Job
from services.cache import make_cache_key, cache_lookup


class FakeSession:
    def __init__(self, jobs):
        self.jobs = jobs


def test_same_inputs_same_key():
    assert make_cache_key('p','1','u','b','c') == make_cache_key('p','1','u','b','c')


def test_diff_commit_diff_key():
    assert make_cache_key('p','1','u','b','c1') != make_cache_key('p','1','u','b','c2')


def test_cache_hit_and_miss_and_incomplete():
    s = FakeSession([
        Job(status='completed', cache_key='k1', result_json='{"ok":1}'),
        Job(status='running', cache_key='k2', result_json='{"ok":2}'),
    ])
    assert cache_lookup(s, 'k1') == '{"ok":1}'
    assert cache_lookup(s, 'missing') is None
    assert cache_lookup(s, 'k2') is None
from db.models import Job
from db.session import InMemorySession
from services.cache import get_cached_result, make_cache_key


def test_cache_key_stable_and_changes_on_commit():
    assert make_cache_key("p", "1", "u", "b", "sha1") == make_cache_key("p", "1", "u", "b", "sha1")
    assert make_cache_key("p", "1", "u", "b", "sha1") != make_cache_key("p", "1", "u", "b", "sha2")


def test_cache_hit_miss_and_running_not_hit():
    s = InMemorySession()
    s.jobs = [Job(status="completed", cache_key="abc", result='{"ok":1}'), Job(status="running", cache_key="def", result='{"ok":2}')]
    assert get_cached_result(s, "abc") == '{"ok":1}'
    assert get_cached_result(s, "zzz") is None
    assert get_cached_result(s, "def") is None
