import json
import os
import time
import google.generativeai as genai
from dotenv import load_dotenv

import config
import models
import prompts

# Завантажуємо API ключ
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def format_transcript(dialogue_list: list) -> str:
    """Перетворює список повідомлень у текстовий транскрипт для зручного читання моделлю."""
    transcript = ""
    for msg in dialogue_list:
        role = msg.get("role", "unknown").upper()
        text = msg.get("text", "")
        transcript += f"{role}: {text}\n"
    return transcript


def analyze_chat(transcript_text: str) -> dict:
    """Відправляє транскрипт до LLM і повертає структурований JSON з оцінкою."""
    model = genai.GenerativeModel(
        model_name=config.ANALYSIS_MODEL,
        system_instruction=prompts.ANALYZER_SYSTEM_PROMPT
    )

    # Використовуємо temperature=0.0 для детермінованості
    response = model.generate_content(
        f"Analyze the following transcript:\n\n{transcript_text}",
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=models.AnalysisOutput,
            temperature=config.ANALYSIS_TEMP
        )
    )

    return json.loads(response.text)


def main():
    print("Starting analysis phase...")

    # Читаємо згенерований датасет
    try:
        with open("dataset.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print("Error: dataset.json not found. Run generate.py first.")
        return

    analysis_results = []

    for i, chat in enumerate(dataset):
        print(f"[{i + 1}/{len(dataset)}] Analyzing {chat['id']}...")

        transcript_text = format_transcript(chat["dialogue"])

        try:
            # Отримуємо аналіз від моделі
            analysis_data = analyze_chat(transcript_text)

            # Збираємо фінальний об'єкт
            result_record = {
                "id": chat["id"],
                "analysis": analysis_data
                # Опціонально: можна додати "true_labels": chat["true_labels"]
                # для автоматичного розрахунку точності (Accuracy) вашого алгоритму
            }

            analysis_results.append(result_record)
            print(f"  -> Score: {analysis_data['quality_score']}, Intent: {analysis_data['intent']}")

        except Exception as e:
            print(f"  -> Error analyzing {chat['id']}: {e}")

    # Зберігаємо результати аналізу
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=4, ensure_ascii=False)

    print(f"\nDone! Analysis saved to analysis_results.json.")


if __name__ == "__main__":
    main()