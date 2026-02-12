"""
Commune MCP Server — email infrastructure tools for AI agents.

An MCP server that connects AI agents to Commune's email API.
Manages domains, inboxes, threads, messages, and attachments.

Install:
    pip install commune-mcp

Configure in Claude Desktop / Cursor / Windsurf:
    {
        "mcpServers": {
            "commune": {
                "command": "uvx",
                "args": ["commune-mcp"],
                "env": { "COMMUNE_API_KEY": "comm_..." }
            }
        }
    }
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ── Configuration ────────────────────────────────────────────────────────────

MCP_VERSION = "0.1.2"
API_VERSION = "v1"  # Commune API version this MCP is tested against
MIN_API_VERSION = "v1"  # Minimum compatible API version

API_KEY = os.environ.get("COMMUNE_API_KEY", "")
BASE_URL = os.environ.get(
    "COMMUNE_BASE_URL", "https://web-production-3f46f.up.railway.app"
).rstrip("/")

mcp = FastMCP(
    "Commune",
    instructions=(
        "Email infrastructure for agents — set up an inbox and send your first email in 30 seconds. "
        "Programmatic inboxes (~1 line), consistent threads, custom domains, attachments, and structured data."
    ),
)

# ── HTTP helpers ─────────────────────────────────────────────────────────────

def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def _get(path: str, params: Optional[dict[str, Any]] = None) -> Any:
    """GET request to the Commune v1 API."""
    clean = {k: v for k, v in (params or {}).items() if v is not None}
    resp = httpx.get(
        f"{BASE_URL}{path}", headers=_headers(), params=clean or None, timeout=30
    )
    resp.raise_for_status()
    body = resp.json()
    return body.get("data", body) if isinstance(body, dict) else body


def _post(path: str, payload: Optional[dict[str, Any]] = None) -> Any:
    """POST request to the Commune v1 API."""
    resp = httpx.post(
        f"{BASE_URL}{path}", headers=_headers(), json=payload, timeout=30
    )
    resp.raise_for_status()
    body = resp.json()
    return body.get("data", body) if isinstance(body, dict) else body


def _put(path: str, payload: Optional[dict[str, Any]] = None) -> Any:
    """PUT request to the Commune v1 API."""
    resp = httpx.put(
        f"{BASE_URL}{path}", headers=_headers(), json=payload, timeout=30
    )
    resp.raise_for_status()
    body = resp.json()
    return body.get("data", body) if isinstance(body, dict) else body


def _delete(path: str) -> Any:
    """DELETE request to the Commune v1 API."""
    resp = httpx.delete(f"{BASE_URL}{path}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    body = resp.json()
    return body.get("data", body) if isinstance(body, dict) else body


def _delete_with_body(path: str, payload: dict[str, Any]) -> Any:
    """DELETE request with JSON body to the Commune v1 API."""
    resp = httpx.request("DELETE", f"{BASE_URL}{path}", headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()
    return body.get("data", body) if isinstance(body, dict) else body


def _fmt(data: Any) -> str:
    """Format data as indented JSON for readable tool output."""
    return json.dumps(data, indent=2, default=str)


# ═════════════════════════════════════════════════════════════════════════════
# DOMAIN TOOLS
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_domains() -> str:
    """List all email domains in your Commune account.

    Returns each domain's ID, name, and verification status.
    Use the domain ID with other tools like list_inboxes or create_inbox.
    """
    return _fmt(_get("/v1/domains"))


@mcp.tool()
def create_domain(name: str, region: Optional[str] = None) -> str:
    """Create a new custom email domain.

    After creating a domain, you need to:
    1. Call get_domain_records to see the required DNS records
    2. Add those records at your domain registrar
    3. Call verify_domain to check verification status

    Args:
        name: Domain name, e.g. "example.com"
        region: AWS region (optional), e.g. "us-east-1" or "eu-west-1"
    """
    payload: dict[str, Any] = {"name": name}
    if region:
        payload["region"] = region
    return _fmt(_post("/v1/domains", payload))


@mcp.tool()
def verify_domain(domain_id: str) -> str:
    """Trigger DNS verification for a domain.

    Call this after adding the required DNS records at your registrar.
    Use get_domain_records first to see which records are needed.

    Args:
        domain_id: The domain ID (from list_domains)
    """
    return _fmt(_post(f"/v1/domains/{domain_id}/verify"))


@mcp.tool()
def get_domain_records(domain_id: str) -> str:
    """Get the DNS records required to verify a domain.

    Returns MX, TXT, and CNAME records that must be added
    at your domain registrar before calling verify_domain.

    Args:
        domain_id: The domain ID (from list_domains)
    """
    return _fmt(_get(f"/v1/domains/{domain_id}/records"))


# ═════════════════════════════════════════════════════════════════════════════
# INBOX TOOLS
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_inboxes(domain_id: Optional[str] = None) -> str:
    """List inboxes.

    Without domain_id, lists all inboxes across all domains.
    With domain_id, lists inboxes for that specific domain.

    Each inbox has a local_part (the part before @) that forms
    the email address: {local_part}@{domain_name}

    Args:
        domain_id: Filter by domain (optional, lists all if omitted)
    """
    if domain_id:
        return _fmt(_get(f"/v1/domains/{domain_id}/inboxes"))
    return _fmt(_get("/v1/inboxes"))


@mcp.tool()
def create_inbox(
    local_part: str,
    domain_id: Optional[str] = None,
    name: Optional[str] = None,
    display_name: Optional[str] = None,
    webhook_endpoint: Optional[str] = None,
) -> str:
    """Create a new inbox for receiving emails.

    The inbox email address will be {local_part}@{domain}.
    If no domain_id is provided, Commune auto-assigns your inbox
    to an available domain — no DNS setup required.

    Args:
        local_part: Part before @ (e.g. "support", "billing", "hello")
        domain_id: Domain to create under (optional, auto-resolved if omitted)
        name: Agent name for the inbox (optional, also used as display_name fallback)
        display_name: Sender display name shown in email clients (e.g. "Support Agent", "Acme Sales"). If set, outbound emails show as '"Display Name" <email>' in Gmail/Outlook.
        webhook_endpoint: URL to receive notifications on new emails (optional)
    """
    payload: dict[str, Any] = {"local_part": local_part}
    if domain_id:
        payload["domain_id"] = domain_id
    if name:
        payload["name"] = name
    if display_name:
        payload["display_name"] = display_name
    if webhook_endpoint:
        payload["webhook"] = {"endpoint": webhook_endpoint}
    return _fmt(_post("/v1/inboxes", payload))


@mcp.tool()
def delete_inbox(domain_id: str, inbox_id: str) -> str:
    """Delete an inbox.

    Args:
        domain_id: The domain ID
        inbox_id: The inbox ID to delete
    """
    return _fmt(_delete(f"/v1/domains/{domain_id}/inboxes/{inbox_id}"))


# ═════════════════════════════════════════════════════════════════════════════
# THREAD TOOLS
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def list_threads(
    inbox_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[str] = None,
    order: str = "desc",
) -> str:
    """List email threads (conversations) with pagination.

    Returns thread summaries: subject, message count, last activity, snippet.
    Use next_cursor from the response to fetch the next page.

    Provide at least one of inbox_id or domain_id.

    Args:
        inbox_id: Filter threads by inbox (recommended)
        domain_id: Filter threads by domain
        limit: Results per page, 1-100 (default: 20)
        cursor: Pagination cursor from a previous response's next_cursor
        order: "desc" for newest first (default), "asc" for oldest first
    """
    params: dict[str, Any] = {"limit": limit, "order": order}
    if inbox_id:
        params["inbox_id"] = inbox_id
    if domain_id:
        params["domain_id"] = domain_id
    if cursor:
        params["cursor"] = cursor

    # Thread endpoint returns {data, next_cursor, has_more} — return full body
    resp = httpx.get(
        f"{BASE_URL}/v1/threads",
        headers=_headers(),
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return _fmt(resp.json())


@mcp.tool()
def get_thread_messages(
    thread_id: str,
    limit: int = 50,
    order: str = "asc",
) -> str:
    """Get all messages in an email thread.

    Returns the full conversation with sender, content, timestamps.

    Args:
        thread_id: The thread ID (from list_threads)
        limit: Max messages, 1-1000 (default: 50)
        order: "asc" for chronological (default), "desc" for newest first
    """
    return _fmt(
        _get(
            f"/v1/threads/{thread_id}/messages",
            {"limit": limit, "order": order},
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# MESSAGE TOOLS
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def send_email(
    to: str,
    subject: str,
    html: Optional[str] = None,
    text: Optional[str] = None,
    from_address: Optional[str] = None,
    reply_to: Optional[str] = None,
    thread_id: Optional[str] = None,
    inbox_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    attachments: Optional[str] = None,
) -> str:
    """Send an email message.

    Provide html or text (or both) for the body.
    To reply in an existing thread, pass thread_id.
    To attach files, first call upload_attachment, then pass
    the attachment IDs as a comma-separated string.

    You only need inbox_id to send — the domain is inferred automatically.

    Args:
        to: Recipient email address (for multiple, comma-separate)
        subject: Email subject line
        html: HTML body content
        text: Plain text body (fallback)
        from_address: Sender address (optional, uses inbox default)
        reply_to: Reply-to address (optional)
        thread_id: Reply within an existing thread (optional)
        inbox_id: Send from a specific inbox (recommended — domain is auto-resolved)
        domain_id: Send from a specific domain (optional, inferred from inbox_id)
        attachments: Comma-separated attachment IDs from upload_attachment (optional)
    """
    # Parse comma-separated to into list
    to_list = [addr.strip() for addr in to.split(",") if addr.strip()]

    payload: dict[str, Any] = {
        "to": to_list if len(to_list) > 1 else to_list[0],
        "subject": subject,
    }
    if html:
        payload["html"] = html
    if text:
        payload["text"] = text
    if from_address:
        payload["from"] = from_address
    if reply_to:
        payload["reply_to"] = reply_to
    if thread_id:
        payload["thread_id"] = thread_id
    if inbox_id:
        payload["inboxId"] = inbox_id
    if domain_id:
        payload["domainId"] = domain_id
    if attachments:
        payload["attachments"] = [
            a.strip() for a in attachments.split(",") if a.strip()
        ]

    return _fmt(_post("/v1/messages/send", payload))


# ═════════════════════════════════════════════════════════════════════════════
# ATTACHMENT TOOLS
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def upload_attachment(
    content: str,
    filename: str,
    mime_type: str,
) -> str:
    """Upload a file for use when sending emails.

    Returns an attachment_id to pass to send_email's attachments parameter.

    Args:
        content: Base64-encoded file content
        filename: Original filename, e.g. "report.pdf"
        mime_type: MIME type, e.g. "application/pdf" or "image/png"
    """
    return _fmt(
        _post(
            "/v1/attachments/upload",
            {"content": content, "filename": filename, "mime_type": mime_type},
        )
    )


@mcp.tool()
def get_attachment_url(attachment_id: str, expires_in: int = 3600) -> str:
    """Get a temporary download URL for an attachment.

    Args:
        attachment_id: The attachment ID
        expires_in: URL lifetime in seconds (default: 3600 = 1 hour)
    """
    return _fmt(
        _get(
            f"/v1/attachments/{attachment_id}/url",
            {"expires_in": expires_in},
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# SEARCH TOOLS
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def search_threads(
    query: str,
    inbox_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    limit: int = 20,
) -> str:
    """Search across email threads by subject or content.

    Returns matching thread summaries with subject, snippet, and message count.
    Provide at least one of inbox_id or domain_id.

    Args:
        query: Search query (searches subject and message content)
        inbox_id: Filter by inbox (recommended)
        domain_id: Filter by domain
        limit: Max results, 1-100 (default: 20)
    """
    params: dict[str, Any] = {"q": query, "limit": limit}
    if inbox_id:
        params["inbox_id"] = inbox_id
    if domain_id:
        params["domain_id"] = domain_id
    return _fmt(_get("/v1/search/threads", params))


# ═════════════════════════════════════════════════════════════════════════════
# TRIAGE TOOLS (tags, status, assignment)
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_thread_metadata(thread_id: str) -> str:
    """Get triage metadata for a thread: tags, status, and assignment.

    Args:
        thread_id: The thread ID
    """
    return _fmt(_get(f"/v1/threads/{thread_id}/metadata"))


@mcp.tool()
def set_thread_status(
    thread_id: str,
    status: str,
) -> str:
    """Set the status of a thread for triage.

    Valid statuses: "open", "needs_reply", "waiting", "closed"

    Args:
        thread_id: The thread ID
        status: New status — one of: open, needs_reply, waiting, closed
    """
    return _fmt(_put(f"/v1/threads/{thread_id}/status", {"status": status}))


@mcp.tool()
def tag_thread(
    thread_id: str,
    tags: str,
) -> str:
    """Add tags/labels to a thread. Tags are additive — existing tags are preserved.

    Use tags for categorization: "vip", "bug-report", "sales-lead", "urgent", etc.

    Args:
        thread_id: The thread ID
        tags: Comma-separated tags to add (e.g. "urgent,vip,sales-lead")
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    return _fmt(_post(f"/v1/threads/{thread_id}/tags", {"tags": tag_list}))


@mcp.tool()
def untag_thread(
    thread_id: str,
    tags: str,
) -> str:
    """Remove tags/labels from a thread.

    Args:
        thread_id: The thread ID
        tags: Comma-separated tags to remove (e.g. "urgent,vip")
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    return _fmt(_delete_with_body(f"/v1/threads/{thread_id}/tags", {"tags": tag_list}))


@mcp.tool()
def assign_thread(
    thread_id: str,
    assigned_to: Optional[str] = None,
) -> str:
    """Assign a thread to an agent or user. Pass null/empty to unassign.

    Args:
        thread_id: The thread ID
        assigned_to: Agent/user identifier to assign to (empty or omit to unassign)
    """
    return _fmt(
        _put(
            f"/v1/threads/{thread_id}/assign",
            {"assigned_to": assigned_to if assigned_to else None},
        )
    )


# ═════════════════════════════════════════════════════════════════════════════
# DELIVERABILITY TOOLS
# ═════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def get_deliverability_stats(
    inbox_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    period: str = "7d",
) -> str:
    """Get email deliverability metrics: sent, delivered, bounced, complained, failed.

    Provides bounce rate, complaint rate, and delivery rate percentages.
    Use this to monitor sender reputation and identify deliverability issues.

    Args:
        inbox_id: Filter metrics by inbox (recommended)
        domain_id: Filter metrics by domain
        period: Time period — "24h", "7d", "30d" (default: "7d")
    """
    params: dict[str, Any] = {"period": period}
    if inbox_id:
        params["inbox_id"] = inbox_id
    if domain_id:
        params["domain_id"] = domain_id
    return _fmt(_get("/v1/delivery/metrics", params))


@mcp.tool()
def get_suppressions(
    inbox_id: Optional[str] = None,
    limit: int = 50,
) -> str:
    """List suppressed email addresses (bounces, complaints, unsubscribes).

    Suppressed addresses are automatically skipped when sending.
    Use this to audit why certain recipients aren't receiving emails.

    Args:
        inbox_id: Filter by inbox (optional)
        limit: Max results (default: 50)
    """
    params: dict[str, Any] = {"limit": limit}
    if inbox_id:
        params["inbox_id"] = inbox_id
    return _fmt(_get("/v1/delivery/suppressions", params))


@mcp.tool()
def get_delivery_events(
    message_id: Optional[str] = None,
    inbox_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
) -> str:
    """Get delivery event log: sent, delivered, bounced, complained, failed.

    Track the lifecycle of individual emails or audit delivery across an inbox.

    Args:
        message_id: Filter events for a specific message
        inbox_id: Filter events by inbox
        event_type: Filter by type: "sent", "delivered", "bounced", "complained", "failed"
        limit: Max results (default: 50)
    """
    params: dict[str, Any] = {"limit": limit}
    if message_id:
        params["message_id"] = message_id
    if inbox_id:
        params["inbox_id"] = inbox_id
    if event_type:
        params["event_type"] = event_type
    return _fmt(_get("/v1/delivery/events", params))


# ═════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

def main():
    """Entry point for the Commune MCP server."""
    # Handle --version flag
    if len(sys.argv) > 1 and sys.argv[1] in ("--version", "-v", "version"):
        print(f"commune-mcp {MCP_VERSION} (API: {API_VERSION})")
        sys.exit(0)

    if not API_KEY:
        print(
            "Error: Set the COMMUNE_API_KEY environment variable.\n"
            "  export COMMUNE_API_KEY=comm_...",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp.run()


if __name__ == "__main__":
    main()
