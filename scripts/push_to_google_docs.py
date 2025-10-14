#!/usr/bin/env python3
"""
Push the generated commit-history markdown into a Google Docs document.

Usage:
    GOOGLE_SERVICE_ACCOUNT_JSON="<base64 creds>" \
    GOOGLE_DOC_ID="<doc id>" \
    python3 scripts/push_to_google_docs.py

The service account needs access to the target doc (share the document with the
service account email address).
"""

from __future__ import annotations

import base64
import binascii
import json
import os
import sys
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = REPO_ROOT / "docs" / "commit-history.md"
SCOPES = ["https://www.googleapis.com/auth/documents"]


def load_credentials():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON environment variable is missing.")
    payload = raw
    try:
        decoded = base64.b64decode(raw, validate=True)
        payload = decoded.decode("utf-8")
    except (ValueError, binascii.Error, UnicodeDecodeError):
        # Treat the original value as JSON if base64 decoding fails.
        payload = raw
    try:
        info = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)


def get_document_id() -> str:
    doc_id = os.environ.get("GOOGLE_DOC_ID")
    if not doc_id:
        raise RuntimeError("GOOGLE_DOC_ID environment variable is missing.")
    return doc_id


def load_source_text() -> str:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"{SOURCE_FILE} does not exist. Generate it first.")
    content = SOURCE_FILE.read_text(encoding="utf-8")
    if not content.endswith("\n"):
        content += "\n"
    return content


def fetch_document_end_index(service, doc_id: str) -> int:
    doc = service.documents().get(documentId=doc_id).execute()
    end_index = 1
    for element in doc.get("body", {}).get("content", []):
        if "endIndex" in element:
            end_index = max(end_index, element["endIndex"])
    return end_index


def replace_document_body(service, doc_id: str, text: str) -> None:
    end_index = fetch_document_end_index(service, doc_id)
    requests = []
    if end_index > 1:
        requests.append(
            {
                "deleteContentRange": {
                    "range": {
                        "startIndex": 1,
                    }
                }
            }
        )
    requests.append(
        {
            "insertText": {
                "location": {"index": 1},
                "text": text,
            }
        }
    )
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def main() -> int:
    try:
        creds = load_credentials()
        doc_id = get_document_id()
        text = load_source_text()
        service = build("docs", "v1", credentials=creds)
        replace_document_body(service, doc_id, text)
        print(f"Updated Google Doc {doc_id} with commit history.")
        return 0
    except (RuntimeError, FileNotFoundError, HttpError) as exc:
        print(f"Failed to push commit history to Google Docs: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
