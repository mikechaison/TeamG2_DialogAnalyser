# Customer Support Chat Generator and Analyzer

This project is a pipeline for generating and automatically evaluating synthetic customer support dialogues. It uses the `gemini-3.0-flash-preview` model. To optimize performance and cost, the generation phase uses a `low` thinking level, while the analysis phase uses a `medium` thinking level. The default dataset size is 100 dialogues, which can be modified in the `config.py` file.

## Project Structure

* **`generate.py`**: The core script for dataset generation. It uses the `config.py` parameters to build prompt instructions via the Orchestrator LLM, and then simulates a chat between the Client and Support LLMs.
* **`analyze.py`**: The two-step analysis script. It reads `dataset.json` and runs the Multi-Agent pipeline (User State Analyzer followed by the Support Analyzer) to evaluate the interactions.
* **`evaluate.py`**: The scoring script. It compares the `dataset.json` (true labels) against `analysis_results.json` (predicted labels) using `scikit-learn` and outputs the metrics to `evaluation_report.txt`.
* **`config.py`**: Centralized configuration file. It contains the data dictionaries (Intents, Scenarios, Satisfaction levels), model parameters (temperature, model version, thinking levels), and the target dataset size.
* **`models.py`**: Contains all Pydantic schemas used to enforce structured JSON outputs from the Gemini API.
* **`prompts.py`**: Stores all system instructions and prompt templates used by the Orchestrator, Client, Support, and Analyzer LLMs.
* **`requirements.txt`**: A list of required Python dependencies.

## Architecture Overview

The system consists of three main components: Generator, Analyzer, and Evaluator.

### 1. Generator
The generation phase uses a multi-agent approach. First, an "Orchestrator" LLM receives a set of parameters to design a chat scenario. 

The parameters include:
* **Intent:** `payment_issues`, `technical_errors`, `account_access`, `tariff_questions`, `refunds`, `other`.
* **Satisfaction:** `satisfied`, `neutral`, `unsatisfied`.
* **Agent Mistakes:** `ignored_question`, `incorrect_info`, `rude_tone`, `no_resolution`, `unnecessary_escalation`.
* **Scenario:** `successful`, `problematic`, `conflict`, `agent_mistake`.
* **Client Persona Data:** Age, Profession, Tech Savviness, Tone, and Urgency.

Logical safeguards are implemented during parameter selection to prevent paradoxical situations (e.g., preventing a user from being 'satisfied' if the problem was not solved, or preventing a 60+ plumber from having 'expert' IT skills).

The Orchestrator returns a JSON object based on the following Pydantic schema:

```json
{
  "scenario_context": "A brief description of the generated situation.",
  "client_prompt": "The system prompt for the Client Agent, including persona and emotional state.",
  "support_prompt": "The system prompt for the Support Agent, including corporate guidelines and specific mistakes to make.",
  "first_message_hint": "A suggested opening line for the Client."
}

```

These prompts are then passed to two separate LLM instances (Client and Support) that chat with each other to generate the dialogue. The conversation is dynamic and continues until the Client LLM decides to end it. Based on its assigned satisfaction target and persona, the Client LLM will output a special `[END_CHAT]` marker when it determines the interaction has reached a natural conclusion. This marker automatically stops the simulation loop. 

The generated dataset is saved as a JSON file with the following schema:

```json
{
  "id": "chat_****",
  "true_labels": {
    "intent": "string",
    "scenario": "string",
    "satisfaction": "string",
    "agent_mistakes": ["string"],
    "age": "string",
    "profession": "string",
    "tech_savviness": "string",
    "tone": "string",
    "urgency": "string"
  },
  "orchestrator_context": "string",
  "dialogue": [
    {
      "role": "string (client or support)",
      "text": "string"
    }
  ]
}

```

### 2. Analyzer

The analyzer evaluates the generated transcripts using a two-step LLM pipeline to prevent context confusion.

* **Step 1 (User State Analyzer):** The first LLM call reads the full chat to determine the client's intent, their final satisfaction level, and writes a summary of the core issue.
* **Step 2 (Support Analyzer):** The second LLM call also receives the full chat and the output from Step 1. Knowing the user's final state allows this model to accurately identify specific agent mistakes and assign a quality score (1 to 5) without hallucinating errors (e.g., it will not assign `no_resolution` if the first model determined the user was `satisfied`).

The output from both steps is merged into a final JSON schema:

```json
{
  "id": "chat_****",
  "analysis": {
    "client_core_issue": "string",
    "reasoning": "string",
    "intent": "string",
    "satisfaction": "string",
    "quality_score": int (1-5),
    "agent_mistakes": ["string"]
  }
}

```

### 3. Evaluator

The evaluator script compares the `analysis_results.json` against the `true_labels` from `dataset.json`. It uses `scikit-learn` to calculate the following metrics:

* **Accuracy:** The overall percentage of correct predictions.
* **Precision:** The ratio of correctly predicted positive observations to the total predicted positives (measures hallucinations).
* **Recall:** The ratio of correctly predicted positive observations to all actual positives (measures missed cases).
* **F1-Score:** The weighted average of Precision and Recall.
* **Jaccard Score:** Used specifically for the `agent_mistakes` array to calculate the degree of partial matches between the expected and received arrays.

### Intent Classification

| Intent Category | Precision | Recall | F1-Score | Support |
| --- | --- | --- | --- | --- |
| `account_access` | 1.00 | 0.88 | 0.94 | 17 |
| `other` | 0.93 | 0.81 | 0.87 | 16 |
| `payment_issues` | 1.00 | 1.00 | 1.00 | 17 |
| `refunds` | 1.00 | 1.00 | 1.00 | 16 |
| `tariff_questions` | 0.89 | 1.00 | 0.94 | 17 |
| `technical_errors` | 0.79 | 0.88 | 0.83 | 17 |
| **Accuracy** |  |  | **0.93** | **100** |
| **Macro Avg** | 0.94 | 0.93 | 0.93 | 100 |
| **Weighted Avg** | 0.93 | 0.93 | 0.93 | 100 |

The model demonstrates high reliability in determining user intent, achieving an overall accuracy of 93%. Performance is consistent across all categories, with `payment_issues` and `refunds` achieving perfect F1-scores (1.00). Minor confusion occurs between `technical_errors` and `other`, which is typical for edge-case technical inquiries, but the macro average F1-score remains very strong at 0.93.

### Satisfaction Classification

| Satisfaction Level | Precision | Recall | F1-Score | Support |
| --- | --- | --- | --- | --- |
| `neutral` | 1.00 | 0.12 | 0.21 | 17 |
| `satisfied` | 0.63 | 1.00 | 0.77 | 17 |
| `unsatisfied` | 0.93 | 1.00 | 0.96 | 66 |
| **Accuracy** |  |  | **0.85** | **100** |
| **Macro Avg** | 0.85 | 0.71 | 0.65 | 100 |
| **Weighted Avg** | 0.89 | 0.85 | 0.80 | 100 |

The overall accuracy for satisfaction classification is 85%. The model is highly effective at identifying the `unsatisfied` state (F1-score: 0.96). However, the metrics reveal a specific difficulty in distinguishing between `neutral` and `satisfied` states. The model frequently misclassifies `neutral` dialogues as `satisfied`, resulting in a very low recall (0.12) for `neutral` and reduced precision (0.63) for `satisfied`.

### Agent Mistakes (Multi-Label)

**Average Jaccard Score (strict element match): 78.42%**

| Agent Mistake | Precision | Recall | F1-Score | Support |
| --- | --- | --- | --- | --- |
| `ignored_question` | 0.63 | 1.00 | 0.77 | 17 |
| `incorrect_info` | 0.89 | 0.62 | 0.73 | 13 |
| `rude_tone` | 0.68 | 1.00 | 0.81 | 15 |
| `no_resolution` | 0.33 | 0.56 | 0.42 | 16 |
| `unnecessary_escalation` | 1.00 | 0.50 | 0.67 | 18 |
| **Micro Avg** | 0.62 | 0.73 | 0.67 | 79 |
| **Macro Avg** | 0.71 | 0.74 | 0.68 | 79 |
| **Weighted Avg** | 0.71 | 0.73 | 0.68 | 79 |
| **Samples Avg** | 0.30 | 0.38 | 0.33 | 79 |

The multi-label classification achieves a strong Average Jaccard Score of 78.42%, indicating a high degree of overlap between predicted and actual mistakes per chat.

* The model excels at detecting `ignored_question` and `rude_tone` (Recall: 1.00 for both), meaning it rarely misses these errors.
* `Unnecessary_escalation` is identified with perfect precision (1.00), meaning there are no false positives, though it misses 50% of the actual occurrences.
* The primary weakness is the `no_resolution` category (Precision: 0.33, F1-score: 0.42), indicating a tendency to over-flag this mistake (false positives).

## How to Run with Docker

The project is fully containerized using Docker. You do not need to install Python or any dependencies on your local machine.

### Prerequisites

* Docker installed on your system.
* A Gemini API Key.

### 1. Setup the Environment Variable

Create a plain text file named `.env` in the root directory of the project (the same folder where the `Dockerfile` is located). Add your API key to this file:

```text
GEMINI_API_KEY=your_actual_api_key_here

```

*Note: This file is ignored by Docker during the build process for security reasons and is only passed at runtime.*

### 2. Build the Docker Image

Open your terminal in the project directory and build the image. This command installs all dependencies listed in `requirements.txt`:

```bash
docker build -t support-pipeline .

```

### 3. Run the Pipeline Stages

You can run each stage of the pipeline independently. The commands below use volume mapping (`-v`) to ensure that the generated JSON and TXT files are saved directly to your local machine.

**Step 1: Generate the Dataset**

```bash
docker run --rm --env-file .env -v "$(pwd):/app" support-pipeline python generate.py

```

*(This will create `dataset.json` in your directory).*

**Step 2: Run the Analyzer**

```bash
docker run --rm --env-file .env -v "$(pwd):/app" support-pipeline python analyze.py

```

*(This will read `dataset.json` and create `analysis_results.json`).*

**Step 3: Run the Evaluator**

```bash
docker run --rm -v "$(pwd):/app" support-pipeline python evaluate.py

```

*(This does not require the API key. It will read the JSON files and create an `evaluation_report.txt` with the final metrics).*

> **Windows Users:** If you are using PowerShell, replace `$(pwd)` with `${PWD}` in the commands above.
