# deploy_kb_and_tools.py — Deployment Engineering (REST API bypass)
#
# Obejście zepsutego narzędzia MCP `add_knowledge_base_to_agent`
# (bug serwera: `'AgentConfig' object has no attribute 'get'`).
#
# ZWERYFIKOWANE na żywym API ElevenLabs (2026-08-22):
#   - KB trzymane w:  conversation_config.agent.prompt.knowledge_base  (lista)
#   - RAG toggle:     conversation_config.agent.prompt.rag.enabled
#   - turn_eagerness: conversation_config.turn.turn_eagerness  ('patient')
#   - speed:          conversation_config.tts.speed  (0.85)
#   - narzędzia:      conversation_config.agent.prompt.tools / tool_ids
#
# Endpointy:
#   POST /v1/convai/knowledge-base       (multipart: file + name) -> {id}
#   GET  /v1/convai/knowledge-base       -> {"documents": [{id, name, type, ...}]}
#   PATCH /v1/convai/agents/{agent_id}   (JSON Merge Patch — uzupełnia, nie nadpisuje)
#
# Użycie:  python deploy_kb_and_tools.py
# Wymaga:  pip install requests  (albo zamień requests na httpx/urllib)

import os
import sys
import json
import requests

API_KEY = os.getenv("ELEVENLABS_API_KEY")
AGENT_ID = "agent_8401m0n03cggfgebhfh0cj96t7aj"
KB_DIR = "docs/baza_wiedzy_rag_bukowy_dwor_txt"
BASE = "https://api.elevenlabs.io/v1"

# usage_mode: 'prompt' = pełny kontekst (krytyczne: ceny/procedury), 'auto' = RAG
USAGE = {
    "01_informacje_ogolne_i_dojazd": "auto",
    "02_katalog_zabiegow_spa_i_zdrowie": "auto",
    "03_pokoje_i_cennik": "prompt",
    "04_restauracja_i_diety": "auto",
    "05_procedury_i_polityki": "prompt",
}

H = {"xi-api-key": API_KEY}


def list_kb():
    r = requests.get(f"{BASE}/convai/knowledge-base", headers=H, timeout=30)
    r.raise_for_status()
    return r.json().get("documents", [])


def create_kb_doc(file_path, name):
    with open(file_path, "rb") as f:
        r = requests.post(
            f"{BASE}/convai/knowledge-base",
            headers=H,
            files={"file": (os.path.basename(file_path), f, "text/plain")},
            data={"name": name},
            timeout=60,
        )
    r.raise_for_status()
    return r.json()["id"]


def attach_and_configure(agent_id, kb_entries):
    payload = {
        "conversation_config": {
            "agent": {"prompt": {
                "knowledge_base": kb_entries,
                "rag": {"enabled": True},
                "timezone": "Europe/Warsaw",
            }},
            "turn": {"turn_eagerness": "patient"},
            "tts": {"speed": 0.85},
        }
    }
    r = requests.patch(f"{BASE}/convai/agents/{agent_id}", headers=H, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def main():
    if not API_KEY:
        sys.exit("Ustaw ELEVENLABS_API_KEY (env) przed uruchomieniem.")

    # 1) upewnij się, że 5 dokumentów istnieje (twórz brakujące)
    existing = {d["name"]: d["id"] for d in list_kb()}
    files = sorted(f for f in os.listdir(KB_DIR) if f.endswith(".txt"))
    doc_ids = {}
    for fname in files:
        stem = fname[:-4]  # bez .txt
        name = "Bukowy_Dwor_" + stem.replace("informacje_ogolne_i_dojazd", "01_dojazd") \
            .replace("katalog_zabiegow_spa_i_zdrowie", "02_zabiegi") \
            .replace("pokoje_i_cennik", "03_pokoje") \
            .replace("restauracja_i_diety", "04_diety") \
            .replace("procedury_i_polityki", "05_procedury")
        if name in existing:
            doc_ids[name] = existing[name]
            print(f"  (istnieje) {name} -> {existing[name]}")
        else:
            doc_ids[name] = create_kb_doc(os.path.join(KB_DIR, fname), name)
            print(f"  (utworzono) {name} -> {doc_ids[name]}")

    # 2) zbuduj knowledge_base z poprawnym usage_mode
    kb_entries = []
    for name, did in doc_ids.items():
        suffix = name.split("Bukowy_Dwor_")[1]  # 01_dojazd, 02_zabiegi, ...
        usage = USAGE.get(suffix, "auto")
        kb_entries.append({"type": "file", "id": did, "name": name, "usage_mode": usage})

    # 3) PATCH agenta
    attach_and_configure(AGENT_ID, kb_entries)
    print(f"\n✅ Agent {AGENT_ID}: {len(kb_entries)} dokumentów KB + RAG + turn_eagerness=patient + speed=0.85")


if __name__ == "__main__":
    main()
