FROM python:3.12-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо залежності та встановлюємо їх
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проєкту
COPY . .

# Створюємо директорію для persistent storage (HF Spaces)
RUN mkdir -p /data

# Hugging Face Spaces використовує порт 7860
EXPOSE 7860

# Запускаємо через gunicorn на порті 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "2", "app:app"]
