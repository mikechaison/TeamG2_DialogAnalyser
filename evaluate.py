import json
from collections import defaultdict


def load_json(filepath: str) -> list:
    """Завантажує JSON файл."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Помилка: Файл {filepath} не знайдено.")
        return []


def calculate_macro_metrics(metrics_dict):
    """Рахує Macro Precision, Recall та F1 для мультикласової класифікації."""
    classes = set(metrics_dict['tp'].keys()) | set(metrics_dict['fp'].keys()) | set(metrics_dict['fn'].keys())
    if not classes:
        return 0.0, 0.0, 0.0

    macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
    for c in classes:
        tp = metrics_dict['tp'][c]
        fp = metrics_dict['fp'][c]
        fn = metrics_dict['fn'][c]

        p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

        macro_p += p
        macro_r += r
        macro_f1 += f1

    n = len(classes)
    return macro_p / n, macro_r / n, macro_f1 / n


def calculate_micro_metrics(tp, fp, fn):
    """Рахує Micro Precision, Recall та F1 для мультилейбл класифікації."""
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    return p, r, f1


def main():
    print("Початок оцінки результатів (Evaluation)...\n")

    # 1. Завантажуємо дані
    dataset = load_json("dataset.json")
    results = load_json("analysis_results.json")

    if not dataset or not results:
        return

    # Створюємо словник з правильними відповідями
    true_labels_map = {chat["id"]: chat["true_labels"] for chat in dataset}

    total_chats = len(results)
    correct_intent = 0
    correct_satisfaction = 0
    total_mistakes_score = 0.0  # Для Jaccard Similarity

    # Словники для підрахунку TP, FP, FN по класах
    intent_metrics = {'tp': defaultdict(int), 'fp': defaultdict(int), 'fn': defaultdict(int)}
    sat_metrics = {'tp': defaultdict(int), 'fp': defaultdict(int), 'fn': defaultdict(int)}

    # Змінні для підрахунку Mistakes
    mistakes_tp = 0
    mistakes_fp = 0
    mistakes_fn = 0

    print("-" * 50)
    print("ДЕТАЛЬНИЙ ЗВІТ ПО ПОМИЛКАХ:")
    print("-" * 50)

    # 2. Порівнюємо результати
    for res in results:
        chat_id = res["id"]
        analysis = res["analysis"]
        truth = true_labels_map.get(chat_id)

        if not truth:
            print(f"Попередження: Не знайдено true_labels для {chat_id}")
            continue

        # --- Перевірка Intent ---
        t_intent = truth["intent"]
        p_intent = analysis["intent"]
        if p_intent == t_intent:
            correct_intent += 1
            intent_metrics['tp'][t_intent] += 1
        else:
            intent_metrics['fn'][t_intent] += 1
            intent_metrics['fp'][p_intent] += 1
            print(f"[{chat_id}] Помилка Intent: Очікувалось '{t_intent}', отримано '{p_intent}'")

        # --- Перевірка Satisfaction ---
        t_sat = truth["satisfaction"]
        p_sat = analysis["satisfaction"]
        if p_sat == t_sat:
            correct_satisfaction += 1
            sat_metrics['tp'][t_sat] += 1
        else:
            sat_metrics['fn'][t_sat] += 1
            sat_metrics['fp'][p_sat] += 1
            print(f"[{chat_id}] Помилка Satisfaction: Очікувалось '{t_sat}', отримано '{p_sat}'")

        # --- Перевірка Agent Mistakes ---
        truth_mistakes = set(truth["agent_mistakes"])
        analysis_mistakes = set(analysis["agent_mistakes"])

        intersection = truth_mistakes.intersection(analysis_mistakes)
        union = truth_mistakes.union(analysis_mistakes)

        # Рахуємо Jaccard Score (Бал)
        if not truth_mistakes and not analysis_mistakes:
            chat_mistake_score = 1.0
        elif not union:
            chat_mistake_score = 0.0
        else:
            chat_mistake_score = len(intersection) / len(union)

        total_mistakes_score += chat_mistake_score

        # Збираємо TP, FP, FN для Mistakes
        mistakes_tp += len(intersection)
        mistakes_fp += len(analysis_mistakes - truth_mistakes)  # Знайдено, але їх там не було (Галюцинації)
        mistakes_fn += len(truth_mistakes - analysis_mistakes)  # Були, але не знайдено (Пропуски)

        # Виводимо лог, якщо збіг не 100%
        if chat_mistake_score < 1.0:
            print(f"[{chat_id}] Частковий/Хибний збіг Mistakes (Бал: {chat_mistake_score * 100:.1f}%):")
            print(f"    Очікувалось: {list(truth_mistakes)}")
            print(f"    Отримано:    {list(analysis_mistakes)}")

    # Обчислення метрик
    intent_acc = (correct_intent / total_chats) * 100
    intent_p, intent_r, intent_f1 = calculate_macro_metrics(intent_metrics)

    sat_acc = (correct_satisfaction / total_chats) * 100
    sat_p, sat_r, sat_f1 = calculate_macro_metrics(sat_metrics)

    mist_acc = (total_mistakes_score / total_chats) * 100  # Jaccard
    mist_p, mist_r, mist_f1 = calculate_micro_metrics(mistakes_tp, mistakes_fp, mistakes_fn)

    # 3. Вивід фінальних метрик
    print("\n" + "=" * 65)
    print("ФІНАЛЬНІ МЕТРИКИ (ACCURACY, PRECISION, RECALL, F1):")
    print("=" * 65)
    print(f"Всього проаналізовано діалогів: {total_chats}")
    print("-" * 65)

    print(f"INTENT (Macro Avg):")
    print(f"  Accuracy:  {intent_acc:.2f}%")
    print(f"  Precision: {intent_p * 100:.2f}% | Recall: {intent_r * 100:.2f}% | F1-Score: {intent_f1 * 100:.2f}%")
    print("-" * 65)

    print(f"SATISFACTION (Macro Avg):")
    print(f"  Accuracy:  {sat_acc:.2f}%")
    print(f"  Precision: {sat_p * 100:.2f}% | Recall: {sat_r * 100:.2f}% | F1-Score: {sat_f1 * 100:.2f}%")
    print("-" * 65)

    print(f"AGENT MISTAKES (Micro Avg & Jaccard):")
    print(f"  Jaccard Accuracy (Ступінь часткового збігу): {mist_acc:.2f}%")
    print(f"  Precision: {mist_p * 100:.2f}% | Recall: {mist_r * 100:.2f}% | F1-Score: {mist_f1 * 100:.2f}%")
    print("=" * 65)


if __name__ == "__main__":
    main()