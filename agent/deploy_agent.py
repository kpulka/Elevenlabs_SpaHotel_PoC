#!/usr/bin/env python3
"""Deploy the knowledge base and agent configuration to ElevenLabs.

Workaround for the MCP tool `add_knowledge_base_to_agent`, which fails on the
server side with "'AgentConfig' object has no attribute 'get'". This script
calls the REST API directly instead.

Configuration paths verified against the live API (2026-08-22):
  - knowledge base:  conversation_config.agent.prompt.knowledge_base (list)
  - RAG toggle:      conversation_config.agent.prompt.rag.enabled
  - turn eagerness:  conversation_config.turn.turn_eagerness ("patient")
  - TTS speed:       conversation_config.tts.speed (0.85)

Endpoints used:
  POST  /v1/convai/knowledge-base      multipart (file, name) -> {id}
  GET   /v1/convai/knowledge-base      -> {"documents": [{id, name, ...}]}
  PATCH /v1/convai/agents/{agent_id}   JSON merge patch (updates, does not replace)

Usage:
  python agent/deploy_agent.py --dry-run     # show the plan, no API calls
  ELEVENLABS_API_KEY=... python agent/deploy_agent.py

Environment:
  ELEVENLABS_API_KEY   required unless --dry-run
  ELEVENLABS_AGENT_ID  optional, defaults to the Anna agent used in this PoC

Requires: requests
"""

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import requests

API_BASE = "https://api.elevenlabs.io/v1"
DEFAULT_AGENT_ID = "agent_8401m0n03cggfgebhfh0cj96t7aj"
TIMEOUT_SECONDS = 60

KB_DIR = Path(__file__).resolve().parent / "knowledge_base"

# Knowledge base file stem -> usage mode.
# 'prompt' = full text goes into the system prompt (used for prices and procedures),
# 'auto'   = retrieved on demand via RAG.
USAGE = {
    "01_general_info_and_directions": "auto",
    "02_spa_treatments_and_health": "auto",
    "03_rooms_and_pricing": "prompt",
    "04_restaurant_and_diets": "auto",
    "05_procedures_and_policies": "prompt",
}

# Knowledge base file stem -> document name in the ElevenLabs workspace.
# These names match the previous deployment, so re-running the script reuses
# existing documents instead of creating duplicates.
KB_NAMES = {
    "01_general_info_and_directions": "Bukowy_Dwor_01_dojazd",
    "02_spa_treatments_and_health": "Bukowy_Dwor_02_zabiegi",
    "03_rooms_and_pricing": "Bukowy_Dwor_03_pokoje",
    "04_restaurant_and_diets": "Bukowy_Dwor_04_diety",
    "05_procedures_and_policies": "Bukowy_Dwor_05_procedury",
}


@dataclass
class KBDocument:
    stem: str
    path: Path
    name: str
    usage: str
    content: bytes


def load_documents():
    """Read every knowledge base file; fail early if one is missing."""
    docs = []
    for stem, usage in USAGE.items():
        path = KB_DIR / f"{stem}.md"
        if not path.is_file():
            sys.exit(f"[error] Knowledge base file not found: {path}")
        docs.append(KBDocument(stem, path, KB_NAMES[stem], usage, path.read_bytes()))
    return docs


def auth_headers(api_key):
    return {"xi-api-key": api_key}


def list_kb_documents(api_key):
    r = requests.get(f"{API_BASE}/convai/knowledge-base", headers=auth_headers(api_key), timeout=30)
    r.raise_for_status()
    return r.json().get("documents", [])


def create_kb_document(api_key, doc):
    """Upload the Markdown content as a plain-text document and return its id."""
    r = requests.post(
        f"{API_BASE}/convai/knowledge-base",
        headers=auth_headers(api_key),
        files={"file": (f"{doc.stem}.txt", doc.content, "text/plain")},
        data={"name": doc.name},
        timeout=TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    return r.json()["id"]


def attach_and_configure(api_key, agent_id, kb_entries):
    payload = {
        "conversation_config": {
            "agent": {
                "prompt": {
                    "knowledge_base": kb_entries,
                    "rag": {"enabled": True},
                    "timezone": "Europe/Warsaw",
                }
            },
            "turn": {"turn_eagerness": "patient"},
            "tts": {"speed": 0.85},
        }
    }
    r = requests.patch(
        f"{API_BASE}/convai/agents/{agent_id}",
        headers=auth_headers(api_key),
        json=payload,
        timeout=TIMEOUT_SECONDS,
    )
    r.raise_for_status()
    return r.json()


def print_plan(agent_id, docs):
    print(f"[dry-run] Agent: {agent_id}")
    print(f"[dry-run] Knowledge base directory: {KB_DIR}")
    print("[dry-run] Documents to upload (existing documents with the same name are reused):")
    for doc in docs:
        print(
            f"  {doc.path.name} -> upload as {doc.stem}.txt (text/plain), "
            f"name={doc.name}, usage_mode={doc.usage}, {len(doc.content)} bytes"
        )
    print("[dry-run] Agent configuration: RAG enabled, turn_eagerness=patient, tts.speed=0.85, timezone=Europe/Warsaw")
    print("[dry-run] No API calls were made.")


def deploy(api_key, agent_id, docs):
    # 1) Make sure every document exists; create the missing ones.
    existing = {d["name"]: d["id"] for d in list_kb_documents(api_key)}
    doc_ids = {}
    for doc in docs:
        if doc.name in existing:
            doc_ids[doc.name] = existing[doc.name]
            print(f"  [exists]  {doc.name} -> {doc_ids[doc.name]}")
        else:
            doc_ids[doc.name] = create_kb_document(api_key, doc)
            print(f"  [created] {doc.name} -> {doc_ids[doc.name]}")

    # 2) Build the knowledge_base list with the configured usage modes.
    kb_entries = [
        {"type": "file", "id": doc_ids[doc.name], "name": doc.name, "usage_mode": doc.usage}
        for doc in docs
    ]

    # 3) Patch the agent.
    attach_and_configure(api_key, agent_id, kb_entries)
    print(
        f"\n[ok] Agent {agent_id}: {len(kb_entries)} KB documents, RAG on, "
        "turn_eagerness=patient, speed=0.85"
    )


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Upload the Bukowy Dwor knowledge base to ElevenLabs and configure the Anna agent."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be uploaded and configured, without calling the ElevenLabs API",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    agent_id = os.getenv("ELEVENLABS_AGENT_ID", DEFAULT_AGENT_ID)
    docs = load_documents()

    if args.dry_run:
        print_plan(agent_id, docs)
        return 0

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("[error] ELEVENLABS_API_KEY is not set. Export it before running, or use --dry-run.")

    deploy(api_key, agent_id, docs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
