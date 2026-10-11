import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

URL = os.getenv('PRIVATE_LLM_URL', 'http://127.0.0.1:8000').rstrip('/') + '/chat'
KEY = os.getenv('PRIVATE_LLM_API_KEY', '')
if not KEY:
    raise SystemExit('Set PRIVATE_LLM_API_KEY first')

def call(n):
    start = time.perf_counter()
    try:
        r = requests.post(URL, headers={'X-API-Key': KEY}, json={
            'messages': [{'role': 'user', 'content': f'Say the number {n} in one word.'}]
        }, timeout=200)
        return n, r.status_code, round(time.perf_counter() - start, 2)
    except requests.RequestException as exc:
        return n, 'ERROR', str(exc)

with ThreadPoolExecutor(max_workers=3) as pool:
    for result in as_completed([pool.submit(call, i) for i in range(1, 8)]):
        print(*result.result(), sep=' | ')
print('Expected: up to 5 HTTP 200 and at least 2 HTTP 429 in a fresh 60s window.')
