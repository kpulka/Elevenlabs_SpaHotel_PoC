# Contributing

This is a portfolio case study, so changes are welcome mainly as fixes, tests or documentation corrections.

## Setup and checks

Python is pinned to **3.12** (CI and the backend image both use it). Node is 22, pnpm is 10.

1. **Backend:** `cd mock_backend && pip install -r requirements.txt -r requirements-dev.txt`, then
   `python -m pytest -q`. The CI job also enforces a coverage threshold; see `.github/workflows/ci.yml`.
   Lint and types as in CI: `ruff check mock_backend` (from the repo root) and `python -m mypy .` (from `mock_backend/`).
2. **Frontend:** `cd frontend && pnpm install`, then `pnpm typecheck && pnpm lint && pnpm test && pnpm i18n:check && pnpm data:check && pnpm build`.
   The Playwright end-to-end job runs when `frontend/playwright.config.ts` exists; run it locally with `pnpm test:e2e`.
3. **Repository gates:** `python presentation/verify_deck.py` (figures agree across the deck, the HTML decks, the spec
   files and the business case), `python docs/verify_index.py` (every doc is listed in `docs/INDEX.md`),
   `python scripts/check_kb_parity.py` (knowledge base source and uploaded copy match).
4. **Knowledge base:** edit `agent/knowledge_base/*.md` only, then copy 1:1 to `agent/knowledge_base_txt/*.txt`
   (see the README in that folder).
5. **Agent prompts and procedures** (`agent/`) describe what is deployed. A change there is not live until it is
   uploaded to ElevenLabs; say so in the pull request.

## Commits and pull requests

- Commit messages are in **English** and follow **Conventional Commits** (`feat:`, `fix:`, `docs:`, `test:`,
  `refactor:`, `ci:`, `chore:`). Describe what you verified in the body. Domain terms (entity names, prompt text)
  may stay in Polish.
- Keep commits focused: one topic per commit, each one passing the checks above.
- Open a pull request against `main` and fill in the template.
- Dependency updates arrive as Dependabot pull requests (pip, npm, GitHub Actions).
- Security issues go through [SECURITY.md](SECURITY.md), not a public issue.

## Secrets and generated state

- Never commit `.env*` files, API keys, webhook secrets, tunnel state, databases or backups. Run `git status`
  before committing. The gitleaks job in CI scans the full history.
- Do not paste real guest data into fixtures, transcripts or screenshots.
