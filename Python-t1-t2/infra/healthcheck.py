#!/usr/bin/env python3
"""Programmatic health checks: database, function, and the function's own /health endpoint.

    python healthcheck.py        # exit code 0 = all healthy, 1 = something is wrong
"""

import sys

import requests
from google.api_core import exceptions
from google.cloud import firestore, firestore_admin_v1, functions_v2

import common as c


def check_database_exists():
    admin = firestore_admin_v1.FirestoreAdminClient()
    db = admin.get_database(name=f"projects/{c.PROJECT_ID}/databases/{c.DATABASE_ID}")
    return f"{db.type_.name}, location {db.location_id}"


def check_database_read_write():
    client = firestore.Client(project=c.PROJECT_ID, database=c.DATABASE_ID)
    ref = client.collection("_health").document("healthcheck")
    ref.set({"checked_at": firestore.SERVER_TIMESTAMP})
    if not ref.get().exists:
        raise RuntimeError("document written but not found")
    return "write + read back ok"


def check_function_state():
    fn = functions_v2.FunctionServiceClient().get_function(name=c.FUNCTION_PATH)
    if fn.state.name != "ACTIVE":
        raise RuntimeError(f"state is {fn.state.name}")
    return f"ACTIVE, revision {fn.service_config.revision}"


def check_function_endpoint():
    url = c.function_url()
    resp = requests.get(f"{url}/health", headers={"Authorization": f"Bearer {c.identity_token()}"}, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    return f"HTTP 200 {resp.json()}"


CHECKS = [
    ("Firestore database exists", check_database_exists),
    ("Firestore read/write", check_database_read_write),
    ("Cloud Function state", check_function_state),
    ("Function /health endpoint", check_function_endpoint),
]


def main():
    failed = 0
    print(f"Health checks for {c.PROJECT_ID} / {c.FUNCTION_NAME}\n")
    for name, fn in CHECKS:
        try:
            print(f"  PASS  {name:<28} {fn()}")
        except (exceptions.GoogleAPICallError, requests.RequestException, RuntimeError) as exc:
            failed += 1
            print(f"  FAIL  {name:<28} {exc}")
    print(f"\n{len(CHECKS) - failed}/{len(CHECKS)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
