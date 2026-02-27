import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

# Завантажуємо змінні з файлу .env
load_dotenv()

# Отримуємо ключ безпечним шляхом
GOOGLE_API_KEY = "AIzaSyBHgIKNUuFUZQRluhNzSHwqcTOCaHaGAnY"

if not GOOGLE_API_KEY:
    raise ValueError("API ключ не знайдено! Перевір файл .env")

# Конфігуруємо API
genai.configure(api_key=GOOGLE_API_KEY)

# Ініціалізуємо модель
model = genai.GenerativeModel('gemini-2.5-flash')

print("--- ТЕСТ 1: Звичайна генерація тексту ---")
# Це підхід для вашого generate.py
prompt_chat = "Напиши одну коротку репліку клієнта служби підтримки, який незадоволений тим, що його оплата не пройшла."

response = model.generate_content(prompt_chat)
print("Відповідь моделі:\n", response.text)
print("-" * 40)


print("\n--- ТЕСТ 2: Структурований вивід (JSON) ---")
# Це підхід для вашого analyze.py, де потрібен суворий формат
prompt_analyze = """
Проаналізуй цей текст: "Я вже втретє вам пишу! Гроші зняло, а підписки немає. Поверніть кошти негайно!"
Поверни результат у форматі JSON з такими полями:
- "intent": категорія звернення
- "satisfaction": рівень задоволеності клієнта
"""

# Використовуємо response_mime_type щоб примусити модель видати валідний JSON
response_json = model.generate_content(
    prompt_analyze,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.0 # Для детермінованості ставимо температуру на 0
    )
)

print("Сирий JSON від моделі:\n", response_json.text)

# Перевіряємо, чи парситься це в Python словник
try:
    parsed_data = json.loads(response_json.text)
    print("\nУспішно розпарсено в словник. Intent:", parsed_data.get("intent"))
except json.JSONDecodeError:
    print("\nПомилка: Модель повернула невалідний JSON.")