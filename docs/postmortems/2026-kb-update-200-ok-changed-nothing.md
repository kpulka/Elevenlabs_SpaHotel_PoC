# Postmortem: a corrected knowledge-base file returned 200 and changed nothing

| Field | Value |
|---|---|
| Status | reviewed (retrospective, written from the repository record) |
| Severity | SEV2: the agent gave outdated business information. No safety information was affected. |
| Environment | PoC (ElevenLabs agent, widget channel) |
| Detected | while checking a KB correction in a test conversation |
| Duration | unknown: the source does not record start or end times |
| Source | [`docs/lessons-learned.md`, lesson 7](../lessons-learned.md#7-a-200-ok-is-not-proof-that-anything-changed), [`scripts/deploy_kb_and_tools.py`](../../deploy_kb_and_tools.py) |

> **Faithfulness note.** The facts below come from `lessons-learned.md` (lesson 7) and from reading `scripts/deploy_kb_and_tools.py`. Where the two disagree, the table in section 6 says so. Timestamps and the exact number of affected conversations are not in the record and are marked `unknown`.

## 1. Summary

A corrected knowledge-base file was uploaded to the agent's knowledge base. The upload returned `200 OK`, but the agent kept answering from the old text. The status code was treated as proof that the change had landed. It was not. The platform's `PATCH` on the knowledge-base document accepted the multipart upload and ignored its content.

## 2. Impact

| Area | Impact |
|---|---|
| Callers | `unknown` (PoC; no record of live callers receiving the old text) |
| Business | the agent answered from outdated KB text for as long as the change was believed to be live. Which facts were outdated is not recorded in the source. |
| Safety | none recorded. The lesson concerns business content. |
| Data | none |

## 3. Timeline

| # | Time (UTC) | Event | Source |
|---|---|---|---|
| 1 | unknown | A corrected KB file was sent with `PATCH /v1/convai/knowledge-base/{id}`. The response was `200`. | lesson 7 |
| 2 | unknown | A test conversation was run. The agent answered with the text from before the correction. | lesson 7 |
| 3 | unknown | The cause was traced to the endpoint: it accepts the upload and ignores `content`. | lesson 7 |
| 4 | unknown | The KB procedure was changed to use create, re-point, delete and a read-back check (see section 6). | lesson 7 |

## 4. Root cause

- **Direct cause:** `PATCH /v1/convai/knowledge-base/{id}` accepts a multipart upload and does not apply its content. The agent kept the old document text.
- **Underlying cause:** the process treated the HTTP status as the outcome. There was no check that read the document back from the platform.
- **Contributing factors:**
  - The hosted prompt and the KB on the live agent can differ from the files in the repository. The audit in `docs/pl/audyt_agenta_2026-08.md` (section 7) notes a hosted prompt whose length differs from the file, so a change can be "deployed" to a copy the agent does not use.
  - The KB has no version field that a reviewer could compare against the repository.

## 5. Detection

- Detected by a person reading the agent's answer in a test conversation, not by a check.
- The misleading signal was the `200 OK` from the upload.
- Earlier detection would have come from reading the document back after the change and searching for a marker string that exists only in the new text.

## 6. Fix

**What the lesson records as the procedure now:**

1. Create a new KB document with the corrected content.
2. Re-point the agent's `knowledge_base` list to the new document, keeping each entry's `usage_mode`.
3. Delete the old document.
4. Verify by searching for a marker string in the document's `extracted_inner_html`.

**What the repository code does (`scripts/deploy_kb_and_tools.py`, function `deploy`):**

| Step | Lesson 7 says | Code does | Matches? |
|---|---|---|---|
| Create new document | step 1 | `create_kb_doc` runs after the old one is deleted (line 241 deletes, line 245 creates) | **no: order differs** |
| Re-point agent | step 2, keep `usage_mode` | `build_kb_entries` keeps `usage_mode`; `attach_and_configure` sends a PATCH to the agent | yes |
| Delete old | step 3 | `delete_kb_doc` runs before the create | **no: order differs** |
| Read-back verification | step 4, search `extracted_inner_html` | no such check in the code (`extracted_inner_html` appears only in the lesson text) | **no: not implemented** |

The delete-before-create order means a failure between the delete and the create leaves the agent pointing at a document that no longer exists. The script does not roll back. The agent's references are updated only in the final PATCH.

## 7. Prevention and follow-ups

| # | Action | Type | Owner (role) | Status |
|---|---|---|---|---|
| 1 | Add a read-back check after deploy: fetch each new document and assert a marker string from the local `.md` file is present in the platform copy | detect | engineering | open |
| 2 | Change the order to create, re-point, then delete the old document, so a failure leaves the old reference working | prevent | engineering | open |
| 3 | Make the lesson text and the code agree (either fix the code per 1 and 2, or correct lesson 7) | prevent | engineering | open |
| 4 | Compare the live prompt and KB with the repository before each release (a `diff` command) | detect | engineering | design only |
| 5 | Keep the KB `.md` and `.txt` copies in parity with a check in CI | prevent | engineering | open (parity script exists in `scripts/`; not confirmed as a CI gate here) |

Nothing in this table is marked `done`. The lesson describes the procedure as if it existed in code. Until items 1 and 2 are merged, the procedure is a manual step.

## 8. What went well

- The symptom was caught by reading the agent's answer, not discovered later by a guest.
- The root cause was traced to the API behaviour, not to the model.
- The deployment is scripted, so the procedure can be changed in one place and reviewed.
