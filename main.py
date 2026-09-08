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

    def load_history(self):
        if not os.path.exists(self.history_file):
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return []

    def save_history(self):
        with open(self.history_file, "w", encoding="utf-8") as file:
            json.dump(
                self.messages,
                file,
                ensure_ascii=False,
                indent=2
            )

    def build_prompt(self, user_message):
        prompt_parts = []

        for message in self.messages:
            role = message["role"]
            text = message["text"]

            if role == "user":
                prompt_parts.append(f"Пользователь: {text}")
            else:
                prompt_parts.append(f"Ассистент: {text}")

        prompt_parts.append(f"Пользователь: {user_message}")
        prompt_parts.append("Ассистент:")

        return "\n\n".join(prompt_parts)

    def ask(self, user_message):
        prompt = self.build_prompt(user_message)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        answer = response.text

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


def main():
    agent = GeminiAgent()

    print("=" * 60)
    print("ДЕНЬ 7 — СОХРАНЕНИЕ КОНТЕКСТА")
    print("=" * 60)

    print()
    print(f"Загружено сообщений из истории: {len(agent.messages)}")
    print()
    print("Введите сообщение.")
    print("Для выхода напишите: exit")

    while True:
        print()

        user_message = input("Вы: ")

        if user_message.lower() == "exit":
            print("Агент: До свидания!")
            break

        try:
            answer = agent.ask(user_message)

            print()
            print("Агент:")
            print(answer)

        except Exception as error:
            print()
            print("Ошибка при обращении к API:")
            print(error)


if __name__ == "__main__":
    main()