# RAG question set (offline ground truth)

> **This does not measure retrieval quality yet.** What exists: 48 Polish guest questions, each paired with the KB file and an exact snippet that must appear in that file. An offline check proves the pairs are consistent with the KB. Nothing here asks the agent a question, and nothing here measures whether the agent or the retriever finds the right passage.

## Files

| File | Purpose |
|---|---|
| `questions.json` | 48 questions: `id`, `topic`, `question`, `expected_doc` (a file in `agent/knowledge_base_txt/`), `expected_snippet` (exact, single-line substring of that file) |
| `check_rag_questions.py` | Stdlib-only checker. Default mode verifies the set offline. `--live` is a stub. |
| `../../mock_backend/tests/test_rag_questions.py` | Runs the offline check under pytest (part of the offline test run). |

## What the offline check verifies

| Check | Result on current set |
|---|---|
| At least 40 questions | 48 |
| Unique ids and unique question texts | pass |
| `expected_doc` exists in `agent/knowledge_base_txt/` | pass (5 files) |
| `expected_snippet` is a single line and an exact substring of the file | pass (48 of 48) |
| Snippet occurs exactly once in its file | pass (warnings are printed for ambiguous snippets) |

Run:

```bash
python evals/rag/check_rag_questions.py          # exit 0 when all checks pass
python evals/rag/check_rag_questions.py --live   # prints: not implemented: requires ElevenLabs agent simulation (exit 3)
```

## Deliberate exclusions

- **Conflicting KB lines are not used as expected answers.** Two lines in the current KB disagree with each other (the room-service price in `04_restauracja_i_diety.txt`, and the diet count "dokładnie trzy" next to four named diets). A question that rewarded either version would certify a contradiction, so neither is in the set. Fixing the KB is a separate task for the content owner.
- **No out-of-scope questions.** Questions the KB cannot answer (for example implant prices) belong to a hand-off test, not a retrieval test. They are covered by the dental vertical scenarios (`agent/verticals/dental_clinic/scenarios.json`), not here.

## What a real hit-rate run would need

A retrieval or answer hit-rate needs a runnable path that this repository does not have yet:

1. **A simulation runner that asks each question** to the live agent (ElevenLabs conversation simulation, `simulate_conversation`), or to a local retrieval function if the KB is searched outside the platform.
2. **A decision rule for a hit.** For example: the agent's reply contains `expected_snippet` (or its key facts), or the retrieved chunk contains it. The snippet is a fact check, not a paraphrase check, so a paraphrase needs a rubric or a judge model.
3. **Retrieval logs** (which chunk was used). The platform's RAG call details are not exposed in this repo, so this step is open.
4. **A budget.** Each live question costs simulation credits; 48 questions times a few repetitions is a non-trivial spend. Get approval before running.
5. **A results file** committed next to this README, with the date, the agent configuration version and the pass rate, plus the list of failing ids.

Until those exist, the honest claim is: the question set is consistent with the KB, and the live check is not implemented.

## Notes

- The KB files are the `.txt` deployment copies. Two of them start with a byte-order mark; the checker reads them with `utf-8-sig` so the mark is not part of any snippet.
- Snippets are matched exactly, including punctuation and the `**` markdown bold markers used in the KB.
