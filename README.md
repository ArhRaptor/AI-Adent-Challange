# Day 31 — Developer Assistant (RAG + MCP)

Local developer assistant that answers questions about a Git project using README and docs as RAG sources, plus live Git context through a real MCP stdio server.

## Requirements

- Python 3.10+
- Git
- Ollama running locally
- Models: `qwen2.5-coder:0.5b`, `nomic-embed-text`

## Install (PowerShell)

```powershell
ollama pull qwen2.5-coder:0.5b
ollama pull nomic-embed-text
```

Copy `developer_assistant.py`, `index_project.py`, `mcp_git_server.py` and the `docs/day31_architecture.md` file into your existing Git project root. Keep the existing `README.md` and `docs/` files: the indexer reads them.

If needed, point the scripts to your repository:

```powershell
$env:DAY31_PROJECT_ROOT = (Get-Location).Path
```

Build the index:

```powershell
py index_project.py
```

Start the assistant:

```powershell
py developer_assistant.py
```

Example commands:

```text
/branch
/files
/status
/help Какие основные компоненты проекта?
/help Как запустить локальный LLM сервис?
/reindex
/exit
```

## How it works

1. `index_project.py` scans `README.md` and `docs/` for Markdown, text, JSON, YAML documents (up to 1 MB per file).
2. Text is split into overlapping character chunks and embedded locally via Ollama `/api/embed`.
3. The `/help` command retrieves the four nearest chunks by cosine similarity.
4. A separate MCP stdio server provides the actual current Git branch and tracked file names.
5. The assistant sends retrieved documentation and Git context to Ollama `/api/chat` and displays the answer and source paths.

## MCP tools

- `git_branch`: `git branch --show-current`
- `git_status`: `git status --short`
- `project_files`: `git ls-files` (first 100 files)

All Git tools are read-only and operate in `DAY31_PROJECT_ROOT`.

## Notes

- No cloud API key is required.
- The small `qwen2.5-coder:0.5b` model can make mistakes; check the named source files.
- Rebuild the index with `/reindex` whenever documentation changes.
- Do not index secrets or credentials.
- The generated `indexes/day31_project.json` may be large and should be excluded from Git.
- No benchmark or user test results are claimed until run locally.

## Demo video checklist

Show the root README and docs folder, build the index, run `/branch`, `/files`, ask two project-specific `/help` questions, show source names, then show the Git commit and push.
