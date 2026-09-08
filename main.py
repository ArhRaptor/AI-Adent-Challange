from google import genai


class GeminiAgent:
    def __init__(self, model="gemini-3.6-flash"):
        self.client = genai.Client()
        self.model = model

    def ask(self, user_message):
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_message
        )

        return response.text


def main():
    agent = GeminiAgent()

    print("=" * 60)
    print("ДЕНЬ 6 — ПЕРВЫЙ АГЕНТ")
    print("=" * 60)

    print()
    print("Простой CLI-агент на базе Gemini.")
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