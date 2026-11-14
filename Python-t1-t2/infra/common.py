"""Names and helpers shared by the infra scripts. Every resource is prefixed `ar-` so cleanup is safe."""

import os
import subprocess

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "gd-gcp-gridu-devops-t1-t2")
REGION = os.environ.get("GCP_REGION", "europe-west1")
PREFIX = "ar"

DATABASE_ID = f"{PREFIX}-serverless-db"
COLLECTION = "ar_github_repos"
RUNS_COLLECTION = "ar_runs"

FUNCTION_NAME = f"{PREFIX}-fetch-store"
RUNTIME = "python312"
ENTRY_POINT = "run"

SA_ID = f"{PREFIX}-fn-runtime"
SA_EMAIL = f"{SA_ID}@{PROJECT_ID}.iam.gserviceaccount.com"

BUCKET = f"{PREFIX}-fn-src-{PROJECT_ID}"
LOG_METRIC = "ar_fn_pipeline_errors"
CHANNEL_NAME = f"{PREFIX}-fn-alerts-email"
DASHBOARD_NAME = f"{PREFIX}-fn-dashboard"
POLICY_NAMES = {
    "errors": f"{PREFIX}-fn: 5xx responses",
    "latency": f"{PREFIX}-fn: p95 latency above 30s",
    "pipeline": f"{PREFIX}-fn: pipeline errors in logs",
}

FUNCTION_PATH = f"projects/{PROJECT_ID}/locations/{REGION}/functions/{FUNCTION_NAME}"


def step(message):
    print(f"\n==> {message}")


def ok(message):
    print(f"    ok: {message}")


def identity_token():
    """ID token of the logged-in gcloud user, used to call the (private) function."""
    return subprocess.check_output(["gcloud", "auth", "print-identity-token"], text=True).strip()


def function_url():
    from google.cloud import functions_v2

    fn = functions_v2.FunctionServiceClient().get_function(name=FUNCTION_PATH)
    return fn.service_config.uri
