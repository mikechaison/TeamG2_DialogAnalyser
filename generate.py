import os
import json
import random
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

import config
import prompts
import models

load_dotenv()
client = genai.Client()


# ==========================================

def generate_random_config() -> dict:
    """Randomly selects ALL parameters for the chat scenario, including persona."""
    intent = random.choice(list(config.Intent)).value
    scenario = random.choice(list(config.CaseScenario)).value
    satisfaction = random.choice(list(config.Satisfaction)).value

    mistakes = []
    if scenario in [config.CaseScenario.AGENT_MISTAKE.value, config.CaseScenario.CONFLICT.value,
                    config.CaseScenario.PROBLEMATIC.value]:
        num_mistakes = random.randint(1, 2)
        mistakes = [m.value for m in random.sample(list(config.AgentMistake), k=num_mistakes)]

    return {
        "intent": intent,
        "scenario": scenario,
        "satisfaction": satisfaction,
        "agent_mistakes": mistakes,
        "age": random.choice(config.CLIENT_AGES),
        "profession": random.choice(config.CLIENT_PROFESSIONS),
        "tech_savviness": random.choice(config.TECH_SAVVINESS),
        "tone": random.choice(config.CLIENT_TONES),
        "urgency": random.choice(config.URGENCY_LEVELS)
    }


def get_orchestrator_instructions(chat_config: dict) -> dict:
    """Отримує системні промпти від Оркестратора використовуючи новий SDK."""
    mistakes_str = ", ".join(chat_config["agent_mistakes"]) if chat_config["agent_mistakes"] else "None"

    user_prompt = prompts.ORCHESTRATOR_USER_TEMPLATE.format(
        intent=chat_config["intent"],
        scenario=chat_config["scenario"],
        satisfaction=chat_config["satisfaction"],
        mistakes=mistakes_str,
        age=chat_config["age"],
        profession=chat_config["profession"],
        tech_savviness=chat_config["tech_savviness"],
        tone=chat_config["tone"],
        urgency=chat_config["urgency"]
    )

    response = client.models.generate_content(
        model=config.GENERATION_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=prompts.ORCHESTRATOR_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=models.OrchestratorOutput,
            temperature=config.GENERATION_TEMP,
            thinking_config={"thinking_level": config.THINKING_LEVEL}
        )
    )

    return json.loads(response.text)


def simulate_chat(instructions: dict) -> list:
    """Запускає цикл спілкування (Ping-Pong Loop) між агентами через новий SDK."""

    # Створюємо сесію чату для агента-клієнта
    client_chat = client.chats.create(
        model=config.GENERATION_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=instructions["client_prompt"],
            temperature=config.GENERATION_TEMP,
            thinking_config={"thinking_level": config.THINKING_LEVEL}
        )
    )

    # Створюємо сесію чату для агента-сапорта
    support_chat = client.chats.create(
        model=config.GENERATION_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=instructions["support_prompt"],
            temperature=config.GENERATION_TEMP
        )
    )

    transcript = []

    # 1. The Client sends the first message
    current_input = instructions["first_message_hint"]
    transcript.append({"role": "client", "text": current_input})

    for turn in range(config.MAX_CHAT_TURNS):
        # 2. Support Agent replies
        support_response = support_chat.send_message(current_input)
        transcript.append({"role": "support", "text": support_response.text})
        current_input = support_response.text

        # 3. Client Agent replies
        client_response = client_chat.send_message(current_input)
        client_text = client_response.text

        # Check for the stopping criterion provided by the Orchestrator
        if "[END_CHAT]" in client_text:
            clean_text = client_text.replace("[END_CHAT]", "").strip()
            if clean_text:
                transcript.append({"role": "client", "text": clean_text})
            break

        transcript.append({"role": "client", "text": client_text})
        current_input = client_text

    return transcript


if __name__ == "__main__":
    print(f"Starting generation of {config.DATASET_SIZE} conversations...\n")
    dataset = []

    for i in range(config.DATASET_SIZE):
        print(f"[{i + 1}/{config.DATASET_SIZE}] Generating chat...")

        try:
            # 1. Define conditions
            chat_config = generate_random_config()
            print(f"  -> Config: {chat_config['intent']} | {chat_config['scenario']} | {chat_config['satisfaction']}")

            # 2. Get roles from Orchestrator
            instructions = get_orchestrator_instructions(chat_config)

            # 3. Run Simulation
            transcript = simulate_chat(instructions)

            # 4. Save to dataset with ground truth labels
            chat_record = {
                "id": f"chat_{i + 1:04d}",
                "true_labels": chat_config,
                "orchestrator_context": instructions["scenario_context"],
                "dialogue": transcript
            }
            dataset.append(chat_record)
            print(f"  -> Success! Turns: {len(transcript)}")

        except Exception as e:
            print(f"  -> Error during generation: {e}")

    # Save the final dataset
    with open("dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=4, ensure_ascii=False)

    print(f"\nDone! Dataset saved to dataset.json with {len(dataset)} records.")