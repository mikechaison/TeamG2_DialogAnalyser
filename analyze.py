import json
from dotenv import load_dotenv

# Correct imports for the new SDK
from google import genai
from google.genai import types

import config
import models
import prompts

# Load environment variables
load_dotenv()
# Client will automatically pick up GEMINI_API_KEY from .env
client = genai.Client()


def format_transcript(dialogue_list: list) -> str:
    transcript = ""
    for msg in dialogue_list:
        role = msg.get("role", "unknown").upper()
        text = msg.get("text", "")
        transcript += f"{role}: {text}\n"
    return transcript


def analyze_chat(transcript_text: str) -> dict:
    """Sends the transcript to the LLM using the new SDK."""

    response = client.models.generate_content(
        model=config.ANALYSIS_MODEL,
        contents=f"Analyze the following chat:\n\n{transcript_text}",
        config=types.GenerateContentConfig(
            system_instruction=prompts.ANALYZER_SYSTEM_PROMPT,
            temperature=config.ANALYSIS_TEMP,
            response_mime_type="application/json",
            response_schema=models.AnalysisOutput,
            thinking_config={"thinking_level": config.ANALYZE_THINKING_LEVEL}
        )
    )

    return json.loads(response.text)


if __name__ == "__main__":
    print("Starting analysis phase...")

    # Read the generated dataset
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
            # Get analysis from the model
            analysis_data = analyze_chat(transcript_text)

            # Assemble the final object
            result_record = {
                "id": chat["id"],
                "analysis": analysis_data
            }

            analysis_results.append(result_record)
            print(f"  -> Score: {analysis_data['quality_score']}, Intent: {analysis_data['intent']}")


        except Exception as e:
            print(f"  -> Error analyzing {chat['id']}: {e}")

            # Save analysis results
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=4, ensure_ascii=False)

    print(f"\nDone! Analysis saved to analysis_results.json.")