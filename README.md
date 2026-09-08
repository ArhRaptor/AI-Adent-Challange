# День 7 — Сохранение контекста

## Задание

Добавить агенту сохранение контекста между запусками приложения.

Требования:

- хранить историю диалога (`messages`) в JSON или SQLite;
- при запуске агента загружать сохранённую историю;
- передавать предыдущий контекст в LLM;
- после каждого ответа сохранять обновлённую историю;
- после перезапуска приложения продолжать диалог с учётом предыдущих сообщений.

Необходимо проверить работу на практике:

1. начать диалог с агентом;
2. сообщить агенту информацию;
3. завершить приложение;
4. запустить приложение повторно;
5. задать вопрос о предыдущем разговоре;
6. убедиться, что агент использует сохранённый контекст.

---

## Цель

В Day 6 был создан простой класс `GeminiAgent`, который принимал сообщение пользователя, отправлял его в Gemini API и возвращал ответ.

Однако после завершения программы информация о предыдущем разговоре терялась.

Цель Day 7 — добавить агенту постоянную историю диалога.

Теперь схема работы выглядит так:

```text
             ┌─────────────────┐
             │  history.json   │
             └────────┬────────┘
                      │
                      ↓
Пользователь → CLI → GeminiAgent → Gemini API
                      │
                      ↓
             ┌─────────────────┐
             │  history.json   │
             └─────────────────┘
```

При запуске агент читает историю из `history.json`.

После каждого успешного ответа новая история записывается обратно в файл.

---

## Используемые технологии

- Python
- Google Gemini API
- `google-genai`
- JSON
- модуль `json`
- модуль `os`
- CLI

В качестве языковой модели используется:

`gemini-3.6-flash`

---

## Структура проекта

Основные файлы:

```text
AI-Adent-Challange/
│
├── main.py
├── history.json
└── README.md
```

`main.py` содержит агента и CLI-интерфейс.

`history.json` содержит сохранённую историю разговора.

`README.md` содержит описание реализации.

---

## Хранение истории

История хранится внутри агента:

```python
self.messages = self.load_history()
```

`messages` представляет собой список сообщений пользователя и ассистента.

Например:

```json
[
  {
    "role": "user",
    "text": "Запомни: моего робота зовут Марсик."
  },
  {
    "role": "assistant",
    "text": "Хорошо, я запомнил, что твоего робота зовут Марсик."
  }
]
```

Каждое сообщение содержит:

- `role` — автор сообщения;
- `text` — текст сообщения.

---

## Загрузка истории

При создании агента вызывается:

```python
self.messages = self.load_history()
```

Метод `load_history()` проверяет существование файла:

```python
def load_history(self):
    if not os.path.exists(self.history_file):
        return []

    try:
        with open(self.history_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []
```

Если `history.json` ещё не существует, агент начинает работу с пустой историей:

```python
[]
```

Если файл существует, сохранённые сообщения загружаются обратно в `self.messages`.

Таким образом, история восстанавливается даже после полного завершения программы.

---

## Сохранение истории

Для сохранения используется метод:

```python
def save_history(self):
    with open(self.history_file, "w", encoding="utf-8") as file:
        json.dump(
            self.messages,
            file,
            ensure_ascii=False,
            indent=2
        )
```

Параметр:

```python
ensure_ascii=False
```

позволяет сохранять русский текст в читаемом виде.

Параметр:

```python
indent=2
```

форматирует JSON, чтобы его было удобно читать.

---

## Формирование контекста

Самого хранения сообщений в JSON недостаточно.

Чтобы модель действительно учитывала предыдущий разговор, история добавляется к новому запросу.

За это отвечает метод:

```python
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
```

Например, пользователь ранее сообщил:

```text
Запомни: моего робота зовут Марсик.
```

После перезапуска он спрашивает:

```text
Как зовут моего робота?
```

Агент формирует запрос примерно следующего вида:

```text
Пользователь: Запомни: моего робота зовут Марсик.

Ассистент: Хорошо, я запомнил, что твоего робота зовут Марсик.

Пользователь: Как зовут моего робота?

Ассистент:
```

Таким образом, Gemini получает не только новый вопрос, но и предыдущий контекст.

---

## Метод `ask()`

Основная логика работы агента находится в методе:

```python
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
```

Метод выполняет следующие действия:

1. получает новое сообщение пользователя;
2. добавляет к нему предыдущую историю;
3. отправляет сформированный контекст в Gemini API;
4. получает ответ модели;
5. добавляет сообщение пользователя в `messages`;
6. добавляет ответ модели в `messages`;
7. сохраняет обновлённую историю в `history.json`;
8. возвращает ответ в CLI.

---

## Полный код

```python
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
```

---

## Проверка работы

### Первый запуск

Запускаем программу:

```powershell
py main.py
```

Сообщаем агенту информацию:

```text
Вы: Запомни: моего робота зовут Марсик.
```

После ответа можно проверить память в рамках текущего запуска:

```text
Вы: Как зовут моего робота?
```

Агент должен использовать предыдущий контекст и ответить:

```text
Агент:
Твоего робота зовут Марсик.
```

После этого завершаем программу:

```text
Вы: exit
```

---

## Проверка файла

После первого разговора появляется файл:

```text
history.json
```

Его содержимое можно посмотреть из PowerShell:

```powershell
Get-Content history.json
```

В файле находятся сообщения предыдущего диалога.

---

## Проверка после перезапуска

Повторно запускаем программу:

```powershell
py main.py
```

При запуске агент сообщает количество загруженных сообщений:

```text
Загружено сообщений из истории: 4
```

Теперь можно сразу спросить:

```text
Вы: Напомни, как зовут моего робота?
```

Несмотря на то, что приложение было полностью завершено и запущено заново, агент получает предыдущую историю из `history.json` и может ответить:

```text
Агент:
Твоего робота зовут Марсик.
```

Это подтверждает, что контекст сохраняется между запусками программы.

---

## Что продемонстрировано на видео

На видео показано:

1. запуск агента;
2. передача агенту информации, которую необходимо запомнить;
3. получение ответа;
4. появление данных в `history.json`;
5. завершение приложения командой `exit`;
6. повторный запуск `main.py`;
7. загрузка предыдущей истории;
8. вопрос о данных из прошлого разговора;
9. правильный ответ агента с использованием восстановленного контекста.

---

## Результат

В рамках Day 7 агент получил постоянную память диалога.

Реализовано:

- хранение `messages`;
- сохранение сообщений пользователя;
- сохранение ответов LLM;
- запись истории в JSON;
- загрузка истории при запуске;
- добавление предыдущей истории к новым запросам;
- восстановление контекста после перезапуска приложения.

Теперь жизненный цикл запроса выглядит так:

```text
Запуск приложения
        ↓
Загрузка history.json
        ↓
Получение сообщения пользователя
        ↓
Добавление предыдущей истории
        ↓
GeminiAgent
        ↓
Gemini API
        ↓
Ответ модели
        ↓
Добавление новых сообщений в messages
        ↓
Сохранение history.json
        ↓
Вывод ответа пользователю
```

---

## Вывод

В Day 6 был создан отдельный агент, инкапсулирующий работу с LLM.

В Day 7 агент был расширен механизмом постоянного хранения контекста.

Главное отличие:

```text
Day 6:

Пользователь → Агент → LLM → Ответ


Day 7:

history.json
     ↓
Пользователь → Агент → LLM → Ответ
                 ↓
            history.json
```

Теперь завершение программы не уничтожает историю разговора.

После нового запуска `GeminiAgent` загружает сохранённые сообщения и использует их при формировании следующих запросов.

Таким образом, агент способен продолжить диалог так, как будто приложение не выключалось.