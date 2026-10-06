import json
import urllib.request
import time


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5-coder:0.5b"


def ask_local_llm(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    start_time = time.perf_counter()

    with urllib.request.urlopen(
        request,
        timeout=300
    ) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    elapsed = time.perf_counter() - start_time

    print()
    print(f"Модель: {MODEL}")
    print(f"Время: {elapsed:.2f} сек.")
    print()

    return result["response"]


def run_test(
    number: int,
    title: str,
    prompt: str
):
    print()
    print("=" * 70)
    print(f"ТЕСТ {number}: {title}")
    print("=" * 70)

    print()
    print("PROMPT:")
    print(prompt)

    try:
        answer = ask_local_llm(prompt)

        print("ANSWER:")
        print(answer)

    except Exception as error:
        print()
        print("ERROR:")
        print(error)


def main():
    print("=" * 70)
    print("DAY 26 — LOCAL LLM WITH OLLAMA")
    print("=" * 70)

    tests = [
        {
            "title": "Простой вопрос",
            "prompt": (
                "Объясни одним предложением, "
                "что такое LLM."
            )
        },
        {
            "title": "Логическая задача",
            "prompt": (
                "У Маши 12 яблок. "
                "Она отдала треть яблок другу, "
                "а затем купила ещё 5. "
                "Сколько яблок стало у Маши? "
                "Кратко объясни вычисление."
            )
        },
        {
            "title": "Программирование",
            "prompt": (
                "Напиши функцию Python is_even(number), "
                "которая возвращает True для чётного числа "
                "и False для нечётного. "
                "Добавь два примера использования."
            )
        }
    ]

    for number, test in enumerate(
        tests,
        start=1
    ):
        run_test(
            number=number,
            title=test["title"],
            prompt=test["prompt"]
        )


if __name__ == "__main__":
    main()