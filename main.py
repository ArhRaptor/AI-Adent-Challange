import json
import time
import urllib.error
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen2.5-coder:0.5b"

SYSTEM_PROMPT = (
    "You are a helpful local AI assistant. "
    "Answer clearly and concisely. "
    "If you do not know something, say that you do not know."
)


class LocalLLMClient:
    def __init__(self, url: str, model: str):
        self.url = url
        self.model = model

    def chat(self, messages: list[dict]) -> tuple[str, float]:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.url,
            data=data,
            headers={
                "Content-Type": "application/json"
            },
            method="POST",
        )

        start_time = time.perf_counter()

        with urllib.request.urlopen(
            request,
            timeout=300,
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        elapsed = time.perf_counter() - start_time

        answer = result["message"]["content"]

        return answer, elapsed


class LocalChatApp:
    def __init__(self):
        self.client = LocalLLMClient(
            url=OLLAMA_URL,
            model=MODEL,
        )

        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

    def print_help(self):
        print()
        print("Команды:")
        print("  /help    - показать команды")
        print("  /history - показать историю")
        print("  /clear   - очистить историю")
        print("  /exit    - выйти")
        print()

    def print_history(self):
        print()
        print("=" * 70)
        print("ИСТОРИЯ")
        print("=" * 70)

        conversation = self.messages[1:]

        if not conversation:
            print("История пуста.")
            return

        for message in conversation:
            role = message["role"].upper()
            content = message["content"]

            print()
            print(f"{role}:")
            print(content)

    def clear_history(self):
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
        ]

        print()
        print("История очищена.")

    def ask(self, user_message: str):
        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        try:
            answer, elapsed = self.client.chat(
                self.messages
            )

        except urllib.error.URLError as error:
            self.messages.pop()

            print()
            print("Ошибка подключения к Ollama.")
            print("Проверь, что Ollama запущена.")
            print()
            print(f"Детали: {error}")
            return

        except Exception as error:
            self.messages.pop()

            print()
            print("Ошибка:")
            print(error)
            return

        self.messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        print()
        print("LOCAL LLM:")
        print(answer)

        print()
        print(f"Время ответа: {elapsed:.2f} сек.")

    def run(self):
        print("=" * 70)
        print("DAY 27 — LOCAL LLM CHAT")
        print("=" * 70)

        print()
        print(f"Модель: {MODEL}")
        print(f"Ollama API: {OLLAMA_URL}")

        print()
        print("Облачные LLM API не используются.")

        self.print_help()

        while True:
            try:
                user_input = input("Вы: ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                print("Завершение работы.")
                break

            if not user_input:
                continue

            command = user_input.lower()

            if command == "/exit":
                print()
                print("Завершение работы.")
                break

            if command == "/help":
                self.print_help()
                continue

            if command == "/history":
                self.print_history()
                continue

            if command == "/clear":
                self.clear_history()
                continue

            self.ask(user_input)


def main():
    app = LocalChatApp()
    app.run()


if __name__ == "__main__":
    main()