from google import genai
from google.genai import types

import json
import os
import time


class GeminiAgent:
    def __init__(
        self,
        model="gemini-3.5-flash-lite",
        history_file="history.json",
        summary_file="summary.txt",
        keep_last=6,
        compress_every=10
    ):
        self.client = genai.Client()

        self.model = model
        self.history_file = history_file
        self.summary_file = summary_file

        # Последние N сообщений храним полностью
        self.keep_last = keep_last

        # Сколько старых сообщений сжимаем за один раз
        self.compress_every = compress_every

        self.messages = self.load_history()
        self.summary = self.load_summary()

        # Статистика последнего запроса
        self.last_input_tokens = 0
        self.last_output_tokens = 0
        self.last_total_tokens = 0
        self.last_request_time = 0

    # =========================================================
    # ЗАГРУЗКА И СОХРАНЕНИЕ
    # =========================================================

    def load_history(self):
        if not os.path.exists(self.history_file):
            return []

        try:
            with open(
                self.history_file,
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file)

        except (json.JSONDecodeError, OSError):
            return []

    def save_history(self):
        with open(
            self.history_file,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.messages,
                file,
                ensure_ascii=False,
                indent=2
            )

    def load_summary(self):
        if not os.path.exists(self.summary_file):
            return ""

        try:
            with open(
                self.summary_file,
                "r",
                encoding="utf-8"
            ) as file:
                return file.read()

        except OSError:
            return ""

    def save_summary(self):
        with open(
            self.summary_file,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(self.summary)

    # =========================================================
    # ИСТОРИЯ -> ТЕКСТ
    # =========================================================

    def messages_to_text(self, messages):
        parts = []

        for message in messages:
            if message["role"] == "user":
                role_name = "Пользователь"
            else:
                role_name = "Ассистент"

            parts.append(
                f"{role_name}: {message['text']}"
            )

        return "\n\n".join(parts)

    # =========================================================
    # СОЗДАНИЕ PROMPT
    # =========================================================

    def build_prompt(self, user_message):
        prompt_parts = []

        # Старый контекст в сжатом виде
        if self.summary:
            prompt_parts.append(
                "Краткое содержание предыдущего диалога:"
            )

            prompt_parts.append(
                self.summary
            )

        # Последние сообщения без изменений
        if self.messages:
            prompt_parts.append(
                "Последние сообщения диалога:"
            )

            prompt_parts.append(
                self.messages_to_text(
                    self.messages
                )
            )

        # Новый вопрос
        prompt_parts.append(
            f"Пользователь: {user_message}"
        )

        prompt_parts.append(
            "Ассистент:"
        )

        return "\n\n".join(prompt_parts)

    # =========================================================
    # СЖАТИЕ ИСТОРИИ
    # =========================================================

    def compress_history(self):
        old_count = (
            len(self.messages)
            - self.keep_last
        )

        # Пока старых сообщений недостаточно
        if old_count < self.compress_every:
            return

        # Берём первые 10 сообщений
        messages_to_compress = (
            self.messages[
                :self.compress_every
            ]
        )

        old_text = self.messages_to_text(
            messages_to_compress
        )

        print()
        print("=" * 60)
        print("СЖАТИЕ ИСТОРИИ")
        print("=" * 60)

        print(
            f"Сообщений для сжатия: "
            f"{len(messages_to_compress)}"
        )

        # -----------------------------------------------------
        # PROMPT ДЛЯ SUMMARY
        # -----------------------------------------------------

        summary_prompt = f"""
Создай краткое содержание предыдущего диалога.

Сохрани только действительно важную информацию:

- имена;
- важные факты;
- предпочтения пользователя;
- решения;
- договорённости;
- важные детали;
- контекст, который может понадобиться позже.

Не добавляй информацию, которой не было в диалоге.

Не пересказывай разговор подробно.

Summary должно быть коротким и информативным.

Предыдущее summary:

{self.summary if self.summary else "Отсутствует"}

Новые сообщения для сжатия:

{old_text}

Создай новое объединённое summary:
"""

        print()
        print("Создаём summary...")

        start = time.perf_counter()

        response = self.client.models.generate_content(
            model=self.model,
            contents=summary_prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(
                    thinking_level="minimal"
                )
            )
        )

        summary_time = (
            time.perf_counter() - start
        )

        new_summary = response.text

        usage = response.usage_metadata

        input_tokens = (
            usage.prompt_token_count or 0
        )

        output_tokens = (
            usage.candidates_token_count or 0
        )

        thinking_tokens = (
            getattr(
                usage,
                "thoughts_token_count",
                0
            ) or 0
        )

        total_tokens = (
            usage.total_token_count or 0
        )

        print()
        print("-" * 60)
        print("SUMMARY СОЗДАН")
        print("-" * 60)

        print(
            f"Входных токенов:   "
            f"{input_tokens}"
        )

        print(
            f"Токенов summary:   "
            f"{output_tokens}"
        )

        print(
            f"Thinking tokens:   "
            f"{thinking_tokens}"
        )

        print(
            f"Всего токенов API: "
            f"{total_tokens}"
        )

        print(
            f"Время создания:    "
            f"{summary_time:.2f} сек."
        )

        # Сохраняем новый summary
        self.summary = new_summary

        # Удаляем сообщения,
        # которые уже вошли в summary
        self.messages = (
            self.messages[
                self.compress_every:
            ]
        )

        self.save_history()
        self.save_summary()

        print()
        print(
            "Старые сообщения заменены summary."
        )

        print(
            f"Сообщений осталось без сжатия: "
            f"{len(self.messages)}"
        )

    # =========================================================
    # СТАТИСТИКА
    # =========================================================

    def show_stats(self):
        print()
        print("=" * 60)
        print("СТАТИСТИКА КОНТЕКСТА")
        print("=" * 60)

        print(
            f"Сообщений без сжатия: "
            f"{len(self.messages)}"
        )

        print(
            f"Summary существует:   "
            f"{'Да' if self.summary else 'Нет'}"
        )

        print()

        if self.last_input_tokens > 0:
            print(
                "Последний запрос:"
            )

            print(
                f"Входных токенов:       "
                f"{self.last_input_tokens}"
            )

            print(
                f"Токенов ответа:        "
                f"{self.last_output_tokens}"
            )

            print(
                f"Всего токенов API:     "
                f"{self.last_total_tokens}"
            )

            print(
                f"Время ответа:          "
                f"{self.last_request_time:.2f} сек."
            )

        else:
            print(
                "Запросов в текущем запуске "
                "ещё не было."
            )

    # =========================================================
    # ПОКАЗАТЬ SUMMARY
    # =========================================================

    def show_summary(self):
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if self.summary:
            print(self.summary)
        else:
            print(
                "Summary пока отсутствует."
            )

    # =========================================================
    # ОЧИСТКА
    # =========================================================

    def clear(self):
        self.messages = []
        self.summary = ""

        self.last_input_tokens = 0
        self.last_output_tokens = 0
        self.last_total_tokens = 0
        self.last_request_time = 0

        self.save_history()
        self.save_summary()

    # =========================================================
    # ОСНОВНОЙ ЗАПРОС
    # =========================================================

    def ask(self, user_message):
        total_start = time.perf_counter()

        # Создаём prompt локально.
        # Никакого count_tokens() здесь больше нет.
        prompt = self.build_prompt(
            user_message
        )

        print()
        print("-" * 60)
        print("ЗАПРОС К GEMINI")
        print("-" * 60)

        print(
            f"Summary: "
            f"{'есть' if self.summary else 'нет'}"
        )

        print(
            f"Сообщений в обычной истории: "
            f"{len(self.messages)}"
        )

        print()
        print("Отправляем запрос Gemini...")

        # -----------------------------------------------------
        # GEMINI
        # -----------------------------------------------------

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

        gemini_time = (
            time.perf_counter() - start
        )

        answer = response.text
        usage = response.usage_metadata

        # -----------------------------------------------------
        # ТОКЕНЫ БЕРЁМ ИЗ ОТВЕТА GEMINI
        # -----------------------------------------------------

        input_tokens = (
            usage.prompt_token_count or 0
        )

        output_tokens = (
            usage.candidates_token_count or 0
        )

        thinking_tokens = (
            getattr(
                usage,
                "thoughts_token_count",
                0
            ) or 0
        )

        total_tokens = (
            usage.total_token_count or 0
        )

        # Запоминаем статистику
        self.last_input_tokens = (
            input_tokens
        )

        self.last_output_tokens = (
            output_tokens
        )

        self.last_total_tokens = (
            total_tokens
        )

        self.last_request_time = (
            gemini_time
        )

        print()
        print("-" * 60)
        print("ТОКЕНЫ")
        print("-" * 60)

        print(
            f"Входных токенов:   "
            f"{input_tokens}"
        )

        print(
            f"Токенов ответа:    "
            f"{output_tokens}"
        )

        print(
            f"Thinking tokens:   "
            f"{thinking_tokens}"
        )

        print(
            f"Всего токенов API: "
            f"{total_tokens}"
        )

        print()
        print(
            f"Время Gemini:      "
            f"{gemini_time:.2f} сек."
        )

        # -----------------------------------------------------
        # СОХРАНЯЕМ ИСТОРИЮ
        # -----------------------------------------------------

        self.messages.append({
            "role": "user",
            "text": user_message
        })

        self.messages.append({
            "role": "assistant",
            "text": answer
        })

        self.save_history()

        # -----------------------------------------------------
        # ПРОВЕРЯЕМ, НУЖНО ЛИ СЖАТИЕ
        # -----------------------------------------------------

        self.compress_history()

        total_time = (
            time.perf_counter()
            - total_start
        )

        print(
            f"Общее время:       "
            f"{total_time:.2f} сек."
        )

        return answer


# =============================================================
# HELP
# =============================================================

def show_help():
    print()
    print("=" * 60)
    print("ДОСТУПНЫЕ КОМАНДЫ")
    print("=" * 60)

    print(
        "  help     — показать подсказку"
    )

    print(
        "  stats    — показать статистику"
    )

    print(
        "  summary  — показать summary"
    )

    print(
        "  clear    — очистить историю и summary"
    )

    print(
        "  exit     — завершить программу"
    )

    print()
    print(
        "Любой другой текст "
        "будет отправлен агенту."
    )

    print("=" * 60)


# =============================================================
# MAIN
# =============================================================

def main():
    agent = GeminiAgent()

    print("=" * 60)
    print("ДЕНЬ 9 — УПРАВЛЕНИЕ КОНТЕКСТОМ")
    print("=" * 60)

    print()

    print(
        f"Модель:                     "
        f"{agent.model}"
    )

    print(
        "Thinking level:             minimal"
    )

    print(
        f"Последних сообщений храним: "
        f"{agent.keep_last}"
    )

    print(
        f"Сжимаем за один раз:        "
        f"{agent.compress_every}"
    )

    print(
        f"Сообщений загружено:        "
        f"{len(agent.messages)}"
    )

    print(
        f"Summary существует:         "
        f"{'Да' if agent.summary else 'Нет'}"
    )

    show_help()

    while True:
        print()

        user_message = input(
            "Вы: "
        ).strip()

        if not user_message:
            continue

        command = user_message.lower()

        # EXIT
        if command == "exit":
            print()
            print(
                "Агент: До свидания!"
            )
            break

        # HELP
        if command == "help":
            show_help()
            continue

        # STATS
        if command == "stats":
            agent.show_stats()
            continue

        # SUMMARY
        if command == "summary":
            agent.show_summary()
            continue

        # CLEAR
        if command == "clear":
            agent.clear()

            print()
            print(
                "История и summary очищены."
            )

            continue

        # ОБЫЧНЫЙ ЗАПРОС
        try:
            answer = agent.ask(
                user_message
            )

            print()
            print("Агент:")
            print(answer)

        except Exception as error:
            print()
            print(
                "Ошибка при обращении к API:"
            )
            print(error)


if __name__ == "__main__":
    main()