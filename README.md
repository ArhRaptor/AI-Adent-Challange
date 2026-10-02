# День 25 — Мини-чат с RAG + памятью

## Цель

Создать мини-чат, который объединяет:

- историю диалога;
- RAG-поиск по локальной базе;
- contextual query rewrite;
- фильтрацию по similarity;
- источники в ответах;
- task memory;
- сохранение состояния между запусками.

Теперь RAG работает не с одним независимым вопросом, а внутри продолжительного диалога.

---

# Развитие проекта

## День 21 — Document Indexing

```text
Documents
    ↓
Chunking
    ↓
Embeddings
    ↓
Metadata
    ↓
Local Index
```

## День 22 — First RAG

```text
Question
    ↓
Embedding
    ↓
Retrieval
    ↓
Top-K
    ↓
Context
    ↓
LLM
```

## День 23 — Improved Retrieval

```text
Question
    ↓
Query Rewrite
    ↓
Top-K Candidates
    ↓
Similarity Filter
    ↓
Relevant Chunks
```

## День 24 — Grounded Answers

```text
Retrieve
    ↓
Filter
    ↓
Relevance Gate
    ↓
Grounded Answer
    ↓
Sources
    ↓
Validation
```

## День 25 — Conversational RAG

```text
User Message
     │
     ├──────────────→ Conversation History
     │
     ↓
Task Memory Update
     │
     ↓
Contextual Query Rewrite
     │
     ↓
RAG Retrieval
     │
     ↓
Similarity Filter
     │
     ↓
History + Task State + RAG Context
     │
     ↓
LLM
     │
     ↓
Answer + Sources
     │
     ↓
Save History
```

---

# Структура проекта

```text
.
├── main.py
├── index_documents.py
├── control_questions.json
├── README.md
├── .gitignore
│
├── documents/
│   ├── README.md
│   ├── rag_notes.md
│   ├── mcp_notes.md
│   ├── android_architecture.md
│   ├── agent_design.txt
│   ├── chunking_comparison.md
│   ├── python_services.md
│   ├── software_architecture.md
│   ├── indexer_example.py
│   ├── compose_example.kt
│   └── index_config_examples.json
│
├── indexes/
│   ├── index_fixed.json
│   └── index_structured.json
│
└── data/
    ├── chat_history.json
    └── task_state.json
```

`indexes/` и `data/` являются runtime/generated data и не обязаны храниться в Git.

---

# Три вида памяти

Главная идея Day 25 — разделить три разных источника контекста.

```text
Knowledge Memory
Conversation Memory
Task Memory
```

Они решают разные задачи.

---

## 1. Knowledge Memory — RAG

Источником знаний служит:

```text
indexes/index_structured.json
```

Индекс содержит:

```text
chunk text
metadata
embedding
```

RAG отвечает на вопрос:

```text
Что написано в документах?
```

---

## 2. Conversation Memory — History

История хранится в:

```text
data/chat_history.json
```

Пример:

```json
[
  {
    "role": "user",
    "content": "Я хочу разобраться с RAG."
  },
  {
    "role": "assistant",
    "content": "..."
  }
]
```

History отвечает на вопрос:

```text
О чём мы недавно разговаривали?
```

Полная история сохраняется на диск.

При этом в prompt передаётся только ограниченное окно:

```python
HISTORY_WINDOW = 8
```

Это предотвращает бесконечный рост prompt.

---

## 3. Task Memory — Task State

Task state хранится отдельно:

```text
data/task_state.json
```

Структура:

```json
{
  "goal": "",
  "clarifications": [],
  "constraints": [],
  "terms": {}
}
```

Task State отвечает на вопросы:

```text
Какая сейчас цель?

Что пользователь уже уточнил?

Какие ограничения действуют?

Какие термины были определены?
```

---

# Почему History и Task State разделены

История — это последовательность сообщений:

```text
Message 1
Message 2
Message 3
...
Message 20
```

Но в prompt используется только часть:

```text
last 8 messages
```

Поэтому важная информация из начала разговора может выйти за пределы окна.

Например:

```text
Message 1:
"Моя цель — улучшить retrieval."
```

После длинного разговора это сообщение может исчезнуть из recent history.

Task state продолжает хранить:

```json
{
  "goal": "Улучшить retrieval"
}
```

Таким образом:

```text
History
=
что недавно происходило

Task State
=
что важно помнить для задачи
```

---

# Persistent Memory

История и task state сохраняются на диск:

```text
data/chat_history.json
data/task_state.json
```

Поэтому после:

```text
/exit
```

и повторного:

```powershell
py main.py
```

состояние может быть загружено обратно.

Получается:

```text
Chat
 ↓
Save
 ↓
Exit
 ↓
Restart
 ↓
Load
 ↓
Continue
```

---

# Task State Update

Перед каждым RAG-запросом вызывается:

```python
update_task_state()
```

Модель получает:

```text
Current Task State
+
Recent History
+
New User Message
```

и обновляет:

```text
goal
clarifications
constraints
terms
```

---

# Goal

Поле:

```json
"goal"
```

хранит главную текущую цель диалога.

Например:

```json
{
  "goal": "Разобраться, как улучшить retrieval в RAG-системе"
}
```

---

# Clarifications

Поле:

```json
"clarifications"
```

содержит важные уточнения пользователя.

Например:

```json
{
  "clarifications": [
    "Для задачи важнее сохранение логической структуры"
  ]
}
```

---

# Constraints

Поле:

```json
"constraints"
```

хранит ограничения текущей задачи.

Например:

```json
{
  "constraints": [
    "Использовать только локальный индекс"
  ]
}
```

---

# Terms

Пользователь может определить собственное значение термина.

Например:

```text
Под retrieval я имею в виду
поиск chunks до вызова LLM.
```

Task memory может сохранить:

```json
{
  "terms": {
    "retrieval": "поиск chunks до вызова LLM"
  }
}
```

Это помогает сохранять одинаковое значение термина на протяжении длинного разговора.

---

# Conversational Query Rewrite

В обычном RAG пользователь задаёт самостоятельный вопрос:

```text
Какие недостатки есть у fixed chunking?
```

В чате follow-up может выглядеть так:

```text
А какие у него недостатки?
```

Сам по себе такой запрос плохо подходит для semantic search.

Поэтому Day 25 использует:

```python
rewrite_query()
```

Модель получает:

```text
Current Question
+
Recent History
+
Task State
```

и строит самостоятельный поисковый запрос.

Pipeline:

```text
"А какие у него недостатки?"
            ↓
History + Task State
            ↓
Contextual Query Rewrite
            ↓
самостоятельный search query
```

---

# Retrieval

После rewriting создаётся query embedding.

```text
Rewritten Query
       ↓
Embedding
       ↓
Vector Search
```

Embedding сравнивается с embeddings chunks через cosine similarity.

Сначала выбираются:

```python
TOP_K_BEFORE_FILTER = 8
```

кандидатов.

---

# Similarity Filtering

После retrieval применяется:

```python
SIMILARITY_THRESHOLD = 0.45
```

Остаются только chunks:

```text
similarity >= threshold
```

После этого используется максимум:

```python
TOP_K_AFTER_FILTER = 4
```

Полный retrieval:

```text
Query
  ↓
Embedding
  ↓
All Chunks
  ↓
Top-8
  ↓
Similarity Filter
  ↓
Top-4 max
```

Значение threshold является экспериментальным и должно оцениваться по реальным similarity scores проекта.

---

# Формирование ответа

Для генерации ответа модель получает три блока:

```text
TASK STATE

RECENT HISTORY

RAG CONTEXT
```

и текущий вопрос:

```text
CURRENT QUESTION
```

Получается:

```text
Task State
     │
History
     ├────→ LLM → Answer
RAG  │
     │
Question
```

---

# Разделение ролей контекста

Task State и History используются для понимания разговора.

RAG Context используется как источник фактической информации из локальных документов.

Важно:

```text
History != Knowledge Base
```

То, что пользователь или ассистент ранее что-то сказал, само по себе не превращает это утверждение в факт из документов.

---

# Источники

Содержательный RAG-ответ должен возвращать:

```text
Answer
+
Sources
```

Каждый source содержит:

```text
source
section
chunk_id
```

Пример:

```text
documents/rag_notes.md

Section:
Retrieval

Chunk ID:
rag_notes.md::structured::0004
```

---

# Source Validation

После генерации вызывается:

```python
validate_sources()
```

Программа проверяет:

```text
есть ли sources

существует ли chunk_id
среди retrieved chunks

совпадает ли source

совпадает ли section
```

Таким образом LLM не должна использовать источник, который отсутствовал в RAG context.

---

# Режим "Не знаю"

Если после similarity filtering не осталось подходящих chunks:

```text
Retrieval
    ↓
Filter
    ↓
0 Relevant Chunks
```

система возвращает:

```text
Не знаю. В локальной базе
недостаточно релевантной информации.
Пожалуйста, уточните вопрос.
```

В таком случае:

```text
Источники:
Нет.
```

Это корректнее, чем прикреплять нерелевантный или выдуманный источник.

---

# CLI

Основной интерфейс проекта — консольный чат.

Запуск:

```powershell
py main.py
```

После запуска пользователь может вести продолжительный диалог:

```text
Вы: ...

Ассистент:
...

Источники:
...
```

---

# Команды

## `/help`

Показывает доступные команды.

```text
/help
```

## `/state`

Показывает текущую task memory:

```text
/state
```

## `/history`

Показывает recent conversation history:

```text
/history
```

## `/clear`

Удаляет текущую историю и task state:

```text
/clear
```

## `/exit`

Завершает приложение:

```text
/exit
```

---

# Первый длинный сценарий

Перед тестированием:

```text
/clear
```

Сценарий:

```text
1. Я хочу разобраться, как улучшить retrieval в RAG-системе.

2. Начнем с chunking. Какие варианты есть в нашей базе?

3. Чем fixed chunking отличается от structured?

4. А какой недостаток у fixed подхода?

5. Зачем тогда нужен overlap?

6. Считай, что для нашей задачи важнее сохранение логической структуры.

7. Какие преимущества тогда дает structured chunking?

8. Но что делать, если section получился слишком большим?

9. Теперь перейдем к embeddings.

10. Как они участвуют в retrieval?

11. А similarity какую роль здесь играет?

12. С учетом всего, что мы обсудили, какая сейчас цель нашего диалога?
```

После этого:

```text
/state
```

позволяет проверить, сохранилась ли первоначальная цель и важные ограничения.

---

# Второй длинный сценарий

После:

```text
/clear
```

можно проверить другой диалог:

```text
1. Я хочу спроектировать агента для работы с технической базой знаний.

2. Он должен использовать RAG.

3. Источники должны выводиться в каждом содержательном ответе.

4. Под памятью будем понимать отдельно историю и task state.

5. Зачем нам вообще task state?

6. Чем он отличается от истории?

7. Допустим история ограничена последними 8 сообщениями.

8. Что произойдет со старыми деталями?

9. Поэтому цель задачи должна храниться отдельно.

10. Какие еще ограничения стоит держать в task state?

11. А термины пользователя зачем сохранять?

12. Напомни, какие требования к агенту мы уже зафиксировали.

13. Теперь свяжи это с RAG.

14. Какая итоговая архитектура получается?
```

После этого:

```text
/state
```

проверяет сохранение цели и требований после длинного диалога.

---

# Что проверяем

В двух длинных сценариях необходимо проверить:

```text
Conversation continuity
Task goal preservation
Constraint preservation
Term preservation
Contextual query rewrite
RAG retrieval
Similarity filtering
Sources in answers
Source validation
Persistence
```

Особенно важны follow-up вопросы:

```text
А какие у него недостатки?
```

```text
А зачем он нужен?
```

```text
А что делать в таком случае?
```

Они проверяют, способен ли query rewrite восстановить смысл из истории и task state.

---

# Проверка Persistence

После нескольких сообщений:

```text
/exit
```

Запускаем приложение снова:

```powershell
py main.py
```

Затем:

```text
/state
```

и:

```text
/history
```

Task state и история должны загружаться из JSON-файлов.

---

# Runtime Files

Приложение автоматически создаёт:

```text
data/chat_history.json
data/task_state.json
```

Эти файлы не требуется создавать вручную.

Они содержат состояние конкретного запуска/диалога и могут быть исключены из Git.

---

# Индекс

Индекс создаётся отдельным скриптом:

```powershell
py index_documents.py
```

Результат:

```text
indexes/index_fixed.json
indexes/index_structured.json
```

Основной чат использует:

```text
indexes/index_structured.json
```

Если индекс уже существует и документы не изменились, создавать его заново перед каждым запуском не требуется.

---

# Git Ignore

Генерируемые данные рекомендуется исключить:

```gitignore
indexes/
data/
__pycache__/
*.pyc
```

При этом в Git остаются:

```text
main.py
index_documents.py
control_questions.json
README.md
documents/
```

---

# Что реализовано

В Day 25 реализованы:

- CLI chat;
- persistent conversation history;
- ограниченное history window;
- task memory;
- goal;
- clarifications;
- constraints;
- user-defined terms;
- автоматическое обновление task state;
- contextual query rewriting;
- semantic retrieval;
- similarity filtering;
- RAG для каждого сообщения;
- ответы с источниками;
- source validation;
- режим `unknown`;
- сохранение состояния между запусками;
- команды управления CLI.

---

# Production-like подход

Проект разделяет разные типы состояния:

```text
Knowledge
    ↓
RAG Index

Conversation
    ↓
Chat History

Task
    ↓
Task State
```

Вместо передачи всей истории в каждый prompt используется:

```text
Recent History
+
Compact Task State
+
Retrieved Knowledge
```

Это позволяет лучше контролировать размер контекста и сохранять важную информацию длинного диалога.

---

# Итоговая архитектура

```text
                     USER
                       ↓
                  New Message
                       │
          ┌────────────┴────────────┐
          ↓                         ↓
   Conversation                 Task State
      History                     Update
          │                         │
          └────────────┬────────────┘
                       ↓
             Contextual Rewrite
                       ↓
                 RAG Retrieval
                       ↓
               Similarity Filter
                       ↓
                Relevant Chunks
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
       History     Task State    RAG Context
          └────────────┼────────────┘
                       ↓
                      LLM
                       ↓
               Answer + Sources
                       ↓
              Source Validation
                       ↓
                Save History
```

---

# Результат

Получен мини-чат с:

```text
RAG
+
Conversation History
+
Task Memory
+
Contextual Query Rewrite
+
Sources
+
Persistence
```

Система способна поддерживать многошаговый диалог, использовать локальную базу знаний и отдельно сохранять важное состояние текущей задачи.

Ключевая идея Day 25:

```text
History ≠ Task State ≠ Knowledge Base
```

Каждый слой памяти имеет отдельную роль.

Итоговый pipeline:

```text
Remember
→ Rewrite
→ Retrieve
→ Filter
→ Answer
→ Cite
→ Validate
→ Persist
```