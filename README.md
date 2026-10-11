# Day 30 — Private Local LLM Service

## Overview

A private AI chat service powered by a local LLM using Ollama and FastAPI.

The LLM runs on a server computer, while other computers on the local network can communicate with it through an HTTP API.

The service includes API key authentication, rate limiting, input restrictions, and a Python chat client.

No cloud LLM API is required.

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Ollama
- Qwen2.5-Coder 0.5B
- Requests
- Windows PowerShell

## Architecture

```text
Client Computer
    |
    | HTTP POST /chat
    | X-API-Key authentication
    v
FastAPI Server (Port 8000)
    |
    | Local HTTP request
    v
Ollama (127.0.0.1:11434)
    |
    v
qwen2.5-coder:0.5b
    |
    v
Response to Client
```

The client computer does not need Ollama or the model installed.

## Project Files

```text
AI-Adent-Challange/
├── server.py
├── client.py
├── load_test.py
├── requirements.txt
├── .gitignore
└── README.md
```

The repository may also contain files from previous challenge days.

## Features

- Local LLM inference
- HTTP chat endpoint
- API key authentication
- LAN access from a separate computer
- Request rate limiting
- Input and context restrictions
- Parallel request testing
- Command-line chat client

## Server Setup

### 1. Install Dependencies

```powershell
py -m pip install -r requirements.txt
```

### 2. Install and Prepare Ollama

Make sure Ollama is running and the model is available:

```powershell
ollama pull qwen2.5-coder:0.5b
ollama list
```

Ollama should remain accessible locally rather than being exposed directly to the network.

### 3. Configure the API Key

```powershell
$env:PRIVATE_LLM_API_KEY = [guid]::NewGuid().ToString("N")
```

Keep the generated key private. The client must use the same key.

### 4. Start the API Server

```powershell
py -m uvicorn server:app --host 0.0.0.0 --port 8000
```

### 5. Check Server Health

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```text
status service
------ -------
ok     private-llm
```

## Client Setup

On another Windows computer connected to the same local network:

### 1. Install Python

```powershell
winget install --id Python.Python.3.13 -e --source winget
```

### 2. Install Requests

```powershell
py -m pip install requests
```

### 3. Copy the Client

Copy `client.py` to the client computer.

### 4. Configure Connection

Replace the example address with the server's actual LAN IP address.

```powershell
$env:PRIVATE_LLM_URL = "http://192.168.1.50:8000"
$env:PRIVATE_LLM_API_KEY = "YOUR_SERVER_API_KEY"
```

### 5. Start Chat

```powershell
py client.py
```

The client sends messages to the remote FastAPI service, which processes them using the local Ollama model.

## API

### GET /health

Checks whether the HTTP service is running.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### POST /chat

Sends a list of chat messages to the local LLM.

Example request body:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What is Python? Answer briefly."
    }
  ]
}
```

PowerShell example:

```powershell
$body = @{
    messages = @(
        @{
            role = "user"
            content = "What is Python? Answer briefly."
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/chat" `
    -Method Post `
    -Headers @{"X-API-Key" = $env:PRIVATE_LLM_API_KEY} `
    -ContentType "application/json" `
    -Body $body
```

## Rate Limiting

The service uses a request limit of five requests per 60-second window.

Run the load test:

```powershell
py load_test.py
```

### Actual Test Results

```text
2 | 200 | 0.81
1 | 200 | 1.02
3 | 200 | 1.02
5 | 429 | 0.23
4 | 200 | 0.44
7 | 429 | 0.02
6 | 200 | 0.29
```

Results:

- Total requests: 7
- HTTP 200: 5
- HTTP 429: 2
- Rate limiting: Passed

HTTP 429 indicates that the service rejected a request because the rate limit was reached.

## Security

The service is intended for private use.

Security measures include:

- API key authentication
- Rate limiting
- Input restrictions
- Limited model context configuration
- Ollama running on localhost
- Restricted LAN access through Windows Firewall

Do not commit real API keys to GitHub.

Do not expose port 8000 directly to the public internet without additional protections such as HTTPS and a secure authentication and network access layer.

For access outside the home network, a private VPN such as Tailscale is preferable.

## Verified Results

- FastAPI health endpoint responds successfully.
- API key validation works.
- HTTP chat requests work.
- Parallel load test completed with expected rate limiting.
- A separate client computer successfully connected to the service.

The short load test demonstrates basic operation, not long-term production stability.

## Conclusion

Day 30 demonstrates how to turn a local Ollama model into a private network-accessible AI service.

The server hosts the model and HTTP API, while client computers use a lightweight Python script to chat with it.

The project provides a foundation for building private AI assistants, internal tools, and local-network AI applications.