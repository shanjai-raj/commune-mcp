# Common Errors — Commune MCP

Troubleshooting guide for the most common issues when using commune-mcp with Claude Desktop, Cursor, or Windsurf.

---

## 1. Server not appearing in Claude Desktop

**Symptom:** You've added the Commune block to `claude_desktop_config.json` but no Commune tools show up in Claude.

**Causes and fixes:**

- **Config JSON has a syntax error.** JSON is strict — trailing commas and missing brackets break the whole file. Validate it at [jsonlint.com](https://jsonlint.com) or run:
  ```bash
  cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool
  ```
  Fix any errors it reports.

- **Claude Desktop wasn't restarted.** MCP servers are loaded at startup. Quit Claude Desktop completely (`Cmd+Q` on macOS, not just close the window) and reopen it.

- **The config file is in the wrong location.** The correct path on macOS is:
  ```
  ~/Library/Application Support/Claude/claude_desktop_config.json
  ```
  On Windows it is `%APPDATA%\Claude\claude_desktop_config.json`. Double-check you're editing the right file.

- **The commune block is nested incorrectly.** It must be inside `"mcpServers"`. The correct structure:
  ```json
  {
    "mcpServers": {
      "commune": {
        "command": "uvx",
        "args": ["commune-mcp"],
        "env": { "COMMUNE_API_KEY": "comm_your_key_here" }
      }
    }
  }
  ```

---

## 2. "COMMUNE_API_KEY not set" error

**Symptom:** The MCP server starts but immediately exits with `Error: Set the COMMUNE_API_KEY environment variable.`

**Fix:** Your API key is missing from the `env` block in the config. Make sure your config includes it exactly:

```json
"env": {
  "COMMUNE_API_KEY": "comm_your_actual_key_here"
}
```

Common mistakes:
- Leaving the placeholder `comm_your_key_here` instead of pasting your real key.
- Putting the key outside the `env` block.
- Setting `COMMUNE_API_KEY` as a shell environment variable instead of in the config — this works for terminal use but MCP clients launch servers in a clean environment and don't inherit shell variables.

Get your API key from the [Commune dashboard](https://commune.email).

---

## 3. Tools listed but all return errors

**Symptom:** Claude can see Commune tools and tries to call them, but every call returns a 401 or 403 error.

**Cause:** The API key is present but invalid, revoked, or expired.

**Fix:**
1. Log in to your [Commune dashboard](https://commune.email) and verify the key exists and is active.
2. If it was rotated or deleted, create a new one and update your MCP config.
3. Make sure there are no extra spaces or newlines in the key value — copy it fresh from the dashboard.

If the error message says `403 Forbidden` rather than `401 Unauthorized`, your key may lack permissions for the operation. Admin-gated operations (like phone number provisioning) require a key with admin-level access.

---

## 4. `send_email` succeeds but email is not received

**Symptom:** The tool returns success and a message ID, but the recipient never gets the email.

**Check these in order:**

1. **Recipient is on the suppression list.** Call `get_suppressions` for your inbox or domain. If the recipient address appears, Commune skips delivery automatically (to protect sender reputation). Remove them from the suppression list via the Commune dashboard if they want to receive email again.

2. **Sending domain is not verified.** Call `list_domains` and check that your domain's `status` is `"verified"`. If it's `"pending"`, add the required DNS records (from `get_domain_records`) and call `verify_domain`. Until verified, emails may be rejected or land in spam.

3. **Email landed in spam.** Ask the recipient to check their spam folder. New domains with no sending history are more likely to be flagged. Check `get_deliverability_stats` for high bounce or complaint rates that may be hurting your reputation.

4. **Delivery event shows bounced or failed.** Call `get_delivery_events` with the `message_id` returned by `send_email`. The `event_type` field will tell you whether it was a hard bounce, soft bounce, or delivery failure — and the event payload typically includes a reason code.

---

## 5. `list_threads` returns empty

**Symptom:** `list_threads` returns `{"data": [], "has_more": false}` even though you believe emails have been received.

**Causes and fixes:**

- **Wrong inbox ID.** Call `list_inboxes` first to get the correct `id` for your inbox. Inbox IDs look like `i_xyz789` — don't confuse them with the inbox address (`support@example.com`) or domain ID.

- **No emails have arrived yet.** If this is a new inbox, send a test email to the inbox address and wait a few seconds, then call `list_threads` again.

- **Filtering by domain instead of inbox.** If you pass `domain_id` without `inbox_id`, you'll see threads across all inboxes in that domain. If you only want one inbox's threads, always pass `inbox_id`.

- **Inbound email not configured.** Your domain's MX record must point to Commune's inbound SMTP server. Call `get_domain_records` and verify the MX record is present and has propagated (use `dig MX yourdomain.com` to check).

---

## 6. `get_thread_messages` returns the wrong thread

**Symptom:** You pass a thread ID but get messages that don't match the thread you were looking at.

**Cause:** Confusion between the `thread_id` field (used by Commune tools) and the `conv_` prefixed conversation ID shown in some contexts.

**Fix:** Always use the `thread_id` value from `list_threads` response data. It looks like `conv_abc123`. Do not construct or guess thread IDs — always retrieve them from `list_threads` or `search_threads` first.

If you passed a `thread_id` from a previous session or hardcoded it, verify it still exists by calling `get_thread_metadata` with that ID — it will error if the thread ID is invalid.

---

## 7. Custom domain not working after DNS setup

**Symptom:** You've added DNS records but `verify_domain` still returns `"status": "pending"` or verification fails.

**Causes and fixes:**

- **DNS changes haven't propagated yet.** DNS propagation can take anywhere from 5 minutes to 48 hours depending on your registrar and TTL settings. Check propagation status at [dnschecker.org](https://dnschecker.org) by entering your domain and checking the record types (MX, TXT, CNAME) required by `get_domain_records`.

- **Records were added incorrectly.** Compare each record from `get_domain_records` against what's actually in your DNS provider's dashboard. Common mistakes include adding a trailing dot to the hostname, miscopying the value, or creating the wrong record type (e.g. A instead of TXT).

- **Registrar strips special characters.** Some registrars modify TXT record values (especially SPF). Double-check the raw TXT value after saving. The SPF record must be verbatim.

- **Old records are conflicting.** If you have an existing MX record pointing elsewhere, it may conflict. Review all existing records and remove or update any that conflict with Commune's requirements.

---

## 8. `uvx not found` when starting the MCP server

**Symptom:** Claude Desktop shows an error like `spawn uvx ENOENT` or `uvx: command not found`.

**Cause:** `uv` (and its `uvx` command) is not installed on your system.

**Fix:** Install `uv` using the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then restart your terminal and try again. Verify installation:

```bash
uvx --version
```

On macOS you can also install via Homebrew:

```bash
brew install uv
```

After installing, restart Claude Desktop so it picks up the updated PATH. If `uvx` is installed but still not found by Claude Desktop, check that the install location (usually `~/.cargo/bin` or `~/.local/bin`) is in your PATH, and consider using the full path in the MCP config:

```json
{
  "command": "/Users/yourname/.local/bin/uvx",
  "args": ["commune-mcp"]
}
```

Alternatively, install commune-mcp with `pip install commune-mcp` and use `commune-mcp` as the command instead of `uvx`.
