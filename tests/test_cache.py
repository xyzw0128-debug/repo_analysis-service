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
