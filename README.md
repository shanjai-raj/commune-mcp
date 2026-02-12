# Commune MCP Server

Email infrastructure for agents — set up an inbox and send your first email in 30 seconds.

Programmatic inboxes (~1 line), consistent threads, setup and verify custom domains, send and receive attachments, structured data extraction. Works with Claude Desktop, Cursor, Windsurf, or any [MCP](https://modelcontextprotocol.io) client. Install from PyPI — no cloning required.

---

## Setup

### 1. Get your API key

Create an API key from your [Commune dashboard](https://commune.sh). It starts with `comm_`.

### 2. Add to your MCP client

Pick your client and add the Commune server. No local files needed — `uvx` fetches the package automatically.

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "commune": {
      "command": "uvx",
      "args": ["commune-mcp"],
      "env": {
        "COMMUNE_API_KEY": "comm_your_key_here"
      }
    }
  }
}
```

#### Cursor

Open **Settings → MCP → Add Server**:

```json
{
  "commune": {
    "command": "uvx",
    "args": ["commune-mcp"],
    "env": {
      "COMMUNE_API_KEY": "comm_your_key_here"
    }
  }
}
```

#### Windsurf

Open **Settings → MCP**, same format as Cursor.

### Alternative: pip install

If you prefer `pip` over `uvx`:

```bash
pip install commune-mcp
```

Then use `commune-mcp` as the command:

```json
{
  "commune": {
    "command": "commune-mcp",
    "env": {
      "COMMUNE_API_KEY": "comm_your_key_here"
    }
  }
}
```

---

## How It Works

Once configured, your AI agent can use Commune tools in natural conversation:

> **You:** Check my support inbox for new emails
>
> **Agent:** *(calls `list_domains` → `list_inboxes` → `list_threads`)*
> You have 3 new threads in support@example.com:
> 1. "Order not received" — 4 messages, last activity 2h ago
> 2. "Billing question" — 1 message, received today
> 3. "Feature request" — 2 messages, last activity yesterday

> **You:** What's the order issue about?
>
> **Agent:** *(calls `get_thread_messages`)*
> Customer john@gmail.com says their order #4521 shipped 5 days ago but hasn't arrived. They've followed up twice asking for tracking info.

> **You:** Reply that we're checking with shipping and will update within 24h
>
> **Agent:** *(calls `send_email` with `thread_id`)*
> Done — reply sent to john@gmail.com in the existing thread.

The agent decides which tools to call based on your request. You don't need to specify tool names.

---

## Tools Reference

### Domain Tools

These manage your email domains. Domains must be verified via DNS before you can send/receive.

#### `list_domains`

List all email domains in your account.

**Parameters:** None

**Output:**
```json
[
  {
    "id": "d_abc123",
    "name": "example.com",
    "status": "verified",
    "region": "us-east-1"
  }
]
```

---

#### `create_domain`

Create a new custom domain. After creating, use `get_domain_records` to see required DNS entries, then `verify_domain` to check.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Domain name (e.g. `"example.com"`) |
| `region` | `str` | No | AWS region (e.g. `"us-east-1"`) |

**Output:** The created domain object with its ID and status.

---

#### `get_domain_records`

Get DNS records you need to add at your registrar before verification passes.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain_id` | `str` | Yes | Domain ID from `list_domains` |

**Output:**
```json
[
  { "type": "MX", "name": "example.com", "value": "inbound-smtp.us-east-1.amazonaws.com", "status": "pending" },
  { "type": "TXT", "name": "example.com", "value": "v=spf1 include:amazonses.com ~all", "status": "pending" }
]
```

---

#### `verify_domain`

Trigger DNS verification. Call after adding records at your registrar.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain_id` | `str` | Yes | Domain ID |

---

### Inbox Tools

Inboxes are mailboxes under a domain. `support` under `example.com` → `support@example.com`.

#### `list_inboxes`

List inboxes. Without `domain_id`, lists all inboxes across all domains.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain_id` | `str` | No | Filter by domain (lists all if omitted) |

**Output:**
```json
[
  {
    "id": "i_xyz789",
    "localPart": "support",
    "address": "support@example.com",
    "webhook": { "endpoint": "https://..." }
  }
]
```

---

#### `create_inbox`

Create a new inbox. Domain is **auto-resolved** if not provided — no DNS setup needed.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `local_part` | `str` | Yes | Part before `@` (e.g. `"support"`, `"billing"`) |
| `domain_id` | `str` | No | Domain to create under. Auto-resolved if omitted. |
| `name` | `str` | No | Display name |
| `webhook_endpoint` | `str` | No | URL for email notifications |

---

#### `delete_inbox`

Delete an inbox permanently.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain_id` | `str` | Yes | Domain ID |
| `inbox_id` | `str` | Yes | Inbox ID |

---

### Thread Tools

Threads are email conversations — groups of related messages. These are the most commonly used tools.

#### `list_threads`

List threads for an inbox with cursor-based pagination. Returns newest first by default.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inbox_id` | `str` | One of these | Filter by inbox |
| `domain_id` | `str` | required | Filter by domain |
| `limit` | `int` | No | 1–100, default 20 |
| `cursor` | `str` | No | Pagination cursor from previous response |
| `order` | `str` | No | `"desc"` (newest first) or `"asc"` |

**Output:**
```json
{
  "data": [
    {
      "thread_id": "conv_abc123",
      "subject": "Order not received",
      "message_count": 4,
      "last_message_at": "2025-03-15T14:30:00Z",
      "snippet": "Hi, I ordered 5 days ago and still haven't...",
      "last_direction": "inbound",
      "has_attachments": false
    }
  ],
  "next_cursor": "eyJsYXN0...",
  "has_more": true
}
```

To get the next page, pass `next_cursor` as the `cursor` parameter.

---

#### `get_thread_messages`

Get all messages in a thread. Returns oldest first (chronological).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | `str` | Yes | Thread ID from `list_threads` |
| `limit` | `int` | No | 1–1000, default 50 |
| `order` | `str` | No | `"asc"` (chronological) or `"desc"` |

**Output:**
```json
[
  {
    "message_id": "msg_001",
    "direction": "inbound",
    "participants": [
      { "role": "sender", "identity": "john@gmail.com" },
      { "role": "to", "identity": "support@example.com" }
    ],
    "content": "Hi, I placed order #4521 five days ago...",
    "metadata": {
      "subject": "Order not received",
      "created_at": "2025-03-10T09:15:00Z"
    }
  },
  {
    "message_id": "msg_002",
    "direction": "outbound",
    "content": "We're looking into this for you...",
    "metadata": {
      "subject": "Re: Order not received",
      "created_at": "2025-03-10T10:30:00Z"
    }
  }
]
```

---

### Search Tools

#### `search_threads`

Search across email threads by subject or content. Uses vector search (semantic) when available, falls back to text matching.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `str` | Yes | Search query (natural language) |
| `inbox_id` | `str` | One of these | Filter by inbox |
| `domain_id` | `str` | required | Filter by domain |
| `limit` | `int` | No | 1–100, default 20 |

---

### Triage Tools

Manage thread status, tags, and assignment — agent-native workflow primitives.

#### `get_thread_metadata`

Get triage metadata for a thread: tags, status, and assignment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | `str` | Yes | Thread ID |

---

#### `set_thread_status`

Set the triage status of a thread.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | `str` | Yes | Thread ID |
| `status` | `str` | Yes | `"open"`, `"needs_reply"`, `"waiting"`, or `"closed"` |

---

#### `tag_thread`

Add tags/labels to a thread. Tags are additive — existing tags are preserved.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | `str` | Yes | Thread ID |
| `tags` | `str` | Yes | Comma-separated tags (e.g. `"urgent,vip,sales-lead"`) |

---

#### `untag_thread`

Remove tags from a thread.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | `str` | Yes | Thread ID |
| `tags` | `str` | Yes | Comma-separated tags to remove |

---

#### `assign_thread`

Assign a thread to an agent or user. Pass empty to unassign.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `thread_id` | `str` | Yes | Thread ID |
| `assigned_to` | `str` | No | Agent/user identifier (empty to unassign) |

---

### Deliverability Tools

#### `get_deliverability_stats`

Get delivery metrics: sent, delivered, bounced, complained, failed counts and rates.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inbox_id` | `str` | One of these | Filter by inbox |
| `domain_id` | `str` | required | Filter by domain |
| `period` | `str` | No | `"24h"`, `"7d"`, `"30d"` (default: `"7d"`) |

---

#### `get_suppressions`

List suppressed email addresses (bounces, complaints, unsubscribes).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inbox_id` | `str` | No | Filter by inbox |
| `limit` | `int` | No | Max results (default: 50) |

---

#### `get_delivery_events`

Get delivery event log for tracking individual emails.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | `str` | No | Filter for a specific message |
| `inbox_id` | `str` | No | Filter by inbox |
| `event_type` | `str` | No | `"sent"`, `"delivered"`, `"bounced"`, `"complained"`, `"failed"` |
| `limit` | `int` | No | Max results (default: 50) |

---

### Message Tools

#### `send_email`

Send an email. Can send fresh emails or reply within an existing thread.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | `str` | Yes | Recipient(s), comma-separated for multiple |
| `subject` | `str` | Yes | Subject line |
| `html` | `str` | No* | HTML body |
| `text` | `str` | No* | Plain text body |
| `from_address` | `str` | No | Sender address |
| `reply_to` | `str` | No | Reply-to address |
| `thread_id` | `str` | No | Reply in existing thread |
| `inbox_id` | `str` | No | Send from specific inbox |
| `domain_id` | `str` | No | Send from specific domain |
| `attachments` | `str` | No | Comma-separated attachment IDs |

*Provide at least `html` or `text`.

**To reply in a thread**, pass the `thread_id` from `list_threads` or `get_thread_messages`. The email will be threaded in the recipient's mailbox.

---

### Attachment Tools

#### `upload_attachment`

Upload a file. Returns an `attachment_id` to use with `send_email`.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | `str` | Yes | Base64-encoded file content |
| `filename` | `str` | Yes | Filename (e.g. `"report.pdf"`) |
| `mime_type` | `str` | Yes | MIME type (e.g. `"application/pdf"`) |

**Output:**
```json
{
  "attachment_id": "att_abc123",
  "filename": "report.pdf",
  "mime_type": "application/pdf",
  "size": 45230
}
```

---

#### `get_attachment_url`

Get a temporary download URL for an attachment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `attachment_id` | `str` | Yes | Attachment ID |
| `expires_in` | `int` | No | Seconds until URL expires (default: 3600) |

**Output:**
```json
{
  "url": "https://res.cloudinary.com/...",
  "expires_in": 3600,
  "filename": "report.pdf",
  "mime_type": "application/pdf",
  "size": 45230
}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COMMUNE_API_KEY` | **Yes** | Your API key (starts with `comm_`) |
| `COMMUNE_BASE_URL` | No | Override API URL (default: Commune cloud) |

## License

MIT
