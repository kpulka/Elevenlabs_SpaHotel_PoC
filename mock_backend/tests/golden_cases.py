"""Generowanie i weryfikacja wzorców (golden) dla modułu odpowiedzi SPA."""

from __future__ import annotations

from catalog import Usluga
from data import USLUGI
from schemas import AnulowanieSPA, PrzelozenieSPA, RezerwacjaSPA, ZapytanieSPA
from services.spa import (
    Dostepnosc,
    Odmowa,
    Oplata,
    Potwierdzenie,
    Powod,
    Przeniesienie,
    RegulaOplaty,
    WynikAnulowania,
)
from store import Rezerwacja


def collect_responses(responses_mod) -> dict[str, dict]:
    """Uruchamia wszystkie gałęzie responses i zwraca mapę klucz -> słownik odpowiedzi."""
    results: dict[str, dict] = {}

    usluga: Usluga = USLUGI[0]  # Kąpiel siarczkowa
    fake_rezerwacja = Rezerwacja(
        confirmation_id="SPA-1234",
        kod_uslugi=usluga.kod,
        data="2026-11-20",
        godzina="10:00",
        gosc="Jan Kowalski",
    )
    nowa_rezerwacja = Rezerwacja(
        confirmation_id="SPA-5678",
        kod_uslugi=usluga.kod,
        data="2026-11-21",
        godzina="12:00",
        gosc="Jan Kowalski",
    )

    # 1. dostepnosc
    req_dost = ZapytanieSPA(service_name="kąpiel siarczkowa", date="2026-11-20")
    results["dostepnosc_sukces"] = responses_mod.dostepnosc(
        req_dost,
        Dostepnosc(usluga=usluga, status="dopasowano", powod=None, wolne=("10:00", "12:00")),
    )
    results["dostepnosc_brak_slotow"] = responses_mod.dostepnosc(
        req_dost,
        Dostepnosc(usluga=usluga, status="dopasowano", powod=Powod.BRAK_SLOTOW, wolne=()),
    )
    results["dostepnosc_przeszlosc"] = responses_mod.dostepnosc(
        ZapytanieSPA(service_name="kąpiel siarczkowa", date="2026-11-01"),
        Dostepnosc(usluga=usluga, status="dopasowano", powod=Powod.PRZESZLOSC, wolne=()),
    )
    results["dostepnosc_poza_oknem"] = responses_mod.dostepnosc(
        ZapytanieSPA(service_name="kąpiel siarczkowa", date="2026-12-30"),
        Dostepnosc(usluga=usluga, status="dopasowano", powod=Powod.POZA_OKNEM, wolne=()),
    )
    results["dostepnosc_nieznany"] = responses_mod.dostepnosc(
        ZapytanieSPA(service_name="lot balonem", date="2026-11-20"),
        Dostepnosc(usluga=None, status="nieznane", powod=Powod.NIEZNANY),
    )
    results["dostepnosc_niejednoznaczny"] = responses_mod.dostepnosc(
        ZapytanieSPA(service_name="masaż", date="2026-11-20"),
        Dostepnosc(
            usluga=None,
            status="niejednoznaczne",
            powod=Powod.NIEJEDNOZNACZNY,
            kandydaci=("Masaż klasyczny", "Masaż leczniczy"),
        ),
    )

    # 2. rezerwacja
    req_rez = RezerwacjaSPA(
        service_name="kąpiel siarczkowa",
        date="2026-11-20",
        time="10:00",
        guest_name="Jan Kowalski",
    )
    results["rezerwacja_sukces"] = responses_mod.rezerwacja(
        req_rez,
        Potwierdzenie(rezerwacja=fake_rezerwacja, usluga=usluga),
    )
    results["rezerwacja_odmowa_niejednoznaczny"] = responses_mod.rezerwacja(
        req_rez,
        Odmowa(powod=Powod.NIEJEDNOZNACZNY, kandydaci=("Masaż klasyczny", "Masaż leczniczy")),
    )
    results["rezerwacja_odmowa_nieznany"] = responses_mod.rezerwacja(
        req_rez,
        Odmowa(powod=Powod.NIEZNANY),
    )
    results["rezerwacja_odmowa_przeszlosc"] = responses_mod.rezerwacja(
        req_rez,
        Odmowa(powod=Powod.PRZESZLOSC, usluga=usluga),
    )
    results["rezerwacja_odmowa_poza_oknem"] = responses_mod.rezerwacja(
        req_rez,
        Odmowa(powod=Powod.POZA_OKNEM, usluga=usluga),
    )
    results["rezerwacja_odmowa_poza_grafikiem"] = responses_mod.rezerwacja(
        req_rez,
        Odmowa(powod=Powod.POZA_GRAFIKIEM, usluga=usluga, wolne=("10:00", "12:00")),
    )
    results["rezerwacja_odmowa_zajety"] = responses_mod.rezerwacja(
        req_rez,
        Odmowa(powod=Powod.ZAJETY, usluga=usluga, wolne=("12:00", "14:00")),
    )
    results["rezerwacja_odmowa_wyscig"] = responses_mod.rezerwacja(
        req_rez,
        Odmowa(powod=Powod.WYSCIG, usluga=usluga, wolne=("12:00", "14:00")),
    )

    # 3. anulowanie (PL i EN)
    for lang in ("pl", "en"):
        pfx = f"anulowanie_{lang}_"
        req_anul_not_found = AnulowanieSPA(confirmation_id="SPA-0000", language=lang)
        results[pfx + "nie_znaleziono"] = responses_mod.anulowanie(
            req_anul_not_found,
            WynikAnulowania(znaleziona=False),
        )

        req_anul_found = AnulowanieSPA(
            confirmation_id="SPA-1234",
            appointment_datetime="2026-11-20T10:00:00",
            language=lang,
        )
        for regula in (
            RegulaOplaty.MEDYCZNA,
            RegulaOplaty.BRAK_GODZINY,
            RegulaOplaty.PONAD_2H,
            RegulaOplaty.PONIZEJ_2H,
        ):
            ulamek = 0.0 if regula in (RegulaOplaty.MEDYCZNA, RegulaOplaty.PONAD_2H) else 0.5
            oplata = Oplata(ulamek=ulamek, regula=regula)
            results[f"{pfx}{regula.value}"] = responses_mod.anulowanie(
                req_anul_found,
                WynikAnulowania(znaleziona=True, oplata=oplata, zwolniona=True),
            )

    # 4. przelozenie (PL i EN)
    for lang in ("pl", "en"):
        pfx = f"przelozenie_{lang}_"
        req_przel = PrzelozenieSPA(
            confirmation_id="SPA-1234",
            service_name="kąpiel siarczkowa",
            new_date="2026-11-21",
            new_time="12:00",
            guest_name="Jan Kowalski",
            language=lang,
        )
        results[pfx + "sukces"] = responses_mod.przelozenie(
            req_przel,
            Przeniesienie(stara_numer="SPA-1234", nowa=nowa_rezerwacja, usluga=usluga),
        )
        results[pfx + "odmowa_nie_znaleziono"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(powod=Powod.NIE_ZNALEZIONO),
        )
        results[pfx + "odmowa_niejednoznaczny"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(
                powod=Powod.NIEJEDNOZNACZNY,
                kandydaci=("Masaż klasyczny", "Masaż leczniczy"),
                stara=fake_rezerwacja,
            ),
        )
        results[pfx + "odmowa_nieznany"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(powod=Powod.NIEZNANY, stara=fake_rezerwacja),
        )
        results[pfx + "odmowa_przeszlosc"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(powod=Powod.PRZESZLOSC, usluga=usluga, stara=fake_rezerwacja),
        )
        results[pfx + "odmowa_poza_oknem"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(powod=Powod.POZA_OKNEM, usluga=usluga, stara=fake_rezerwacja),
        )
        results[pfx + "odmowa_poza_grafikiem"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(powod=Powod.POZA_GRAFIKIEM, usluga=usluga, stara=fake_rezerwacja),
        )
        results[pfx + "odmowa_zajety"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(powod=Powod.ZAJETY, usluga=usluga, wolne=("10:00", "14:00"), stara=fake_rezerwacja),
        )
        results[pfx + "odmowa_wyscig"] = responses_mod.przelozenie(
            req_przel,
            Odmowa(powod=Powod.WYSCIG, usluga=usluga, wolne=("10:00", "14:00"), stara=fake_rezerwacja),
        )

    return results
