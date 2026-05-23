"""Крок 4 — Моделі даних (Class Diagram)."""

import uuid
from datetime import datetime


class UserModel:
    """Зареєстрований користувач."""

    def __init__(self, email: str, password_hash: str):
        self.user_id: str = str(uuid.uuid4())
        self.email: str = email
        self.password_hash: str = password_hash

    # OPT-4
    def verify_account(self) -> bool:
        return bool(self.email and self.password_hash)

    def to_dict(self) -> dict:
        return {"user_id": self.user_id, "email": self.email}


class Contact:
    """Контакт користувача (FR-02)."""

    def __init__(self, name: str, reminder_frequency_days: int = 7):
        self.contact_id: str = str(uuid.uuid4())
        self.name: str = name
        self.reminder_frequency_days: int = reminder_frequency_days

    def to_dict(self) -> dict:
        return {
            "contact_id": self.contact_id,
            "name": self.name,
            "reminder_frequency_days": self.reminder_frequency_days,
        }


class VirtualPlant:
    """Віртуальна рослина, що відповідає контакту (FR-03)."""

    MAX_GROWTH = 10

    def __init__(self, contact_id: str):
        self.plant_id: str = str(uuid.uuid4())
        self.contact_id: str = contact_id
        self.growth_level: int = 1
        self.last_watering: datetime = datetime.now()

    # OPT-13 — анімація росту
    def animate_growth(self) -> int:
        if self.growth_level < self.MAX_GROWTH:
            self.growth_level += 1
        self.last_watering = datetime.now()
        return self.growth_level

    def wither(self) -> int:
        if self.growth_level > 0:
            self.growth_level -= 1
        return self.growth_level

    def to_dict(self) -> dict:
        return {
            "plant_id": self.plant_id,
            "contact_id": self.contact_id,
            "growth_level": self.growth_level,
            "last_watering": self.last_watering.isoformat(),
        }
