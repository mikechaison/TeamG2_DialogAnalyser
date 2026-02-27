import os
import json
import random
import time
import google.generativeai as genai
from dotenv import load_dotenv

import config
import prompts
import models

# Load API key securely
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ==========================================
# PARAMETERS
# ==========================================
# The number of conversations to generate
DATASET_SIZE = 5


# ==========================================

def generate_random_config() -> dict:
    """Randomly selects parameters for the chat scenario based on requirements."""
    intent = random.choice(list(config.Intent)).value
    scenario = random.choice(list(config.CaseScenario)).value
    satisfaction = random.choice(list(config.Satisfaction)).value

    # Add agent mistakes only if the scenario implies it
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
        "patience": random.choice(["high", "medium", "low"]),
        "style": random.choice(["professional", "slang"]),
        "client_mistakes_lvl": random.randint(0, 5),
        "message_split_rate": random.randint(1, 3),
        "explanation_request_cnt": random.randint(0, 3)
    }


def get_orchestrator_instructions(chat_config: dict) -> dict:
    """Calls the Orchestrator to generate detailed prompts for the Client and Support agents."""
    model = genai.GenerativeModel(
        model_name=config.GENERATION_MODEL,
        system_instruction=prompts.ORCHESTRATOR_SYSTEM_PROMPT
    )

    mistakes_str = ", ".join(chat_config["agent_mistakes"]) if chat_config["agent_mistakes"] else "None"

    # Оновлюємо шаблон для передачі нових параметрів
    user_prompt = f"""
        Please generate the setup for the following configuration:
        - Intent: {chat_config['intent']}
        - Scenario Type: {chat_config['scenario']}
        - Target Satisfaction: {chat_config['satisfaction']}
        - Agent Mistakes: {mistakes_str}
        - Client Patience: {chat_config['patience']}
        - Communication Style: {chat_config['style']}
        - Typos Intensity: {chat_config['client_mistakes_lvl']} errors per message
        - Message Splitting: Split thoughts into {chat_config['message_split_rate']} messages
        - Tech Illiteracy: Client will ask to explain {chat_config['explanation_request_cnt']} terms
        """

    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=models.OrchestratorOutput,
            temperature=config.GENERATION_TEMP
        )
    )

    return json.loads(response.text)


def simulate_chat(instructions: dict) -> list:
    """Runs the ping-pong dialogue loop between two AI agents."""
    client_model = genai.GenerativeModel(
        model_name=config.GENERATION_MODEL,
        system_instruction=instructions["client_prompt"]
    )
    support_model = genai.GenerativeModel(
        model_name=config.GENERATION_MODEL,
        system_instruction=instructions["support_prompt"]
    )

    # Start chat sessions to keep dialogue history automatically
    client_chat = client_model.start_chat(history=[])
    support_chat = support_model.start_chat(history=[])

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


def main():
    print(f"Starting generation of {DATASET_SIZE} conversations...\n")
    dataset = []

    for i in range(DATASET_SIZE):
        print(f"[{i + 1}/{DATASET_SIZE}] Generating chat...")

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
                "true_labels": chat_config,  # The golden standard for analyze.py
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


if __name__ == "__main__":
    main()