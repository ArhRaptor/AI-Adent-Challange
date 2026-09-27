# День 20 — Orchestration MCP

## Цель

Реализовать оркестрацию нескольких MCP-серверов и инструментов.

Система должна:

- подключаться к нескольким MCP-серверам;
- принимать запрос пользователя на естественном языке;
- определять необходимый маршрут;
- выбирать нужные инструменты;
- вызывать инструменты с разных MCP-серверов;
- передавать результаты между инструментами;
- выполнять длинный многошаговый flow.

---

# Архитектура

В проекте используются три независимых MCP-сервера:

```text
Warehouse MCP Server
├── search_products
└── get_product

Analytics MCP Server
└── analyze_products

Report MCP Server
└── save_report
```

Над ними находится агент-маршрутизатор:

```text
                    ┌─────────────────────┐
                    │        USER         │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │    Gemini Router    │
                    └──────────┬──────────┘
                               ↓
                     выбор маршрута
                               ↓
             ┌─────────────────┼─────────────────┐
             ↓                 ↓                 ↓
         search             analyze         full_report
             │                 │                 │
             ↓                 ↓                 ↓
        Warehouse         Warehouse          Warehouse
                               ↓                 ↓
                          Analytics          Analytics
                                                 ↓
                                              Report
```

---

# Структура проекта

```text
.
├── main.py
├── warehouse_server.py
├── analytics_server.py
├── report_server.py
├── README.md
└── reports/
    └── warehouse_report.txt
```

`reports/` содержит генерируемые программой файлы и может быть добавлен в `.gitignore`.

---

# Компоненты

## main.py

Главный файл приложения.

Он отвечает за:

```text
User Request
     ↓
Gemini Router
     ↓
Route Selection
     ↓
MCP Orchestrator
     ↓
Tool Calls
```

Также `main.py` устанавливает соединения сразу с тремя MCP-серверами.

---

## warehouse_server.py

MCP-сервер для работы с товарами.

Инструменты:

```text
search_products
get_product
```

### search_products

Ищет товары по:

- названию;
- ID;
- складу.

Например:

```text
Москва
```

может вернуть несколько товаров московского склада.

### get_product

Получает конкретный товар по его ID.

Например:

```text
101
```

---

## analytics_server.py

Отдельный MCP-сервер для анализа данных.

Инструмент:

```text
analyze_products
```

Он получает список товаров и рассчитывает:

```text
Количество товаров
Общий остаток
Стоимость остатков
Товары без остатка
```

Также инструмент формирует текстовый аналитический отчёт.

---

## report_server.py

Отдельный MCP-сервер для сохранения результатов.

Инструмент:

```text
save_report
```

Он получает готовый текст отчёта и сохраняет его:

```text
reports/warehouse_report.txt
```

Для файла используется кодировка UTF-8.

---

# Несколько MCP-серверов

Главное отличие этого проекта — инструменты находятся не на одном сервере.

Используются три отдельных процесса:

```text
warehouse_server.py
analytics_server.py
report_server.py
```

В `main.py` для каждого создаётся отдельное MCP-соединение:

```text
Warehouse Client
Analytics Client
Report Client
```

В результате один пользовательский запрос может привести к вызовам инструментов на нескольких серверах.

---

# Agent Router

Для маршрутизации используется Gemini.

Пользователь может писать запрос обычным текстом:

```text
Найди товары в Москве
```

или:

```text
Проанализируй товары Logitech
```

или:

```text
Найди товары в Москве,
проанализируй остатки
и сохрани отчёт
```

Router анализирует запрос и возвращает структурированное решение.

Пример:

```json
{
  "route": "full_report",
  "query": "Москва"
}
```

---

# Доступные маршруты

В проекте реализованы три маршрута.

## search

Для обычного поиска:

```text
USER
 ↓
Gemini Router
 ↓
Warehouse MCP
 ↓
search_products
```

---

## analyze

Для поиска и анализа:

```text
USER
 ↓
Gemini Router
 ↓
Warehouse MCP
 ↓
search_products
 ↓
products
 ↓
Analytics MCP
 ↓
analyze_products
```

---

## full_report

Полный длинный flow:

```text
USER
 ↓
Gemini Router
 ↓
Warehouse MCP
 ↓
search_products
 ↓
products
 ↓
Analytics MCP
 ↓
analyze_products
 ↓
report
 ↓
Report MCP
 ↓
save_report
 ↓
warehouse_report.txt
```

Это основной сценарий Дня 20.

---

# Передача данных между MCP-серверами

Серверы не работают изолированно.

Результат одного MCP Tool используется как вход другого.

После поиска:

```text
Warehouse MCP

search_products
      ↓
products
```

список товаров передаётся:

```text
products
   ↓
Analytics MCP
   ↓
analyze_products
```

После анализа:

```text
analyze_products
       ↓
report
```

готовый отчёт передаётся:

```text
report
  ↓
Report MCP
  ↓
save_report
```

Таким образом данные проходят через несколько независимых MCP-серверов.

---

# Orchestrator

Функция:

```text
orchestrate()
```

управляет выполнением выбранного маршрута.

Router принимает решение:

```text
search
```

или:

```text
analyze
```

или:

```text
full_report
```

После этого orchestrator выполняет соответствующую последовательность MCP Tool Calls.

---

# Почему маршрутизация разделена на два уровня

В проекте Gemini отвечает за решение:

```text
Что хочет пользователь?
```

Например:

```text
full_report
```

Python отвечает за контролируемое выполнение:

```text
Какие именно инструменты
и в каком порядке вызвать?
```

Получается:

```text
LLM
 ↓
Route Decision
 ↓
Python Orchestrator
 ↓
Allowed MCP Tools
```

Такой подход позволяет совместить гибкость LLM с предсказуемым выполнением программы.

---

# Сценарий №1 — Search

Запуск:

```powershell
py main.py
```

Запрос:

```text
Найди товары в Москве
```

Ожидаемый маршрут:

```text
Route: search
Query: Москва
```

Выполняется:

```text
Warehouse MCP
      ↓
search_products
```

Analytics и Report для этого запроса не требуются.

---

# Сценарий №2 — Analyze

Запуск:

```powershell
py main.py
```

Запрос:

```text
Проанализируй товары Logitech
```

Router выбирает:

```text
analyze
```

Выполняется:

```text
Warehouse MCP
      ↓
search_products
      ↓
Analytics MCP
      ↓
analyze_products
```

Report MCP не вызывается.

---

# Сценарий №3 — Full Report

Главный тест проекта:

```powershell
py main.py
```

Запрос:

```text
Найди товары в Москве, проанализируй остатки и сохрани отчёт
```

Router должен определить:

```text
Route: full_report
Query: Москва
```

После этого автоматически выполняется длинный flow:

```text
Warehouse MCP
      ↓
search_products
      ↓
products
      ↓
Analytics MCP
      ↓
analyze_products
      ↓
report
      ↓
Report MCP
      ↓
save_report
```

---

# Результат полного flow

После выполнения создаётся:

```text
reports/warehouse_report.txt
```

Проверить его в PowerShell:

```powershell
Get-Content .\reports\warehouse_report.txt -Encoding UTF8
```

Или открыть в Блокноте:

```powershell
notepad .\reports\warehouse_report.txt
```

---

# Пример аналитики

Для московского склада используются товары:

```text
Ноутбук Lenovo ThinkBook
Монитор Samsung 27
Мышь Logitech
```

Остаток:

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

Также определяется товар без остатка:

```text
Монитор Samsung 27
```

---

# Контроль порядка вызовов

Для проверки orchestration программа выводит текущий сервер и инструмент.

Например:

```text
SERVER: WAREHOUSE
TOOL: search_products
```

затем:

```text
SERVER: ANALYTICS
TOOL: analyze_products
```

затем:

```text
SERVER: REPORT
TOOL: save_report
```

В конце:

```text
FLOW COMPLETED

Маршрут:
Warehouse → Analytics → Report
```

Таким образом в консоли можно увидеть не только итоговый результат, но и фактический порядок выполнения flow.

---

# Отличие Дня 19 от Дня 20

## День 19 — Tool Composition

Несколько инструментов находились на одном MCP-сервере:

```text
MCP Server
├── search
├── summarize
└── save_to_file
```

Pipeline:

```text
search
 ↓
summarize
 ↓
save_to_file
```

Основная задача:

```text
Соединить несколько MCP Tools
в один pipeline.
```

---

## День 20 — MCP Orchestration

Теперь инструменты распределены между несколькими MCP-серверами:

```text
Warehouse MCP
      ↓
Analytics MCP
      ↓
Report MCP
```

Дополнительно появился:

```text
Gemini Router
```

Он определяет маршрут на основе запроса пользователя.

Основная задача:

```text
Выбрать нужные инструменты
      +
маршрутизировать запрос
      +
выполнить flow
между несколькими MCP-серверами
```

---

# Результат

Реализована система orchestration с несколькими MCP-серверами.

Система умеет:

- подключаться к трём MCP-серверам;
- принимать запрос на естественном языке;
- использовать Gemini для определения маршрута;
- выбирать короткий или длинный сценарий;
- выполнять инструменты с разных MCP-серверов;
- передавать данные между серверами;
- сохранять итоговый отчёт;
- показывать порядок выполнения инструментов.

Полный flow:

```text
USER
 ↓
GEMINI ROUTER
 ↓
WAREHOUSE MCP
 ↓
search_products
 ↓
ANALYTICS MCP
 ↓
analyze_products
 ↓
REPORT MCP
 ↓
save_report
 ↓
FILE
```

## Итог

На Дне 20 отдельные MCP-инструменты объединены в многошаговую систему.

Теперь агент не просто вызывает заранее заданную цепочку.

Сначала он определяет намерение пользователя:

```text
search
analyze
full_report
```

После этого orchestrator выполняет необходимую последовательность инструментов на разных MCP-серверах.

Это позволяет строить более сложные агентные системы, где разные MCP-серверы отвечают за разные области работы.