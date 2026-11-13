"""Scenariusze symulacji K2 jako dane + składanie payloadów z seedami (bez sieci).

Każdy scenariusz to zwykły słownik: ``slug``, ``seed`` (który seed rezerwacji wplatamy),
``prompt`` (rola gościa), ``success_criteria``, ``max_turns`` i ``expect`` (asercje na
transkrypt). Miejsca na dane seeda zapisane są jako ``{pole}``: ``id``, ``service``,
``date`` (ISO), ``date_pl`` (DD.MM.RRRR), ``time`` i ``datetime`` (``date`` + ``T`` + ``time``).

Daty są liczone w czasie uruchomienia (``dry_run_seeds``/``seed`` w ``run_simulations.py``),
nigdy nie są wpisane na sztywno: backend liczy opłatę z ``appointment_datetime`` względem „teraz”.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

TEST_PREFIX = "K2-"

SCENARIOS: List[Dict[str, Any]] = [
    {
        "slug": "01-rezerwacja-masaz-ambiguous",
        "seed": "book",
        "prompt": (
            "Jesteś gościem uzdrowiska Bukowy Dwór w Krynicy-Zdroju i dzwonisz, żeby zarezerwować "
            "masaż na {date_pl} na godzinę {time}. Na początku "
            "mówisz tylko, że chcesz zarezerwować 'masaż', i nie precyzujesz rodzaju, dopóki agent "
            "sam o to nie zapyta. Gdy agent wymieni kandydatów, wybierasz 'masaż leczniczy pleców'. "
            "Na pytanie o imię i nazwisko podajesz 'Piotr Zieliński'. Na pytanie o numer telefonu "
            "podajesz '+48 600 100 200'. Mówisz po polsku, krótko i naturalnie, jak osoba w średnim "
            "wieku. Nie znasz cen ani godzin — pytasz o nie agenta. Na końcu dziękujesz."
        ),
        "max_turns": 16,
        "success_criteria": [
            "Agent zapytał gościa, który masaż ma na myśli, zanim podał termin lub cenę.",
            "Agent podał cenę 120 zł i czas trwania 30 minut z odpowiedzi check_spa_availability.",
            "Agent zarezerwował zabieg przez book_spa_appointment i podał numer SPA-XXXX.",
            "Agent nie wymyślił ceny, godziny ani dostępności — wszystkie liczby z narzędzi.",
        ],
        "expect": {
            "tool": "book_spa_appointment",
            "text": ["120", "SPA-"],
            "forbid": ["129", "150 zł"],
        },
    },
    {
        "slug": "02-anulowanie-ponad-2h",
        "seed": "cancel_free",
        "prompt": (
            "Jesteś gościem uzdrowiska Bukowy Dwór. Dzwonisz, żeby odwołać rezerwację zabiegu o "
            "numerze {id} ({service}). Zabieg jest "
            "{date_pl} o godzinie "
            "{time}. Powód odwołania: zmiana planów wyjazdu, powód NIE jest medyczny. "
            "Mówisz po polsku, krótko. Numer rezerwacji i termin podajesz, gdy agent o nie zapyta."
        ),
        "max_turns": 8,
        "success_criteria": [
            "Agent przekazał appointment_datetime {datetime} w wywołaniu cancel_spa_appointment.",
            "Agent przekazał medical_release jako false.",
            "Agent powtórzył gościowi fee_rule: ponad 2 godziny przed zabiegiem — bezpłatnie (0%).",
            "Agent nie potwierdził anulowania bez wywołania narzędzia.",
        ],
        "expect": {
            "tool": "cancel_spa_appointment",
            "text": ["0%", "{id}"],
            "forbid": ["50%"],
        },
    },
    {
        "slug": "03-anulowanie-ponizej-2h",
        "seed": "cancel_fee",
        "prompt": (
            "Jesteś gościem uzdrowiska Bukowy Dwór. Dzwonisz, żeby odwołać rezerwację zabiegu o "
            "numerze {id} ({service}). Zabieg jest dzisiaj, "
            "{date_pl}, o godzinie "
            "{time} — czyli w ciągu najbliższych dwóch godzin. Powód: zmiana planów, "
            "NIE medyczny, czujesz się dobrze. Mówisz po polsku, krótko. Numer i godzinę podajesz, "
            "gdy agent o nie zapyta."
        ),
        "max_turns": 8,
        "success_criteria": [
            "Agent przekazał appointment_datetime {datetime} w wywołaniu cancel_spa_appointment.",
            "Agent przekazał medical_release jako false.",
            "Agent poinformował gościa o opłacie 50% zgodnie z fee_rule z backendu.",
            "Agent nie wymyślił kwoty — powtórzył regułę i wartość fee z narzędzia.",
        ],
        "expect": {
            "tool": "cancel_spa_appointment",
            "text": ["50%", "{id}"],
            "forbid": ["bezpłatn"],
        },
    },
]


def dry_run_seeds(today: date) -> Dict[str, Dict[str, Any]]:
    """Seedy do ``--dry-run``: żadnych zapisów w backendzie, daty względem ``today``."""
    return {
        "book": {"id": "SPA-0001", "date": (today + timedelta(days=1)).isoformat(),
                 "time": "11:00", "service": "masaż leczniczy pleców", "guest": "Piotr Zieliński"},
        "cancel_free": {"id": "SPA-0002", "date": (today + timedelta(days=2)).isoformat(),
                        "time": "10:00", "service": "masaż leczniczy pleców", "guest": "Jan Kowalski"},
        "cancel_fee": {"id": "SPA-0003", "date": today.isoformat(),
                       "time": "16:00", "service": "kąpiel siarczkowa", "guest": "Maria Nowak"},
    }


def _context(seed: Dict[str, Any]) -> Dict[str, str]:
    """Pola jednego seeda w formie gotowej do wstawienia w tekst scenariusza."""
    return {
        "id": seed["id"],
        "service": seed["service"],
        "date": seed["date"],
        "date_pl": date.fromisoformat(seed["date"]).strftime("%d.%m.%Y"),
        "time": seed["time"],
        "datetime": f"{seed['date']}T{seed['time']}",
    }


def scenario_payloads(seeds: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Składa body (API ElevenLabs ``agent-testing/create``) i asercje dla każdego scenariusza."""
    payloads: List[Dict[str, Any]] = []
    for scenario in SCENARIOS:
        ctx = _context(seeds[scenario["seed"]])
        body = {
            "type": "simulation",
            "name": TEST_PREFIX + scenario["slug"],
            "simulation_scenario": scenario["prompt"].format_map(ctx),
            "simulation_max_turns": scenario["max_turns"],
            "success_conditions": [line.format_map(ctx) for line in scenario["success_criteria"]],
            "dynamic_variables": {"user_language": "pl"},
            "tool_mock_config": {"mocking_strategy": "none"},
            "simulation_environment": "production",
        }
        expect = scenario["expect"]
        payloads.append({
            "slug": scenario["slug"],
            "body": body,
            "expect": {
                "tool": expect["tool"],
                "text": [item.format_map(ctx) for item in expect["text"]],
                "forbid": [item.format_map(ctx) for item in expect["forbid"]],
            },
        })
    return payloads
