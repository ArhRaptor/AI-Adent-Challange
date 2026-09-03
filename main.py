from google import genai
from google.genai import types
import time

client = genai.Client()

MODEL = "gemini-3.6-flash"

task = """
Придумай короткую историю о роботе, который впервые оказался на Земле.

Требования:
- 100–150 слов;
- история должна иметь начало, развитие и конец;
- текст должен быть понятным;
"""


def ask_gemini(prompt, temperature):
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature
            )
        )

        return response.text

    except Exception as error:
        print()
        print("Ошибка API:")
        print(error)
        return None


def run_temperature(temperature):
    print()
    print("=" * 60)
    print(f"TEMPERATURE = {temperature}")
    print("=" * 60)

    response = ask_gemini(task, temperature)

    if response:
        print(response)
    else:
        print("Не удалось получить ответ.")


print("=" * 60)
print("ДЕНЬ 4 — TEMPERATURE")
print("=" * 60)

print()
print("Задача:")
print(task)

print()
print("Выберите вариант:")
print("1 — Temperature = 0")
print("2 — Temperature = 0.7")
print("3 — Temperature = 1.2")
print("4 — Все варианты")

choice = input("\nВаш выбор: ")

if choice == "1":
    run_temperature(0)

elif choice == "2":
    run_temperature(0.7)

elif choice == "3":
    run_temperature(1.2)

elif choice == "4":
    run_temperature(0)

    time.sleep(3)

    run_temperature(0.7)

    time.sleep(3)

    run_temperature(1.2)

else:
    print("Ошибка: выберите вариант от 1 до 4.")