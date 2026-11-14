import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "function"))

import requests  # noqa: E402

import pipeline  # noqa: E402


class FakeResponse:
    def __init__(self, status=200, data=None, headers=None):
        self.status_code = status
        self._data = data if data is not None else []
        self.headers = headers or {}

    def json(self):
        return self._data


class FakeSession:
    """Returns the queued responses (or raises queued exceptions) one per call."""

    def __init__(self, *items):
        self.items = list(items)
        self.calls = 0

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def good_repo(**overrides):
    repo = {
        "id": 1, "name": "demo", "full_name": "org/demo", "html_url": "https://github.com/org/demo",
        "stargazers_count": 150, "forks_count": 3, "open_issues_count": 2, "language": "Python",
        "updated_at": "2026-01-02T03:04:05Z", "archived": False, "fork": False,
    }
    repo.update(overrides)
    return repo


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.sleeps = []

    def get(self, session, **kwargs):
        return pipeline.get_with_retries(session, "https://api.test/x", sleep=self.sleeps.append, base_delay=1, **kwargs)

    def test_retries_server_errors_then_succeeds(self):
        session = FakeSession(FakeResponse(500), FakeResponse(503), FakeResponse(200, [1]))
        resp = self.get(session, max_retries=3)
        self.assertEqual(resp.json(), [1])
        self.assertEqual(session.calls, 3)
        self.assertEqual(len(self.sleeps), 2)

    def test_gives_up_after_max_retries(self):
        session = FakeSession(*[FakeResponse(500) for _ in range(4)])
        with self.assertRaises(pipeline.FetchError):
            self.get(session, max_retries=3)
        self.assertEqual(session.calls, 4)  # first try + 3 retries

    def test_retries_network_errors(self):
        session = FakeSession(requests.ConnectionError("boom"), FakeResponse(200, []))
        self.get(session, max_retries=2)
        self.assertEqual(session.calls, 2)

    def test_does_not_retry_404(self):
        session = FakeSession(FakeResponse(404))
        with self.assertRaises(pipeline.FetchError):
            self.get(session, max_retries=3)
        self.assertEqual(session.calls, 1)
        self.assertEqual(self.sleeps, [])

    def test_waits_for_retry_after_on_429(self):
        session = FakeSession(FakeResponse(429, headers={"Retry-After": "7"}), FakeResponse(200, []))
        self.get(session, max_retries=3)
        self.assertEqual(self.sleeps, [7])

    def test_waits_on_403_with_exhausted_rate_limit(self):
        session = FakeSession(FakeResponse(403, headers={"X-RateLimit-Remaining": "0", "Retry-After": "2"}),
                              FakeResponse(200, []))
        self.get(session, max_retries=3)
        self.assertEqual(self.sleeps, [2])

    def test_plain_403_is_not_a_rate_limit(self):
        session = FakeSession(FakeResponse(403, headers={"X-RateLimit-Remaining": "10"}))
        with self.assertRaises(pipeline.FetchError):
            self.get(session, max_retries=3)
        self.assertEqual(session.calls, 1)

    def test_refuses_to_wait_longer_than_the_limit(self):
        session = FakeSession(FakeResponse(429, headers={"Retry-After": "900"}))
        with self.assertRaises(pipeline.FetchError) as ctx:
            self.get(session, max_retries=3, max_rate_limit_wait=30)
        self.assertIn("rate limited", str(ctx.exception))
        self.assertEqual(self.sleeps, [])


class FetchReposTests(unittest.TestCase):
    def test_stops_when_a_page_is_not_full(self):
        session = FakeSession(FakeResponse(200, [good_repo(id=i) for i in range(1, 3)]))
        repos = pipeline.fetch_repos(session, "https://api.test", "org", per_page=5, max_pages=3)
        self.assertEqual(len(repos), 2)
        self.assertEqual(session.calls, 1)

    def test_follows_pages_up_to_max_pages(self):
        full = [good_repo(id=i) for i in range(1, 3)]
        session = FakeSession(FakeResponse(200, full), FakeResponse(200, full), FakeResponse(200, full))
        repos = pipeline.fetch_repos(session, "https://api.test", "org", per_page=2, max_pages=2)
        self.assertEqual(len(repos), 4)
        self.assertEqual(session.calls, 2)

    def test_rejects_unexpected_shape(self):
        session = FakeSession(FakeResponse(200, {"message": "nope"}))
        with self.assertRaises(pipeline.FetchError):
            pipeline.fetch_repos(session, "https://api.test", "org")


class ValidateTests(unittest.TestCase):
    def test_valid_record_has_no_problems(self):
        self.assertEqual(pipeline.validate(good_repo()), [])

    def test_language_may_be_null(self):
        self.assertEqual(pipeline.validate(good_repo(language=None)), [])

    def test_reports_each_problem(self):
        problems = pipeline.validate(good_repo(id=-1, name="  ", html_url="http://insecure",
                                               stargazers_count="12", updated_at="yesterday"))
        self.assertEqual(len(problems), 5)

    def test_booleans_are_not_integers(self):
        self.assertTrue(pipeline.validate(good_repo(stargazers_count=True)))

    def test_not_a_dict(self):
        self.assertEqual(pipeline.validate("oops"), ["record is not an object"])


class TransformTests(unittest.TestCase):
    def test_schema_and_derived_fields(self):
        doc = pipeline.transform(good_repo(stargazers_count=1500), source="test")
        self.assertEqual(doc["language"], "python")
        self.assertEqual(doc["popularity"], "high")
        self.assertEqual(doc["updated_at"].year, 2026)
        self.assertEqual(doc["source"], "test")
        self.assertEqual(len(doc["content_hash"]), 64)

    def test_missing_language_becomes_unknown(self):
        self.assertEqual(pipeline.transform(good_repo(language=None), source="t")["language"], "unknown")

    def test_hash_ignores_fetch_time_but_changes_with_content(self):
        a = pipeline.transform(good_repo(), source="t")
        b = pipeline.transform(good_repo(), source="t")
        c = pipeline.transform(good_repo(stargazers_count=999), source="t")
        self.assertEqual(a["content_hash"], b["content_hash"])
        self.assertNotEqual(a["content_hash"], c["content_hash"])

    def test_popularity_buckets(self):
        self.assertEqual([pipeline.popularity(n) for n in (0, 99, 100, 999, 1000)],
                         ["low", "low", "medium", "medium", "high"])


class ProcessTests(unittest.TestCase):
    def test_splits_valid_invalid_and_duplicates(self):
        raw = [good_repo(id=1), good_repo(id=2, name=""), good_repo(id=1), good_repo(id=3)]
        docs, rejected = pipeline.process(raw, source="t")
        self.assertEqual([d["id"] for d in docs], [1, 3])
        self.assertEqual(len(rejected), 2)


if __name__ == "__main__":
    unittest.main()
