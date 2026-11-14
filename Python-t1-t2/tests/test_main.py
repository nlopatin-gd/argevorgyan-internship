"""Tests the HTTP handler end to end with the GitHub API and Firestore mocked out."""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "function"))
os.environ.setdefault("FIRESTORE_DATABASE", "test-db")

import main  # noqa: E402
import pipeline  # noqa: E402
from test_pipeline import good_repo  # noqa: E402


def call(path="/", json_body=None, query=""):
    import functions_framework

    flask_app = functions_framework.create_app(target="run", source=main.__file__)
    client = flask_app.test_client()
    return client.post(path + query, json=json_body) if json_body is not None else client.get(path + query)


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.client = mock.MagicMock()
        patches = [
            mock.patch.object(main.store, "get_client", return_value=self.client),
            mock.patch.object(main.store, "record_run"),
        ]
        self.record_run = patches[1].start()
        patches[0].start()
        self.addCleanup(mock.patch.stopall)

    def test_success_stores_valid_records_and_reports_rejected(self):
        raw = [good_repo(id=1), good_repo(id=2, name=""), good_repo(id=3)]
        with mock.patch.object(main.pipeline, "fetch_repos", return_value=raw), \
                mock.patch.object(main.store, "write_documents",
                                  return_value={"inserted": 2, "updated": 0, "unchanged": 0}) as write:
            resp = call("/", json_body={"org": "some-org"})
        body = resp.get_json()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual((body["fetched"], body["valid"], body["rejected"], body["inserted"]), (3, 2, 1, 2))
        self.assertEqual(len(write.call_args.args[2]), 2)
        self.record_run.assert_called_once()  # audit record written

    def test_external_api_failure_returns_502_and_is_recorded(self):
        with mock.patch.object(main.pipeline, "fetch_repos", side_effect=pipeline.FetchError("rate limited")):
            resp = call("/", json_body={"org": "some-org"})
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(resp.get_json()["status"], "failed")
        self.record_run.assert_called_once()

    def test_invalid_org_is_rejected_before_any_call(self):
        with mock.patch.object(main.pipeline, "fetch_repos") as fetch:
            resp = call("/", json_body={"org": "../../etc/passwd"})
        self.assertEqual(resp.status_code, 400)
        fetch.assert_not_called()

    def test_all_records_invalid_is_an_error(self):
        with mock.patch.object(main.pipeline, "fetch_repos", return_value=[good_repo(name="")]):
            resp = call("/", json_body={"org": "some-org"})
        self.assertEqual(resp.status_code, 500)

    def test_health_ok(self):
        with mock.patch.object(main.store, "health_check", return_value=True):
            resp = call("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "ok")

    def test_health_reports_unhealthy_database(self):
        with mock.patch.object(main.store, "health_check", side_effect=RuntimeError("db down")):
            resp = call("/health")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.get_json()["status"], "unhealthy")


if __name__ == "__main__":
    unittest.main()
