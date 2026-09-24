# День 19 — Композиция MCP-инструментов

## Цель

Реализовать автоматический pipeline из нескольких MCP-инструментов, где результат одного инструмента становится входными данными следующего.

В проекте реализована цепочка:

```text
search
   ↓
summarize
   ↓
save_to_file
```

Каждый этап является отдельным MCP Tool.

---

# Задача

Pipeline должен автоматически:

1. найти данные;
2. обработать найденные данные;
3. сформировать сводку;
4. сохранить результат в файл.

Главное требование — корректная передача результатов между MCP-инструментами.

---

# Архитектура

Общая схема:

```text
USER
 ↓
main.py
 ↓
MCP Client
 ↓
┌─────────────────────────┐
│       MCP Server        │
│                         │
│  search                 │
│    ↓                    │
│  summarize              │
│    ↓                    │
│  save_to_file           │
│                         │
└─────────────────────────┘
 ↓
reports/
 ↓
warehouse_report.txt
```

Pipeline запускается одной пользовательской командой.

После запуска следующие инструменты выполняются автоматически.

---

# Структура проекта

```text
.
├── main.py
├── mcp_server.py
├── warehouse_api.py
├── README.md
└── reports/
    └── warehouse_report.txt
```

### main.py

Содержит:

```text
MCP Client
+
Pipeline Orchestrator
```

Он определяет порядок выполнения инструментов и передаёт результаты между ними.

### mcp_server.py

Содержит три MCP-инструмента:

```text
search
summarize
save_to_file
```

### warehouse_api.py

Содержит Mock API склада и функцию поиска товаров.

### reports/

Каталог, в который MCP-инструмент сохраняет итоговый отчёт.

---

# Pipeline

Полная цепочка выглядит так:

```text
QUERY
  ↓
search(query)
  ↓
SEARCH RESULT
  ↓
summarize(search_result)
  ↓
SUMMARY RESULT
  ↓
save_to_file(summary)
  ↓
warehouse_report.txt
```

Главная особенность:

```text
OUTPUT TOOL #1
      ↓
INPUT TOOL #2

OUTPUT TOOL #2
      ↓
INPUT TOOL #3
```

Инструменты не выполняются независимо друг от друга.

Они образуют единый workflow.

---

# Tool 1 — search

Первый MCP-инструмент:

```text
search
```

Принимает:

```text
query
```

Например:

```text
Москва
```

Инструмент обращается к:

```text
warehouse_api.py
```

и ищет товары по:

- ID;
- названию;
- складу.

---

# Mock API

В учебном проекте используется локальный набор товаров.

Например:

```python
PRODUCTS = {
    101: {
        "id": 101,
        "name": "Ноутбук Lenovo ThinkBook",
        "quantity": 7,
        "price": 85000,
        "warehouse": "Москва"
    }
}
```

В реальном приложении вместо Mock API здесь может находиться:

```text
REST API
Database
CRM
ERP
Git
Яндекс.Трекер
```

Pipeline при этом может остаться прежним.

---

# Результат search

Инструмент возвращает структурированные данные.

Например:

```json
{
  "success": true,
  "query": "Москва",
  "count": 3,
  "products": [
    {
      "id": 101,
      "name": "Ноутбук Lenovo ThinkBook",
      "quantity": 7,
      "price": 85000,
      "warehouse": "Москва"
    }
  ]
}
```

Этот результат не просто выводится пользователю.

Он автоматически передаётся следующему MCP-инструменту.

---

# Tool 2 — summarize

Второй инструмент:

```text
summarize
```

получает:

```text
search_result
```

То есть результат первого инструмента становится входом второго:

```text
search()
   ↓
search_result
   ↓
summarize(search_result)
```

В коде это выглядит как передача:

```python
{
    "search_result": search_result
}
```

---

# Агрегация

`summarize` рассчитывает:

```text
Количество найденных товаров
Общий остаток
Стоимость остатков
Товары без остатка
```

Общий остаток рассчитывается по всем найденным товарам.

Стоимость остатков:

```text
quantity × price
```

для каждого товара с последующим суммированием.

---

# Пример

Для запроса:

```text
Москва
```

было найдено три товара:

```text
Ноутбук Lenovo ThinkBook
Монитор Samsung 27
Мышь Logitech
```

Остатки:

```text
7 + 0 + 15 = 22
```

Стоимость остатков:

```text
7 × 85000 = 595000

0 × 32000 = 0

15 × 3500 = 52500
```

Итого:

```text
647500 руб.
```

---

# Сформированная сводка

Результат обработки имеет вид:

```text
Сводка по запросу: Москва

Найдено товаров: 3
Общий остаток: 22
Стоимость остатков: 647500 руб.

Товары:
- Ноутбук Lenovo ThinkBook: 7 шт., 85000 руб., склад: Москва
- Монитор Samsung 27: 0 шт., 32000 руб., склад: Москва
- Мышь Logitech: 15 шт., 3500 руб., склад: Москва

Нет в наличии:
- Монитор Samsung 27
```

После этого текст автоматически передаётся третьему инструменту.

---

# Tool 3 — save_to_file

Последний MCP-инструмент:

```text
save_to_file
```

принимает:

```text
content
filename
```

В качестве `content` используется результат `summarize`.

Получается:

```text
summary_result
      ↓
summary
      ↓
save_to_file
```

В pipeline передаётся:

```python
{
    "content": summary_text,
    "filename": "warehouse_report.txt"
}
```

---

# Сохранение файла

Инструмент автоматически создаёт каталог:

```text
reports
```

если его ещё нет.

После этого результат сохраняется:

```text
reports/warehouse_report.txt
```

Для записи используется UTF-8:

```python
with open(
    file_path,
    "w",
    encoding="utf-8"
) as file:
    file.write(content)
```

---

# Безопасность пути

Имя файла обрабатывается через:

```python
os.path.basename(filename)
```

Это не позволяет переданному имени файла напрямую выйти за пределы каталога `reports` с помощью пути вида:

```text
../../file.txt
```

Для production-системы потребовались бы дополнительные проверки, но для учебного примера это добавляет базовое ограничение пути.

---

# Автоматическое выполнение

Pipeline реализован в:

```text
run_pipeline()
```

После ввода поискового запроса пользователю больше не требуется вручную запускать каждый инструмент.

Выполнение происходит автоматически:

```text
USER INPUT
    ↓
[1/3] SEARCH
    ↓
[2/3] SUMMARIZE
    ↓
[3/3] SAVE TO FILE
    ↓
PIPELINE COMPLETED
```

---

# Передача данных

Это основная часть задания.

После `search`:

```python
search_result = get_result(
    search_response
)
```

полученный результат передаётся:

```python
await client.call_tool(
    "summarize",
    {
        "search_result": search_result
    }
)
```

Затем из результата `summarize` берётся:

```python
summary_text = summary_result.get(
    "summary",
    ""
)
```

и передаётся:

```python
await client.call_tool(
    "save_to_file",
    {
        "content": summary_text,
        "filename": "warehouse_report.txt"
    }
)
```

Таким образом:

```text
search_result
      ↓
summarize

summary_result["summary"]
      ↓
save_to_file
```

---

# Обработка ошибок

После каждого MCP-вызова проверяется результат.

Если инструмент сообщает об ошибке:

```text
result.is_error
```

pipeline останавливается на соответствующем этапе.

Например:

```text
search
 ↓
ERROR
 ↓
STOP
```

В этом случае `summarize` и `save_to_file` не выполняются с некорректными входными данными.

---

# Тест №1 — поиск по складу

Запуск:

```powershell
py main.py
```

Запрос:

```text
Москва
```

Pipeline автоматически выполняет:

```text
search("Москва")
       ↓
3 товара
       ↓
summarize(...)
       ↓
сводка
       ↓
save_to_file(...)
       ↓
reports/warehouse_report.txt
```

---

# Проверка результата

В PowerShell:

```powershell
Get-Content .\reports\warehouse_report.txt -Encoding UTF8
```

Также файл можно открыть через:

```powershell
notepad .\reports\warehouse_report.txt
```

---

# Тест №2 — поиск по названию

Запуск:

```powershell
py main.py
```

Запрос:

```text
Logitech
```

Pipeline снова автоматически проходит все три этапа:

```text
search
 ↓
summarize
 ↓
save_to_file
```

Но теперь сводка строится только по товарам, соответствующим запросу `Logitech`.

---

# Тест №3 — пустой результат

Запрос:

```text
iPhone
```

Если товары не найдены, `search` возвращает:

```json
{
  "success": true,
  "query": "iPhone",
  "count": 0,
  "products": []
}
```

Pipeline при этом не падает.

`summarize` создаёт сообщение:

```text
По запросу «iPhone» товары не найдены.
```

После чего `save_to_file` сохраняет этот результат.

Это показывает, что инструменты корректно обрабатывают и передают пустой результат.

---

# MCP и Orchestration

Важно разделять две части системы.

MCP предоставляет инструменты:

```text
search
summarize
save_to_file
```

А порядок их выполнения определяет:

```text
main.py
```

То есть:

```text
MCP
→ предоставляет Tools

main.py
→ строит Workflow
```

В текущей реализации orchestration является детерминированным:

```text
search
 ↓
summarize
 ↓
save_to_file
```

Это делает pipeline предсказуемым и удобным для тестирования.

---

# Отличие от Дня 18

На Дне 18 основной задачей были:

```text
Scheduler
Background Worker
Periodic Execution
JSON Persistence
```

Поэтому использовались:

```text
worker.py
storage.py
```

На Дне 19 задача другая:

```text
Tool Composition
Pipeline
Data Transfer
```

Поэтому `worker.py` и `storage.py` в текущей реализации не используются.

Архитектура Дня 19:

```text
main.py
      ↓
MCP Server
      ↓
search
      ↓
warehouse_api.py
      ↓
summarize
      ↓
save_to_file
      ↓
warehouse_report.txt
```

---

# День 18 vs День 19

## День 18

```text
CREATE TASK
    ↓
SCHEDULE
    ↓
WORKER
    ↓
PERIODIC EXECUTION
```

Основная идея:

```text
Когда выполнить работу?
```

## День 19

```text
SEARCH
    ↓
SUMMARIZE
    ↓
SAVE
```

Основная идея:

```text
Как связать несколько инструментов
в единый workflow?
```

---

# Результат

В результате реализован автоматический pipeline из трёх MCP-инструментов:

```text
search
 ↓
summarize
 ↓
save_to_file
```

Реализованы:

- несколько независимых MCP Tools;
- поиск данных;
- обработка данных;
- агрегация результатов;
- создание текстовой сводки;
- сохранение результата в файл;
- автоматическая последовательность вызовов;
- передача результата между инструментами;
- обработка пустого результата;
- остановка pipeline при ошибке;
- UTF-8 для сохранённого отчёта.

Главный результат:

```text
TOOL #1
   │
   │ result
   ↓
TOOL #2
   │
   │ result
   ↓
TOOL #3
   │
   ↓
FINAL RESULT
```

---

# Вывод

День 19 показывает, что MCP-инструменты можно использовать не только независимо друг от друга.

Из небольших специализированных Tools можно строить более сложные процессы:

```text
GET DATA
    ↓
PROCESS DATA
    ↓
SAVE RESULT
```

В нашем примере:

```text
search
    ↓
summarize
    ↓
save_to_file
```

Pipeline запускается одной командой, а передача данных и выполнение последующих этапов происходят автоматически.

Это является основой для построения более сложных AI workflows и агентных систем из небольших MCP-инструментов.