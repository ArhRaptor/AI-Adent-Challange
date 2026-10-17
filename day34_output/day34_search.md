# Search: Ollama

Files scanned: 13
Matches: 25

- `day34_file_assistant/file_assistant.py:1` — `"""Day 34: goal-driven project file assistant. Python stdlib + optional Ollama planner."""`
- `day34_file_assistant/file_assistant.py:54` — `os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/') + '/api/chat',`
- `day34_file_assistant/file_assistant.py:63` — `print(f'[planner] Ollama unavailable; fallback: {exc}')`
- `day34_file_assistant/file_assistant.py:72` — `for term in ('Ollama', 'Retrofit', 'NavHost', 'MCP', 'FastAPI'):`
- `day34_file_assistant/README_DAY34.md:3` — `A goal-driven project file assistant. Python standard library; Ollama ('qwen2.5-coder:3b') optionally selects one of three file tools: 'search', 'document', 'audit'. When Ollama is`
- `day34_file_assistant/README_DAY34.md:11` — `py file_assistant.py --task 'Найди все использования Ollama в проекте'`
- `day34_file_assistant/README_DAY34.md:17` — `Use '--no-llm' to demonstrate fully reproducible behavior without a model, or '--root PATH' to scan a different directory. Only text source files up to 120 KB each are scanned, up `
- `day34_file_assistant/README_DAY34.md:22` — `2. Search 'Ollama' across source files; inspect 'day34_search.md'.`
- `developer_assistant.py:8` — `from index_project import ROOT, INDEX, EMBED_MODEL, OLLAMA, embed, post, build`
- `developer_assistant.py:91` — `7. Не перечисляй Python, Git и Ollama как самостоятельные`
- `docs/day31_architecture.md:7` — `- 'developer_assistant.py': interactive CLI, RAG retrieval, MCP client and Ollama chat generation.`
- `docs/day31_architecture.md:8` — `- 'index_project.py': indexes the root 'README.md' and supported text documents recursively under 'docs/' using Ollama 'nomic-embed-text'.`
- `docs/day31_architecture.md:17` — `4. The assistant sends documentation excerpts, Git context, and the question to Ollama 'qwen2.5-coder:0.5b'.`
- `index_project.py:1` — `"""Index README and docs locally using Ollama embeddings."""`
- `index_project.py:9` — `OLLAMA = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')`
- `index_project.py:14` — `req = urllib.request.Request(OLLAMA + path, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})`
- `README.md:9` — `- Ollama running locally`
- `README.md:15` — `ollama pull qwen2.5-coder:0.5b`
- `README.md:16` — `ollama pull nomic-embed-text`
- `README.md:54` — `2. Text is split into overlapping character chunks and embedded locally via Ollama '/api/embed'.`
- `README.md:57` — `5. The assistant sends retrieved documentation and Git context to Ollama '/api/chat' and displays the answer and source paths.`
- `server.py:12` — `MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:0.5b')`
- `server.py:13` — `OLLAMA_URL = 'http://127.0.0.1:11434/api/chat'`
- `server.py:70` — `response = await client.post(OLLAMA_URL, json=payload)`
- `server.py:74` — `raise HTTPException(502, 'Ollama unavailable or invalid response') from exc`
