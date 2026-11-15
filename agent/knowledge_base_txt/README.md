# Baza wiedzy RAG — artefakty `.txt` (wgrywane do ElevenLabs)

- `agent/knowledge_base_txt/*.txt` — **artefakt wdrożeniowy** wgrywany do ElevenLabs przez `scripts/deploy_kb_and_tools.py` (katalog główny repo). Nie edytuj ręcznie.
- `agent/knowledge_base/*.md` — **źródło** (human-readable, kanon faktów). Edytuj wyłącznie te pliki, potem skopiuj 1:1 do `.txt`.
- Każdy `.txt` jest kopią 1:1 swojego `.md`: ta sama treść, nagłówki `#`, pola `- **Pole:**`, końce linii CRLF, BOM zachowany.
- Kolejność pracy: zmiana w `.md` → kopia na `.txt` → `python scripts/deploy_kb_and_tools.py`.
- Deploy wgrywa 5 par `01`–`05`; skrypt bierze każdy `*.txt` z katalogu, dlatego ten README ma rozszerzenie `.md` i nie trafia do bazy wiedzy.
- Kontrola zgodności, jedna komenda z katalogu repo: `for f in agent/knowledge_base/0*.md; do sha256sum "$f" "agent/knowledge_base_txt/$(basename "$f" .md).txt"; done` — hashe w każdej parze muszą być identyczne (BOM jest zachowany w obu plikach, więc nie trzeba go zdejmować).
