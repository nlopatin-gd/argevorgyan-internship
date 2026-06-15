import base64
import datetime
import json
import os

from google.cloud import storage


def process_message(event, context):
    """
    Cloud Function triggered by Pub/Sub.
    Decodes the message and writes it as a new file in GCS.
    """
    bucket_name = os.environ["BUCKET_NAME"]

    # Decode Pub/Sub message
    raw = event.get("data", "")
    message_data = base64.b64decode(raw).decode("utf-8") if raw else ""

    # Try to pretty-print if JSON, otherwise store as-is
    try:
        payload = json.loads(message_data)
        content = json.dumps(payload, indent=2)
    except (json.JSONDecodeError, ValueError):
        content = message_data

    # Use message timestamp + Pub/Sub message ID as filename
    message_id = context.event_id
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"messages/{timestamp}_{message_id}.txt"

    # Write to GCS
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(content, content_type="text/plain")

    print(f"Message {message_id} written to gs://{bucket_name}/{filename}")
