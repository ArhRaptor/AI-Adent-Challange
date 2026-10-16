"""Minimal MCP stdio server exposing read-only Git project tools."""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get('DAY31_PROJECT_ROOT', Path(__file__).resolve().parent)).resolve()


def git(*args):
    p = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace')
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or 'Git command failed')
    return p.stdout.strip()


def tools():
    return [
        {'name': 'git_branch', 'description': 'Return the current Git branch', 'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
        {'name': 'git_status', 'description': 'Return short Git status', 'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
        {'name': 'project_files', 'description': 'List tracked project files', 'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
    ]


def respond(message):
    method = message.get('method')
    ident = message.get('id')
    if ident is None:
        return None  # JSON-RPC notification
    try:
        if method == 'initialize':
            result = {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}}, 'serverInfo': {'name': 'day31-git', 'version': '1.0.0'}}
        elif method == 'ping':
            result = {}
        elif method == 'tools/list':
            result = {'tools': tools()}
        elif method == 'tools/call':
            name = message.get('params', {}).get('name')
            if name == 'git_branch':
                output = git('branch', '--show-current') or '(detached HEAD)'
            elif name == 'git_status':
                output = git('status', '--short') or '(clean)'
            elif name == 'project_files':
                output = git('ls-files') or '(no tracked files)'
                output = '\n'.join(output.splitlines()[:100])
            else:
                result = {'content': [{'type': 'text', 'text': f'Unknown tool: {name}'}], 'isError': True}
                return {'jsonrpc': '2.0', 'id': ident, 'result': result}
            result = {'content': [{'type': 'text', 'text': output}], 'isError': False}
        else:
            return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32601, 'message': f'Method not found: {method}'}}
        return {'jsonrpc': '2.0', 'id': ident, 'result': result}
    except Exception as exc:
        return {'jsonrpc': '2.0', 'id': ident, 'result': {'content': [{'type': 'text', 'text': str(exc)}], 'isError': True}}


def main():
    # MCP stdio transport: one JSON-RPC object per line; stdout is protocol-only.
    for line in sys.stdin:
        try:
            message = json.loads(line)
            reply = respond(message)
            if reply is not None:
                sys.stdout.write(json.dumps(reply, ensure_ascii=False) + '\n')
                sys.stdout.flush()
        except Exception as exc:
            print(f'MCP parse error: {exc}', file=sys.stderr)


if __name__ == '__main__':
    main()
