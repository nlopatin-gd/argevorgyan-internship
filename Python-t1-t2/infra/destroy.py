#!/usr/bin/env python3
"""Delete everything deploy.py created (all resources are named ar-...).

    python destroy.py                 # asks for confirmation
    python destroy.py --keep-database # keep the Firestore database and its data
"""

import argparse

from google.api_core import exceptions
from google.cloud import (
    firestore_admin_v1,
    functions_v2,
    iam_admin_v1,
    monitoring_dashboard_v1,
    monitoring_v3,
    resourcemanager_v3,
    storage,
)
from google.cloud.firestore_admin_v1 import types as fs_types
from google.cloud.logging_v2.services.metrics_service_v2 import MetricsServiceV2Client
from google.iam.v1 import iam_policy_pb2, options_pb2, policy_pb2

import common as c


def attempt(description, fn):
    try:
        fn()
        c.ok(description)
    except exceptions.NotFound:
        c.ok(f"{description} (already gone)")
    except exceptions.GoogleAPICallError as exc:
        print(f"    FAILED: {description}: {exc.message}")


def delete_function():
    c.step("Cloud Function")
    attempt("function deleted",
            lambda: functions_v2.FunctionServiceClient().delete_function(name=c.FUNCTION_PATH).result(timeout=600))


def delete_monitoring():
    c.step("Monitoring: alert policies, channel, dashboard, log metric")
    parent = f"projects/{c.PROJECT_ID}"
    policies = monitoring_v3.AlertPolicyServiceClient()
    for p in policies.list_alert_policies(request={"name": parent}):
        if p.display_name in c.POLICY_NAMES.values():
            attempt(f"policy '{p.display_name}'", lambda p=p: policies.delete_alert_policy(request={"name": p.name}))
    channels = monitoring_v3.NotificationChannelServiceClient()
    for ch in channels.list_notification_channels(request={"name": parent, "filter": f'display_name="{c.CHANNEL_NAME}"'}):
        attempt("notification channel", lambda ch=ch: channels.delete_notification_channel(request={"name": ch.name, "force": True}))
    dashboards = monitoring_dashboard_v1.DashboardsServiceClient()
    for d in dashboards.list_dashboards(request={"parent": parent}):
        if d.display_name == c.DASHBOARD_NAME:
            attempt("dashboard", lambda d=d: dashboards.delete_dashboard(request={"name": d.name}))
    attempt("log metric", lambda: MetricsServiceV2Client().delete_log_metric(
        log_metric_name=f"projects/{c.PROJECT_ID}/metrics/{c.LOG_METRIC}"))


def delete_bucket():
    c.step("Source bucket")

    def run():
        bucket = storage.Client(project=c.PROJECT_ID).get_bucket(c.BUCKET)
        bucket.delete(force=True)

    attempt("bucket deleted", run)


def remove_iam():
    c.step("IAM binding + service account")
    rm = resourcemanager_v3.ProjectsClient()
    resource = f"projects/{c.PROJECT_ID}"
    member = f"serviceAccount:{c.SA_EMAIL}"
    policy = rm.get_iam_policy(request=iam_policy_pb2.GetIamPolicyRequest(
        resource=resource, options=options_pb2.GetPolicyOptions(requested_policy_version=3)))
    policy.version = 3
    changed = False
    kept = []
    for b in policy.bindings:
        if member in b.members:
            b.members.remove(member)  # only our member, never other members of the binding
            changed = True
            if not b.members:
                continue
        kept.append(b)
    if changed:
        del policy.bindings[:]
        policy.bindings.extend(kept)
        rm.set_iam_policy(request=iam_policy_pb2.SetIamPolicyRequest(resource=resource, policy=policy))
        c.ok("project binding removed")
    attempt("service account deleted", lambda: iam_admin_v1.IAMClient().delete_service_account(
        request=iam_admin_v1.DeleteServiceAccountRequest(name=f"projects/{c.PROJECT_ID}/serviceAccounts/{c.SA_EMAIL}")))


def delete_database():
    c.step("Firestore database")
    attempt("database deleted", lambda: firestore_admin_v1.FirestoreAdminClient().delete_database(
        request=fs_types.DeleteDatabaseRequest(
            name=f"projects/{c.PROJECT_ID}/databases/{c.DATABASE_ID}")).result(timeout=600))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--keep-database", action="store_true")
    parser.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    args = parser.parse_args()

    print(f"This deletes the ar-... resources in project {c.PROJECT_ID}.")
    if not args.yes and input("Type 'delete' to continue: ") != "delete":
        print("aborted")
        return
    delete_function()
    delete_monitoring()
    delete_bucket()
    remove_iam()
    if not args.keep_database:
        delete_database()
    print("\nDone.")


if __name__ == "__main__":
    main()
