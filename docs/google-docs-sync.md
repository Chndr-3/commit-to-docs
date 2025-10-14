# Google Docs Synchronisation

The commit history is generated as `docs/commit-history.md`, a plain-language
update log that summarises recent changes for non-technical readers. To mirror
the same content into a Google Docs document:

1. Create or reuse a Google Cloud project and enable the **Google Docs API**.
2. Create a **service account** and download its JSON key file.
3. Share the target Google Doc with the service account email address so it can edit the document.
4. Store the following repository secrets so the GitHub Action can authenticate:
   - `GOOGLE_DOC_ID` – the document ID from the Google Doc URL (`https://docs.google.com/document/d/<doc-id>/edit`).
   - `GOOGLE_SERVICE_ACCOUNT_JSON` – either the raw JSON key or a base64-encoded version of the JSON key file.
5. Commit and push to the `main` branch (or wait for the nightly schedule). The workflow will regenerate the markdown and then push the content into the Google Doc.

### Local Testing

Before running the automation in CI you can test locally:

```bash
pip install google-api-python-client google-auth-httplib2
export GOOGLE_DOC_ID="<doc-id>"
export GOOGLE_SERVICE_ACCOUNT_JSON="$(base64 -i path/to/service-account.json)"
python3 scripts/generate_commit_history.py
python3 scripts/push_to_google_docs.py
```

If everything is configured correctly the script will overwrite the Google Doc
with the generated commit history.
