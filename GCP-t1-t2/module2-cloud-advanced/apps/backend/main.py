import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from google.cloud import storage, pubsub_v1
import psycopg2

app = FastAPI()

# Config from environment variables
DB_HOST = os.environ["DB_HOST"]
DB_NAME = os.environ.get("DB_NAME", "argevorgyan_appdb")
DB_USER = os.environ["DB_USER"]
DB_PASS = os.environ["DB_PASS"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
PUBSUB_TOPIC = os.environ["PUBSUB_TOPIC"]
GCP_PROJECT = os.environ["GCP_PROJECT"]


def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        sslmode="require"
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Upload to GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    filename = f"{uuid.uuid4()}_{file.filename}"
    blob = bucket.blob(f"uploads/{filename}")
    contents = await file.read()
    blob.upload_from_string(contents, content_type=file.content_type)
    gcs_path = f"gs://{BUCKET_NAME}/uploads/{filename}"

    # 2. Insert row into Cloud SQL
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO uploads (filename, gcs_path) VALUES (%s, %s)",
        (file.filename, gcs_path)
    )
    conn.commit()
    cur.close()
    conn.close()

    # 3. Publish message to Pub/Sub
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(GCP_PROJECT, PUBSUB_TOPIC)
    publisher.publish(topic_path, data=gcs_path.encode("utf-8"))

    return {"message": "Upload successful", "gcs_path": gcs_path}


@app.get("/uploads")
def list_uploads():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, gcs_path, created_at FROM uploads ORDER BY created_at DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "filename": r[1], "gcs_path": r[2], "created_at": str(r[3])} for r in rows]
