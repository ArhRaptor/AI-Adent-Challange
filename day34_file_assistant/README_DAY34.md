# Day 34 — File assistant

A goal-driven project file assistant. Python standard library; Ollama (`qwen2.5-coder:3b`) optionally selects one of three file tools: `search`, `document`, `audit`. When Ollama is unavailable, a deterministic heuristic planner is used. No external package installation required.

## PowerShell

From repository root, with `file_assistant.py` copied there:

```powershell
$env:DAY34_CHAT_MODEL = 'qwen2.5-coder:3b'
py file_assistant.py --task 'Найди все использования Ollama в проекте'
py file_assistant.py --task 'Создай документацию по Python API проекта'
py file_assistant.py --task 'Проверь синтаксис Python и ссылки Markdown'
Get-Content .\day34_output\day34_last.diff -Encoding UTF8
```

Use `--no-llm` to demonstrate fully reproducible behavior without a model, or `--root PATH` to scan a different directory. Only text source files up to 120 KB each are scanned, up to 250 files. The assistant never executes repository code or overwrites original source files. Outputs are `day34_output/day34_search.md`, `day34_api.md`, `day34_audit.md`, and `day34_last.diff` (latest changed report only). Existing report is unchanged on repeated identical runs. Results may vary if the project changes. The Ollama planner is constrained to a small set of actions; never expose write-to-arbitrary-file functionality without additional safeguards.

## Demonstration

1. Show Git branches and project files.
2. Search `Ollama` across source files; inspect `day34_search.md`.
3. Generate `day34_api.md` from AST-parsed Python files; show diff.
4. Audit Python syntax and Markdown links; inspect `day34_audit.md`.
5. Repeat documentation command to show `[UNCHANGED]` and reproducibility.
