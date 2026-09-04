from google import genai
import time

client = genai.Client()

MODELS = {
    "1": {
        "name": "Слабая",
        "model": "gemini-3.1-flash-lite",
        "input_price": 0.25,
        "output_price": 1.50,
    },
    "2": {
        "name": "Средняя",
        "model": "gemini-3.6-flash",
        "input_price": 0.75,
        "output_price": 3.75,
    },
    "3": {
        "name": "Сильная",
        "model": "gemini-3.1-pro-preview",
        "input_price": 2.00,
        "output_price": 12.00,
    },
}

PROMPT = """
Объясни простыми словами, что такое искусственный интеллект.

Приведи 3 примера его использования в повседневной жизни.

Ответ должен быть понятным человеку, который только начинает изучать тему.
"""


def ask_model(model_info):
    print()
    print("=" * 70)
    print(f"МОДЕЛЬ: {model_info['name']}")
    print(f"ID: {model_info['model']}")
    print("=" * 70)

    start_time = time.perf_counter()

    try:
        response = client.models.generate_content(
            model=model_info["model"],
            contents=PROMPT
        )

        end_time = time.perf_counter()

        elapsed = end_time - start_time

        usage = response.usage_metadata

        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        total_tokens = usage.total_token_count

        input_cost = input_tokens / 1_000_000 * model_info["input_price"]
        output_cost = output_tokens / 1_000_000 * model_info["output_price"]
        total_cost = input_cost + output_cost

        print()
        print("ОТВЕТ:")
        print(response.text)

        print()
        print("-" * 70)
        print("СТАТИСТИКА")
        print("-" * 70)

        print(f"Время ответа:       {elapsed:.2f} сек.")
        print(f"Входных токенов:    {input_tokens}")
        print(f"Выходных токенов:   {output_tokens}")
        print(f"Всего токенов:      {total_tokens}")
        print(f"Примерная стоимость: ${total_cost:.8f}")

        return {
            "name": model_info["name"],
            "model": model_info["model"],
            "time": elapsed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost": total_cost,
        }

    except Exception as error:
        print()
        print("ОШИБКА:")
        print(error)
        return None


print("=" * 70)
print("ДЕНЬ 5 — СРАВНЕНИЕ ВЕРСИЙ МОДЕЛЕЙ")
print("=" * 70)

print()
print("Один и тот же запрос будет отправлен трём моделям:")
print()
print(PROMPT)

print()
print("Выберите вариант:")
print("1 — Слабая модель")
print("2 — Средняя модель")
print("3 — Сильная модель")
print("4 — Все модели")

choice = input("\nВаш выбор: ")

results = []

if choice in MODELS:
    result = ask_model(MODELS[choice])

    if result:
        results.append(result)

elif choice == "4":
    for number in ["1", "2", "3"]:
        result = ask_model(MODELS[number])

        if result:
            results.append(result)

        if number != "3":
            print()
            print("Пауза 3 секунды...")
            time.sleep(3)

else:
    print("Ошибка: выберите вариант от 1 до 4.")


if len(results) > 1:
    print()
    print("=" * 70)
    print("СРАВНЕНИЕ")
    print("=" * 70)

    print()

    for result in results:
        print(f"Модель: {result['name']}")
        print(f"  Время:       {result['time']:.2f} сек.")
        print(f"  Токены:      {result['total_tokens']}")
        print(f"  Стоимость:   ${result['cost']:.8f}")
        print()