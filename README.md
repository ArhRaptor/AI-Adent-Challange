# День 21 — Индексация документов

## Цель

Создать локальный pipeline индексации документов для дальнейшего использования в semantic search и RAG.

Pipeline выполняет:

```text
Documents
    ↓
Loading
    ↓
Chunking
    ↓
Embeddings
    ↓
Metadata
    ↓
Local Index
```

Дополнительно реализованы и сравниваются две стратегии разбиения документов:

```text
Fixed-size Chunking
        VS
Structure-aware Chunking
```

---

# Корпус документов

Для эксперимента подготовлен локальный набор документов разных типов:

```text
documents/
├── README.md
├── rag_notes.md
├── mcp_notes.md
├── android_architecture.md
├── agent_design.txt
├── chunking_comparison.md
├── python_services.md
├── software_architecture.md
├── indexer_example.py
├── compose_example.kt
└── index_config_examples.json
```

Корпус содержит:

- Markdown;
- обычный текст;
- Python-код;
- Kotlin-код;
- JSON.

Общий объём подготовленного корпуса составляет около:

```text
79 700 символов
```

При условной оценке:

```text
~1800 символов = 1 страница
```

получается около:

```text
44 страниц текста
```

Это превышает минимальное требование задания в 20–30 страниц или эквивалентный объём кода.

---

# Тематика документов

Корпус содержит материалы по нескольким темам:

```text
RAG
MCP
AI Agents
Chunking
Embeddings
Software Architecture
Python Services
Android
Kotlin
Jetpack Compose
Document Indexing
```

Разные типы документов позволяют проверить работу chunking не только на обычном тексте, но и на структурированных Markdown-файлах и исходном коде.

---

# Структура проекта

```text
.
├── main.py
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
└── README.md
```

---

# Pipeline индексации

Полный процесс:

```text
documents/
    ↓
load_documents()
    ↓
┌───────────────────────┐
│                       │
↓                       ↓
Fixed Chunking     Structured Chunking
│                       │
↓                       ↓
Chunks                  Chunks
│                       │
↓                       ↓
Embeddings             Embeddings
│                       │
↓                       ↓
Metadata               Metadata
│                       │
↓                       ↓
index_fixed.json   index_structured.json
```

Обе стратегии используют один и тот же набор документов и одну модель embeddings.

Это позволяет сравнивать именно способ chunking.

---

# Загрузка документов

Функция:

```python
load_documents()
```

рекурсивно читает каталог:

```text
documents/
```

Поддерживаются расширения:

```text
.txt
.md
.py
.kt
.java
.json
```

Файлы читаются в UTF-8.

Пустые документы пропускаются.

Для каждого документа сохраняются:

```text
source
title
text
```

Например:

```json
{
  "source": "documents/rag_notes.md",
  "title": "rag_notes.md",
  "text": "..."
}
```

---

# Strategy 1 — Fixed-size Chunking

Первая стратегия делит документ по фиксированному размеру.

Настройки:

```python
FIXED_CHUNK_SIZE = 1200
FIXED_CHUNK_OVERLAP = 200
```

То есть один chunk содержит максимум примерно:

```text
1200 символов
```

а соседние chunks имеют overlap:

```text
200 символов
```

---

# Зачем нужен overlap

Без overlap:

```text
Chunk 1
[----------------]

Chunk 2
                  [----------------]
```

Информация на границе может потерять контекст.

С overlap:

```text
Chunk 1
[----------------]

             [----------------]
             Chunk 2
```

часть предыдущего chunk повторяется в следующем.

Это уменьшает вероятность потери смысловой связи на границе.

---

# Преимущества Fixed Chunking

Fixed-size chunking:

- очень простой;
- работает почти с любым текстом;
- создаёт chunks похожего размера;
- легко настраивается;
- не требует понимания формата документа.

---

# Недостатки Fixed Chunking

Алгоритм ничего не знает о структуре документа.

Например:

```markdown
# Authentication

Для авторизации приложение использует
JWT token, который...

---------- CHUNK BOUNDARY ----------

...передаётся серверу в HTTP header.
```

Граница может пройти:

- внутри предложения;
- внутри раздела;
- внутри функции;
- между заголовком и его содержимым.

---

# Metadata Fixed Chunk

Пример:

```json
{
  "source": "documents/rag_notes.md",
  "title": "rag_notes.md",
  "section": null,
  "chunk_id": "rag_notes.md::fixed::0003",
  "strategy": "fixed",
  "start_char": 3000,
  "end_char": 4200
}
```

Здесь `section` может быть `null`, потому что fixed chunking не анализирует логическую структуру документа.

---

# Strategy 2 — Structured Chunking

Вторая стратегия учитывает структуру документа.

Функции:

```python
detect_sections()
structured_chunking()
```

Сначала документ разбивается на логические разделы.

После этого большие разделы дополнительно ограничиваются по размеру.

---

# Markdown Chunking

Для Markdown используются заголовки:

```markdown
# RAG

## Chunking

## Embeddings

## Retrieval

## Evaluation
```

Каждый раздел становится отдельной логической единицей.

Например:

```text
section = Chunking
```

или:

```text
section = Embeddings
```

---

# Python Chunking

Для Python определяются конструкции:

```python
class Agent:
    ...
```

```python
def search():
    ...
```

```python
async def execute():
    ...
```

Таким образом chunk может соответствовать конкретной функции или классу.

Например:

```json
{
  "source": "documents/indexer_example.py",
  "title": "indexer_example.py",
  "section": "fixed_chunks",
  "chunk_id": "indexer_example.py::structured::0003",
  "strategy": "structured"
}
```

---

# Остальные форматы

Если для документа нет специального структурного parser-а, весь файл сначала рассматривается как один section:

```text
section = filename
```

Если section слишком большой, он дополнительно разбивается на ограниченные chunks.

---

# Ограничение размера Structured Chunk

Structured chunking не означает:

```text
1 section = chunk любого размера
```

Если один раздел содержит очень много текста:

```text
SECTION
   ↓
слишком большой
   ↓
разделить внутри section
```

При этом metadata исходного section сохраняются.

Это позволяет совместить:

```text
логическую структуру
+
ограниченный размер chunk
```

---

# Metadata

Каждый chunk содержит metadata.

Основные поля:

```text
source
title
section
chunk_id
strategy
```

---

# source

Путь к исходному документу.

Например:

```text
documents/mcp_notes.md
```

---

# title

Имя исходного файла.

Например:

```text
mcp_notes.md
```

---

# section

Логический раздел.

Например:

```text
Tool Composition
```

или:

```text
Agent Routing
```

Для fixed chunking значение может быть:

```text
null
```

---

# chunk_id

Каждый chunk получает уникальный идентификатор.

Fixed:

```text
mcp_notes.md::fixed::0004
```

Structured:

```text
mcp_notes.md::structured::0004
```

Это позволяет определить:

```text
документ
+
стратегию
+
номер chunk
```

---

# strategy

Metadata также явно хранит использованную стратегию:

```text
fixed
```

или:

```text
structured
```

---

# Embeddings

После chunking каждый текстовый chunk преобразуется в embedding.

Pipeline:

```text
Chunk Text
    ↓
Embedding Model
    ↓
Vector
```

Embedding представляет текст как числовой вектор.

В проекте используется Gemini Embedding API.

Модель задаётся через:

```python
EMBEDDING_MODEL
```

Для индекса используется размерность:

```python
EMBEDDING_DIMENSIONS = 768
```

---

# Создание embedding

Для каждого chunk вызывается:

```python
client.models.embed_content(...)
```

После чего полученный vector сохраняется вместе с:

```text
text
metadata
```

---

# Структура индексированного chunk

Итоговая запись выглядит примерно так:

```json
{
  "text": "Chunking determines the retrieval unit...",
  "metadata": {
    "source": "documents/chunking_comparison.md",
    "title": "chunking_comparison.md",
    "section": "Purpose",
    "chunk_id": "chunking_comparison.md::structured::0000",
    "strategy": "structured"
  },
  "embedding": [
    0.012,
    -0.034,
    0.081
  ]
}
```

Реальный embedding содержит значительно больше чисел.

---

# Local Index

В учебной реализации используется JSON.

Создаются два отдельных индекса:

```text
indexes/index_fixed.json
indexes/index_structured.json
```

Первый содержит chunks:

```text
fixed
```

второй:

```text
structured
```

---

# Структура Index

Пример:

```json
{
  "strategy": "structured",
  "embedding_model": "...",
  "embedding_dimensions": 768,
  "chunks_count": 42,
  "chunks": [
    {
      "text": "...",
      "metadata": {
        "source": "...",
        "title": "...",
        "section": "...",
        "chunk_id": "...",
        "strategy": "structured"
      },
      "embedding": [
        0.1,
        -0.2
      ]
    }
  ]
}
```

Таким образом индекс полностью локальный.

---

# Почему JSON

В задании разрешены:

```text
FAISS
SQLite
JSON
```

Для учебного проекта выбран JSON.

Преимущества:

- не требуется отдельная база;
- легко открыть;
- легко проверить embeddings;
- хорошо видны metadata;
- удобно демонстрировать на видео;
- помогает понять структуру vector index.

Для большого production-проекта JSON не является оптимальным vector storage.

В дальнейшем его можно заменить на:

```text
FAISS
SQLite
Vector Database
```

---

# Сравнение стратегий

После chunking программа выводит статистику:

```text
Документов
Количество символов
Примерный объём страниц

Количество Fixed chunks
Количество Structured chunks

Средний размер Fixed chunk
Средний размер Structured chunk
```

Это позволяет увидеть, как разные алгоритмы разбивают один и тот же корпус.

---

# Fixed vs Structured

## Fixed

```text
Document
 ↓
1200 chars
 ↓
200 overlap
 ↓
next 1200 chars
```

Преимущество:

```text
простота
```

Недостаток:

```text
не учитывает смысловые границы
```

---

## Structured

```text
Document
 ↓
Sections
 ↓
Headings / Functions / Classes
 ↓
Size Limit
 ↓
Chunks
```

Преимущество:

```text
лучше сохраняется структура документа
```

Недостаток:

```text
нужны правила для разных форматов
```

---

# Главное отличие

Fixed chunking отвечает на вопрос:

```text
Сколько символов поместить в chunk?
```

Structured chunking сначала отвечает:

```text
Где находится логическая граница?
```

а затем:

```text
Не слишком ли большой получился section?
```

---

# Запуск

Проверить документы:

```powershell
Get-ChildItem .\documents
```

Запустить индексатор:

```powershell
py main.py
```

---

# Проверка индексов

После завершения:

```powershell
Get-ChildItem .\indexes
```

Должны появиться:

```text
index_fixed.json
index_structured.json
```

---

# Просмотр Structured Index

PowerShell:

```powershell
Get-Content .\indexes\index_structured.json -Encoding UTF8 -TotalCount 40
```

---

# Просмотр Fixed Index

```powershell
Get-Content .\indexes\index_fixed.json -Encoding UTF8 -TotalCount 40
```

---

# Что проверяется

Проект демонстрирует полный ingestion pipeline:

```text
DOCUMENTS
    ↓
LOAD
    ↓
CHUNK
    ↓
EMBED
    ↓
METADATA
    ↓
INDEX
```

Также выполняется сравнительный эксперимент:

```text
              SAME DOCUMENTS
                    ↓
           ┌────────┴────────┐
           ↓                 ↓
        FIXED            STRUCTURED
           ↓                 ↓
        CHUNKS             CHUNKS
           ↓                 ↓
      EMBEDDINGS         EMBEDDINGS
           ↓                 ↓
      FIXED INDEX      STRUCTURED INDEX
```

---

# Результат

В результате реализованы:

- корпус документов объёмом более 20–30 страниц;
- загрузка нескольких форматов;
- fixed-size chunking;
- chunk overlap;
- structure-aware chunking;
- обработка Markdown sections;
- обработка Python classes/functions;
- metadata;
- уникальные chunk IDs;
- embeddings;
- локальное хранение embeddings;
- два независимых JSON-индекса;
- статистика;
- сравнение двух стратегий chunking.

Финальный результат:

```text
documents/
    ↓
2 Chunking Strategies
    ↓
Embeddings
    ↓
Metadata
    ↓
Local Vector Indexes
```

---

# Что дальше

Текущий этап решает задачу:

```text
INDEXING
```

Но пока не выполняет:

```text
SEMANTIC SEARCH
```

Следующим логическим этапом является retrieval:

```text
User Query
    ↓
Query Embedding
    ↓
Vector Similarity
    ↓
Top-K Chunks
    ↓
Relevant Context
```

Созданные на Дне 21 индексы уже содержат необходимые для этого embeddings и metadata.

---

# Итог

День 21 создаёт основу локальной RAG-системы.

Мы перешли от обычных документов:

```text
README
Articles
Code
Text
```

к структурированному индексу:

```text
Chunk
+
Embedding
+
Metadata
```

и экспериментально подготовили две разные стратегии chunking для одного и того же корпуса документов.