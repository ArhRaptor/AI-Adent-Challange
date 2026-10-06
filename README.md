# День 27 — Интеграция локальной LLM в приложение

## Цель

Интегрировать локальную Large Language Model в реальное приложение.

В качестве приложения реализован консольный AI-чат:

```text
CLI Application
+
Ollama
+
Qwen2.5-Coder 0.5B
```

Приложение:

- принимает сообщения пользователя;
- отправляет их локальной LLM;
- получает ответ через HTTP API;
- отображает ответ в консоли;
- хранит историю текущего диалога;
- не использует облачные LLM API.

---

# Развитие проекта

## День 26

На предыдущем этапе была запущена локальная модель:

```text
qwen2.5-coder:0.5b
```

и проверена работа:

```text
Ollama
↓
CLI
↓
HTTP API
↓
Python
```

Day 26 отвечал на вопрос:

```text
Можем ли мы запустить LLM локально?
```

## День 27

Теперь локальная модель интегрирована в приложение.

```text
User
 ↓
CLI Application
 ↓
Local LLM
 ↓
Response
 ↓
User
```

Day 27 отвечает уже на другой вопрос:

```text
Можем ли мы использовать локальную LLM
как часть собственного приложения?
```

---

# Используемые технологии

```text
Python
Ollama
Qwen2.5-Coder 0.5B
HTTP API
```

Модель:

```text
qwen2.5-coder:0.5b
```

Локальный Ollama API:

```text
http://localhost:11434
```

Chat endpoint:

```text
POST /api/chat
```

---

# Архитектура

```text
                  USER
                    ↓
             CLI Application
                    ↓
              LocalChatApp
                    ↓
            LocalLLMClient
                    ↓
               HTTP POST
                    ↓
       localhost:11434/api/chat
                    ↓
                 Ollama
                    ↓
        qwen2.5-coder:0.5b
                    ↓
             Local Inference
                    ↓
                Response
                    ↓
             CLI Application
                    ↓
                  USER
```

Вся генерация выполняется локальной моделью.

Облачные LLM API для генерации ответов не используются.

---

# Основные классы

Приложение разделено на две основные части:

```text
LocalLLMClient
LocalChatApp
```

---

# LocalLLMClient

Класс:

```python
LocalLLMClient
```

отвечает за взаимодействие с Ollama.

Он получает:

```python
messages
```

формирует HTTP request и отправляет его на:

```text
http://localhost:11434/api/chat
```

Пример payload:

```json
{
  "model": "qwen2.5-coder:0.5b",
  "messages": [
    {
      "role": "user",
      "content": "What is Python?"
    }
  ],
  "stream": false
}
```

Ответ Ollama содержит сообщение модели:

```json
{
  "message": {
    "role": "assistant",
    "content": "..."
  }
}
```

Приложение извлекает:

```python
result["message"]["content"]
```

и показывает текст пользователю.

---

# LocalChatApp

Класс:

```python
LocalChatApp
```

реализует интерфейс консольного приложения.

Он отвечает за:

- ввод пользователя;
- историю сообщений;
- команды;
- вызов LocalLLMClient;
- отображение ответа;
- обработку ошибок.

---

# История диалога

В отличие от одиночного запроса Day 26, приложение Day 27 хранит сообщения текущего разговора.

История находится в:

```python
self.messages
```

Структура:

```python
[
    {
        "role": "system",
        "content": "..."
    },
    {
        "role": "user",
        "content": "What is Python?"
    },
    {
        "role": "assistant",
        "content": "..."
    }
]
```

При следующем запросе история снова передаётся модели.

Получается:

```text
Question 1
   ↓
Answer 1
   ↓
Question 2
   ↓
History + Question 2
   ↓
Answer 2
```

Это позволяет вести многошаговый диалог.

---

# System Prompt

В начало истории добавляется system message:

```text
You are a helpful local AI assistant.
Answer clearly and concisely.
If you do not know something,
say that you do not know.
```

Он задаёт базовое поведение локального ассистента.

---

# Chat API

В Day 26 использовался endpoint:

```text
/api/generate
```

В Day 27 используется:

```text
/api/chat
```

Основное отличие состоит в том, что приложение передаёт не только один prompt, а список сообщений:

```python
"messages": messages
```

Это позволяет передавать модели историю разговора.

---

# Работа без облачной модели

В приложении отсутствуют:

```text
Gemini API
OpenAI API
Cloud LLM API keys
```

Вместо этого используется:

```python
OLLAMA_URL = "http://localhost:11434/api/chat"
```

и:

```python
MODEL = "qwen2.5-coder:0.5b"
```

Цепочка выглядит так:

```text
Python
 ↓
localhost
 ↓
Ollama
 ↓
Local LLM
```

---

# Запуск

Сначала необходимо убедиться, что Ollama установлена.

```powershell
ollama --version
```

Проверить локальные модели:

```powershell
ollama list
```

В списке должна присутствовать:

```text
qwen2.5-coder:0.5b
```

После этого приложение запускается:

```powershell
py main.py
```

---

# Интерфейс

После запуска приложение показывает:

```text
DAY 27 — LOCAL LLM CHAT

Модель: qwen2.5-coder:0.5b
Ollama API: http://localhost:11434/api/chat

Облачные LLM API не используются.
```

После этого пользователь может вводить произвольные сообщения:

```text
Вы: What is Python?
```

Приложение отправляет запрос локальной модели и выводит:

```text
LOCAL LLM:
...
```

Также отображается время генерации:

```text
Время ответа: ... сек.
```

---

# Команды

CLI поддерживает несколько команд.

## Help

```text
/help
```

Показывает список доступных команд.

## History

```text
/history
```

Показывает историю текущего разговора.

## Clear

```text
/clear
```

Очищает историю диалога.

System prompt при этом сохраняется.

## Exit

```text
/exit
```

Завершает приложение.

---

# Проверка контекста

Для проверки можно использовать последовательный диалог:

```text
What is Python?
```

Затем:

```text
Write a simple Python function that adds two numbers.
```

После этого:

```text
What did I ask you to write in my previous message?
```

Последний запрос проверяет передачу истории предыдущих сообщений модели.

---

# Обработка ошибок

Приложение обрабатывает ошибку подключения к Ollama.

Например, если локальный сервер недоступен:

```text
Ошибка подключения к Ollama.
Проверь, что Ollama запущена.
```

Это позволяет отличить проблему приложения от отсутствия локального LLM runtime.

---

# Зависимости

Для HTTP-запросов используется стандартная библиотека Python:

```python
urllib.request
```

Для JSON:

```python
json
```

Для измерения времени:

```python
time
```

Поэтому дополнительные Python-пакеты для работы клиента не требуются.

---

# Day 26 vs Day 27

| Возможность | Day 26 | Day 27 |
|---|---|---|
| Local LLM | Да | Да |
| Ollama | Да | Да |
| HTTP API | Да | Да |
| Python client | Да | Да |
| Заранее заданные тесты | Да | Нет |
| Интерактивный пользовательский ввод | Нет | Да |
| CLI application | Нет | Да |
| Chat history | Нет | Да |
| Несколько сообщений в диалоге | Нет | Да |

Таким образом Day 27 превращает технический эксперимент Day 26 в пользовательское приложение.

---

# Ограничения

Текущая версия является учебным CLI-приложением.

История:

```python
self.messages
```

хранится только в оперативной памяти.

После:

```text
/exit
```

она не сохраняется на диск.

Также используется компактная модель:

```text
qwen2.5-coder:0.5b
```

Эксперимент Day 26 уже показал, что небольшая модель может допускать ошибки в reasoning и объяснениях.

Поэтому:

```text
Local execution
≠
Guaranteed answer quality
```

---

# Что реализовано

В Day 27 реализовано:

- CLI-приложение;
- интеграция с Ollama;
- локальная LLM;
- HTTP `/api/chat`;
- пользовательский ввод;
- получение ответа модели;
- отображение ответа;
- измерение времени ответа;
- conversation history;
- system prompt;
- `/help`;
- `/history`;
- `/clear`;
- `/exit`;
- обработка ошибки подключения;
- работа без облачных LLM API.

---

# Результат

Получено приложение:

```text
User
 ↓
CLI
 ↓
Python
 ↓
Ollama HTTP API
 ↓
Local LLM
 ↓
Response
 ↓
CLI
 ↓
User
```

Таким образом локальная LLM больше не является отдельным экспериментом.

Она стала backend-моделью собственного CLI-приложения.

Ключевой результат Day 27:

```text
Local LLM
+
Application
=
Local AI Application
```

Приложение может принимать пользовательские запросы и генерировать ответы полностью через локальную модель без использования облачного LLM API.