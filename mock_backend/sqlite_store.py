"""SQLite persistence for the SPA calendar (stdlib ``sqlite3`` only).

Activated by ``ANNA_DB_PATH``; without it the process keeps the in-memory ``store.SpaStore``.
``SqliteSpaStore`` keeps the same public interface and business rules (window, slot key,
idempotency) and overrides only the storage primitives.

Guarantees:

* **Schema versioning** - ``migrate()`` applies the migrations in ``MIGRATIONS`` that are newer
  than ``schema_version``; running it again is a no-op.
* **Slot exclusivity** - a UNIQUE index on ``(klucz_slotu, godzina)`` makes the insert fail for a
  second booking of the same slot, even if two requests race past the service-level check.
* **Idempotency keys** - ``klucze_idempotencji.klucz`` is the PRIMARY KEY (UNIQUE); the key row and
  the reservation are written in one transaction. ``purge_klucze()`` removes keys older than a TTL.
* **Thread safety** - one connection (``check_same_thread=False``) serialised by an ``RLock``.

Limits: the service layer's read-then-write checks are not transactional across *processes*,
so run one worker (see ``mock_backend/README.md``).
"""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

from catalog import Usluga
from store import Rezerwacja, SpaStore, klucz_goscia

SCHEMA_V1 = """
CREATE TABLE rezerwacje (
    confirmation_id TEXT PRIMARY KEY,
    kod_uslugi      TEXT NOT NULL,
    data            TEXT NOT NULL,
    godzina         TEXT NOT NULL,
    gosc            TEXT NOT NULL,
    gosc_klucz      TEXT NOT NULL,
    klucz_slotu     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE UNIQUE INDEX ux_rezerwacje_slot ON rezerwacje (klucz_slotu, godzina);

CREATE TABLE klucze_idempotencji (
    klucz           TEXT PRIMARY KEY,
    confirmation_id TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX ix_klucze_created_at ON klucze_idempotencji (created_at);

CREATE TABLE sekwencja (
    nazwa   TEXT PRIMARY KEY,
    wartosc INTEGER NOT NULL
);
INSERT INTO sekwencja (nazwa, wartosc) VALUES ('confirmation', 1000);
"""

# Ordered, append-only. Add a new (version, sql) pair for every schema change.
MIGRATIONS: tuple[tuple[int, str], ...] = ((1, SCHEMA_V1),)

SEQUENCE_NAME = "confirmation"
SEQUENCE_START = 1000  # same as SpaStore._next_id: the first confirmation is SPA-1001

_UPSERT_KLUCZ = """
INSERT INTO klucze_idempotencji (klucz, confirmation_id, created_at) VALUES (?, ?, ?)
ON CONFLICT (klucz) DO UPDATE SET confirmation_id = excluded.confirmation_id,
                                  created_at = excluded.created_at
"""


def _iso_utc(moment: datetime) -> str:
    """Canonical timestamp for ``created_at`` (fixed format, so string comparison = time order)."""
    return moment.astimezone(timezone.utc).isoformat(timespec="seconds")


def _current_version(conn: sqlite3.Connection) -> int:
    (wersja,) = conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()
    return int(wersja)


def _apply(conn: sqlite3.Connection, version: int, body: str) -> None:
    """Runs one migration atomically; ``executescript`` needs the BEGIN/COMMIT inside the script."""
    script = (
        "BEGIN IMMEDIATE;\n"
        f"{body}\n"
        "INSERT INTO schema_version (version, applied_at) "
        f"VALUES ({version}, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));\n"
        "COMMIT;"
    )
    try:
        conn.executescript(script)
    except sqlite3.Error:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise


def migrate(conn: sqlite3.Connection) -> int:
    """Brings the schema up to the newest version and returns it. Idempotent."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)")
    current = _current_version(conn)
    for version, body in MIGRATIONS:
        if version > current:
            _apply(conn, version, body)
            current = version
    return current


def _z_wiersza(wiersz: sqlite3.Row) -> Rezerwacja:
    return Rezerwacja(
        confirmation_id=wiersz["confirmation_id"],
        kod_uslugi=wiersz["kod_uslugi"],
        data=wiersz["data"],
        godzina=wiersz["godzina"],
        gosc=wiersz["gosc"],
    )


class SqliteSpaStore(SpaStore):
    """``SpaStore`` whose reservations, idempotency keys and numbering live in SQLite."""

    def __init__(self, path: str | Path, uslugi: Sequence[Usluga], horyzont_dni: int = 14) -> None:
        super().__init__(uslugi, horyzont_dni=horyzont_dni)
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False, timeout=5.0)
        self._conn.row_factory = sqlite3.Row
        try:
            with self._lock:
                self._conn.execute("PRAGMA journal_mode=WAL")
                self.schema_version = migrate(self._conn)
        except sqlite3.Error:
            self._conn.close()  # do not leak the handle when the schema cannot be brought up
            raise

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ── prymitywy magazynu (nadpisanie SpaStore) ────────────────────────────
    def _zajete_godziny(self, klucz: str) -> set[str]:
        with self._lock:
            wiersze = self._conn.execute("SELECT godzina FROM rezerwacje WHERE klucz_slotu = ?", (klucz,)).fetchall()
        return {wiersz["godzina"] for wiersz in wiersze}

    def zajmij(self, rezerwacja: Rezerwacja, idempotency_key: str | None = None) -> bool:
        """Inserts the reservation (and its key) in one transaction; False if the slot is taken."""
        teraz = _iso_utc(datetime.now(timezone.utc))
        with self._lock, self._conn:
            try:
                self._conn.execute(
                    "INSERT INTO rezerwacje (confirmation_id, kod_uslugi, data, godzina, gosc, gosc_klucz,"
                    " klucz_slotu, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        rezerwacja.confirmation_id,
                        rezerwacja.kod_uslugi,
                        rezerwacja.data,
                        rezerwacja.godzina,
                        rezerwacja.gosc,
                        klucz_goscia(rezerwacja.gosc),
                        rezerwacja.klucz_slotu,
                        teraz,
                    ),
                )
            except sqlite3.IntegrityError:
                return False  # UNIQUE (klucz_slotu, godzina): the slot was taken first
            if idempotency_key:
                self._conn.execute(_UPSERT_KLUCZ, (idempotency_key, rezerwacja.confirmation_id, teraz))
        return True

    def zwolnij(self, confirmation_id: str) -> Rezerwacja | None:
        with self._lock, self._conn:
            rezerwacja = self._pobierz(confirmation_id)
            if rezerwacja is None:
                return None
            self._conn.execute("DELETE FROM rezerwacje WHERE confirmation_id = ?", (confirmation_id,))
        return rezerwacja

    def rezerwacja(self, confirmation_id: str) -> Rezerwacja | None:
        with self._lock:
            return self._pobierz(confirmation_id)

    def rezerwacja_po_kluczu(self, klucz: str) -> Rezerwacja | None:
        with self._lock:
            wiersz = self._conn.execute(
                "SELECT r.* FROM klucze_idempotencji k JOIN rezerwacje r ON r.confirmation_id = k.confirmation_id"
                " WHERE k.klucz = ?",
                (klucz,),
            ).fetchone()
        return _z_wiersza(wiersz) if wiersz is not None else None

    def duplikat(self, kod_uslugi: str, data_iso: str, godzina: str, gosc: str) -> Rezerwacja | None:
        with self._lock:
            wiersz = self._conn.execute(
                "SELECT * FROM rezerwacje WHERE kod_uslugi = ? AND data = ? AND godzina = ? AND gosc_klucz = ?"
                " LIMIT 1",
                (kod_uslugi, data_iso, godzina, klucz_goscia(gosc)),
            ).fetchone()
        return _z_wiersza(wiersz) if wiersz is not None else None

    def nowy_numer(self) -> str:
        """Monotonic SPA-XXXX number kept in the database, so numbers never repeat across restarts."""
        with self._lock, self._conn:
            self._conn.execute("UPDATE sekwencja SET wartosc = wartosc + 1 WHERE nazwa = ?", (SEQUENCE_NAME,))
            (wartosc,) = self._conn.execute(
                "SELECT wartosc FROM sekwencja WHERE nazwa = ?", (SEQUENCE_NAME,)
            ).fetchone()
        return f"SPA-{wartosc}"

    def purge_klucze(self, max_wiek: timedelta, teraz: datetime | None = None) -> int:
        """Deletes idempotency keys created more than ``max_wiek`` ago; returns how many were removed.

        Reservations are not touched. After a key is purged, a retry without the key falls back to
        the duplicate check (same service, date, time and guest), not to a new booking.
        """
        granica = _iso_utc((teraz or datetime.now(timezone.utc)) - max_wiek)
        with self._lock, self._conn:
            kursor = self._conn.execute("DELETE FROM klucze_idempotencji WHERE created_at < ?", (granica,))
            return kursor.rowcount

    def reset(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM rezerwacje")
            self._conn.execute("DELETE FROM klucze_idempotencji")
            self._conn.execute("UPDATE sekwencja SET wartosc = ? WHERE nazwa = ?", (SEQUENCE_START, SEQUENCE_NAME))

    def _pobierz(self, confirmation_id: str) -> Rezerwacja | None:
        """Reads one reservation; the caller must hold ``self._lock``."""
        wiersz = self._conn.execute(
            "SELECT * FROM rezerwacje WHERE confirmation_id = ?", (confirmation_id,)
        ).fetchone()
        return _z_wiersza(wiersz) if wiersz is not None else None
