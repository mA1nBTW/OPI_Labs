"""Крок 4 — NotificationManager (FR-04, OPT-7/OPT-8).

Заглушка для FCM push-нагадувань.
У реальному додатку тут буде виклик Firebase Admin SDK.
"""

from datetime import datetime, timedelta

class NotificationManager:
    """Перевірка та планування push-нагадувань (≤ 1 на добу на контакт)."""

    def __init__(self):
        # contact_id → datetime останнього push
        self._last_sent: dict[str, datetime] = {}

    def _is_rate_limited(self, contact_id: str, current_time: datetime) -> bool:
        """Перевіряє, чи не перевищено ліміт відправки (1 повідомлення на добу)."""
        last_sent_time = self._last_sent.get(contact_id)
        return bool(last_sent_time and (current_time - last_sent_time) < timedelta(days=1))

    def send_push(self, contact_id: str, contact_name: str) -> str | None:
        """Формує та відправляє нагадування, якщо не перевищено ліміт."""
        now = datetime.now()

        if self._is_rate_limited(contact_id, now):
            return None  # не більше 1 push за 24 год (FR-04)

        self._last_sent[contact_id] = now
        message = f"[Garden] Ne zabudj zv'jazatysja z {contact_name}!"
        print(f"[FCM STUB] -> {message}")
        return message

    def check_if_reminder_needed(
        self, last_interaction_iso: str, frequency_days: int
    ) -> bool:
        last_dt = datetime.fromisoformat(last_interaction_iso)
        return (datetime.now() - last_dt) >= timedelta(days=frequency_days)
