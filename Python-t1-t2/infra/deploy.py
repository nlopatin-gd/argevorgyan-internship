#!/usr/bin/env python3
"""Create all cloud infrastructure with the Google Cloud Python SDKs (no gcloud, no console).

    python deploy.py --alert-email you@example.com

Safe to re-run: every step checks whether the resource already exists.
Authentication: Application Default Credentials (`gcloud auth application-default login`).
"""

import argparse
import hashlib
import io
import json
import time
import zipfile
from pathlib import Path

from google.api_core import exceptions
from google.cloud import (
    firestore_admin_v1,
    functions_v2,
    iam_admin_v1,
    monitoring_dashboard_v1,
    monitoring_v3,
    resourcemanager_v3,
    service_usage_v1,
    storage,
)
from google.cloud.firestore_admin_v1 import types as fs_types
from google.cloud.logging_v2.services.metrics_service_v2 import MetricsServiceV2Client
from google.cloud.logging_v2.types import LogMetric
from google.iam.v1 import iam_policy_pb2, options_pb2, policy_pb2
from google.protobuf import duration_pb2
from google.type import expr_pb2

import common as c

FUNCTION_DIR = Path(__file__).resolve().parent.parent / "function"

APIS = [
    "serviceusage.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "firestore.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
]


# ---------------------------------------------------------------------------------------------
# 1. APIs
# ---------------------------------------------------------------------------------------------
def enable_apis():
    c.step("Enabling APIs")
    client = service_usage_v1.ServiceUsageClient()
    request = service_usage_v1.BatchEnableServicesRequest(parent=f"projects/{c.PROJECT_ID}", service_ids=APIS)
    client.batch_enable_services(request=request).result(timeout=300)
    c.ok(f"{len(APIS)} APIs enabled")


# ---------------------------------------------------------------------------------------------
# 2. Firestore: database + schema (index)
# ---------------------------------------------------------------------------------------------
def create_database():
    c.step(f"Firestore database {c.DATABASE_ID}")
    admin = firestore_admin_v1.FirestoreAdminClient()
    name = f"projects/{c.PROJECT_ID}/databases/{c.DATABASE_ID}"
    try:
        admin.get_database(name=name)
        c.ok("already exists")
        return
    except exceptions.NotFound:
        pass
    database = fs_types.Database(
        location_id=c.REGION,
        type_=fs_types.Database.DatabaseType.FIRESTORE_NATIVE,
        delete_protection_state=fs_types.Database.DeleteProtectionState.DELETE_PROTECTION_DISABLED,
    )
    request = fs_types.CreateDatabaseRequest(
        parent=f"projects/{c.PROJECT_ID}", database_id=c.DATABASE_ID, database=database
    )
    admin.create_database(request=request).result(timeout=600)
    c.ok(f"created in {c.REGION} (native mode)")


def create_index():
    """Firestore is schemaless; the 'schema' is the document shape in pipeline.transform() plus this index,
    which makes queries like 'top repos per language' possible."""
    c.step("Firestore composite index (language ASC, stars DESC)")
    admin = firestore_admin_v1.FirestoreAdminClient()
    Index = firestore_admin_v1.Index
    index = Index(
        query_scope=Index.QueryScope.COLLECTION,
        fields=[
            Index.IndexField(field_path="language", order=Index.IndexField.Order.ASCENDING),
            Index.IndexField(field_path="stars", order=Index.IndexField.Order.DESCENDING),
        ],
    )
    parent = f"projects/{c.PROJECT_ID}/databases/{c.DATABASE_ID}/collectionGroups/{c.COLLECTION}"
    try:
        admin.create_index(request=firestore_admin_v1.CreateIndexRequest(parent=parent, index=index))
        c.ok("index creation started (finishes in a few minutes, in the background)")
    except exceptions.AlreadyExists:
        c.ok("already exists")


# ---------------------------------------------------------------------------------------------
# 3. Identity + permissions (least privilege)
# ---------------------------------------------------------------------------------------------
def create_service_account():
    c.step(f"Service account {c.SA_ID}")
    iam = iam_admin_v1.IAMClient()
    try:
        iam.create_service_account(
            request=iam_admin_v1.CreateServiceAccountRequest(
                name=f"projects/{c.PROJECT_ID}",
                account_id=c.SA_ID,
                service_account=iam_admin_v1.ServiceAccount(display_name="ar function runtime"),
            )
        )
        c.ok("created")
    except exceptions.AlreadyExists:
        c.ok("already exists")


ADMIN_GRANT_COMMAND = (
    f"gcloud projects add-iam-policy-binding {c.PROJECT_ID} "
    f"--member=serviceAccount:{c.SA_EMAIL} --role=roles/datastore.user "
    f"--condition='title=only-ar-serverless-db,"
    f"expression=resource.name == \"projects/{c.PROJECT_ID}/databases/{c.DATABASE_ID}\"'"
)


def grant_database_access():
    """Returns True if the binding exists. Without project IAM admin rights this cannot be done by us,
    so we print the exact command for an administrator and carry on."""
    try:
        _grant_database_access()
    except exceptions.PermissionDenied:
        print("    WARNING: you are not allowed to change the project IAM policy.")
        print("    Ask a project admin to run this ONE command (it only gives the function access to our database):\n")
        print(f"      {ADMIN_GRANT_COMMAND}\n")
        print("    Until then the function deploys fine, but writes to Firestore will fail with 403.")
        return False
    return True


def _grant_database_access():
    """roles/datastore.user, but ONLY on our database (IAM condition), not on every database in the project."""
    c.step("Granting the service account access to ONLY this Firestore database")
    rm = resourcemanager_v3.ProjectsClient()
    resource = f"projects/{c.PROJECT_ID}"
    member = f"serviceAccount:{c.SA_EMAIL}"
    role = "roles/datastore.user"
    title = "only-ar-serverless-db"
    expression = f'resource.name == "projects/{c.PROJECT_ID}/databases/{c.DATABASE_ID}"'

    for attempt in range(1, 7):  # a brand new service account can take a few seconds to be visible to IAM
        policy = rm.get_iam_policy(
            request=iam_policy_pb2.GetIamPolicyRequest(
                resource=resource, options=options_pb2.GetPolicyOptions(requested_policy_version=3)
            )
        )
        policy.version = 3
        for b in policy.bindings:
            if b.role == role and member in b.members and b.condition.title == title:
                c.ok("binding already exists")
                return
        policy.bindings.append(
            policy_pb2.Binding(
                role=role, members=[member], condition=expr_pb2.Expr(title=title, expression=expression)
            )
        )
        try:
            rm.set_iam_policy(request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy))
            c.ok(f"{role} on {c.DATABASE_ID} granted to {c.SA_EMAIL}")
            return
        except (exceptions.InvalidArgument, exceptions.Aborted, exceptions.FailedPrecondition) as exc:
            print(f"    retrying ({attempt}/6): {exc.message}")
            time.sleep(5)
    raise RuntimeError("could not grant the IAM binding")


# ---------------------------------------------------------------------------------------------
# 4. Function: upload source + deploy
# ---------------------------------------------------------------------------------------------
def build_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(FUNCTION_DIR.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                zf.write(path, path.relative_to(FUNCTION_DIR).as_posix())
    return buf.getvalue()


def upload_source():
    c.step(f"Uploading function source to gs://{c.BUCKET}")
    client = storage.Client(project=c.PROJECT_ID)
    bucket = client.lookup_bucket(c.BUCKET)
    if bucket is None:
        bucket = client.bucket(c.BUCKET)
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket = client.create_bucket(bucket, location=c.REGION)
        c.ok("bucket created")
    data = build_zip()
    object_name = f"source/{hashlib.sha256(data).hexdigest()[:16]}.zip"  # new code => new object => new build
    bucket.blob(object_name).upload_from_string(data, content_type="application/zip")
    c.ok(object_name)
    return object_name


def deploy_function(object_name, runtime_sa=c.SA_EMAIL):
    c.step(f"Deploying Cloud Function {c.FUNCTION_NAME} (gen2, {c.RUNTIME}) running as {runtime_sa}")
    client = functions_v2.FunctionServiceClient()
    parent = f"projects/{c.PROJECT_ID}/locations/{c.REGION}"
    function = functions_v2.Function(
        name=c.FUNCTION_PATH,
        description="Fetches GitHub repos, validates, transforms and stores them in Firestore",
        build_config=functions_v2.BuildConfig(
            runtime=c.RUNTIME,
            entry_point=c.ENTRY_POINT,
            source=functions_v2.Source(
                storage_source=functions_v2.StorageSource(bucket=c.BUCKET, object_=object_name)
            ),
        ),
        service_config=functions_v2.ServiceConfig(
            available_memory="256M",
            timeout_seconds=120,
            min_instance_count=0,
            max_instance_count=2,
            service_account_email=runtime_sa,
            ingress_settings=functions_v2.ServiceConfig.IngressSettings.ALLOW_ALL,
            # configuration through environment variables: database + API endpoint + tuning
            environment_variables={
                "FIRESTORE_DATABASE": c.DATABASE_ID,
                "FIRESTORE_COLLECTION": c.COLLECTION,
                "FIRESTORE_RUNS_COLLECTION": c.RUNS_COLLECTION,
                "API_BASE_URL": "https://api.github.com",
                "GITHUB_ORG": "GoogleCloudPlatform",
                "MAX_RETRIES": "3",
                "MAX_PAGES": "2",
                "RATE_LIMIT_MAX_WAIT_SECONDS": "30",
                "LOG_LEVEL": "INFO",
            },
        ),
    )
    try:
        client.get_function(name=c.FUNCTION_PATH)
        print("    function exists, updating (build takes a few minutes)...")
        op = client.update_function(request=functions_v2.UpdateFunctionRequest(function=function))
    except exceptions.NotFound:
        print("    creating (build takes a few minutes)...")
        op = client.create_function(
            request=functions_v2.CreateFunctionRequest(parent=parent, function=function, function_id=c.FUNCTION_NAME)
        )
    result = op.result(timeout=900)
    c.ok(f"state={result.state.name}  url={result.service_config.uri}")


# ---------------------------------------------------------------------------------------------
# 5. Logging + monitoring
# ---------------------------------------------------------------------------------------------
RUN_FILTER = f'resource.type="cloud_run_revision" AND resource.labels.service_name="{c.FUNCTION_NAME}"'


def create_log_metric():
    c.step(f"Log-based metric {c.LOG_METRIC} (counts ERROR log entries of the function)")
    client = MetricsServiceV2Client()
    metric = LogMetric(
        name=c.LOG_METRIC,
        description="ERROR logs written by the ar fetch/store function",
        filter=f"{RUN_FILTER} AND severity>=ERROR",
    )
    try:
        client.create_log_metric(parent=f"projects/{c.PROJECT_ID}", metric=metric)
        c.ok("created")
    except exceptions.AlreadyExists:
        c.ok("already exists")


def create_notification_channel(email):
    c.step(f"Notification channel ({email})")
    client = monitoring_v3.NotificationChannelServiceClient()
    parent = f"projects/{c.PROJECT_ID}"
    for ch in client.list_notification_channels(request={"name": parent, "filter": f'display_name="{c.CHANNEL_NAME}"'}):
        c.ok("already exists")
        return ch.name
    ch = client.create_notification_channel(
        request={
            "name": parent,
            "notification_channel": {
                "type_": "email",
                "display_name": c.CHANNEL_NAME,
                "labels": {"email_address": email},
            },
        }
    )
    c.ok("created")
    return ch.name


def _threshold_condition(name, flt, aligner, reducer, comparison, threshold, period=300):
    Cond = monitoring_v3.AlertPolicy.Condition
    return Cond(
        display_name=name,
        condition_threshold=Cond.MetricThreshold(
            filter=flt,
            comparison=comparison,
            threshold_value=threshold,
            duration=duration_pb2.Duration(seconds=0),
            trigger=Cond.Trigger(count=1),
            aggregations=[
                monitoring_v3.Aggregation(
                    alignment_period=duration_pb2.Duration(seconds=period),
                    per_series_aligner=aligner,
                    cross_series_reducer=reducer,
                )
            ],
        ),
    )


def create_alert_policies(channel):
    c.step("Alert policies")
    client = monitoring_v3.AlertPolicyServiceClient()
    parent = f"projects/{c.PROJECT_ID}"
    Agg = monitoring_v3.Aggregation
    GT = monitoring_v3.ComparisonType.COMPARISON_GT
    channels = [channel] if channel else []

    policies = {
        "errors": _threshold_condition(
            "5xx responses > 0",
            f'{RUN_FILTER} AND metric.type="run.googleapis.com/request_count" '
            f'AND metric.labels.response_code_class="5xx"',
            Agg.Aligner.ALIGN_SUM, Agg.Reducer.REDUCE_SUM, GT, 0,
        ),
        "latency": _threshold_condition(
            "p95 request latency > 30s",
            f'{RUN_FILTER} AND metric.type="run.googleapis.com/request_latencies"',
            Agg.Aligner.ALIGN_PERCENTILE_95, Agg.Reducer.REDUCE_MAX, GT, 30000,
        ),
        "pipeline": _threshold_condition(
            "ERROR log entries > 0",
            f'metric.type="logging.googleapis.com/user/{c.LOG_METRIC}" AND resource.type="cloud_run_revision"',
            Agg.Aligner.ALIGN_SUM, Agg.Reducer.REDUCE_SUM, GT, 0,
        ),
    }
    existing = {p.display_name for p in client.list_alert_policies(request={"name": parent})}
    for key, condition in policies.items():
        display_name = c.POLICY_NAMES[key]
        if display_name in existing:
            c.ok(f"'{display_name}' already exists")
            continue
        client.create_alert_policy(
            request={
                "name": parent,
                "alert_policy": monitoring_v3.AlertPolicy(
                    display_name=display_name,
                    combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
                    conditions=[condition],
                    notification_channels=channels,
                    documentation=monitoring_v3.AlertPolicy.Documentation(
                        content=f"Alert for Cloud Function {c.FUNCTION_NAME}. Check its logs first.",
                        mime_type="text/markdown",
                    ),
                ),
            }
        )
        c.ok(f"'{display_name}' created")
    if not channels:
        print("    note: no --alert-email given, policies have no notification channel")


def _tile(x, y, title, flt, aligner, reducer=None, group_by=None, plot="LINE"):
    agg = {"alignmentPeriod": "60s", "perSeriesAligner": aligner}
    if reducer:
        agg["crossSeriesReducer"] = reducer
    if group_by:
        agg["groupByFields"] = [group_by]
    return {
        "xPos": x, "yPos": y, "width": 6, "height": 4,
        "widget": {
            "title": title,
            "xyChart": {
                "dataSets": [{"plotType": plot, "timeSeriesQuery": {"timeSeriesFilter": {"filter": flt, "aggregation": agg}}}]
            },
        },
    }


def create_dashboard():
    c.step(f"Monitoring dashboard {c.DASHBOARD_NAME}")
    client = monitoring_dashboard_v1.DashboardsServiceClient()
    parent = f"projects/{c.PROJECT_ID}"
    for d in client.list_dashboards(request={"parent": parent}):
        if d.display_name == c.DASHBOARD_NAME:
            c.ok("already exists")
            return
    run_filter = f'resource.type="cloud_run_revision" resource.labels.service_name="{c.FUNCTION_NAME}"'
    body = {
        "displayName": c.DASHBOARD_NAME,
        "mosaicLayout": {
            "columns": 12,
            "tiles": [
                _tile(0, 0, "Requests per second by response class",
                      f'{run_filter} metric.type="run.googleapis.com/request_count"',
                      "ALIGN_RATE", "REDUCE_SUM", 'metric.label."response_code_class"', "STACKED_BAR"),
                _tile(6, 0, "Request latency p95 (ms)",
                      f'{run_filter} metric.type="run.googleapis.com/request_latencies"',
                      "ALIGN_PERCENTILE_95", "REDUCE_MAX"),
                _tile(0, 4, "Pipeline errors (from logs)",
                      f'metric.type="logging.googleapis.com/user/{c.LOG_METRIC}"',
                      "ALIGN_SUM", "REDUCE_SUM", None, "STACKED_BAR"),
                _tile(6, 4, "Container instances",
                      f'{run_filter} metric.type="run.googleapis.com/container/instance_count"',
                      "ALIGN_MAX", "REDUCE_SUM"),
            ],
        },
    }
    dashboard = monitoring_dashboard_v1.Dashboard.from_json(json.dumps(body))
    client.create_dashboard(request={"parent": parent, "dashboard": dashboard})
    c.ok("created")


# ---------------------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--alert-email", help="address that receives the alert emails")
    parser.add_argument("--skip-apis", action="store_true", help="skip enabling APIs (already enabled / no permission)")
    parser.add_argument("--runtime-sa", help="run the function as this EXISTING service account instead of creating "
                                             "ar-fn-runtime (e.g. the default compute service account)")
    args = parser.parse_args()

    print(f"Project {c.PROJECT_ID}, region {c.REGION}")
    if not args.skip_apis:
        enable_apis()
    create_database()
    create_index()
    if args.runtime_sa:
        runtime_sa = args.runtime_sa
        print(f"\n==> Using existing service account {runtime_sa} (skipping ar-fn-runtime and the IAM binding)")
    else:
        runtime_sa = c.SA_EMAIL
        create_service_account()
        grant_database_access()
    deploy_function(upload_source(), runtime_sa)
    create_log_metric()
    channel = create_notification_channel(args.alert_email) if args.alert_email else None
    create_alert_policies(channel)
    create_dashboard()
    print("\nDone. Next: python healthcheck.py, then python invoke.py")


if __name__ == "__main__":
    main()
