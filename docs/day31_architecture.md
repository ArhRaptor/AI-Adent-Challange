# Day 31 — Developer Assistant Architecture

The Day 31 developer assistant is a Python CLI that combines retrieval-augmented generation (RAG) with read-only Model Context Protocol (MCP) tools.

## Main components

- `developer_assistant.py`: interactive CLI, RAG retrieval, MCP client and Ollama chat generation.
- `index_project.py`: indexes the root `README.md` and supported text documents recursively under `docs/` using Ollama `nomic-embed-text`.
- `mcp_git_server.py`: MCP stdio JSON-RPC server exposing `git_branch`, `git_status`, and `project_files`.
- `indexes/day31_project.json`: generated local embeddings index; do not commit it.

## Data flow

1. User enters `/help <question>`.
2. The assistant embeds the question and selects four relevant documentation chunks using cosine similarity.
3. The assistant requests the current Git branch and tracked files from the MCP server.
4. The assistant sends documentation excerpts, Git context, and the question to Ollama `qwen2.5-coder:0.5b`.
5. The CLI prints the answer, documentation source paths, and the current branch.

## Commands

- `/help <question>`: project question answered with RAG and MCP context.
- `/branch`: current Git branch via MCP.
- `/status`: short Git status via MCP.
- `/files`: up to 100 tracked project files via MCP.
- `/reindex`: rebuild the documentation index.
- `/exit`: close the assistant.

## Limits

This assistant is read-only with respect to Git. It does not execute arbitrary shell commands, change branches, edit project files, or create commits. The RAG index must be rebuilt after documentation changes. Model answers may be inaccurate and should be verified against cited files.
