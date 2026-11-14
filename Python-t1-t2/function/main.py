"""Cloud Function entry point: fetch repos from the GitHub API, validate, transform, store in Firestore."""

import json
import logging
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone

import functions_framework
import requests

import pipeline
import store


class JsonFormatter(logging.Formatter):
    """One JSON object per line on stdout: Cloud Logging turns `severity` and the other keys into fields."""

    def format(self, record):
        payload = {"severity": record.levelname, "message": record.getMessage(), "logger": record.name}
        payload.update(getattr(record, "fields", {}))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging():
    root = logging.getLogger()
    if not any(isinstance(h.formatter, JsonFormatter) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        root.handlers = [handler]
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())


setup_logging()
logger = logging.getLogger("main")
ORG_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,39}$")


def log(level, message, **fields):
    logger.log(level, message, extra={"fields": fields})


def _config():
    """Everything configurable comes from environment variables (set at deploy time)."""
    return {
        "api_base_url": os.environ.get("API_BASE_URL", "https://api.github.com"),
        "default_org": os.environ.get("GITHUB_ORG", "GoogleCloudPlatform"),
        "collection": os.environ.get("FIRESTORE_COLLECTION", "ar_github_repos"),
        "runs_collection": os.environ.get("FIRESTORE_RUNS_COLLECTION", "ar_runs"),
        "max_retries": int(os.environ.get("MAX_RETRIES", "3")),
        "max_pages": int(os.environ.get("MAX_PAGES", "2")),
        "max_rate_limit_wait": int(os.environ.get("RATE_LIMIT_MAX_WAIT_SECONDS", "30")),
    }


def _json(body, status=200):
    return json.dumps(body, default=str), status, {"Content-Type": "application/json"}


def handle_health():
    """Database health check, exposed as GET /health."""
    try:
        ok = store.health_check(store.get_client())
    except Exception as exc:  # noqa: BLE001 - report any failure as unhealthy
        log(logging.ERROR, "health check failed", error=str(exc))
        return _json({"status": "unhealthy", "database": "unreachable", "error": str(exc)}, 503)
    log(logging.INFO, "health check ok", database="firestore")
    return _json({"status": "ok" if ok else "unhealthy", "database": "firestore"}, 200 if ok else 503)


def handle_run(request):
    cfg = _config()
    body = request.get_json(silent=True) or {}
    org = str(body.get("org") or request.args.get("org") or cfg["default_org"])
    if not ORG_PATTERN.match(org):
        return _json({"status": "error", "error": "invalid org name"}, 400)
    max_pages = max(1, min(int(body.get("max_pages") or cfg["max_pages"]), 5))

    run_id = uuid.uuid4().hex[:12]
    started = time.time()
    run = {"run_id": run_id, "org": org, "started_at": datetime.now(timezone.utc), "status": "running"}
    source = f"{cfg['api_base_url']}/orgs/{org}/repos"
    log(logging.INFO, "run started", run_id=run_id, org=org, max_pages=max_pages)

    client = None
    try:
        client = store.get_client()

        # 1. fetch
        t = time.time()
        with requests.Session() as session:
            session.headers.update({"Accept": "application/vnd.github+json", "User-Agent": "ar-fetch-store"})
            raw = pipeline.fetch_repos(session, cfg["api_base_url"], org, max_pages=max_pages,
                                       max_retries=cfg["max_retries"], max_rate_limit_wait=cfg["max_rate_limit_wait"])
        log(logging.INFO, "step fetch done", run_id=run_id, fetched=len(raw), seconds=round(time.time() - t, 2))

        # 2 + 3. validate and transform
        t = time.time()
        docs, rejected = pipeline.process(raw, source=source)
        log(logging.INFO, "step validate+transform done", run_id=run_id, valid=len(docs), rejected=len(rejected),
            seconds=round(time.time() - t, 2))
        if raw and not docs:
            raise ValueError("every fetched record failed validation")

        # 4. store
        t = time.time()
        counts = store.write_documents(client, cfg["collection"], docs)
        log(logging.INFO, "step store done", run_id=run_id, seconds=round(time.time() - t, 2), **counts)

        run.update(status="success", fetched=len(raw), valid=len(docs), rejected=len(rejected), **counts)
        code = 200
    except pipeline.FetchError as exc:
        log(logging.ERROR, "run failed: external API", run_id=run_id, error=str(exc))
        run.update(status="failed", error=str(exc))
        code = 502
    except Exception as exc:  # noqa: BLE001 - always record the failure, then report it
        logger.error("run failed", extra={"fields": {"run_id": run_id, "error": str(exc)}}, exc_info=True)
        run.update(status="failed", error=str(exc))
        code = 500

    run["duration_seconds"] = round(time.time() - started, 2)
    try:
        if client is not None:
            store.record_run(client, cfg["runs_collection"], run)
    except Exception as exc:  # noqa: BLE001
        log(logging.ERROR, "could not write run record", run_id=run_id, error=str(exc))
    log(logging.INFO if code == 200 else logging.ERROR, "run finished", **{k: v for k, v in run.items()
                                                                           if k != "started_at"})
    return _json(run, code)


@functions_framework.http
def run(request):
    if request.path.rstrip("/") == "/health":
        return handle_health()
    return handle_run(request)
