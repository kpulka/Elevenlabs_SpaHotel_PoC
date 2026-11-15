"""Testy lintu „fakt w prompcie/procedurach musi być w bazie wiedzy" (scripts/lint_prompt_kb.py).

Offline: skrypt jest stdlib-only, a testy działają na syntetycznych tekstach albo na kopii
struktury repo w katalogu tymczasowym. Ostatni test uruchamia lint na prawdziwym repo.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location("lint_prompt_kb", REPO_ROOT / "scripts" / "lint_prompt_kb.py")
assert _SPEC is not None and _SPEC.loader is not None
lint = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = lint  # dataclasses potrzebuje modułu w sys.modules
_SPEC.loader.exec_module(lint)

KB_TEXT = (
    "# Katalog\n"
    "- **Kąpiel siarczkowa \"Ukojenie Stawów\":** 80 PLN.\n"
    "- **Masaż leczniczy pleców:** 120 PLN, 30 minut.\n"
    "- **Jonoforeza:** 70 PLN.\n"
    "- Recepcja czynna całą dobę. Zameldowanie od 15:00.\n"
    "- Restauracja \"Bukowy Smak\": śniadanie 7:30 - 10:00.\n"
    "- Gimnastyka lecznicza (grupowa).\n"
)


def _kb(*texts: str) -> "lint.KnowledgeBase":
    return lint.KnowledgeBase.from_texts(list(texts) or [KB_TEXT])


def _lint(text: str, allow=None):
    allow = allow or lint.Allowlist({}, {}, {})
    findings, checks = lint.lint_text("test.md", text, _kb(), allow)
    return findings, checks


def _kinds(findings):
    return [(f.kind, f.value) for f in findings]


# ── kwoty ────────────────────────────────────────────────────────────────
def test_amount_in_zl_is_grounded_by_pln_in_kb():
    findings, checks = _lint("Masaż kosztuje 120 zł.")
    assert findings == [] and checks >= 1


def test_ungrounded_amount_is_flagged():
    findings, _ = _lint("Późny wyjazd kosztuje 75 PLN.")
    assert _kinds(findings) == [("kwota", "75 PLN")]


def test_amount_with_decimal_comma_is_normalised():
    kb = _kb("Opłata 50,00 PLN.")
    findings, _ = lint.lint_text("t", "Zapłacisz 50 zł.", kb, lint.Allowlist({}, {}, {}))
    assert findings == []


# ── godziny ──────────────────────────────────────────────────────────────
def test_clock_present_in_kb_is_grounded():
    findings, _ = _lint("Zameldowanie od 15:00.")
    assert findings == []


def test_ungrounded_clock_is_flagged_and_allowlist_suppresses_it():
    findings, _ = _lint("Przyjdź o 14:00.")
    assert _kinds(findings) == [("godzina", "14:00")]
    allow = lint.Allowlist({}, {"14:00": "przykład"}, {})
    assert _lint("Przyjdź o 14:00.", allow)[0] == []


def test_iso_datetime_is_format_not_fact():
    findings, _ = _lint("Podaj appointment_datetime, np. 2026-11-09T18:30.")
    assert findings == []


def test_clock_without_leading_zero_matches_kb_form():
    findings, _ = _lint("Śniadanie od 07:30 do 10:00.")
    assert findings == []


# ── usługi (odmiana po pierwszych 5 literach) ───────────────────────────
def test_inflected_service_name_is_grounded():
    findings, _ = _lint("Chcesz kąpielą siarczkową się zająć?")
    assert findings == []


def test_unknown_service_phrase_is_flagged():
    findings, _ = _lint("Oferujemy bezpłatną przechowalnię bagażu.")
    assert any(f.kind == "usługa" and "przechowal" in f.value for f in findings)


def test_grota_and_herbata_are_flagged():
    findings, _ = _lint("Zaproponuj herbatę ziołową lub grotę solną.")
    values = [f.value for f in findings]
    assert any("herbat" in v for v in values) and any("grot" in v for v in values)


def test_dietitian_claim_is_flagged():
    findings, _ = _lint("Posiłki pod nadzorem dietetyka klinicznego.")
    assert any(f.kind == "usługa" and "dietetyk" in f.value for f in findings)


def test_adverb_after_service_does_not_create_a_false_positive():
    findings, _ = _lint("Jonoforezie zawsze wymaga konsultacji.")
    assert findings == []


def test_service_name_present_in_kb_with_second_word_is_grounded():
    findings, _ = _lint("Gimnastyka lecznicza odbywa się rano.")
    assert findings == []


# ── nazwy własne w cudzysłowie ───────────────────────────────────────────
def test_title_case_quoted_name_in_kb_is_grounded():
    findings, _ = _lint("Restauracja „Bukowy Smak” jest otwarta.")
    assert findings == []


def test_title_case_quoted_name_missing_from_kb_is_flagged():
    findings, _ = _lint("Zapraszamy do „Spokojny Sen” na wypoczynek.")
    assert _kinds(findings) == [("nazwa", "Spokojny Sen")]


def test_quoted_sentences_and_lowercase_phrases_are_not_names():
    text = ("Mów „wiadomość na telefon” zamiast „zabieg”, a na końcu „Dziękuję za kontakt, do usłyszenia”. "
            "Powiedz „Przepraszam, nie mam dostępu”.")
    findings, _ = _lint(text)
    assert [f for f in findings if f.kind == "nazwa"] == []


# ── pomocnicze ───────────────────────────────────────────────────────────
def test_fenced_only_keeps_line_numbers_and_drops_documentation():
    text = "# „Anna” w nagłówku\n```\nKoszt 50 zł\n```\nTekst dokumentacji 99 zł"
    masked = lint.fenced_only(text)
    lines = masked.split("\n")
    assert len(lines) == len(text.split("\n"))
    assert lines[0] == "" and lines[2] == "Koszt 50 zł" and lines[4] == ""


def test_allowlist_loads_and_normalises_keys(tmp_path):
    path = tmp_path / "allow.json"
    path.write_text('{"phrases": {"Pani": "forma"}, "hours": {"18:30": "przykład"}}', encoding="utf-8")
    allow = lint.Allowlist.load(path)
    assert "pani" in allow.phrases and "18:30" in allow.hours


def test_missing_allowlist_means_empty_allowlist(tmp_path):
    allow = lint.Allowlist.load(tmp_path / "nie-ma.json")
    assert allow.amounts == {} and allow.hours == {} and allow.phrases == {}


# ── całe przebiegi ───────────────────────────────────────────────────────
def _write_repo(root: Path, kb: str, prompt: str, procedures: str) -> None:
    (root / "agent" / "knowledge_base").mkdir(parents=True)
    (root / "agent" / "procedures").mkdir(parents=True)
    (root / "agent" / "knowledge_base" / "01_test.md").write_text(kb, encoding="utf-8")
    (root / "agent" / "system_prompt_v3.md").write_text(prompt, encoding="utf-8")
    (root / "agent" / "procedures" / "procedures_7.md").write_text(procedures, encoding="utf-8")


def test_synthetic_repo_with_ungrounded_fact_fails(tmp_path):
    _write_repo(
        tmp_path,
        kb=KB_TEXT,
        prompt="# nagłówek\n```\nZadzwoń o 15:00. Dopłata 500 zł.\n```\n",
        procedures="Wczesny przyjazd: grota solna gratis.\n",
    )
    findings, checks = lint.run(tmp_path, lint.Allowlist({}, {}, {}))
    kinds = {f.kind for f in findings}
    assert {"kwota", "usługa"} <= kinds
    assert checks > 0
    assert lint.main(["--root", str(tmp_path), "--allowlist", str(tmp_path / "none.json")]) == 1


def test_synthetic_repo_with_grounded_facts_passes(tmp_path, capsys):
    _write_repo(
        tmp_path,
        kb=KB_TEXT,
        prompt="```\nZameldowanie od 15:00, masaż leczniczy pleców za 120 zł.\n```\n",
        procedures="Kąpiel siarczkowa: 80 PLN, do 15:00.\n",
    )
    assert lint.main(["--root", str(tmp_path), "--allowlist", str(tmp_path / "none.json")]) == 0
    assert "OK:" in capsys.readouterr().out


def test_missing_kb_directory_is_reported_as_error(tmp_path, capsys):
    (tmp_path / "agent").mkdir()
    assert lint.main(["--root", str(tmp_path), "--allowlist", str(tmp_path / "none.json")]) == 1
    assert "BŁĄD" in capsys.readouterr().out


def test_real_repo_has_no_ungrounded_facts():
    allow = lint.Allowlist.load(lint.DEFAULT_ALLOWLIST)
    findings, checks = lint.run(REPO_ROOT, allow)
    assert findings == [], [f.render() for f in findings]
    assert checks > 20


@pytest.mark.parametrize("bad", ["Koszt 999 zł.", "Otwarte o 23:45."])
def test_obvious_violations_are_caught(bad):
    findings, _ = _lint(bad)
    assert findings, bad
