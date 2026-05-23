"""Крок 4 — Локальна БД (OPT-5, FR-02): SQLite через sqlite3."""

import sqlite3
from datetime import datetime
from models import Contact, VirtualPlant


class LocalDatabase:
    """Обгортка над SQLite — відповідає класу LocalDatabase з діаграми."""

    def __init__(self, db_path: str = "garden.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    # OPT-5 — ініціалізація схеми
    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id   TEXT PRIMARY KEY,
                email     TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contacts (
                contact_id             TEXT PRIMARY KEY,
                user_id                TEXT NOT NULL,
                name                   TEXT NOT NULL,
                reminder_frequency_days INTEGER DEFAULT 7,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );
            CREATE TABLE IF NOT EXISTS plants (
                plant_id      TEXT PRIMARY KEY,
                contact_id    TEXT UNIQUE NOT NULL,
                growth_level  INTEGER DEFAULT 1,
                last_watering TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
            );
            CREATE TABLE IF NOT EXISTS interactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id  TEXT NOT NULL,
                timestamp   TEXT NOT NULL,
                media_path  TEXT,
                FOREIGN KEY (contact_id) REFERENCES contacts(contact_id)
            );
        """)
        self.conn.commit()

    # ---------- users ----------
    def insert_user(self, user_id: str, email: str, password_hash: str) -> None:
        self.conn.execute(
            "INSERT INTO users VALUES (?, ?, ?)",
            (user_id, email, password_hash),
        )
        self.conn.commit()

    def get_user_by_email(self, email: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        return dict(row) if row else None

    # ---------- contacts ----------
    def insert_contact(self, user_id: str, contact: Contact) -> None:
        self.conn.execute(
            "INSERT INTO contacts VALUES (?, ?, ?, ?)",
            (contact.contact_id, user_id, contact.name, contact.reminder_frequency_days),
        )
        self.conn.commit()

    def get_contacts(self, user_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM contacts WHERE user_id = ?", (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def delete_contact(self, contact_id: str) -> None:
        self.conn.execute("DELETE FROM plants WHERE contact_id = ?", (contact_id,))
        self.conn.execute("DELETE FROM interactions WHERE contact_id = ?", (contact_id,))
        self.conn.execute("DELETE FROM contacts WHERE contact_id = ?", (contact_id,))
        self.conn.commit()

    # ---------- plants ----------
    def insert_plant(self, plant: VirtualPlant) -> None:
        self.conn.execute(
            "INSERT INTO plants VALUES (?, ?, ?, ?)",
            (plant.plant_id, plant.contact_id, plant.growth_level,
             plant.last_watering.isoformat()),
        )
        self.conn.commit()

    def update_plant_state(self, plant: VirtualPlant) -> None:
        self.conn.execute(
            "UPDATE plants SET growth_level = ?, last_watering = ? WHERE contact_id = ?",
            (plant.growth_level, plant.last_watering.isoformat(), plant.contact_id),
        )
        self.conn.commit()

    def get_plant(self, contact_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM plants WHERE contact_id = ?", (contact_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_plants(self, user_id: str) -> list[dict]:
        rows = self.conn.execute("""
            SELECT p.* FROM plants p
            JOIN contacts c ON c.contact_id = p.contact_id
            WHERE c.user_id = ?
        """, (user_id,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- interactions (FR-05 / FR-10) ----------
    def add_interaction(self, contact_id: str, media_path: str | None = None) -> None:
        self.conn.execute(
            "INSERT INTO interactions (contact_id, timestamp, media_path) VALUES (?, ?, ?)",
            (contact_id, datetime.now().isoformat(), media_path),
        )
        self.conn.commit()

    def get_interactions(self, contact_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM interactions WHERE contact_id = ? ORDER BY timestamp DESC",
            (contact_id,),
        ).fetchall()
        return [dict(r) for r in rows]
