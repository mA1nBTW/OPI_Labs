"""
Модульні тести для garden_service.py

Фреймворк: pytest
Патерн: AAA (Arrange → Act → Assert)
Техніки: EP (Equivalence Partitioning), BVA (Boundary Value Analysis)

Загальна кількість тест-кейсів: 16
"""

import sys
import os
import pytest
from datetime import datetime, timedelta

# Додаємо кореневу директорію проєкту в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from garden_service import GardenService
from models import Contact


# ═════════════════════════════════════════════════════════════════════════
# Метод 1: validate_and_create_contact
# ═════════════════════════════════════════════════════════════════════════


class TestValidateAndCreateContact:
    """Тести для методу validate_and_create_contact."""

    # TC-01 | EP-позитивний | Валідний контакт
    def test_valid_contact_creation(self):
        """EP-позитивний: коректне ім'я + коректна частота → Contact."""
        # Arrange
        name = "Мама"
        frequency = 7

        # Act
        contact = GardenService.validate_and_create_contact(name, frequency)

        # Assert
        assert isinstance(contact, Contact)
        assert contact.name == "Мама"
        assert contact.reminder_frequency_days == 7

    # TC-02 | EP-негативний | Порожнє ім'я
    def test_empty_name_raises_value_error(self):
        """EP-негативний: порожній рядок → ValueError."""
        # Arrange
        name = ""
        frequency = 7

        # Act & Assert
        with pytest.raises(ValueError, match="порожнім"):
            GardenService.validate_and_create_contact(name, frequency)

    # TC-03 | EP-негативний | Ім'я не є рядком
    def test_name_not_string_raises_type_error(self):
        """EP-негативний: name = int → TypeError."""
        # Arrange
        name = 12345
        frequency = 7

        # Act & Assert
        with pytest.raises(TypeError, match="рядком"):
            GardenService.validate_and_create_contact(name, frequency)

    # TC-04 | BVA | Частота нижче мінімуму (0)
    def test_frequency_below_min_raises_value_error(self):
        """BVA: frequency = 0 (нижче мінімуму 1) → ValueError."""
        # Arrange
        name = "Тато"
        frequency = 0

        # Act & Assert
        with pytest.raises(ValueError, match=">= 1"):
            GardenService.validate_and_create_contact(name, frequency)

    # TC-05 | BVA | Частота на мінімальній межі (1)
    def test_frequency_at_min_boundary(self):
        """BVA: frequency = 1 (мінімальна межа) → успіх."""
        # Arrange
        name = "Тато"
        frequency = 1

        # Act
        contact = GardenService.validate_and_create_contact(name, frequency)

        # Assert
        assert contact.reminder_frequency_days == 1

    # TC-06 | BVA | Частота на максимальній межі (365)
    def test_frequency_at_max_boundary(self):
        """BVA: frequency = 365 (максимальна межа) → успіх."""
        # Arrange
        name = "Бабуся"
        frequency = 365

        # Act
        contact = GardenService.validate_and_create_contact(name, frequency)

        # Assert
        assert contact.reminder_frequency_days == 365

    # TC-07 | BVA | Частота вище максимуму (366)
    def test_frequency_above_max_raises_value_error(self):
        """BVA: frequency = 366 (вище максимуму 365) → ValueError."""
        # Arrange
        name = "Дідусь"
        frequency = 366

        # Act & Assert
        with pytest.raises(ValueError, match="<= 365"):
            GardenService.validate_and_create_contact(name, frequency)

    # TC-08 | EP-негативний | Частота передана як bool
    def test_frequency_bool_raises_type_error(self):
        """EP-негативний: frequency = True (bool, підклас int) → TypeError."""
        # Arrange
        name = "Друг"
        frequency = True

        # Act & Assert
        with pytest.raises(TypeError, match="цілим числом"):
            GardenService.validate_and_create_contact(name, frequency)


# ═════════════════════════════════════════════════════════════════════════
# Метод 2: calculate_plant_health
# ═════════════════════════════════════════════════════════════════════════


class TestCalculatePlantHealth:
    """Тести для методу calculate_plant_health."""

    # TC-09 | EP-позитивний | Здорова рослина (нещодавно полита)
    def test_healthy_plant_thriving(self):
        """EP-позитивний: growth=8, полита сьогодні → thriving, health≥80."""
        # Arrange
        now = datetime(2025, 6, 1, 12, 0, 0)
        last_watering = now.isoformat()
        growth_level = 8
        frequency = 7

        # Act
        result = GardenService.calculate_plant_health(
            growth_level, last_watering, frequency, now=now
        )

        # Assert
        assert result["status"] == "thriving"
        assert result["health_pct"] == 80
        assert result["days_overdue"] == 0
        assert result["should_wither"] is False

    # TC-10 | EP-негативний | Від'ємний growth_level
    def test_negative_growth_raises_value_error(self):
        """EP-негативний: growth_level = -1 → ValueError."""
        # Arrange
        growth_level = -1
        last_watering = "2025-06-01T12:00:00"
        frequency = 7

        # Act & Assert
        with pytest.raises(ValueError, match="від'ємним"):
            GardenService.calculate_plant_health(
                growth_level, last_watering, frequency
            )

    # TC-11 | EP-негативний | Некоректний ISO-рядок дати
    def test_invalid_iso_date_raises_value_error(self):
        """EP-негативний: невалідний ISO-рядок → ValueError."""
        # Arrange
        growth_level = 5
        last_watering = "not-a-date"
        frequency = 7

        # Act & Assert
        with pytest.raises(ValueError, match="Некоректний формат"):
            GardenService.calculate_plant_health(
                growth_level, last_watering, frequency
            )

    # TC-12 | EP-позитивний | Прострочена рослина → wilting / withered
    def test_overdue_plant_should_wither(self):
        """EP-позитивний: 10 днів прострочення → should_wither=True."""
        # Arrange
        now = datetime(2025, 6, 20, 12, 0, 0)
        last_watering = datetime(2025, 6, 1, 12, 0, 0).isoformat()  # 19 днів
        growth_level = 5
        frequency = 7  # overdue = 19 - 7 = 12 днів

        # Act
        result = GardenService.calculate_plant_health(
            growth_level, last_watering, frequency, now=now
        )

        # Assert
        assert result["should_wither"] is True
        assert result["days_overdue"] == 12
        # base=50, penalty=12*15=180 → health=max(0,50-180)=0
        assert result["health_pct"] == 0
        assert result["status"] == "withered"

    # TC-13 | BVA | growth_level = 0 → health_pct = 0, withered
    def test_zero_growth_level(self):
        """BVA: growth_level = 0 (мінімальна межа) → withered."""
        # Arrange
        now = datetime(2025, 6, 1, 12, 0, 0)
        last_watering = now.isoformat()
        growth_level = 0
        frequency = 7

        # Act
        result = GardenService.calculate_plant_health(
            growth_level, last_watering, frequency, now=now
        )

        # Assert
        assert result["health_pct"] == 0
        assert result["status"] == "withered"

    # TC-14 | BVA | Межа між healthy і thriving (health_pct = 79)
    def test_boundary_healthy_thriving(self):
        """BVA: growth_level=10, 2 дні overdue → health=100-30=70, healthy."""
        # Arrange
        now = datetime(2025, 6, 10, 12, 0, 0)
        last_watering = datetime(2025, 6, 1, 12, 0, 0).isoformat()  # 9 днів
        growth_level = 10
        frequency = 7  # overdue = 9 - 7 = 2

        # Act
        result = GardenService.calculate_plant_health(
            growth_level, last_watering, frequency, now=now
        )

        # Assert
        # base=100, penalty=2*15=30, health=70
        assert result["health_pct"] == 70
        assert result["status"] == "healthy"


# ═════════════════════════════════════════════════════════════════════════
# Метод 3: process_garden_reminders
# ═════════════════════════════════════════════════════════════════════════


class TestProcessGardenReminders:
    """Тести для методу process_garden_reminders."""

    def _make_contact(
        self, name: str, freq: int, last_iso: str, cid: str = "c1"
    ) -> dict:
        """Допоміжний метод для створення тестового контакту."""
        return {
            "contact_id": cid,
            "name": name,
            "reminder_frequency_days": freq,
            "last_interaction_iso": last_iso,
        }

    # TC-15 | EP-позитивний | Є прострочені контакти → нагадування
    def test_overdue_contact_generates_reminder(self):
        """EP-позитивний: контакт прострочений → 1 нагадування."""
        # Arrange
        now = datetime(2025, 6, 15, 12, 0, 0)
        contacts = [
            self._make_contact(
                "Мама", 7,
                datetime(2025, 6, 1, 12, 0, 0).isoformat(),
            ),
        ]

        # Act
        result = GardenService.process_garden_reminders(contacts, now=now)

        # Assert
        assert len(result) == 1
        assert result[0]["name"] == "Мама"
        assert result[0]["days_overdue"] == 7  # 14 - 7

    # TC-16 | EP-позитивний | Немає прострочених → порожній список
    def test_no_overdue_returns_empty(self):
        """EP-позитивний: взаємодія була вчора, freq=7 → порожній список."""
        # Arrange
        now = datetime(2025, 6, 15, 12, 0, 0)
        contacts = [
            self._make_contact(
                "Тато", 7,
                datetime(2025, 6, 14, 12, 0, 0).isoformat(),
            ),
        ]

        # Act
        result = GardenService.process_garden_reminders(contacts, now=now)

        # Assert
        assert result == []

    # TC-17 | EP-негативний | Вхід не є списком → TypeError
    def test_not_a_list_raises_type_error(self):
        """EP-негативний: передано рядок замість списку → TypeError."""
        # Arrange
        bad_input = "not a list"

        # Act & Assert
        with pytest.raises(TypeError, match="список"):
            GardenService.process_garden_reminders(bad_input)

    # TC-18 | EP-негативний | Відсутні обов'язкові ключі → ValueError
    def test_missing_keys_raises_value_error(self):
        """EP-негативний: dict без обов'язкових ключів → ValueError."""
        # Arrange
        contacts = [{"name": "Мама"}]  # бракує contact_id, freq, iso

        # Act & Assert
        with pytest.raises(ValueError, match="не містить ключів"):
            GardenService.process_garden_reminders(contacts)

    # TC-19 | EP-позитивний | Сортування за терміновістю
    def test_reminders_sorted_by_urgency(self):
        """EP-позитивний: два прострочені контакти → сортовано desc."""
        # Arrange
        now = datetime(2025, 6, 30, 12, 0, 0)
        contacts = [
            self._make_contact(
                "Друг", 7,
                datetime(2025, 6, 20, 12, 0, 0).isoformat(),  # overdue=3
                cid="c1",
            ),
            self._make_contact(
                "Сестра", 3,
                datetime(2025, 6, 10, 12, 0, 0).isoformat(),  # overdue=17
                cid="c2",
            ),
        ]

        # Act
        result = GardenService.process_garden_reminders(contacts, now=now)

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "Сестра"  # більш прострочений → перший
        assert result[1]["name"] == "Друг"

    # TC-20 | EP-позитивний | Некоректна дата у контакті → пропускається
    def test_invalid_date_skipped(self):
        """EP-позитивний: контакт з bad ISO → пропускається без помилки."""
        # Arrange
        now = datetime(2025, 6, 15, 12, 0, 0)
        contacts = [
            self._make_contact("Хтось", 7, "bad-date"),
        ]

        # Act
        result = GardenService.process_garden_reminders(contacts, now=now)

        # Assert
        assert result == []
