import os
import time
import hmac
import threading
from collections import deque
from typing import Literal

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

MODEL = os.getenv('OLLAMA_MODEL', 'qwen2.5-coder:0.5b')
OLLAMA_URL = 'http://127.0.0.1:11434/api/chat'
API_KEY = os.getenv('PRIVATE_LLM_API_KEY', '')
RATE_LIMIT = 5
RATE_WINDOW = 60
MAX_MESSAGES = 10
MAX_MESSAGE_CHARS = 1500
MAX_TOTAL_CHARS = 6000
MAX_CONTEXT = 2048
MAX_OUTPUT = 180

app = FastAPI(title='Day 30 Private LLM API', docs_url=None, redoc_url=None)
requests_by_key: dict[str, deque] = {}
rate_lock = threading.Lock()

class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)

class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=MAX_MESSAGES)

@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'private-llm'}

@app.post('/chat')
async def chat(body: ChatRequest, request: Request, x_api_key: str | None = Header(default=None)):
    if not API_KEY:
        raise HTTPException(503, 'Server API key not configured')
    if not x_api_key or not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401, 'Invalid API key')
    if body.messages[-1].role != 'user':
        raise HTTPException(422, 'Last message must be from user')
    if sum(len(m.content) for m in body.messages) > MAX_TOTAL_CHARS:
        raise HTTPException(413, 'Conversation too large')

    # Single shared bucket for this private service; protects against key/IP switching.
    now = time.monotonic()
    with rate_lock:
        bucket = requests_by_key.setdefault('global', deque())
        while bucket and now - bucket[0] >= RATE_WINDOW:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT:
            raise HTTPException(429, 'Rate limit exceeded: 5 requests per 60 seconds')
        bucket.append(now)

    payload = {
        'model': MODEL,
        'stream': False,
        'messages': [
            {'role': 'system', 'content': 'You are a private AI assistant. Answer clearly and briefly.'},
            *[m.model_dump() for m in body.messages],
        ],
        'options': {'temperature': 0.1, 'num_ctx': MAX_CONTEXT, 'num_predict': MAX_OUTPUT},
    }
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise HTTPException(502, 'Ollama unavailable or invalid response') from exc

    return {
        'model': MODEL,
        'answer': data.get('message', {}).get('content', ''),
        'prompt_tokens': data.get('prompt_eval_count'),
        'output_tokens': data.get('eval_count'),
    }
