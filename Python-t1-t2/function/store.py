"""Firestore access. Imports are lazy so the pure logic can be tested without Google libraries."""

import os

BATCH_SIZE = 400  # Firestore allows 500 writes per batch


def get_client():
    from google.cloud import firestore

    # project comes from the runtime environment; the database name from an environment variable
    return firestore.Client(database=os.environ["FIRESTORE_DATABASE"])


def write_documents(client, collection, docs):
    """Idempotent upsert: doc id = repo id. Documents whose content hash did not change are skipped.

    Returns {"inserted": n, "updated": n, "unchanged": n}.
    """
    refs = {d["id"]: client.collection(collection).document(str(d["id"])) for d in docs}
    existing = {}
    if refs:
        for snap in client.get_all(list(refs.values()), field_paths=["content_hash"]):
            if snap.exists:
                existing[snap.id] = snap.get("content_hash")

    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    batch = client.batch()
    pending = 0
    for d in docs:
        key = str(d["id"])
        if key not in existing:
            counts["inserted"] += 1
        elif existing[key] != d["content_hash"]:
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1
            continue
        batch.set(refs[d["id"]], d, merge=True)
        pending += 1
        if pending >= BATCH_SIZE:
            batch.commit()
            batch = client.batch()
            pending = 0
    if pending:
        batch.commit()
    return counts


def health_check(client):
    """Write and read back a document: proves the database is reachable AND writable with our identity."""
    from google.cloud import firestore

    ref = client.collection("_health").document("ping")
    ref.set({"checked_at": firestore.SERVER_TIMESTAMP})
    return ref.get().exists


def record_run(client, runs_collection, run):
    """Audit trail: one document per execution."""
    client.collection(runs_collection).document(run["run_id"]).set(run)
