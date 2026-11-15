# Baza wiedzy RAG — Uzdrowisko Termalne "Bukowy Dwór"

- `docs/baza_wiedzy_rag_bukowy_dwor/*.md` — **źródło** (human-readable, kanon faktów). Edytuj wyłącznie te pliki.
- `docs/baza_wiedzy_rag_bukowy_dwor_txt/*.txt` — **artefakt wdrożeniowy** wgrywany do ElevenLabs przez `deploy_kb_and_tools.py`.
- Każdy `.txt` jest kopią 1:1 swojego `.md`: ta sama treść, nagłówki `#`, pola `- **Pole:**`, końce linii CRLF, BOM zachowany.
- Kolejność pracy: zmiana w `.md` → kopia na `.txt` → `python deploy_kb_and_tools.py`. Nie edytuj `.txt` ręcznie.
- Deploy wgrywa 5 par `01`–`05`; skrypt bierze każdy `*.txt` z katalogu, dlatego ten README ma rozszerzenie `.md` i nie trafia do bazy wiedzy.
- Kontrola zgodności, jedna komenda z katalogu repo: `for f in docs/baza_wiedzy_rag_bukowy_dwor/*.md; do sha256sum "$f" "docs/baza_wiedzy_rag_bukowy_dwor_txt/$(basename "$f" .md).txt"; done` — hashe w każdej parze muszą być identyczne (BOM jest zachowany w obu plikach, więc nie trzeba go zdejmować).
