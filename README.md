# Email for Claude Desktop, Cursor & Windsurf

[![PyPI](https://img.shields.io/pypi/v/commune-mcp?color=blue&label=PyPI)](https://pypi.org/project/commune-mcp/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/commune-mcp?label=installs%2Fmo)](https://pypi.org/project/commune-mcp/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://pypi.org/project/commune-mcp/)
[![MIT License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple)](https://modelcontextprotocol.io)
[![Works with Claude](https://img.shields.io/badge/works%20with-Claude%20Desktop-orange)](https://claude.ai)
[![Works with Cursor](https://img.shields.io/badge/works%20with-Cursor-blue)](https://cursor.sh)
[![commune.email](https://img.shields.io/badge/docs-commune.email-blue)](https://commune.email/?ref=commune-mcp)

Give Claude (or any MCP client) a real email inbox and SMS. Install in 30 seconds — no cloning required.

Your AI agent can:
- **Read email** — list threads, search by topic, get full message history
- **Send email** — reply in existing threads, compose fresh messages, attach files
- **Manage inboxes** — create programmatic inboxes, set up custom domains, triage with tags and status
- **Track delivery** — get delivery stats, suppression lists, bounce and complaint events
- **Send and receive SMS** — provision phone numbers, send messages, search SMS history

Works with Claude Desktop, Cursor, Windsurf, or any [MCP](https://modelcontextprotocol.io) client.

---

## Install via Smithery

[![smithery badge](https://smithery.ai/badge/commune)](https://smithery.ai/server/commune)

```bash
npx @smithery/cli install commune --client claude
```

---

## Example prompts

Once configured, you can give your AI assistant natural language instructions for email and SMS:

**Reading email:**
- "Check my support inbox for new emails"
- "Show me all unread threads in the billing inbox"
- "Find emails from customers asking about refunds this week"
- "Search for all threads about the payment issue from last month"
- "What's the full conversation history for thread conv_abc123?"
- "Show me all threads that haven't been replied to"

**Sending email:**
- "Reply to John's email saying we'll process his refund within 48 hours"
- "Send an email to alice@example.com with subject 'Meeting tomorrow' and tell her the meeting is moved to 3pm"
- "Reply to the last message in the support thread about the broken login, staying in thread"
- "Send a follow-up to all leads from last week who didn't respond"

**Organizing and triaging:**
- "Tag this thread as urgent and assign it to the billing team"
- "Mark all threads older than 30 days with no reply as closed"
- "Show me the deliverability stats for the past 7 days"
- "List all suppressed email addresses in the support inbox"

**SMS:**
- "Provision a phone number for my agent"
- "Send an SMS to +14155551234 saying 'Your order has shipped'"
- "Show me all my SMS conversations"
- "Search my SMS messages for anything about delivery issues"

**Domain and inbox management:**
- "Create a new inbox called 'billing' under example.com"
- "What DNS records do I need to add to verify example.com?"
- "Show me all my verified domains"

---

## Setup

### 1. Get your API key

Create an API key from your [Commune dashboard](https://commune.email/?ref=commune-mcp). It starts with `comm_`.

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

## How email flows through Commune MCP

Inbound (you receive email):

```
  User sends email
       |
       v
  Commune receives at your inbox (support@yourdomain.com)
       |
       v
  Commune fires webhook to your app (8 retries, HMAC signed)
       |
       v
  Your MCP client reads thread via list_threads / get_thread_messages
       |
       v
  You ask Claude: "Reply to John saying we're on it"
       |
       v
  Claude calls send_email with thread_id --> reply appears in John's email thread
```

Outbound (you send email):

```
  You: "Send an update email to all VIP customers"
       |
       v
  Claude calls list_threads --> get_thread_messages --> send_email (per thread)
       |
       v
  Commune delivers via DKIM-signed SMTP
       |
       v
  Delivery events tracked: sent --> delivered / bounced / complained
```

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
| `name` | `str` | No | Agent name for the inbox |
| `display_name` | `str` | No | Sender display name shown in email clients |
| `webhook_endpoint` | `str` | No | URL for email notifications |

---

#### `delete_inbox`

Delete an inbox permanently.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain_id` | `str` | Yes | Domain ID |
| `inbox_id` | `str` | Yes | Inbox ID |

---

#### `set_extraction_schema`

Configure structured extraction for an inbox using a JSON Schema.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain_id` | `str` | Yes | Domain ID |
| `inbox_id` | `str` | Yes | Inbox ID |
| `name` | `str` | Yes | Schema name |
| `schema` | `str` | Yes | JSON string of schema object |
| `description` | `str` | No | Human-readable description |
| `enabled` | `bool` | No | Enable extraction (default true) |

---

#### `remove_extraction_schema`

Remove structured extraction from an inbox.

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
| `domain_id` | `str` | No | Filter by domain |
| `limit` | `int` | No | Max results (default: 50) |

---

#### `get_delivery_events`

Get delivery event log for tracking individual emails.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | `str` | No | Filter for a specific message |
| `inbox_id` | `str` | No | Filter by inbox |
| `domain_id` | `str` | No | Filter by domain |
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

### Phone Number Tools

Manage provisioned phone numbers for SMS.

#### `list_phone_numbers`

List all provisioned phone numbers in your account.

**Parameters:** None

---

#### `get_phone_number`

Get details for a single provisioned phone number.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | Phone number ID from `list_phone_numbers` |

---

#### `list_available_phone_numbers`

Browse available phone numbers before purchasing.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | `str` | No | `"TollFree"` (default) or `"Local"` |
| `country` | `str` | No | Two-letter country code (default: `"US"`) |
| `limit` | `int` | No | Max results (default: 10) |

---

#### `provision_phone_number`

Purchase a phone number for SMS. Deducts credits from your balance.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number` | `str` | No | Specific E.164 number to buy (auto-selected if omitted) |
| `type` | `str` | No | `"tollfree"` (default) or `"local"` |
| `friendly_name` | `str` | No | Human-readable label |

---

#### `update_phone_number`

Update a phone number's friendly name or auto-reply message.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | Phone number ID |
| `friendly_name` | `str` | No | Human-readable label |
| `auto_reply` | `str` | No | Auto-reply text for all inbound SMS (empty string to disable) |

---

#### `release_phone_number`

Release a provisioned phone number back to the pool. No credit refund. Message history is retained.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | Phone number ID to release |

---

#### `set_phone_number_webhook`

Configure a webhook for a phone number to receive SMS event notifications.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | Phone number ID |
| `endpoint` | `str` | Yes | HTTPS URL to receive webhook payloads |
| `secret` | `str` | No | Webhook signing secret for payload verification |
| `events` | `list` | No | Event types (default: `["sms.received", "sms.sent"]`) |

---

#### `set_phone_number_allow_list`

Set the allow list for a phone number — only these numbers can send SMS to it. Replaces existing list.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | Phone number ID |
| `numbers` | `list` | Yes | E.164 phone numbers to allow (empty list to clear) |

---

#### `set_phone_number_block_list`

Set the block list for a phone number — these numbers are rejected. Replaces existing list.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | Yes | Phone number ID |
| `numbers` | `list` | Yes | E.164 phone numbers to block (empty list to clear) |

---

### SMS Tools

#### `send_sms`

Send an SMS message.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to` | `str` | Yes | Recipient in E.164 format (e.g. `"+15551234567"`) |
| `body` | `str` | Yes | SMS message text |
| `phone_number_id` | `str` | No | Send from a specific phone number (auto-assigned if omitted) |

---

#### `list_sms_conversations`

List SMS conversation threads.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | No | Filter by phone number (lists all if omitted) |
| `limit` | `int` | No | 1–100, default 20 |

---

#### `get_sms_thread`

Get all messages in an SMS thread with a specific number.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `remote_number` | `str` | Yes | External phone number in E.164 format |
| `phone_number_id` | `str` | Yes | Your Commune phone number ID |

---

#### `search_sms`

Semantic search across SMS messages.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | `str` | Yes | Search query |
| `phone_number_id` | `str` | No | Scope to a specific phone number |
| `limit` | `int` | No | 1–100, default 20 |

---

#### `list_sms_suppressions`

List phone numbers suppressed from receiving SMS (opted out via STOP keyword).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number_id` | `str` | No | Filter by phone number (lists all if omitted) |

---

#### `remove_sms_suppression`

Remove a phone number from the SMS suppression list (re-enable SMS delivery).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `phone_number` | `str` | Yes | E.164 phone number to remove from suppressions |

---

### Credits Tools

#### `get_credit_balance`

Get current credit balance for your Commune account.

**Parameters:** None

---

#### `list_credit_bundles`

List available credit bundles that can be purchased.

**Parameters:** None

---

#### `credits_checkout`

Create a Stripe checkout session to purchase a credit bundle.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bundle` | `str` | Yes | Bundle ID: `"starter"`, `"growth"`, or `"scale"` |
| `return_url` | `str` | No | URL to redirect to after payment |

---

## FAQ

**How do I add Commune to Claude Desktop?**
Edit `~/Library/Application Support/Claude/claude_desktop_config.json` and add the commune MCP server block (see Setup above). Restart Claude Desktop. The Commune tools will appear in Claude's tool list automatically.

**What's the difference between commune-mcp and the Python/TypeScript SDKs?**
commune-mcp is for interactive use in MCP clients like Claude Desktop or Cursor — you give natural language instructions and the AI calls the tools. The Python/TypeScript SDKs are for building autonomous agents programmatically in code. Both connect to the same Commune backend.

**Does it work with Cursor's agent mode?**
Yes. Add commune-mcp to Cursor via Settings → MCP → Add Server using the JSON block shown in the Setup section. Once configured, Cursor's agent mode can use all Commune tools — reading threads, sending email, and managing inboxes — during any chat or Composer session.

**How do I create a new inbox through the MCP server?**
Just ask: "Create a new inbox called support under example.com." The agent will call `create_inbox` with `local_part: "support"` and your domain ID. If you don't specify a domain, Commune auto-assigns one — so you can create an inbox with just a local part and no DNS configuration.

**Can Claude actually send real emails through this?**
Yes. When the agent calls `send_email`, Commune delivers a real email via DKIM-signed SMTP to the recipient's inbox. The email appears exactly like a normal email — it threads correctly in Gmail and Outlook, supports HTML and attachments, and generates delivery events you can track.

**What happens to emails that arrive while I'm not in a chat session?**
Commune stores all inbound emails and threads persistently. When you open a new chat and ask to check your inbox, the agent calls `list_threads` and retrieves everything that arrived since your last session. Optionally, you can configure a webhook on each inbox so your app gets notified in real-time (8 retries, HMAC-signed).

**How do I reply in a thread instead of starting a new email?**
Pass the `thread_id` to `send_email`. The easiest way is to say "Reply to this thread saying..." after asking the agent to show you a thread — it will keep the `thread_id` in context and pass it automatically. The reply appears threaded in the recipient's email client.

**Is my email content private?**
Your email content is transmitted over TLS and stored encrypted at rest on Commune's infrastructure. API keys authenticate every request, and webhooks are HMAC-signed so your app can verify the payload hasn't been tampered with. Your content is never used for training AI models.

**Can I use this with my own email domain?**
Yes. Use `create_domain` to register your domain, then `get_domain_records` to see the required MX, TXT, and CNAME records, add them at your registrar, and call `verify_domain`. Once verified, all inboxes under that domain use your domain as the sender address (e.g. `support@yourdomain.com`).

**What does the API key look like?**
Commune API keys start with the prefix `comm_` followed by a random string — for example, `comm_sk_live_abc123xyz`. Create one from your [Commune dashboard](https://commune.email). Keep it secret: treat it like a password and never commit it to source control.

**How do I search my inbox for a specific topic?**
Use the `search_threads` tool by asking naturally: "Search my support inbox for emails about refunds." The agent calls `search_threads` with your query. Commune uses semantic search, so it finds relevant threads even if the exact words don't match — for example, "money back" will surface threads about refunds.

**Can multiple people use the same Commune MCP server?**
Yes. Commune uses organizations — multiple team members can share the same account and API key, or each member can have their own API key scoped to the same organization. All keys access the same domains and inboxes. For isolation between projects, create separate inboxes (e.g. `billing@`, `support@`) and filter by `inbox_id` in tool calls.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `COMMUNE_API_KEY` | **Yes** | Your API key (starts with `comm_`) |
| `COMMUNE_BASE_URL` | No | Override API URL (default: Commune cloud) |

## License

MIT
