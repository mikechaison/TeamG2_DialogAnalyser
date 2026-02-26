import json

def load_json(filepath: str) -> list:
    """Завантажує JSON файл."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Помилка: Файл {filepath} не знайдено.")
        return []

def main():
    print("Початок оцінки результатів (Evaluation)...\n")

    # 1. Завантажуємо дані
    dataset = load_json("dataset.json")
    results = load_json("analysis_results.json")

    if not dataset or not results:
        return

    # Створюємо словник з правильними відповідями
    true_labels_map = {chat["id"]: chat["true_labels"] for chat in dataset}

    # Змінні для підрахунку метрик
    total_chats = len(results)
    correct_intent = 0
    correct_satisfaction = 0
    total_mistakes_score = 0.0 # Тепер це float для часткових балів

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
        if analysis["intent"] == truth["intent"]:
            correct_intent += 1
        else:
            print(f"[{chat_id}] Помилка Intent: Очікувалось '{truth['intent']}', отримано '{analysis['intent']}'")

        # --- Перевірка Satisfaction ---
        if analysis["satisfaction"] == truth["satisfaction"]:
            correct_satisfaction += 1
        else:
            print(f"[{chat_id}] Помилка Satisfaction: Очікувалось '{truth['satisfaction']}', отримано '{analysis['satisfaction']}'")

        # --- Перевірка Agent Mistakes (Часткове зарахування / Jaccard Similarity) ---
        truth_mistakes = set(truth["agent_mistakes"])
        analysis_mistakes = set(analysis["agent_mistakes"])

        intersection = truth_mistakes.intersection(analysis_mistakes)
        union = truth_mistakes.union(analysis_mistakes)

        # Рахуємо бал для конкретного чату
        if not truth_mistakes and not analysis_mistakes:
            chat_mistake_score = 1.0  # Обидва порожні = ідеальний збіг
        elif not union:
            chat_mistake_score = 0.0
        else:
            chat_mistake_score = len(intersection) / len(union)

        total_mistakes_score += chat_mistake_score

        # Виводимо лог, якщо збіг не 100%
        if chat_mistake_score < 1.0:
            print(f"[{chat_id}] Частковий/Хибний збіг Mistakes (Бал: {chat_mistake_score*100:.1f}%):")
            print(f"    Очікувалось: {list(truth_mistakes)}")
            print(f"    Отримано:    {list(analysis_mistakes)}")

    # 3. Вивід фінальних метрик (Accuracy)
    print("\n" + "=" * 50)
    print("ФІНАЛЬНІ МЕТРИКИ (ACCURACY):")
    print("=" * 50)
    print(f"Всього проаналізовано діалогів: {total_chats}")
    print(f"Точність визначення Intent:       {(correct_intent / total_chats) * 100:.2f}%")
    print(f"Точність оцінки Satisfaction:     {(correct_satisfaction / total_chats) * 100:.2f}%")
    print(f"Точність виявлення Mistakes:      {(total_mistakes_score / total_chats) * 100:.2f}%")
    print("=" * 50)

if __name__ == "__main__":
    main()