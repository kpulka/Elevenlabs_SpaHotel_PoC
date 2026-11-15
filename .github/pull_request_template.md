## Summary

<!-- What changes and why, in two or three sentences. -->

## What I verified

- [ ] `cd mock_backend && python -m pytest -q`
- [ ] `ruff check mock_backend` and `python -m mypy .` (from `mock_backend/`), if backend code changed
- [ ] `pnpm typecheck && pnpm lint && pnpm test && pnpm build`, if frontend code changed
- [ ] `python docs/verify_index.py`, if documentation or paths changed
- [ ] `python presentation/verify_deck.py`, if figures or the deck changed

## Checklist

- [ ] No secrets, API keys, `.env*` files, tunnel state or backups in the diff
- [ ] If the knowledge base changed: `.md` and `.txt` copies are identical, and the upload was noted below
- [ ] If `agent/` prompts or procedures changed: the change is marked as not yet live, or the redeploy is described
- [ ] Documentation links and paths still resolve

## Notes for the reviewer

<!-- Anything that is not obvious from the diff, including what you did not test. -->
