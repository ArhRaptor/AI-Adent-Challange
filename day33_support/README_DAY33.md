# Day 33 — Support Assistant (MCP + RAG + Ollama)

Демо-продукт HelpDesk Cloud, данные пользователей и тикетов вымышлены.

## Запуск из PowerShell

```powershell
py -m pip install -r requirements.txt
ollama pull qwen2.5-coder:3b
ollama pull nomic-embed-text
$env:DAY33_CHAT_MODEL = 'qwen2.5-coder:3b'
py support_assistant.py --ticket T-1001 --question 'Почему не работает авторизация?'
```

Скрипт запускает MCP stdio-сервер отдельным Python-процессом, вызывает инструменты `get_ticket`, `get_user`, `list_user_tickets`, ищет релевантные фрагменты FAQ и документации с помощью эмбеддингов Ollama и формирует ответ. Отчёт сохраняется в `day33_answer.md`.

## Ещё примеры

```powershell
py support_assistant.py --ticket T-1002 --question 'Почему не приходит письмо для сброса пароля?'
py support_assistant.py --user U-001 --question 'Какой статус моих обращений?'
```

## Ограничения

Учебный пример, не production CRM. Данные JSON не имеют реальной аутентификации или разграничения доступа: не использовать реальные личные данные и не открывать сервис публично. Для настоящей CRM потребуется авторизация пользователя и проверка прав на тикет до вызова MCP. RAG пересчитывает эмбеддинги при каждом запуске.
