#!/usr/bin/env python3
"""Call the deployed function and print the result, then show what ended up in Firestore.

    python invoke.py                      # default org
    python invoke.py --org hashicorp      # another org
    python invoke.py --org this-org-does-not-exist-xyz   # error path: should return 502 and log an ERROR
"""

import argparse
import json

import requests
from google.cloud import firestore

import common as c


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--org", help="GitHub organisation to fetch (default: the function's GITHUB_ORG)")
    parser.add_argument("--max-pages", type=int, default=1)
    args = parser.parse_args()

    url = c.function_url()
    body = {"max_pages": args.max_pages}
    if args.org:
        body["org"] = args.org
    print(f"POST {url}\n{json.dumps(body)}\n")
    resp = requests.post(url, json=body, headers={"Authorization": f"Bearer {c.identity_token()}"}, timeout=150)
    print(f"HTTP {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))

    db = firestore.Client(project=c.PROJECT_ID, database=c.DATABASE_ID)
    print(f"\nFirestore {c.DATABASE_ID}:")
    print(f"  {c.COLLECTION}: {sum(1 for _ in db.collection(c.COLLECTION).select([]).stream())} documents")
    print(f"  {c.RUNS_COLLECTION}: {sum(1 for _ in db.collection(c.RUNS_COLLECTION).select([]).stream())} run records")
    print("\nTop 5 by stars:")
    for doc in db.collection(c.COLLECTION).order_by("stars", direction=firestore.Query.DESCENDING).limit(5).stream():
        d = doc.to_dict()
        print(f"  {d['stars']:>7}  {d['full_name']}  ({d['language']}, {d['popularity']})")


if __name__ == "__main__":
    main()
