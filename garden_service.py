# Починаю ревью
"""
Garden Service — модуль бізнес-логіки застосунку Garden.
Реалізація на основі UML-діаграми класів (ЛР 02).

Містить три методи з нетривіальною логікою:
  1. validate_and_create_contact  — валідація + створення контакту
  2. calculate_plant_health       — розрахунок здоров'я рослини
  3. process_garden_reminders     — обробка нагадувань для всього саду
"""

from datetime import datetime, timedelta
from models import Contact


class GardenService:
    """Сервіс бізнес-логіки для віртуального саду."""

    # ── Константи статусів рослини ───────────────────────────────────────
    HEALTH_THRIVING = "thriving"    # квітуча      (≥ 80 %)
    HEALTH_HEALTHY  = "healthy"     # здорова      (50–79 %)
    HEALTH_WILTING  = "wilting"     # в'яне        (1–49 %)
    HEALTH_WITHERED = "withered"    # зів'яла      (0 %)

    # ── Обмеження для валідації контакту ─────────────────────────────────
    MIN_FREQUENCY   = 1
    MAX_FREQUENCY   = 365
    MAX_NAME_LENGTH = 100

    # =====================================================================
    # Метод 1 — validate_and_create_contact
    # Нетривіальна логіка: перевірка типів, граничних значень, виключення
    # =====================================================================
    @staticmethod
    def validate_and_create_contact(
        name: str,
        reminder_frequency_days: int,
    ) -> Contact:
        """
        Валідує вхідні дані та створює об'єкт Contact.

        Args:
            name: ім'я контакту (непорожній рядок ≤ 100 символів).
            reminder_frequency_days: частота нагадувань у днях [1 .. 365].

        Returns:
            Об'єкт Contact із заповненими полями.

        Raises:
            TypeError:  якщо name не str або frequency не int.
            ValueError: якщо name порожній / занадто довгий,
                        або frequency поза діапазоном [1, 365].
        """
        # --- Перевірка типу name ---
        if not isinstance(name, str):
            raise TypeError("Ім'я контакту має бути рядком")

        # --- Перевірка типу frequency (bool — підклас int, відхиляємо) ---
        if isinstance(reminder_frequency_days, bool):
            raise TypeError("Частота нагадувань має бути цілим числом")
        if not isinstance(reminder_frequency_days, int):
            raise TypeError("Частота нагадувань має бути цілим числом")

        # --- Перевірка значення name ---
        stripped = name.strip()
        if not stripped:
            raise ValueError("Ім'я контакту не може бути порожнім")
        if len(stripped) > GardenService.MAX_NAME_LENGTH:
            raise ValueError(
                f"Ім'я контакту не може перевищувати "
                f"{GardenService.MAX_NAME_LENGTH} символів"
            )

        # --- Перевірка діапазону frequency ---
        if reminder_frequency_days < GardenService.MIN_FREQUENCY:
            raise ValueError(
                f"Частота нагадувань має бути >= {GardenService.MIN_FREQUENCY}"
            )
        if reminder_frequency_days > GardenService.MAX_FREQUENCY:
            raise ValueError(
                f"Частота нагадувань має бути <= {GardenService.MAX_FREQUENCY}"
            )

        return Contact(stripped, reminder_frequency_days)

    # =====================================================================
    # Метод 2 — calculate_plant_health
    # Нетривіальна логіка: парсинг дати, розрахунок штрафу, умовні статуси
    # =====================================================================
    @staticmethod
    def calculate_plant_health(
        growth_level: int,
        last_watering_iso: str,
        reminder_frequency_days: int,
        now: datetime | None = None,
    ) -> dict:
        """
        Розраховує стан здоров'я рослини.

        Алгоритм:
          base_health  = min(growth_level * 10, 100)
          penalty      = days_overdue * 15
          health_pct   = max(0, base_health - penalty)

        Args:
            growth_level: поточний рівень росту (≥ 0).
            last_watering_iso: ISO-рядок останнього «поливу».
            reminder_frequency_days: очікувана частота взаємодії.
            now: поточний момент (для тестування).

        Returns:
            dict: {status, health_pct, days_overdue, should_wither}

        Raises:
            ValueError: від'ємний growth_level або некоректна дата.
        """
        # --- Валідація growth_level ---
        if growth_level < 0:
            raise ValueError("Рівень росту не може бути від'ємним")

        if now is None:
            now = datetime.now()

        # --- Парсинг дати з обробкою виключень ---
        try:
            last_watering = datetime.fromisoformat(last_watering_iso)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Некоректний формат дати: {last_watering_iso}"
            ) from exc

        # --- Розрахунок днів прострочення ---
        days_since = (now - last_watering).days
        days_overdue = max(0, days_since - reminder_frequency_days)

        # --- Розрахунок здоров'я ---
        base_health = min(growth_level * 10, 100)
        penalty = days_overdue * 15
        health_pct = max(0, base_health - penalty)

        # --- Визначення статусу (умовні конструкції) ---
        if health_pct >= 80:
            status = GardenService.HEALTH_THRIVING
        elif health_pct >= 50:
            status = GardenService.HEALTH_HEALTHY
        elif health_pct > 0:
            status = GardenService.HEALTH_WILTING
        else:
            status = GardenService.HEALTH_WITHERED

        should_wither = days_overdue > 0

        return {
            "status": status,
            "health_pct": health_pct,
            "days_overdue": days_overdue,
            "should_wither": should_wither,
        }

    # =====================================================================
    # Метод 3 — process_garden_reminders
    # Нетривіальна логіка: цикл, перевірка ключів, сортування, виключення
    # =====================================================================
    @staticmethod
    def process_garden_reminders(
        contacts_with_interactions: list[dict],
        now: datetime | None = None,
    ) -> list[dict]:
        """
        Обробляє масив контактів і повертає список нагадувань.

        Кожен елемент вхідного списку — dict із ключами:
            contact_id, name, reminder_frequency_days, last_interaction_iso

        Алгоритм (цикл + умовні конструкції):
          1. Для кожного контакту обчислити days_since останньої взаємодії.
          2. Якщо days_since >= frequency → сформувати нагадування.
          3. Контакти з некоректною датою — пропускаються.
          4. Результат сортується за терміновістю (desc).

        Args:
            contacts_with_interactions: список контактів.
            now: поточний момент (для тестування).

        Returns:
            Відсортований список нагадувань.

        Raises:
            TypeError: вхід не є списком або елемент не є dict.
            ValueError: у елементі відсутні обов'язкові ключі.
        """
        if not isinstance(contacts_with_interactions, list):
            raise TypeError("Очікується список контактів")

        if now is None:
            now = datetime.now()

        required_keys = {
            "contact_id", "name",
            "reminder_frequency_days", "last_interaction_iso",
        }
        reminders: list[dict] = []

        for idx, entry in enumerate(contacts_with_interactions):
            # --- Перевірка типу елемента ---
            if not isinstance(entry, dict):
                raise TypeError(f"Елемент #{idx} має бути словником")

            # --- Перевірка обов'язкових ключів ---
            missing = required_keys - entry.keys()
            if missing:
                raise ValueError(
                    f"Елемент #{idx} не містить ключів: {missing}"
                )

            # --- Парсинг дати (пропускаємо некоректні) ---
            try:
                last_dt = datetime.fromisoformat(entry["last_interaction_iso"])
            except (ValueError, TypeError):
                continue

            days_since = (now - last_dt).days
            freq = entry["reminder_frequency_days"]

            # --- Умова: чи потрібно нагадування ---
            if days_since >= freq:
                days_overdue = days_since - freq
                reminders.append({
                    "contact_id": entry["contact_id"],
                    "name": entry["name"],
                    "message": (
                        f"Зв'яжіться з {entry['name']}! "
                        f"Пройшло {days_since} дн."
                    ),
                    "days_overdue": days_overdue,
                })

        # --- Сортування за терміновістю (найбільш прострочені першими) ---
        reminders.sort(key=lambda r: r["days_overdue"], reverse=True)

        return reminders
