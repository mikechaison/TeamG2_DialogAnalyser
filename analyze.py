import json
import os
import time
from dotenv import load_dotenv

# Правильні імпорти для нового SDK
from google import genai
from google.genai import types

import config
import models
import prompts

# Завантажуємо змінні середовища
load_dotenv()
# Клієнт автоматично підхопить ключ GEMINI_API_KEY з файлу .env
client = genai.Client()


def format_transcript(dialogue_list: list) -> str:
    transcript = ""
    for msg in dialogue_list:
        role = msg.get("role", "unknown").upper()
        text = msg.get("text", "")
        transcript += f"{role}: {text}\n"
    return transcript

def _call_llm(prompt: str, response_schema):
    """Допоміжна функція для одного запиту до LLM."""
    response = client.models.generate_content(
        model=config.ANALYSIS_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=config.ANALYSIS_TEMP,
            response_mime_type="application/json",
            response_schema=response_schema,
            thinking_config={"thinking_level": config.THINKING_LEVEL}
        )
    )
    return json.loads(response.text)

def analyze_chat(transcript_text: str) -> dict:
    """Аналізує чат покроково, викликаючи модель для кожного аспекту окремо."""

    context = prompts.BASE_CONTEXT.format(transcript_text=transcript_text)

    intent_res = _call_llm(context + prompts.INTENT_PROMPT, models.IntentOutput)

    sat_res = _call_llm(context + prompts.SATISFACTION_PROMPT, models.SatisfactionOutput)

    mistakes_res = _call_llm(context + prompts.MISTAKES_PROMPT, models.MistakesOutput)

    score_context = (
        f"{context}\n"
        f"Intent found: {intent_res.get('intent')}\n"
        f"Satisfaction found: {sat_res.get('satisfaction')}\n"
        f"Agent mistakes found: {mistakes_res.get('mistakes')}\n"
    )
    score_res = _call_llm(score_context + prompts.SCORE_PROMPT, models.ScoreOutput)

    # Фінальний результат
    final_analysis = {
        "intent": intent_res.get("intent"),
        "satisfaction": sat_res.get("satisfaction"),
        "agent_mistakes": mistakes_res.get("mistakes", []),
        "quality_score": score_res.get("score"),
        "reasoning": {
            "intent": intent_res.get("reasoning"),
            "satisfaction": sat_res.get("reasoning"),
            "mistakes": mistakes_res.get("reasoning"),
            "score": score_res.get("reasoning")
        }
    }
    
    return final_analysis


if __name__ == "__main__":
    print("Starting analysis phase...")

    # Читаємо згенерований датасет
    try:
        with open("dataset.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print("Error: dataset.json not found. Run generate.py first.")
        exit(1)

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
            }

            analysis_results.append(result_record)
            print(f"  -> Score: {analysis_data['quality_score']}, Intent: {analysis_data['intent']}")


        except Exception as e:
            print(f"  -> Error analyzing {chat['id']}: {e}")

            # Зберігаємо результати аналізу
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=4, ensure_ascii=False)

    print(f"\nDone! Analysis saved to analysis_results.json.")