import json
import random
from google import genai
from google.genai import types
from dotenv import load_dotenv

import config
import prompts
import models

load_dotenv()
client = genai.Client()


def generate_balanced_config(index: int) -> dict:
    """Selects parameters using a round-robin approach with a 50% focus on agent mistakes."""

    # 1. Intents cycle through in round-robin
    all_intents = [i.value for i in config.Intent]
    intent = all_intents[index % len(all_intents)]

    # 2. BALANCED SCENARIO SELECTION (50% of dialogues will contain mistakes)
    # Alternate normal scenarios with agent-mistake scenarios
    scenario_cycle = [
        config.CaseScenario.SUCCESSFUL.value,
        "AGENT_MISTAKE",  # Mistake!
        config.CaseScenario.PROBLEMATIC.value,
        "AGENT_MISTAKE",  # Mistake!
        config.CaseScenario.CONFLICT.value,
        "AGENT_MISTAKE"  # Mistake!
    ]
    scenario = scenario_cycle[index % len(scenario_cycle)]
    mistakes = []

    if scenario == config.CaseScenario.SUCCESSFUL.value:
        satisfaction = config.Satisfaction.SATISFIED.value
        tone_choices = ["polite", "confused", "rushed"]

    elif scenario == config.CaseScenario.PROBLEMATIC.value:
        satisfaction = config.Satisfaction.NEUTRAL.value
        tone_choices = ["polite", "confused"]

    elif scenario == config.CaseScenario.CONFLICT.value:
        satisfaction = config.Satisfaction.UNSATISFIED.value
        tone_choices = ["frustrated", "passive-aggressive", "anxious/panicked"]

    else:  # AGENT_MISTAKE
        satisfaction = config.Satisfaction.UNSATISFIED.value
        tone_choices = config.CLIENT_TONES

        # 3. EVEN DISTRIBUTION OF MISTAKES
        all_mistakes = [m.value for m in config.AgentMistake]

        # Use integer division (index // 2) because mistakes occur every other slot.
        # This ensures we cycle through all 5 mistakes smoothly without duplicates.
        mistake_index = (index // 2) % len(all_mistakes)
        primary_mistake = all_mistakes[mistake_index]
        mistakes = [primary_mistake]

        # 40% chance to add a second mistake (to make analysis more interesting)
        if random.random() < 0.50:
            available_second = [m for m in all_mistakes if m != primary_mistake]
            second_mistake = random.choice(available_second)
            mistakes.append(second_mistake)

    tone = random.choice(tone_choices)

    if intent == config.Intent.ACCOUNT_ACCESS.value:
        urgency = random.choice(["high (blocking work/life)", "critical (losing money/time)"])
    elif intent == config.Intent.TARIFF_QUESTIONS.value:
        urgency = random.choice(["low (just asking)", "medium (needs it soon)"])
    else:
        urgency = random.choice(config.URGENCY_LEVELS)

    profession = random.choice(config.CLIENT_PROFESSIONS)
    tech_roles = ["software engineer", "data scientist", "QA tester", "system administrator", "UX/UI designer",
                  "crypto trader"]
    manual_roles = ["construction worker", "mechanic", "farmer", "truck driver", "chef", "plumber", "retired"]

    if profession in tech_roles:
        tech_savviness = random.choice(["high (experienced user)", "expert (developer/IT)"])
    elif profession in manual_roles:
        tech_savviness = random.choice(["low (struggles with basic UI)", "medium (knows basics)"])
    else:
        tech_savviness = random.choice(config.TECH_SAVVINESS)

    age = random.choice(config.CLIENT_AGES)

    return {
        "intent": intent,
        "scenario": scenario,
        "satisfaction": satisfaction,
        "agent_mistakes": mistakes,
        "age": age,
        "profession": profession,
        "tech_savviness": tech_savviness,
        "tone": tone,
        "urgency": urgency
    }


def get_orchestrator_instructions(chat_config: dict) -> dict:
    """Retrieve system prompts from the Orchestrator using the new SDK."""
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
            thinking_config={"thinking_level": config.GEN_THINKING_LEVEL}
        )
    )

    return json.loads(response.text)


def simulate_chat(instructions: dict) -> list:
    """Runs the chat loop producing separated message bubbles ([ENTER])."""

    client_chat = client.chats.create(
        model=config.GENERATION_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=instructions["client_prompt"],
            temperature=config.GENERATION_TEMP
        )
    )

    support_chat = client.chats.create(
        model=config.GENERATION_MODEL,
        config=types.GenerateContentConfig(
            system_instruction=instructions["support_prompt"],
            temperature=config.GENERATION_TEMP
        )
    )

    transcript = []

    # 1. First Client message (Orchestrator may also generate it with [ENTER])
    current_input = instructions["first_message_hint"]

    # Split the first message into bubbles
    for msg in current_input.split("[ENTER]"):
        clean_msg = msg.strip()
        if clean_msg:
            transcript.append({"role": "client", "text": clean_msg})

    for turn in range(config.MAX_CHAT_TURNS):
        # 2. Support response
        support_response = support_chat.send_message(current_input)

        # Split support response into separate bubbles
        support_messages = support_response.text.split("[ENTER]")
        for msg in support_messages:
            clean_msg = msg.strip()
            if clean_msg:
                transcript.append({"role": "support", "text": clean_msg})

        # Pass original text with [ENTER] back to the client so it understands "pause" context
        current_input = support_response.text

        # 3. Client response
        client_response = client_chat.send_message(current_input)
        client_text = client_response.text

        is_end = False
        if "[END_CHAT]" in client_text:
            is_end = True
            # Remove the end marker before splitting
            client_text = client_text.replace("[END_CHAT]", "").strip()

        # Split client response into separate bubbles
        client_messages = client_text.split("[ENTER]")
        for msg in client_messages:
            clean_msg = msg.strip()
            if clean_msg:
                transcript.append({"role": "client", "text": clean_msg})

        current_input = client_text

        if is_end:
            break

    return transcript


if __name__ == "__main__":
    print(f"Starting generation of {config.DATASET_SIZE} conversations...\n")
    dataset = []

    for i in range(config.DATASET_SIZE):
        print(f"[{i + 1}/{config.DATASET_SIZE}] Generating chat...")

        try:
            chat_config = generate_balanced_config(i)
            print(f"  -> Config: {chat_config['intent']} | {chat_config['scenario']} | {chat_config['satisfaction']} | Mistakes: {chat_config['agent_mistakes']}")
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