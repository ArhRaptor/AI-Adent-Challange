import os
import requests

BASE_URL = os.getenv('PRIVATE_LLM_URL', 'http://127.0.0.1:8000').rstrip('/')
API_KEY = os.getenv('PRIVATE_LLM_API_KEY', '')
messages = []

if not API_KEY:
    raise SystemExit('Set PRIVATE_LLM_API_KEY first')

print('Day 30 private chat. Commands: /exit, /clear')
while True:
    try:
        prompt = input('Вы: ').strip()
    except (KeyboardInterrupt, EOFError):
        break
    if prompt == '/exit':
        break
    if prompt == '/clear':
        messages.clear()
        print('История очищена')
        continue
    if not prompt:
        continue
    candidate = messages + [{'role': 'user', 'content': prompt}]
    try:
        response = requests.post(
            f'{BASE_URL}/chat',
            json={'messages': candidate},
            headers={'X-API-Key': API_KEY},
            timeout=200,
        )
        if not response.ok:
            print(f'HTTP {response.status_code}: {response.text}')
            continue
        answer = response.json()['answer']
    except requests.RequestException as exc:
        print(f'Ошибка сети: {exc}')
        continue
    print('LLM:', answer)
    messages = (candidate + [{'role': 'assistant', 'content': answer}])[-8:]
