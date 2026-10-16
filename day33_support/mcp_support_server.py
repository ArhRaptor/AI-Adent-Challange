"""MCP stdio server exposing read-only support CRM records."""
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
mcp = FastMCP('day33-support-crm')


def read_json(filename: str):
    return json.loads((DATA / filename).read_text(encoding='utf-8'))


@mcp.tool()
def get_user(user_id: str) -> dict:
    """Get support user profile by user ID; no secrets are stored."""
    return next((x for x in read_json('users.json') if x['id'] == user_id), {'error': 'User not found'})


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """Get support ticket by ticket ID, including diagnostic context."""
    return next((x for x in read_json('tickets.json') if x['id'] == ticket_id), {'error': 'Ticket not found'})


@mcp.tool()
def list_user_tickets(user_id: str) -> list[dict]:
    """List tickets belonging to a user."""
    return [x for x in read_json('tickets.json') if x['user_id'] == user_id]


if __name__ == '__main__':
    mcp.run(transport='stdio')
