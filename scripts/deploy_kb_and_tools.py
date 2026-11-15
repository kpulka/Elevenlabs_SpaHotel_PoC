#!/usr/bin/env python3
"""Wdrożenie bazy wiedzy i ustawień agenta „Anna" do ElevenLabs (REST API).

Wdraża: 5 dokumentów bazy wiedzy, RAG, strefę czasową, turn_eagerness i prędkość TTS.
NIE wdraża narzędzi (webhooków) ani promptu: narzędzia przepina
``mock_backend/tunnel/sync_agent_tools.py``, prompt wkleja się w panelu (patrz agent/config/README.md).

Obejście zepsutego narzędzia MCP `add_knowledge_base_to_agent`
(bug serwera: `'AgentConfig' object has no attribute 'get'`).

ZWERYFIKOWANE na żywym API ElevenLabs (2026-08-22):
  - KB trzymane w:  conversation_config.agent.prompt.knowledge_base (lista)
  - RAG toggle:     conversation_config.agent.prompt.rag.enabled
  - turn_eagerness: conversation_config.turn.turn_eagerness ('patient')
  - speed:          conversation_config.tts.speed (0.85)

Endpointy:
  GET    /v1/convai/knowledge-base        -> {"documents": [...], "has_more", "next_cursor"} (paginacja)
  POST   /v1/convai/knowledge-base        (multipart: file + name) -> {id}
  DELETE /v1/convai/knowledge-base/{id}
  PATCH  /v1/convai/agents/{agent_id}     (JSON Merge Patch: uzupełnia, nie nadpisuje)

Źródło treści: agent/knowledge_base_txt/NN_*.txt (ścieżka względem TEGO pliku).

Kolejność (bezpieczna przy błędzie w środku):
  1. GET listy dokumentów KB (wszystkie strony).
  2. Dla każdego dokumentu: KEEP, gdy manifest wskazuje istniejące id o tym samym sha256;
     w przeciwnym razie POST nowego dokumentu. Stare id trafiają do ``stale_ids`` w manifeście.
  3. PATCH agenta na nowe id. Dopiero po sukcesie PATCH-a stare dokumenty są kasowane.
  4. Manifest zapisywany po każdym kroku (także przy przerwaniu), więc kolejny start wie,
     co jeszcze trzeba posprzątać. Błąd PATCH-a = zero DELETE: agent nadal wskazuje stare dokumenty.

Logika odświeżania: listing nie zwraca hasha treści, więc skrypt trzyma lokalny manifest
(.kb_deploy_manifest.json w katalogu repo) z id, sha256 i ``stale_ids`` ostatnio wgranych dokumentów.

Zmienne środowiskowe:
  ELEVENLABS_API_KEY   (wymagana we wdrożeniu; w --dry-run niepotrzebna)
  ELEVENLABS_AGENT_ID  (wymagana we wdrożeniu; brak = błąd, bez domyślnego agenta; w --dry-run opcjonalna)

Użycie:
  python scripts/deploy_kb_and_tools.py --dry-run   # plan lokalny, ZERO połączeń sieciowych
  python scripts/deploy_kb_and_tools.py             # wdrożenie (zapisy do API)

Wymaga (tylko wdrożenie): pip install requests
Import: moduł nie wykonuje niczego przy imporcie (main() za strażnikiem __main__).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "agent" / "knowledge_base_txt"
MANIFEST_PATH = ROOT / ".kb_deploy_manifest.json"
BASE = "https://api.elevenlabs.io/v1"
AGENT_ID_PATTERN = re.compile(r"^agent_[A-Za-z0-9]+$")

# usage_mode: 'prompt' = pełny kontekst (krytyczne: ceny/procedury), 'auto' = RAG.
# Klucze to nazwy plików (stem) w KB_DIR.
USAGE: Dict[str, str] = {
    "01_informacje_ogolne_i_dojazd": "auto",
    "02_katalog_zabiegow_spa_i_zdrowie": "auto",
    "03_pokoje_i_cennik": "prompt",
    "04_restauracja_i_diety": "auto",
    "05_procedury_i_polityki": "prompt",
}

# stem pliku -> sufiks nazwy dokumentu w ElevenLabs (Bukowy_Dwor_<sufiks>)
STEM_TO_SUFFIX: Dict[str, str] = {
    "01_informacje_ogolne_i_dojazd": "01_dojazd",
    "02_katalog_zabiegow_spa_i_zdrowie": "02_zabiegi",
    "03_pokoje_i_cennik": "03_pokoje",
    "04_restauracja_i_diety": "04_diety",
    "05_procedury_i_polityki": "05_procedury",
}

TURN_EAGERNESS = "patient"
TTS_SPEED = 0.85
TIMEZONE = "Europe/Warsaw"

Manifest = Dict[str, Dict[str, Any]]


@dataclass(frozen=True)
class LocalDoc:
    name: str
    stem: str
    path: Path
    sha256: str


@dataclass
class DeployResult:
    """Wynik wdrożenia: id dokumentów w kolejności KB i listę nieusuniętych starych id."""

    doc_ids: List[str] = field(default_factory=list)
    leftover_ids: List[str] = field(default_factory=list)


class DeployError(RuntimeError):
    """Błąd, po którym nie wolno kontynuować (np. odrzucony PATCH)."""


def validate_agent_id(agent_id: str) -> str:
    """Akceptuje tylko postać ``agent_<alfanumeryczne>`` (nic, co mogłoby zmienić ścieżkę URL)."""
    if not AGENT_ID_PATTERN.match(agent_id):
        raise SystemExit("ELEVENLABS_AGENT_ID ma niepoprawny format (oczekiwano agent_<znaki alfanumeryczne>).")
    return agent_id


def resolve_agent_id(required: bool) -> Optional[str]:
    """ID agenta z ELEVENLABS_AGENT_ID. Brak zmiennej przy ``required`` to błąd (bez domyślnego agenta)."""
    raw = (os.getenv("ELEVENLABS_AGENT_ID") or "").strip()
    if not raw:
        if required:
            raise SystemExit(
                "Ustaw ELEVENLABS_AGENT_ID (env) z ID agenta Anny, np. agent_xxxx. "
                "Skrypt nie ma domyślnego agenta i nie wdroży bez jawnego ID. (Albo użyj --dry-run.)"
            )
        return None
    return validate_agent_id(raw)


def local_documents(kb_dir: Path = KB_DIR) -> List[LocalDoc]:
    """Dokumenty KB z plików *.txt, z nazwą i sha256 treści (bajty pliku)."""
    docs: List[LocalDoc] = []
    for path in sorted(kb_dir.glob("*.txt")):
        suffix = STEM_TO_SUFFIX.get(path.stem)
        if suffix is None:
            print(f"  (pominięto, brak mapowania w STEM_TO_SUFFIX) {path.name}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        docs.append(LocalDoc(name=f"Bukowy_Dwor_{suffix}", stem=path.stem, path=path, sha256=digest))
    return docs


def load_manifest(path: Path = MANIFEST_PATH) -> Manifest:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(f"(uwaga) nieczytelny manifest {path.name} - traktuję jak brak wpisów")
        return {}
    return data if isinstance(data, dict) else {}


def save_manifest(manifest: Manifest, path: Path = MANIFEST_PATH) -> None:
    """Zapis atomowy (plik tymczasowy + replace), żeby przerwanie nie zostawiło ucięte JSON-a."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def build_kb_entries(docs: List[LocalDoc], doc_ids: List[str]) -> List[Dict[str, Any]]:
    """Wpisy `knowledge_base` dla PATCH agenta (doc_ids zgodne kolejnością z docs), usage_mode wg USAGE."""
    if len(docs) != len(doc_ids):
        raise ValueError("build_kb_entries: liczba dokumentów i id się nie zgadza")
    return [
        {"type": "file", "id": doc_id, "name": doc.name, "usage_mode": USAGE.get(doc.stem, "auto")}
        for doc, doc_id in zip(docs, doc_ids)
    ]


def agent_payload(kb_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "conversation_config": {
            "agent": {"prompt": {
                "knowledge_base": kb_entries,
                "rag": {"enabled": True},
                "timezone": TIMEZONE,
            }},
            "turn": {"turn_eagerness": TURN_EAGERNESS},
            "tts": {"speed": TTS_SPEED},
        }
    }


def plan_local(docs: List[LocalDoc], manifest: Manifest) -> None:
    """Wypisuje plan bez odpytywania API (dry-run)."""
    print(f"KB dir: {KB_DIR}")
    print("Dry-run: brak połączeń sieciowych. Stan zdalny nie jest sprawdzany.\n")
    for doc in docs:
        entry = manifest.get(doc.name)
        if entry and entry.get("sha256") == doc.sha256:
            status = "bez zmian wg manifestu -> KEEP, jeśli zdalny dokument ma to samo id"
        elif entry:
            status = "treść zmieniona wzgl. manifestu -> nowy dokument (POST), stare po PATCH-u (DELETE)"
        else:
            status = "brak wpisu w manifeście -> POST nowego (stare o tej nazwie, jeśli są, po PATCH-u)"
        print(f"  {doc.name}  [{doc.path.name}]  sha256={doc.sha256[:12]}  usage={USAGE.get(doc.stem, 'auto')}")
        print(f"      plan: {status}")
    print(f"\nPATCH /convai/agents/<agent_id> z turn_eagerness={TURN_EAGERNESS}, speed={TTS_SPEED}, "
          f"rag=enabled, timezone={TIMEZONE}, {len(docs)} dokumentów KB.")
    print("Uruchom bez --dry-run (z ELEVENLABS_API_KEY i ELEVENLABS_AGENT_ID), aby wykonać.")


def make_session(api_key: str):
    import requests  # import leniwy: dry-run nie wymaga requests

    session = requests.Session()
    session.headers["xi-api-key"] = api_key
    return session


def list_remote_documents(session) -> List[Dict[str, Any]]:
    """Wszystkie dokumenty KB, z obsługą paginacji (cursor)."""
    documents: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        params: Dict[str, Any] = {"page_size": 100}
        if cursor:
            params["cursor"] = cursor
        r = session.get(f"{BASE}/convai/knowledge-base", params=params, timeout=30)
        r.raise_for_status()
        body = r.json()
        documents.extend(body.get("documents", []))
        cursor = body.get("next_cursor")
        if not body.get("has_more") or not cursor:
            break
    return documents


def create_kb_doc(session, file_path: Path, name: str) -> str:
    with open(file_path, "rb") as f:
        r = session.post(
            f"{BASE}/convai/knowledge-base",
            files={"file": (file_path.name, f, "text/plain")},
            data={"name": name},
            timeout=60,
        )
    r.raise_for_status()
    return r.json()["id"]


def delete_kb_doc(session, doc_id: str) -> None:
    r = session.delete(f"{BASE}/convai/knowledge-base/{doc_id}", timeout=30)
    r.raise_for_status()


def attach_and_configure(session, agent_id: str, kb_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    r = session.patch(f"{BASE}/convai/agents/{agent_id}", json=agent_payload(kb_entries), timeout=60)
    r.raise_for_status()
    return r.json()


def _remote_ids_by_name(remote: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    by_name: Dict[str, List[str]] = {}
    for doc in remote:
        name, doc_id = doc.get("name"), doc.get("id")
        if name and doc_id:
            by_name.setdefault(name, []).append(doc_id)
    return by_name


def deploy(
    agent_id: str,
    docs: List[LocalDoc],
    manifest: Manifest,
    session,
    manifest_path: Path = MANIFEST_PATH,
) -> DeployResult:
    """Wdraża KB: POST nowych dokumentów -> PATCH agenta -> DELETE starych. Patrz docstring modułu.

    Rzuca ``DeployError``, gdy PATCH się nie udał; wtedy nic nie zostało usunięte, a manifest
    zawiera ``stale_ids`` do posprzątania przy kolejnym uruchomieniu.
    """
    remote_ids = _remote_ids_by_name(list_remote_documents(session))
    manifest = {name: dict(entry) for name, entry in manifest.items()}  # nie mutujemy wejścia

    doc_ids: List[str] = []
    for doc in docs:
        existing = remote_ids.get(doc.name, [])
        entry = manifest.get(doc.name) or {}
        if entry.get("id") in existing and entry.get("sha256") == doc.sha256:
            doc_id = str(entry["id"])
            print(f"  (bez zmian) {doc.name} -> {doc_id}")
        else:
            doc_id = create_kb_doc(session, doc.path, doc.name)
            action = "odświeżono (nowy dokument)" if existing else "utworzono"
            print(f"  ({action}) {doc.name} -> {doc_id}")
        stale = [i for i in existing if i != doc_id]
        manifest[doc.name] = {"id": doc_id, "sha256": doc.sha256, "stale_ids": stale}
        save_manifest(manifest, manifest_path)  # po każdym dokumencie: przerwanie nie gubi id
        doc_ids.append(doc_id)

    kb_entries = build_kb_entries(docs, doc_ids)
    try:
        attach_and_configure(session, agent_id, kb_entries)
    except Exception as err:  # noqa: BLE001 - każdy błąd PATCH-a oznacza: nic nie kasujemy
        raise DeployError(f"PATCH agenta nie powiódł się, stare dokumenty zostają: {err}") from err

    leftovers: List[str] = []
    for doc in docs:
        for old_id in manifest[doc.name].get("stale_ids", []):
            try:
                delete_kb_doc(session, old_id)
                print(f"  (usunięto stary dokument) {doc.name} -> {old_id}")
            except Exception as err:  # noqa: BLE001 - zostaje w manifeście do ponowienia
                print(f"  (uwaga) nie usunięto {old_id} ({doc.name}): {err}")
                leftovers.append(old_id)
                continue
            manifest[doc.name]["stale_ids"] = [i for i in manifest[doc.name]["stale_ids"] if i != old_id]
            save_manifest(manifest, manifest_path)
    return DeployResult(doc_ids=doc_ids, leftover_ids=leftovers)


def main(argv: Optional[List[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="wypisz planowane działania bez żadnych połączeń sieciowych")
    args = parser.parse_args(argv)

    docs = local_documents()
    if not docs:
        sys.exit(f"Brak dokumentów *.txt z mapowaniem w {KB_DIR}")
    manifest = load_manifest()

    if args.dry_run:
        agent_id = resolve_agent_id(required=False)
        print(f"ELEVENLABS_AGENT_ID: {'ustawione' if agent_id else 'NIE ustawione (w wdrożeniu wymagane)'}")
        plan_local(docs, manifest)
        return 0

    agent_id = resolve_agent_id(required=True)
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("Ustaw ELEVENLABS_API_KEY (env) przed uruchomieniem (albo użyj --dry-run).")

    session = make_session(api_key)
    try:
        result = deploy(agent_id, docs, manifest, session)
    except DeployError as err:
        print(f"BŁĄD: {err}")
        return 1
    print(f"\nAgent {agent_id}: {len(result.doc_ids)} dokumentów KB + RAG + "
          f"turn_eagerness={TURN_EAGERNESS} + speed={TTS_SPEED}")
    if result.leftover_ids:
        print(f"Nie usunięto {len(result.leftover_ids)} starych dokumentów; ponów uruchomienie, "
              "żeby je posprzątać (są w manifeście).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
