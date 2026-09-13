from google import genai
from google.genai import types

import copy
import json
import os
import time


class GeminiAgent:
    def __init__(
        self,
        model="gemini-3.5-flash-lite",
        window_size=6
    ):
        self.client = genai.Client()
        self.model = model
        self.window_size = window_size

        # Текущая стратегия
        self.strategy = "sliding"

        # Обычная история
        self.messages = []

        # Sticky Facts
        self.facts = {}

        # Branching
        self.branches = {
            "main": []
        }
        self.current_branch = "main"

        # Последняя статистика
        self.last_prompt_tokens = 0
        self.last_response_tokens = 0
        self.last_total_tokens = 0
        self.last_time = 0

    # ---------------------------------------------------------
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ---------------------------------------------------------

    def generate(self, prompt):
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

        elapsed = time.perf_counter() - start

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

        self.last_time = elapsed

        return response.text

    def messages_to_text(self, messages):
        parts = []

        for message in messages:
            if message["role"] == "user":
                role = "Пользователь"
            else:
                role = "Ассистент"

            parts.append(
                f"{role}: {message['text']}"
            )

        return "\n\n".join(parts)

    # ---------------------------------------------------------
    # STRATEGY 1 — SLIDING WINDOW
    # ---------------------------------------------------------

    def build_sliding_prompt(self, user_message):
        recent_messages = self.messages[-self.window_size:]

        history = self.messages_to_text(recent_messages)

        return f"""
Ты полезный AI-ассистент.

История последних сообщений:

{history}

Пользователь: {user_message}
Ассистент:
""".strip()

    # ---------------------------------------------------------
    # STRATEGY 2 — STICKY FACTS
    # ---------------------------------------------------------

    def update_facts(self, user_message):
        current_facts = json.dumps(
            self.facts,
            ensure_ascii=False,
            indent=2
        )

        prompt = f"""
Ты управляешь памятью AI-агента.

Текущие важные факты:

{current_facts}

Новое сообщение пользователя:

{user_message}

Извлеки только важные долгосрочные факты.

Это могут быть:
- цель проекта;
- ограничения;
- предпочтения;
- технологии;
- принятые решения;
- договорённости;
- важные требования.

Не сохраняй приветствия, случайные фразы и обычные вопросы.

Если новый факт изменяет старый — обнови его.

Верни ТОЛЬКО JSON-объект со всеми актуальными фактами.

Пример:

{{
    "platform": "Android",
    "language": "Kotlin",
    "min_android": "12"
}}

Если важных фактов нет, верни текущие факты без изменений.
""".strip()

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(
                        thinking_level="minimal"
                    )
                )
            )

            new_facts = json.loads(response.text)

            if isinstance(new_facts, dict):
                self.facts = new_facts

        except Exception as error:
            print()
            print("Не удалось обновить facts:")
            print(error)

    def build_facts_prompt(self, user_message):
        recent_messages = self.messages[-self.window_size:]

        history = self.messages_to_text(recent_messages)

        facts_text = json.dumps(
            self.facts,
            ensure_ascii=False,
            indent=2
        )

        return f"""
Ты полезный AI-ассистент.

ВАЖНЫЕ ФАКТЫ:

{facts_text}

ПОСЛЕДНИЕ СООБЩЕНИЯ:

{history}

Пользователь: {user_message}
Ассистент:
""".strip()

    # ---------------------------------------------------------
    # STRATEGY 3 — BRANCHING
    # ---------------------------------------------------------

    def build_branching_prompt(self, user_message):
        branch_messages = self.branches[
            self.current_branch
        ]

        history = self.messages_to_text(branch_messages)

        return f"""
Ты полезный AI-ассистент.

Текущая ветка диалога:
{self.current_branch}

История этой ветки:

{history}

Пользователь: {user_message}
Ассистент:
""".strip()

    def create_branch(self, branch_name):
        if branch_name in self.branches:
            print()
            print(
                f"Ветка '{branch_name}' уже существует."
            )
            return

        current_history = self.branches[
            self.current_branch
        ]

        # checkpoint = копия текущего состояния ветки
        self.branches[branch_name] = copy.deepcopy(
            current_history
        )

        print()
        print(
            f"Создана ветка '{branch_name}' "
            f"из '{self.current_branch}'."
        )

    def switch_branch(self, branch_name):
        if branch_name not in self.branches:
            print()
            print(
                f"Ветка '{branch_name}' не существует."
            )
            return

        self.current_branch = branch_name

        print()
        print(
            f"Переключились на ветку: {branch_name}"
        )

    # ---------------------------------------------------------
    # ОСНОВНОЙ ЗАПРОС
    # ---------------------------------------------------------

    def ask(self, user_message):
        print()
        print("-" * 60)
        print("ЗАПРОС К GEMINI")
        print("-" * 60)
        print(f"Стратегия: {self.strategy}")

        if self.strategy == "sliding":

            prompt = self.build_sliding_prompt(
                user_message
            )

        elif self.strategy == "facts":

            print("Обновляем Sticky Facts...")

            self.update_facts(user_message)

            prompt = self.build_facts_prompt(
                user_message
            )

        elif self.strategy == "branching":

            print(
                f"Текущая ветка: "
                f"{self.current_branch}"
            )

            prompt = self.build_branching_prompt(
                user_message
            )

        else:
            raise ValueError(
                "Неизвестная стратегия"
            )

        print("Отправляем запрос Gemini...")

        answer = self.generate(prompt)

        # Сохраняем сообщения
        if self.strategy == "branching":

            self.branches[
                self.current_branch
            ].append({
                "role": "user",
                "text": user_message
            })

            self.branches[
                self.current_branch
            ].append({
                "role": "assistant",
                "text": answer
            })

        else:

            self.messages.append({
                "role": "user",
                "text": user_message
            })

            self.messages.append({
                "role": "assistant",
                "text": answer
            })

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
    # КОМАНДЫ
    # ---------------------------------------------------------

    def set_strategy(self, strategy):
        allowed = [
            "sliding",
            "facts",
            "branching"
        ]

        if strategy not in allowed:
            print()
            print("Неизвестная стратегия.")
            print(
                "Доступно: sliding, facts, branching"
            )
            return

        self.strategy = strategy

        print()
        print(
            f"Текущая стратегия: {strategy}"
        )

    def show_facts(self):
        print()
        print("=" * 60)
        print("STICKY FACTS")
        print("=" * 60)

        if not self.facts:
            print("Facts пока пусты.")
            return

        print(
            json.dumps(
                self.facts,
                ensure_ascii=False,
                indent=2
            )
        )

    def show_branches(self):
        print()
        print("=" * 60)
        print("ВЕТКИ")
        print("=" * 60)

        for name, messages in self.branches.items():

            marker = ""

            if name == self.current_branch:
                marker = " <-- текущая"

            print(
                f"{name}: "
                f"{len(messages)} сообщений"
                f"{marker}"
            )

    def show_stats(self):
        print()
        print("=" * 60)
        print("СТАТИСТИКА")
        print("=" * 60)

        print(
            f"Стратегия:          "
            f"{self.strategy}"
        )

        print(
            f"Sliding Window:      "
            f"{self.window_size} сообщений"
        )

        print(
            f"Обычная история:     "
            f"{len(self.messages)} сообщений"
        )

        print(
            f"Sticky Facts:        "
            f"{len(self.facts)}"
        )

        print(
            f"Текущая ветка:       "
            f"{self.current_branch}"
        )

        print(
            f"Количество веток:    "
            f"{len(self.branches)}"
        )

        print()
        print("Последний запрос:")

        print(
            f"Входных токенов:     "
            f"{self.last_prompt_tokens}"
        )

        print(
            f"Токенов ответа:      "
            f"{self.last_response_tokens}"
        )

        print(
            f"Всего токенов API:   "
            f"{self.last_total_tokens}"
        )

    def clear(self):
        self.messages = []
        self.facts = {}

        self.branches = {
            "main": []
        }

        self.current_branch = "main"

        print()
        print("Память агента очищена.")


def show_help():
    print()
    print("=" * 60)
    print("ДЕНЬ 10 — КОМАНДЫ")
    print("=" * 60)

    print("""
strategy
    показать текущую стратегию

strategy sliding
    Sliding Window

strategy facts
    Sticky Facts

strategy branching
    Branching

facts
    показать сохранённые факты

branch <имя>
    создать новую ветку из текущей

switch <имя>
    переключиться на ветку

branches
    показать все ветки

stats
    показать статистику

clear
    очистить память

help
    показать команды

exit
    завершить программу
""")


def main():
    agent = GeminiAgent()

    print("=" * 60)
    print("ДЕНЬ 10 — СТРАТЕГИИ УПРАВЛЕНИЯ КОНТЕКСТОМ")
    print("=" * 60)

    print()
    print(f"Модель:         {agent.model}")
    print(f"Window size:    {agent.window_size}")
    print(f"Стратегия:      {agent.strategy}")

    show_help()

    while True:

        print()
        user_input = input("Вы: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print()
            print("Агент: До свидания!")
            break

        if user_input.lower() == "help":
            show_help()
            continue

        if user_input.lower() == "stats":
            agent.show_stats()
            continue

        if user_input.lower() == "facts":
            agent.show_facts()
            continue

        if user_input.lower() == "branches":
            agent.show_branches()
            continue

        if user_input.lower() == "clear":
            agent.clear()
            continue

        if user_input.lower() == "strategy":
            print()
            print(
                f"Текущая стратегия: "
                f"{agent.strategy}"
            )
            continue

        if user_input.lower().startswith(
            "strategy "
        ):
            strategy = user_input.split(
                maxsplit=1
            )[1].lower()

            agent.set_strategy(strategy)
            continue

        if user_input.lower().startswith(
            "branch "
        ):
            branch_name = user_input.split(
                maxsplit=1
            )[1]

            agent.create_branch(branch_name)
            continue

        if user_input.lower().startswith(
            "switch "
        ):
            branch_name = user_input.split(
                maxsplit=1
            )[1]

            agent.switch_branch(branch_name)
            continue

        try:
            answer = agent.ask(user_input)

            print()
            print("Агент:")
            print(answer)

        except Exception as error:
            print()
            print("Ошибка:")
            print(error)


if __name__ == "__main__":
    main()