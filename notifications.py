"""Крок 4 — NotificationManager (FR-04, OPT-7/OPT-8).

Заглушка для FCM push-нагадувань.
У реальному додатку тут буде виклик Firebase Admin SDK.
"""

from datetime import datetime, timedelta

#Notifications Manager
class NotificationManager:
    """Перевірка та планування push-нагадувань (≤ 1 на добу на контакт)."""

    def __init__(self):
        # contact_id → datetime останнього push
        self._last_sent: dict[str, datetime] = {}

    # OPT-7
    def schedule_push(self, contact_id: str, contact_name: str) -> str | None:
        """Повертає текст нагадування або None, якщо ліміт вичерпано."""
        now = datetime.now()
        last = self._last_sent.get(contact_id)

        if last and (now - last) < timedelta(days=1):
            return None  # не більше 1 push за 24 год (FR-04)

        self._last_sent[contact_id] = now
        message = f"[Garden] Ne zabudj zv'jazatysja z {contact_name}!"
        print(f"[FCM STUB] -> {message}")
        return message

    def check_if_reminder_needed(
        self, contact_id: str, last_interaction_iso: str, frequency_days: int
    ) -> bool:
        last_dt = datetime.fromisoformat(last_interaction_iso)
        return (datetime.now() - last_dt) >= timedelta(days=frequency_days)
