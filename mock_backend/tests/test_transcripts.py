"""Testy zapisu transkryptów K2 (`tunnel/transcripts.py`) — offline, w katalogu tymczasowym.

Pilnują: domyślnego katalogu `evals/transcripts/` i nadpisania `ANNA_TRANSCRIPTS_DIR`, maskowania
telefonów i pełnych imion gości (także w argumentach narzędzi) oraz tego, że ocena asercji
nadal działa na nieredagowanym tekście.
"""

from __future__ import annotations

import json
from pathlib import Path

from tunnel import transcripts as tr

PHONE = "+48 600 100 200"
GUEST = "Piotr Zieliński"


def test_default_dir_is_evals_transcripts(monkeypatch):
    monkeypatch.delenv(tr.TRANSCRIPTS_ENV, raising=False)
    assert tr.transcripts_dir() == tr.PROJECT_ROOT / "evals" / "transcripts"
    assert tr.transcripts_dir().parts[-2:] == ("evals", "transcripts")


def test_env_override_wins(monkeypatch, tmp_path):
    monkeypatch.setenv(tr.TRANSCRIPTS_ENV, str(tmp_path / "out"))
    assert tr.transcripts_dir() == (tmp_path / "out").resolve()


def test_mask_phone_keeps_only_last_three_digits():
    assert tr.mask_phone(PHONE) == "+48 *** *** 200"
    assert tr.mask_phone("600100200") == "*** *** 200"
    assert tr.mask_phone("600-100-299") == "*** *** 299"


def test_mask_name_keeps_initials():
    assert tr.mask_name(GUEST) == "P*** Z***"
    assert tr.mask_name("Jan") == "J***"


def test_redact_text_masks_phone_and_name_but_not_booking_ids_or_dates():
    text = f"Dzwoni {GUEST}, tel. {PHONE}. Rezerwacja SPA-0001 na 2026-11-14 o 11:00."
    out = tr.redact_text(text, [GUEST])
    assert PHONE not in out and "600 100" not in out
    assert GUEST not in out and "P*** Z***" in out
    assert "SPA-0001" in out and "2026-11-14" in out and "11:00" in out


def test_name_match_is_case_insensitive():
    assert "P*** Z***" in tr.redact_text("pan piotr zieliński", [GUEST])


def test_redact_run_masks_tool_arguments_given_as_json_string():
    run = {
        "test_name": "K2-01-rezerwacja",
        "agent_responses": [{
            "role": "agent",
            "message": "Zapisałem.",
            "tool_calls": [{
                "tool_name": "book_spa_appointment",
                "params_as_json": json.dumps({"guest_name": GUEST, "service_name": "masaż"}, ensure_ascii=False),
            }, {
                "tool_name": "send_sms_summary",
                "params": {"phone_number": PHONE, "summary_text": f"Dla {GUEST}"},
            }],
        }],
    }
    out = tr.redact_run(run, [GUEST])
    raw = json.dumps(out, ensure_ascii=False)
    assert GUEST not in raw and PHONE not in raw
    args = json.loads(out["agent_responses"][0]["tool_calls"][0]["params_as_json"])
    assert args["guest_name"] == "P*** Z***" and args["service_name"] == "masaż"
    sms = out["agent_responses"][0]["tool_calls"][1]["params"]
    assert sms["phone_number"] == "+48 *** *** 200"
    assert out["test_name"] == "K2-01-rezerwacja"  # klucz "name"-podobny poza argumentami nietknięty


def test_redact_run_does_not_mutate_the_original():
    run = {"agent_responses": [{"role": "agent", "message": PHONE}]}
    tr.redact_run(run, [])
    assert run["agent_responses"][0]["message"] == PHONE


def _payloads():
    return [
        {"slug": "02-anulowanie-ponad-2h", "names": [GUEST],
         "body": {"name": "K2-02-anulowanie-ponad-2h"},
         "expect": {"tools": ["cancel_spa_appointment"], "forbid_tools": [],
                    "text": [r"(?<!\d)0 ?%"], "forbid": [r"50 ?%"]}},
        {"slug": "16-anulowanie-zle-nazwisko", "names": [],
         "body": {"name": "K2-16-anulowanie-zle-nazwisko"},
         "expect": {"tools": [], "forbid_tools": ["cancel_spa_appointment"],
                    "text": [], "forbid": [r"anulowa[łl]\w*"]}},
    ]


def _resp(status_ok: bool = True):
    return {
        "id": "inv-1",
        "test_runs": [
            {"test_name": "K2-02-anulowanie-ponad-2h", "status": "passed",
             "success_conditions": [{"result": True}],
             "agent_responses": [
                 {"role": "agent", "message": f"Pan {GUEST}, tel. {PHONE}. Opłata 0%.",
                  "tool_calls": [{"tool_name": "cancel_spa_appointment",
                                  "params_as_json": json.dumps({"guest_name": GUEST,
                                                                "confirmation_id": "SPA-0002"})}]}]},
            {"test_name": "K2-16-anulowanie-zle-nazwisko", "status": "passed",
             "agent_responses": [
                 {"role": "agent", "message": "Anulowałam rezerwację." if not status_ok else "Proszę o nazwisko."}]},
        ],
    }


def test_save_writes_redacted_files_and_summary(monkeypatch, tmp_path):
    monkeypatch.setenv(tr.TRANSCRIPTS_ENV, str(tmp_path))
    seeds = {"cancel_free": {"id": "SPA-0002", "date": "2026-11-15", "time": "10:00",
                             "service": "masaż", "guest": GUEST}}
    failures = tr.save(_resp(), _payloads(), seeds)

    files = sorted(p.name for p in tmp_path.iterdir())
    assert files == ["SUMMARY.md", "k2-02-anulowanie-ponad-2h.json", "k2-16-anulowanie-zle-nazwisko.json"]
    for path in tmp_path.iterdir():
        content = path.read_text(encoding="utf-8")
        assert PHONE not in content and "600 100" not in content, path.name
        assert GUEST not in content, path.name
    summary = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    assert "P*** Z***" in summary and "SPA-0002" in summary
    # 16: brak naruszeń w tym przebiegu (wzorzec nie trafia, brak zakazanego wywołania) -> failures == 0
    assert failures == 0


def test_save_counts_failures_on_assertion_violation(monkeypatch, tmp_path):
    monkeypatch.setenv(tr.TRANSCRIPTS_ENV, str(tmp_path))
    failures = tr.save(_resp(status_ok=False), _payloads(), {})
    assert failures == 1
    summary = (tmp_path / "SUMMARY.md").read_text(encoding="utf-8")
    assert "zakazane wywołanie narzędzia" in summary or "zakazana fraza" in summary


def test_save_checks_run_on_unredacted_text(monkeypatch, tmp_path):
    monkeypatch.setenv(tr.TRANSCRIPTS_ENV, str(tmp_path))
    payloads = [{"slug": "x", "names": [GUEST], "body": {"name": "K2-x"},
                 "expect": {"tools": [], "forbid_tools": [], "text": [GUEST], "forbid": []}}]
    resp = {"test_runs": [{"test_name": "K2-x", "status": "passed",
                           "agent_responses": [{"role": "agent", "message": f"Witam, {GUEST}."}]}]}
    assert tr.save(resp, payloads, {}) == 0


def test_save_respects_missing_directory_and_relative_display(monkeypatch, tmp_path):
    target = tmp_path / "nested" / "dir"
    monkeypatch.setenv(tr.TRANSCRIPTS_ENV, str(target))
    assert tr.save({"test_runs": []}, [], {}) == 0
    assert (target / "SUMMARY.md").exists()
    assert isinstance(tr._display(Path(target) / "k2.json"), str)
