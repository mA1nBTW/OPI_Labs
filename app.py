"""Garden — головний Flask-додаток.

Реалізує REST API для всіх функціональних вимог (FR-01…FR-05).
Запуск:  python app.py
"""

import os

from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import UserModel, Contact, VirtualPlant
from database import LocalDatabase
from notifications import NotificationManager

app = Flask(__name__)
db = LocalDatabase()
notifier = NotificationManager()


# ── Головна сторінка (Frontend) ──────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── FR-01  Реєстрація / Авторизація (OPT-3, OPT-4) ─────────────────────
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    if not data or not data.get("email") or not data.get("password"):
        return jsonify(error="Email and password are required"), 400

    email = data.get("email")
    password = data.get("password")

    if db.get_user_by_email(email):
        return jsonify(error="Email already registered"), 409

    hashed_pw = generate_password_hash(password)
    user = UserModel(email, hashed_pw)
    if not user.verify_account():
        return jsonify(error="Invalid data"), 400

    db.insert_user(user.user_id, user.email, user.password_hash)
    return jsonify(user.to_dict()), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if not data or not data.get("email") or not data.get("password"):
        return jsonify(error="Email and password are required"), 400

    email = data.get("email")
    password = data.get("password")

    user = db.get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Invalid credentials"), 401
    return jsonify(user_id=user["user_id"], email=user["email"])


# ── FR-02  Контакти (OPT-5) ─────────────────────────────────────────────
@app.route("/contacts", methods=["POST"])
def add_contact():
    data = request.json
    if not data or not data.get("user_id") or not data.get("name"):
        return jsonify(error="user_id and name are required"), 400

    user_id = data.get("user_id")
    name = data.get("name")
    reminder_frequency_days = data.get("reminder_frequency_days", 7)

    contact = Contact(name, reminder_frequency_days)
    db.insert_contact(user_id, contact)

    # Автоматично створюємо рослину для контакту
    plant = VirtualPlant(contact.contact_id)
    db.insert_plant(plant)

    return jsonify(contact=contact.to_dict(), plant=plant.to_dict()), 201


@app.route("/contacts/<user_id>", methods=["GET"])
def list_contacts(user_id: str):
    return jsonify(db.get_contacts(user_id))


@app.route("/contacts/<contact_id>", methods=["PUT"])
def edit_contact(contact_id: str):
    data = request.json
    if not data or not data.get("name") or data.get("reminder_frequency_days") is None:
        return jsonify(error="name and reminder_frequency_days are required"), 400

    name = data.get("name")
    reminder_frequency_days = data.get("reminder_frequency_days")

    db.update_contact(contact_id, name, reminder_frequency_days)
    return jsonify(ok=True)


@app.route("/contacts/<contact_id>", methods=["DELETE"])
def delete_contact(contact_id: str):
    db.delete_contact(contact_id)
    return jsonify(ok=True)


# ── FR-03  Сад (OPT-13, OPT-14) ────────────────────────────────────────
@app.route("/garden/<user_id>", methods=["GET"])
def view_garden(user_id: str):
    """Повертає масив рослин з прив'язаними контактами."""
    plants = db.get_all_plants(user_id)
    contacts = {c["contact_id"]: c for c in db.get_contacts(user_id)}

    garden = []
    for p in plants:
        info = contacts.get(p["contact_id"], {})
        garden.append({**p, "contact_name": info.get("name", "?")})
    return jsonify(garden)


# ── FR-05  Відправка медіа (Sequence Diagram) ───────────────────────────
@app.route("/send_media", methods=["POST"])
def send_media():
    """
    Крок 5 — діаграма послідовності:
    1. Отримуємо фото
    2. Зберігаємо взаємодію
    3. Збільшуємо рослину (OPT-13)
    """
    if "contact_id" not in request.form:
        return jsonify(error="contact_id is required"), 400

    contact_id = request.form["contact_id"]

    # 1 — зберігаємо файл
    file = request.files.get("photo")
    media_path = None
    if file:
        filename = secure_filename(file.filename)
        media_path = os.path.join(UPLOAD_DIR, f"{contact_id}_{filename}")
        file.save(media_path)

    # 2 — updateInteractionHistory
    db.add_interaction(contact_id, media_path)

    # 3 — calculateNewPlantLevel → animate_growth
    plant_row = db.get_plant(contact_id)
    if plant_row:
        plant = VirtualPlant(contact_id)
        plant.plant_id = plant_row["plant_id"]
        plant.growth_level = plant_row["growth_level"]
        new_level = plant.animate_growth()
        db.update_plant_state(plant)
        return jsonify(new_growth_level=new_level, media_saved=media_path)

    return jsonify(error="Plant not found"), 404


# ── FR-04  Push-нагадування (OPT-7, OPT-8) ─────────────────────────────
@app.route("/check_reminders/<user_id>", methods=["POST"])
def check_reminders(user_id: str):
    """Перевіряє всіх контактів і надсилає нагадування (≤ 1/добу)."""
    contacts = db.get_contacts(user_id)
    sent = []
    for c in contacts:
        interactions = db.get_interactions(c["contact_id"])
        last_iso = interactions[0]["timestamp"] if interactions else "2000-01-01T00:00:00"

        if notifier.check_if_reminder_needed(
            c["contact_id"], last_iso, c["reminder_frequency_days"]
        ):
            msg = notifier.schedule_push(c["contact_id"], c["name"])
            if msg:
                sent.append({"contact": c["name"], "contact_id": c["contact_id"], "message": msg})

    return jsonify(reminders_sent=sent)


# ── FR-10  Історія взаємодій ─────────────────────────────────────────────
@app.route("/interactions/<contact_id>", methods=["GET"])
def interaction_history(contact_id: str):
    return jsonify(db.get_interactions(contact_id))


# ── FR-08  Чат / повідомлення ────────────────────────────────────────────
@app.route("/messages/<contact_id>", methods=["GET"])
def get_messages(contact_id: str):
    return jsonify(db.get_messages(contact_id))


@app.route("/messages", methods=["POST"])
def send_message():
    data = request.json
    if not data or not data.get("contact_id") or not data.get("content"):
        return jsonify(error="contact_id and content are required"), 400

    contact_id = data.get("contact_id")
    content = data.get("content")
    sender = data.get("sender", "user")

    msg = db.insert_message(contact_id, sender, content)

    # Кожне повідомлення також рахується як взаємодія (рослина росте)
    db.add_interaction(contact_id)
    plant_row = db.get_plant(contact_id)
    if plant_row:
        plant = VirtualPlant(contact_id)
        plant.plant_id = plant_row["plant_id"]
        plant.growth_level = plant_row["growth_level"]
        plant.animate_growth()
        db.update_plant_state(plant)

    return jsonify(msg), 201


# ─────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")
    port = int(os.getenv("PORT", 5000))
    app.run(debug=debug, port=port)
