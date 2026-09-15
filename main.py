from google import genai
from google.genai import types

import json
import os
import time


class GeminiAgent:
    def __init__(
        self,
        model="gemini-3.5-flash-lite",
        short_term_limit=6
    ):
        self.client = genai.Client()
        self.model = model
        self.short_term_limit = short_term_limit

        self.short_term_file = "short_term_memory.json"
        self.working_file = "working_memory.json"
        self.long_term_file = "long_term_memory.json"

        # Три независимых слоя памяти
        self.short_term_memory = self.load_json(
            self.short_term_file,
            []
        )

        self.working_memory = self.load_json(
            self.working_file,
            {}
        )

        self.long_term_memory = self.load_json(
            self.long_term_file,
            {}
        )

        # Статистика последнего запроса
        self.last_prompt_tokens = 0
        self.last_response_tokens = 0
        self.last_total_tokens = 0
        self.last_time = 0

    # ---------------------------------------------------------
    # JSON
    # ---------------------------------------------------------

    def load_json(self, filename, default_value):
        if not os.path.exists(filename):
            return default_value

        try:
            with open(
                filename,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):
            return default_value

    def save_json(self, filename, data):
        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

    # ---------------------------------------------------------
    # SHORT-TERM MEMORY
    # ---------------------------------------------------------

    def add_short_term(self, role, text):
        self.short_term_memory.append({
            "role": role,
            "text": text
        })

        # Храним только последние N сообщений
        self.short_term_memory = (
            self.short_term_memory[
                -self.short_term_limit:
            ]
        )

        self.save_json(
            self.short_term_file,
            self.short_term_memory
        )

    # ---------------------------------------------------------
    # WORKING MEMORY
    # ---------------------------------------------------------

    def remember_working(self, key, value):
        self.working_memory[key] = value

        self.save_json(
            self.working_file,
            self.working_memory
        )

        print()
        print("Сохранено в WORKING MEMORY:")
        print(f"{key} = {value}")

    # ---------------------------------------------------------
    # LONG-TERM MEMORY
    # ---------------------------------------------------------

    def remember_long_term(self, key, value):
        self.long_term_memory[key] = value

        self.save_json(
            self.long_term_file,
            self.long_term_memory
        )

        print()
        print("Сохранено в LONG-TERM MEMORY:")
        print(f"{key} = {value}")

    # ---------------------------------------------------------
    # PROMPT
    # ---------------------------------------------------------

    def short_term_to_text(self):
        parts = []

        for message in self.short_term_memory:

            if message["role"] == "user":
                role = "Пользователь"
            else:
                role = "Ассистент"

            parts.append(
                f"{role}: {message['text']}"
            )

        return "\n\n".join(parts)

    def build_prompt(self, user_message):
        short_term = self.short_term_to_text()

        working = json.dumps(
            self.working_memory,
            ensure_ascii=False,
            indent=2
        )

        long_term = json.dumps(
            self.long_term_memory,
            ensure_ascii=False,
            indent=2
        )

        return f"""
Ты полезный AI-ассистент.

У тебя есть три отдельных слоя памяти.

ДОЛГОВРЕМЕННАЯ ПАМЯТЬ:
Постоянные предпочтения, профиль и важные решения пользователя.

{long_term}


РАБОЧАЯ ПАМЯТЬ:
Информация, относящаяся к текущей задаче или проекту.

{working}


КРАТКОСРОЧНАЯ ПАМЯТЬ:
Последние сообщения текущего диалога.

{short_term}


Используй эту память при ответе.
Не придумывай отсутствующие в памяти факты.

Пользователь: {user_message}
Ассистент:
""".strip()

    # ---------------------------------------------------------
    # GEMINI
    # ---------------------------------------------------------

    def ask(self, user_message):
        prompt = self.build_prompt(
            user_message
        )

        print()
        print("-" * 60)
        print("ЗАПРОС К GEMINI")
        print("-" * 60)

        print(
            f"Short-term: "
            f"{len(self.short_term_memory)} сообщений"
        )

        print(
            f"Working:    "
            f"{len(self.working_memory)} фактов"
        )

        print(
            f"Long-term:  "
            f"{len(self.long_term_memory)} фактов"
        )

        start = time.perf_counter()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="minimal"
                )
            )
        )

        self.last_time = (
            time.perf_counter() - start
        )

        usage = response.usage_metadata

        self.last_prompt_tokens = (
            usage.prompt_token_count or 0
        )

        self.last_response_tokens = (
            usage.candidates_token_count or 0
        )

        self.last_total_tokens = (
            usage.total_token_count or 0
        )

        answer = response.text

        # Обычный диалог автоматически
        # сохраняется только в short-term.
        self.add_short_term(
            "user",
            user_message
        )

        self.add_short_term(
            "assistant",
            answer
        )

        print()
        print("-" * 60)
        print("СТАТИСТИКА")
        print("-" * 60)

        print(
            f"Входных токенов:   "
            f"{self.last_prompt_tokens}"
        )

        print(
            f"Токенов ответа:    "
            f"{self.last_response_tokens}"
        )

        print(
            f"Всего токенов API: "
            f"{self.last_total_tokens}"
        )

        print(
            f"Время Gemini:      "
            f"{self.last_time:.2f} сек."
        )

        return answer

    # ---------------------------------------------------------
    # ПРОСМОТР ПАМЯТИ
    # ---------------------------------------------------------

    def show_memory(self):
        print()
        print("=" * 60)
        print("МОДЕЛЬ ПАМЯТИ АГЕНТА")
        print("=" * 60)

        print()
        print("1. SHORT-TERM MEMORY")
        print("-" * 60)

        if not self.short_term_memory:
            print("Пусто")

        for message in self.short_term_memory:
            print(
                f"{message['role']}: "
                f"{message['text']}"
            )

        print()
        print("2. WORKING MEMORY")
        print("-" * 60)

        if not self.working_memory:
            print("Пусто")
        else:
            print(
                json.dumps(
                    self.working_memory,
                    ensure_ascii=False,
                    indent=2
                )
            )

        print()
        print("3. LONG-TERM MEMORY")
        print("-" * 60)

        if not self.long_term_memory:
            print("Пусто")
        else:
            print(
                json.dumps(
                    self.long_term_memory,
                    ensure_ascii=False,
                    indent=2
                )
            )

    def show_short(self):
        print()
        print("=" * 60)
        print("SHORT-TERM MEMORY")
        print("=" * 60)

        if not self.short_term_memory:
            print("Пусто")
            return

        for message in self.short_term_memory:
            print(
                f"{message['role']}: "
                f"{message['text']}"
            )

    def show_working(self):
        print()
        print("=" * 60)
        print("WORKING MEMORY")
        print("=" * 60)

        if not self.working_memory:
            print("Пусто")
            return

        print(
            json.dumps(
                self.working_memory,
                ensure_ascii=False,
                indent=2
            )
        )

    def show_long_term(self):
        print()
        print("=" * 60)
        print("LONG-TERM MEMORY")
        print("=" * 60)

        if not self.long_term_memory:
            print("Пусто")
            return

        print(
            json.dumps(
                self.long_term_memory,
                ensure_ascii=False,
                indent=2
            )
        )

    # ---------------------------------------------------------
    # ОЧИСТКА ПАМЯТИ
    # ---------------------------------------------------------

    def clear_short(self):
        self.short_term_memory = []

        self.save_json(
            self.short_term_file,
            self.short_term_memory
        )

        print()
        print("Short-term memory очищена.")

    def clear_working(self):
        self.working_memory = {}

        self.save_json(
            self.working_file,
            self.working_memory
        )

        print()
        print("Working memory очищена.")

    def clear_long_term(self):
        self.long_term_memory = {}

        self.save_json(
            self.long_term_file,
            self.long_term_memory
        )

        print()
        print("Long-term memory очищена.")

    def show_stats(self):
        print()
        print("=" * 60)
        print("СТАТИСТИКА")
        print("=" * 60)

        print(
            f"Short-term сообщений: "
            f"{len(self.short_term_memory)}"
        )

        print(
            f"Working фактов:        "
            f"{len(self.working_memory)}"
        )

        print(
            f"Long-term фактов:      "
            f"{len(self.long_term_memory)}"
        )

        print()
        print("Последний запрос:")

        print(
            f"Входных токенов:       "
            f"{self.last_prompt_tokens}"
        )

        print(
            f"Токенов ответа:        "
            f"{self.last_response_tokens}"
        )

        print(
            f"Всего токенов API:     "
            f"{self.last_total_tokens}"
        )


def parse_memory_command(text):
    """
    Получает строку вида:

    remember work min_android=12

    или:

    remember long language=Kotlin

    Возвращает:

    memory_type, key, value
    """

    parts = text.split(
        maxsplit=2
    )

    if len(parts) < 3:
        return None

    memory_type = parts[1]
    data = parts[2]

    if "=" not in data:
        return None

    key, value = data.split(
        "=",
        maxsplit=1
    )

    return (
        memory_type.strip().lower(),
        key.strip(),
        value.strip()
    )


def show_help():
    print()
    print("=" * 60)
    print("ДЕНЬ 11 — МОДЕЛЬ ПАМЯТИ АГЕНТА")
    print("=" * 60)

    print("""
Обычное сообщение
    автоматически попадает в short-term memory


remember work <ключ>=<значение>
    сохранить факт текущей задачи

Пример:
remember work min_android=12


remember long <ключ>=<значение>
    сохранить долговременный факт

Пример:
remember long preferred_language=Kotlin


memory
    показать все слои памяти

short
    показать short-term memory

work
    показать working memory

long
    показать long-term memory

clear short
    очистить краткосрочную память

clear work
    очистить рабочую память

clear long
    очистить долговременную память

stats
    показать статистику

help
    показать команды

exit
    выход
""")


def main():
    agent = GeminiAgent()

    print("=" * 60)
    print("ДЕНЬ 11 — МОДЕЛЬ ПАМЯТИ АГЕНТА")
    print("=" * 60)

    print()
    print(f"Модель: {agent.model}")

    print()
    print("Memory layers:")
    print("1. Short-term")
    print("2. Working")
    print("3. Long-term")

    show_help()

    while True:

        print()
        user_input = input(
            "Вы: "
        ).strip()

        if not user_input:
            continue

        command = user_input.lower()

        if command == "exit":
            print()
            print("Агент: До свидания!")
            break

        if command == "help":
            show_help()
            continue

        if command == "memory":
            agent.show_memory()
            continue

        if command == "short":
            agent.show_short()
            continue

        if command == "work":
            agent.show_working()
            continue

        if command == "long":
            agent.show_long_term()
            continue

        if command == "stats":
            agent.show_stats()
            continue

        if command == "clear short":
            agent.clear_short()
            continue

        if command == "clear work":
            agent.clear_working()
            continue

        if command == "clear long":
            agent.clear_long_term()
            continue

        if command.startswith(
            "remember "
        ):
            result = parse_memory_command(
                user_input
            )

            if result is None:
                print()
                print(
                    "Неверный формат команды."
                )

                print(
                    "Пример:"
                )

                print(
                    "remember work "
                    "min_android=12"
                )

                continue

            memory_type, key, value = result

            if memory_type == "work":

                agent.remember_working(
                    key,
                    value
                )

            elif memory_type == "long":

                agent.remember_long_term(
                    key,
                    value
                )

            else:
                print()
                print(
                    "Тип памяти должен быть "
                    "'work' или 'long'."
                )

            continue

        try:
            answer = agent.ask(
                user_input
            )

            print()
            print("Агент:")
            print(answer)

        except Exception as error:
            print()
            print("Ошибка:")
            print(error)


if __name__ == "__main__":
    main()