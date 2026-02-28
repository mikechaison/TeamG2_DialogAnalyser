import json
from sklearn.metrics import classification_report
from sklearn.preprocessing import MultiLabelBinarizer


def load_json(filepath: str) -> list:
    """Loads a JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        return []


def main():
    print("Starting evaluation of results...\n")

    # 1. Load data
    dataset = load_json("dataset.json")
    results = load_json("analysis_results.json")

    if not dataset or not results:
        return

    # Create a map of ground-truth labels
    true_labels_map = {chat["id"]: chat["true_labels"] for chat in dataset}

    # Arrays for scikit-learn
    y_true_intent, y_pred_intent = [], []
    y_true_sat, y_pred_sat = [], []
    y_true_mistakes, y_pred_mistakes = [], []

    total_mistakes_score = 0.0  # To accumulate a custom Jaccard score

    print("-" * 65)
    print("DETAILED MISMATCH REPORT (Discrepancies):")
    print("-" * 65)

    # 2. Collect data and print mismatch logs
    for res in results:
        chat_id = res["id"]
        analysis = res["analysis"]
        truth = true_labels_map.get(chat_id)

        if not truth:
            print(f"Warning: true_labels not found for {chat_id}")
            continue

        # --- Collect Intent ---
        t_intent = truth["intent"]
        p_intent = analysis["intent"]
        y_true_intent.append(t_intent)
        y_pred_intent.append(p_intent)

        if p_intent != t_intent:
            print(f"[{chat_id}] Intent error: expected '{t_intent}', got '{p_intent}'")

        # --- Collect Satisfaction ---
        t_sat = truth["satisfaction"]
        p_sat = analysis["satisfaction"]
        y_true_sat.append(t_sat)
        y_pred_sat.append(p_sat)

        if p_sat != t_sat:
            print(f"[{chat_id}] Satisfaction error: expected '{t_sat}', got '{p_sat}'")

        # --- Collect Agent Mistakes ---
        t_mistakes = truth["agent_mistakes"]
        p_mistakes = analysis["agent_mistakes"]
        y_true_mistakes.append(t_mistakes)
        y_pred_mistakes.append(p_mistakes)

        # Log partial match (Jaccard) for debugging clarity
        set_t = set(t_mistakes)
        set_p = set(p_mistakes)
        intersection = set_t.intersection(set_p)
        union = set_t.union(set_p)

        if not set_t and not set_p:
            chat_mistake_score = 1.0
        elif not union:
            chat_mistake_score = 0.0
        else:
            chat_mistake_score = len(intersection) / len(union)

        total_mistakes_score += chat_mistake_score

        if chat_mistake_score < 1.0:
            print(f"[{chat_id}] Mistakes mismatch (Jaccard: {chat_mistake_score * 100:.1f}%):")
            print(f"    Expected: {list(set_t)}")
            print(f"    Received:    {list(set_p)}")

    total_chats = len(results)

    # 3. Prepare MultiLabelBinarizer for Mistakes
    # We explicitly set possible classes so the report is complete even if some mistakes are absent in the batch
    all_mistake_classes = [
        'ignored_question', 'incorrect_info', 'rude_tone',
        'no_resolution', 'unnecessary_escalation'
    ]
    mlb = MultiLabelBinarizer(classes=all_mistake_classes)

    # Convert lists like [['no_resolution'], ['rude_tone', 'ignored_question']] to binary matrices
    y_true_mistakes_bin = mlb.fit_transform(y_true_mistakes)
    y_pred_mistakes_bin = mlb.transform(y_pred_mistakes)

    # 4. Print metrics using sklearn.metrics.classification_report
    print("\n" + "=" * 65)
    print("FINAL METRICS (scikit-learn):")
    print("=" * 65)
    print(f"Total dialogues analyzed: {total_chats}\n")

    print("--- INTENT CLASSIFICATION ---")
    print(classification_report(y_true_intent, y_pred_intent, zero_division=0))

    print("--- SATISFACTION CLASSIFICATION ---")
    print(classification_report(y_true_sat, y_pred_sat, zero_division=0))

    print("--- AGENT MISTAKES (MULTI-LABEL) ---")
    print(f"Average Jaccard Score (strict element match): {(total_mistakes_score / total_chats) * 100:.2f}%\n")
    print(classification_report(
        y_true_mistakes_bin,
        y_pred_mistakes_bin,
        target_names=mlb.classes_,
        zero_division=0
    ))
    print("=" * 65)


if __name__ == "__main__":
    main()