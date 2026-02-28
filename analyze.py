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


def analyze_user_state(transcript_text: str) -> dict:
    """Step 1: Analyzes the chat to determine intent and customer satisfaction ONLY."""

    response = client.models.generate_content(
        model=config.ANALYSIS_MODEL,
        contents=f"Analyze the client's state in the following chat:\n\n{transcript_text}",
        config=types.GenerateContentConfig(
            system_instruction=prompts.USER_STATE_ANALYZER_PROMPT,
            temperature=config.ANALYSIS_TEMP,
            response_mime_type="application/json",
            response_schema=models.UserStateOutput,
            thinking_config={"thinking_level": config.ANALYZE_THINKING_LEVEL}
        )
    )
    return json.loads(response.text)


def analyze_agent_performance(transcript_text: str, user_state: dict) -> dict:
    """Step 2: Analyzes the agent's performance using the context from Step 1."""

    # We feed the results of the first agent directly into the prompt of the second agent
    context_payload = (
        f"--- PRE-ANALYZED USER STATE ---\n"
        f"Intent: {user_state['intent']}\n"
        f"Final Satisfaction: {user_state['satisfaction']}\n"
        f"Client Core Issue Summary: {user_state['client_core_issue']}\n\n"
        f"--- CHAT TRANSCRIPT ---\n"
        f"{transcript_text}"
    )

    response = client.models.generate_content(
        model=config.ANALYSIS_MODEL,
        contents=f"Audit the support agent's performance based on this context and transcript:\n\n{context_payload}",
        config=types.GenerateContentConfig(
            system_instruction=prompts.QA_AUDITOR_PROMPT,
            temperature=config.ANALYSIS_TEMP,
            response_mime_type="application/json",
            response_schema=models.QAAuditorOutput,
            thinking_config={"thinking_level": config.ANALYZE_THINKING_LEVEL}
        )
    )
    return json.loads(response.text)


if __name__ == "__main__":
    print("Starting Multi-Agent Analysis Phase...")

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
            # Step 1: Get User State
            state_data = analyze_user_state(transcript_text)

            # Step 2: Get Agent Audit based on User State
            audit_data = analyze_agent_performance(transcript_text, state_data)

            # Combine the results into a single output object that matches original expectations
            final_analysis = {
                "client_core_issue": state_data["client_core_issue"],
                "reasoning": audit_data["reasoning"],
                "intent": state_data["intent"],
                "satisfaction": state_data["satisfaction"],
                "quality_score": audit_data["quality_score"],
                "agent_mistakes": audit_data["agent_mistakes"]
            }

            result_record = {
                "id": chat["id"],
                "analysis": final_analysis
            }

            analysis_results.append(result_record)
            print(
                f"  -> Intent: {final_analysis['intent']}, Satisfaction: {final_analysis['satisfaction']}, Mistakes: {final_analysis['agent_mistakes']}")

        except Exception as e:
            print(f"  -> Error analyzing {chat['id']}: {e}")

    # Save analysis results
    with open("analysis_results.json", "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=4, ensure_ascii=False)

    print(f"\nDone! Analysis saved to analysis_results.json.")