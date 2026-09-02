from google import genai
from google.genai import types

client = genai.Client()

print("=== День 2: Контроль ответа LLM ===")
print()

prompt = input("Введите ваш запрос: ")

print()
print("Выберите вариант:")
print("1 — Без ограничений")
print("2 — Формат + ограничение длины")
print("3 — Stop sequence")
print("4 — Все варианты")

choice = input("Ваш выбор: ")

# -----------------------------
# Вариант 1 — без ограничений
# -----------------------------
if choice == "1":
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    print()
    print("========== БЕЗ ОГРАНИЧЕНИЙ ==========")
    print(response.text)


# -----------------------------------------
# Вариант 2 — формат + ограничение длины
# -----------------------------------------
elif choice == "2":
    controlled_prompt = f"""
{prompt}

Формат ответа:
1. Краткое определение.
2. Один пример.
3. Краткий итог.

Ответ должен быть коротким и не превышать 100 слов.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=controlled_prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=150
        )
    )

    print()
    print("========== ФОРМАТ + ДЛИНА ==========")
    print(response.text)


# -----------------------------------------
# Вариант 3 — stop sequence
# -----------------------------------------
elif choice == "3":
    stop_prompt = f"""
{prompt}

Ответ дай в следующем формате:

Определение: кратко объясни тему.

Пример: приведи один пример.

STOP

После слова STOP ничего больше не пиши.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=stop_prompt,
        config=types.GenerateContentConfig(
            stop_sequences=["STOP"]
        )
    )

    print()
    print("========== STOP SEQUENCE ==========")
    print(response.text)


# -----------------------------------------
# Вариант 4 — все варианты
# -----------------------------------------
elif choice == "4":

    # Вариант 1
    response1 = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    print()
    print("========== 1. БЕЗ ОГРАНИЧЕНИЙ ==========")
    print(response1.text)

    # Вариант 2
    controlled_prompt = f"""
{prompt}

Формат ответа:
1. Краткое определение.
2. Один пример.
3. Краткий итог.

Ответ должен быть коротким и не превышать 100 слов.
"""

    response2 = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=controlled_prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=1000
        )
    )

    print()
    print("========== 2. ФОРМАТ + ДЛИНА ==========")
    print(response2.text)

    # Вариант 3
    stop_prompt = f"""
{prompt}

Ответ дай в следующем формате:

Определение: кратко объясни тему.

Пример: приведи один пример.

STOP

После слова STOP ничего больше не пиши.
"""

    response3 = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=stop_prompt,
        config=types.GenerateContentConfig(
            stop_sequences=["STOP"]
        )
    )

    print()
    print("========== 3. STOP SEQUENCE ==========")
    print(response3.text)


else:
    print("Ошибка: выберите 1, 2, 3 или 4.")