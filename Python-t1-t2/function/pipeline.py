"""Fetch / validate / transform logic. No Google dependencies here, so it is easy to unit test."""

import hashlib
import json
import logging
import random
import time
from datetime import datetime, timezone

import requests

logger = logging.getLogger("pipeline")


def log(level, message, **fields):
    """Structured log line (the JSON formatter in main.py turns `fields` into JSON keys)."""
    logger.log(level, message, extra={"fields": fields})


class FetchError(Exception):
    """The external API could not be read (after retries / rate limiting)."""


# --------------------------------------------------------------------------------------------
# 1. Fetch (retries, backoff, rate limiting)
# --------------------------------------------------------------------------------------------

def _rate_limit_wait(resp, now=time.time):
    """Seconds to wait before retrying a rate limited response (Retry-After, else X-RateLimit-Reset)."""
    retry_after = resp.headers.get("Retry-After")
    if retry_after and retry_after.isdigit():
        return int(retry_after)
    reset = resp.headers.get("X-RateLimit-Reset")
    if reset and reset.isdigit():
        return max(0, int(reset) - int(now())) + 1
    return 60


def get_with_retries(session, url, *, params=None, max_retries=3, base_delay=1.0, timeout=10,
                     max_rate_limit_wait=30, sleep=time.sleep):
    """GET with retries.

    - network errors, timeouts and 5xx: retried with exponential backoff + jitter, up to `max_retries`
    - 429 / 403 with an exhausted rate limit: wait for Retry-After / reset time, but never longer than
      `max_rate_limit_wait` seconds (the function has a time limit); otherwise give up with a clear error
    - other 4xx (404, 401, ...): not retried, they will not fix themselves
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = session.get(url, params=params, timeout=timeout)
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt > max_retries:
                raise FetchError(f"network error after {attempt} attempts: {exc}") from exc
            delay = base_delay * 2 ** (attempt - 1) + random.uniform(0, 0.25)
            log(logging.WARNING, "network error, retrying", attempt=attempt, delay_seconds=round(delay, 2),
                error=str(exc))
            sleep(delay)
            continue

        remaining = resp.headers.get("X-RateLimit-Remaining")
        if resp.status_code == 200:
            if remaining is not None:
                log(logging.INFO, "api rate limit", remaining=remaining, limit=resp.headers.get("X-RateLimit-Limit"))
            return resp

        rate_limited = resp.status_code == 429 or (resp.status_code == 403 and remaining == "0")
        if rate_limited:
            wait = _rate_limit_wait(resp)
            if attempt > max_retries or wait > max_rate_limit_wait:
                raise FetchError(f"rate limited by the API (would need to wait {wait}s, limit is "
                                 f"{max_rate_limit_wait}s)")
            log(logging.WARNING, "rate limited, waiting", attempt=attempt, wait_seconds=wait)
            sleep(wait)
            continue

        if resp.status_code >= 500:
            if attempt > max_retries:
                raise FetchError(f"API returned {resp.status_code} after {attempt} attempts")
            delay = base_delay * 2 ** (attempt - 1) + random.uniform(0, 0.25)
            log(logging.WARNING, "server error, retrying", attempt=attempt, status=resp.status_code,
                delay_seconds=round(delay, 2))
            sleep(delay)
            continue

        raise FetchError(f"API returned {resp.status_code} for {url} (not retried)")


def fetch_repos(session, base_url, org, *, per_page=50, max_pages=2, **retry_options):
    """Fetch up to `max_pages` pages of an organisation's public repositories."""
    repos = []
    for page in range(1, max_pages + 1):
        resp = get_with_retries(session, f"{base_url}/orgs/{org}/repos",
                                params={"per_page": per_page, "page": page, "type": "public"}, **retry_options)
        items = resp.json()
        if not isinstance(items, list):
            raise FetchError(f"unexpected response shape: {type(items).__name__}")
        log(logging.INFO, "page fetched", page=page, items=len(items))
        repos.extend(items)
        if len(items) < per_page:
            break
    return repos


# --------------------------------------------------------------------------------------------
# 2. Validate
# --------------------------------------------------------------------------------------------

def _is_int(value, minimum=0):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate(raw):
    """Return a list of problems with one raw repo record (empty list = valid)."""
    if not isinstance(raw, dict):
        return ["record is not an object"]
    problems = []
    if not _is_int(raw.get("id"), 1):
        problems.append("id must be a positive integer")
    for key in ("name", "full_name"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            problems.append(f"{key} must be a non-empty string")
    url = raw.get("html_url")
    if not isinstance(url, str) or not url.startswith("https://"):
        problems.append("html_url must be an https URL")
    for key in ("stargazers_count", "forks_count", "open_issues_count"):
        if not _is_int(raw.get(key)):
            problems.append(f"{key} must be a non-negative integer")
    if raw.get("language") is not None and not isinstance(raw["language"], str):
        problems.append("language must be a string or null")
    try:
        parse_time(raw["updated_at"])
    except (KeyError, TypeError, ValueError, AttributeError):
        problems.append("updated_at must be an ISO timestamp")
    return problems


# --------------------------------------------------------------------------------------------
# 3. Transform
# --------------------------------------------------------------------------------------------

def popularity(stars):
    if stars >= 1000:
        return "high"
    if stars >= 100:
        return "medium"
    return "low"


def transform(raw, *, source, now=None):
    """Turn a validated GitHub record into the document we store (the schema)."""
    now = now or datetime.now(timezone.utc)
    stars = raw["stargazers_count"]
    doc = {
        "id": raw["id"],
        "name": raw["name"].strip(),
        "full_name": raw["full_name"].strip(),
        "url": raw["html_url"],
        "language": (raw.get("language") or "unknown").lower(),
        "stars": stars,
        "forks": raw["forks_count"],
        "open_issues": raw["open_issues_count"],
        "archived": bool(raw.get("archived", False)),
        "is_fork": bool(raw.get("fork", False)),
        "popularity": popularity(stars),
        "updated_at": parse_time(raw["updated_at"]),
        "source": source,
        "fetched_at": now,
    }
    # hash of the business fields only (not fetched_at), so unchanged repos can be skipped on later runs
    stable = {k: v for k, v in doc.items() if k not in ("fetched_at", "updated_at")}
    stable["updated_at"] = doc["updated_at"].isoformat()
    doc["content_hash"] = hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()
    return doc


def process(raw_records, *, source):
    """Validate + transform. Returns (documents, rejected) where rejected is [(id, problems), ...]."""
    docs, rejected, seen = [], [], set()
    for raw in raw_records:
        problems = validate(raw)
        if not problems and raw["id"] in seen:
            problems = ["duplicate id in response"]
        if problems:
            rejected.append((raw.get("id") if isinstance(raw, dict) else None, problems))
            log(logging.WARNING, "record rejected", record_id=raw.get("id") if isinstance(raw, dict) else None,
                problems=problems)
            continue
        seen.add(raw["id"])
        docs.append(transform(raw, source=source))
    return docs, rejected
