from google import genai
import json
import os


class GeminiAgent:
    def __init__(
        self,
        model="gemini-3.6-flash",
        history_file="history.json"
    ):
        self.client = genai.Client()
        self.model = model
        self.history_file = history_file

        self.messages = self.load_history()

        # Получаем реальные лимиты модели
        model_info = self.client.models.get(model=self.model)

        self.input_token_limit = model_info.input_token_limit
        self.output_token_limit = model_info.output_token_limit

        # По умолчанию используется реальный лимит
        self.token_limit = self.input_token_limit

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

    def clear_history(self):
        self.messages = []
        self.save_history()

    def set_token_limit(self, limit):
        self.token_limit = limit

    def reset_token_limit(self):
        self.token_limit = self.input_token_limit

    def build_prompt(self, user_message=None):
        prompt_parts = []

        for message in self.messages:
            role = message["role"]
            text = message["text"]

            if role == "user":
                prompt_parts.append(
                    f"Пользователь: {text}"
                )
            else:
                prompt_parts.append(
                    f"Ассистент: {text}"
                )

        if user_message is not None:
            prompt_parts.append(
                f"Пользователь: {user_message}"
            )
            prompt_parts.append("Ассистент:")

        return "\n\n".join(prompt_parts)

    def count_tokens(self, text):
        if not text:
            return 0

        result = self.client.models.count_tokens(
            model=self.model,
            contents=text
        )

        return result.total_tokens

    def get_history_tokens(self):
        history_text = self.build_prompt()

        return self.count_tokens(history_text)

    def show_stats(self):
        history_tokens = self.get_history_tokens()

        print()
        print("=" * 60)
        print("СТАТИСТИКА ДИАЛОГА")
        print("=" * 60)

        print(
            f"Сообщений в истории:   "
            f"{len(self.messages)}"
        )

        print(
            f"Токенов в истории:     "
            f"{history_tokens}"
        )

        print(
            f"Текущий лимит:         "
            f"{self.token_limit}"
        )

        print(
            f"Реальный лимит модели: "
            f"{self.input_token_limit}"
        )

        percent = (
            history_tokens
            / self.token_limit
            * 100
        )

        print(
            f"Лимит заполнен:        "
            f"{percent:.2f}%"
        )

    def ask(self, user_message):
        # Токены только нового сообщения
        current_request_tokens = self.count_tokens(
            user_message
        )

        # Токены предыдущей истории
        history_tokens = self.get_history_tokens()

        # История + новый запрос
        prompt = self.build_prompt(user_message)

        full_prompt_tokens = self.count_tokens(
            prompt
        )

        print()
        print("-" * 60)
        print("ТОКЕНЫ ДО ЗАПРОСА")
        print("-" * 60)

        print(
            f"Текущий запрос:        "
            f"{current_request_tokens}"
        )

        print(
            f"История диалога:       "
            f"{history_tokens}"
        )

        print(
            f"Весь вход в модель:    "
            f"{full_prompt_tokens}"
        )

        print(
            f"Текущий лимит:         "
            f"{self.token_limit}"
        )

        print(
            f"Реальный лимит модели: "
            f"{self.input_token_limit}"
        )

        percent = (
            full_prompt_tokens
            / self.token_limit
            * 100
        )

        print(
            f"Лимит заполнен:        "
            f"{percent:.2f}%"
        )

        # Проверка установленного лимита
        if full_prompt_tokens > self.token_limit:
            print()
            print("=" * 60)
            print("КОНТЕКСТ ПЕРЕПОЛНЕН")
            print("=" * 60)

            print(
                f"Количество токенов: "
                f"{full_prompt_tokens}"
            )

            print(
                f"Текущий лимит:      "
                f"{self.token_limit}"
            )

            print()
            print(
                "Запрос НЕ отправлен в Gemini API."
            )

            print(
                "Увеличьте лимит командой "
                "'limit ЧИСЛО' или очистите "
                "историю командой 'clear'."
            )

            return None

        # Проверка реального лимита модели
        if full_prompt_tokens > self.input_token_limit:
            print()
            print("ОШИБКА:")
            print(
                "Превышен реальный лимит "
                "контекста модели."
            )

            return None

        # Запрос к Gemini
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        answer = response.text
        usage = response.usage_metadata

        api_prompt_tokens = (
            usage.prompt_token_count or 0
        )

        response_tokens = (
            usage.candidates_token_count or 0
        )

        total_tokens = (
            usage.total_token_count or 0
        )

        thoughts_tokens = (
            getattr(
                usage,
                "thoughts_token_count",
                0
            ) or 0
        )

        print()
        print("-" * 60)
        print("ТОКЕНЫ ПОСЛЕ ОТВЕТА")
        print("-" * 60)

        print(
            f"Входных токенов API: "
            f"{api_prompt_tokens}"
        )

        print(
            f"Токенов ответа:      "
            f"{response_tokens}"
        )

        print(
            f"Thinking tokens:     "
            f"{thoughts_tokens}"
        )

        print(
            f"Всего токенов API:   "
            f"{total_tokens}"
        )

        # Сохраняем диалог
        self.messages.append({
            "role": "user",
            "text": user_message
        })

        self.messages.append({
            "role": "assistant",
            "text": answer
        })

        self.save_history()

        return answer


def show_help():
    print()
    print("=" * 60)
    print("ДОСТУПНЫЕ КОМАНДЫ")
    print("=" * 60)

    print(
        "  help         — показать подсказку"
    )

    print(
        "  stats        — показать статистику токенов"
    )

    print(
        "  clear        — очистить историю диалога"
    )

    print(
        "  limit 500    — установить лимит 500 токенов"
    )

    print(
        "  limit 1000   — установить лимит 1000 токенов"
    )

    print(
        "  limit real   — вернуть реальный лимит модели"
    )

    print(
        "  exit         — завершить программу"
    )

    print()
    print(
        "Любой другой текст будет отправлен агенту."
    )

    print("=" * 60)


def main():
    agent = GeminiAgent()

    print("=" * 60)
    print("ДЕНЬ 8 — РАБОТА С ТОКЕНАМИ")
    print("=" * 60)

    print()
    print(
        f"Модель:                "
        f"{agent.model}"
    )

    print(
        f"Лимит входа модели:    "
        f"{agent.input_token_limit}"
    )

    print(
        f"Лимит выхода модели:   "
        f"{agent.output_token_limit}"
    )

    print(
        f"Текущий лимит:         "
        f"{agent.token_limit}"
    )

    print(
        f"Сообщений в истории:   "
        f"{len(agent.messages)}"
    )

    print(
        f"Токенов в истории:     "
        f"{agent.get_history_tokens()}"
    )

    # Показываем команды при запуске
    show_help()

    while True:
        print()

        user_message = input("Вы: ").strip()

        if not user_message:
            continue

        command = user_message.lower()

        # HELP
        if command == "help":
            show_help()
            continue

        # EXIT
        if command == "exit":
            print()
            print("Агент: До свидания!")
            break

        # CLEAR
        if command == "clear":
            agent.clear_history()

            print()
            print("История очищена.")
            continue

        # STATS
        if command == "stats":
            agent.show_stats()
            continue

        # LIMIT
        if command.startswith("limit "):
            value = user_message[6:].strip()

            if value.lower() == "real":
                agent.reset_token_limit()

                print()
                print(
                    "Установлен реальный лимит модели:"
                )

                print(agent.token_limit)
                continue

            try:
                new_limit = int(value)

                if new_limit <= 0:
                    print()
                    print(
                        "Лимит должен быть больше 0."
                    )
                    continue

                if new_limit > agent.input_token_limit:
                    print()
                    print(
                        "Нельзя установить лимит выше "
                        "реального лимита модели."
                    )

                    print(
                        f"Реальный лимит: "
                        f"{agent.input_token_limit}"
                    )

                    continue

                agent.set_token_limit(new_limit)

                print()
                print(
                    f"Установлен тестовый лимит: "
                    f"{new_limit} токенов."
                )

            except ValueError:
                print()
                print("Неверное значение.")
                print(
                    "Пример: limit 500"
                )

            continue

        # ЗАПРОС К АГЕНТУ
        try:
            answer = agent.ask(user_message)

            if answer is not None:
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