---
title: Garden
emoji: 🌱
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# Garden 🌱

Мобільний застосунок для підтримки особистих стосунків з рідними та близькими.

## Встановлення та запуск

```bash
pip install -r requirements.txt
python app.py
```

Сервер стартує на `http://localhost:5000`.

## API-ендпоінти

| Метод | URL | Опис | Вимога |
|-------|-----|------|--------|
| POST | `/register` | Реєстрація (email + password) | FR-01 |
| POST | `/login` | Авторизація | FR-01 |
| POST | `/contacts` | Додати контакт (+ створює рослину) | FR-02 |
| GET | `/contacts/<user_id>` | Список контактів | FR-02 |
| DELETE | `/contacts/<contact_id>` | Видалити контакт | FR-09 |
| GET | `/garden/<user_id>` | Перегляд саду | FR-03 |
| POST | `/send_media` | Відправити фото контакту | FR-05 |
| POST | `/check_reminders/<user_id>` | Перевірити нагадування | FR-04 |
| GET | `/interactions/<contact_id>` | Історія взаємодій | FR-10 |

## Приклади запитів (curl)

```bash
# Реєстрація
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'

# Додати контакт
curl -X POST http://localhost:5000/contacts \
  -H "Content-Type: application/json" \
  -d '{"user_id":"<UUID>","name":"Мама","reminder_frequency_days":3}'

# Переглянути сад
curl http://localhost:5000/garden/<UUID>

# Відправити фото
curl -X POST http://localhost:5000/send_media \
  -F "contact_id=<UUID>" \
  -F "photo=@photo.jpg"
```
