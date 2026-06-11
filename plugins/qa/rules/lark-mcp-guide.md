# Lark Access Guide (token modes + reading docs)

How the plugin reads documents, comments, and media from Lark/Feishu, and how
commands/skills discover which token mode to use.

## PREFERRED: read via the Python helper, NOT the MCP

The Lark MCP frequently fails with `99991668 token expired` (it does not refresh).
**Agents/commands should read Lark docs through `scripts/lark_read.py`**, which
re-authenticates per run and handles both token modes + fallback:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_read.py" "<wiki_or_docx_url>" --media-urls
# optional: --mode tenant|user (default = the resolved read_mode), --no-comments
```

It returns JSON: `title`, `obj_type`, `obj_token`, `text`, `images[]` (with `tmp_url`),
`links[]`, `comments[]`, plus `mode` (which token was used) and `fallback_from` if it
had to switch modes. The MCP sections below are reference/back-compat only.

## Token modes (dual) + structured "lark info"

Two ways to reach a doc, both configured in `.claude/qa-claude/.plugin.env` and verified
by `/qa:auth-lark`:
- **user** (UAT) — OAuth login (`/qa:auth-lark --login`); the DOC must be visible to the USER. **Project default** (`LARK_TOKEN_MODE=user`) — reads + writes are attributable to a real person.
- **tenant** (app token) — `LARK_APP_ID`+`LARK_APP_SECRET`; the DOC must be shared with the APP. Fallback for docs the user can't see.

**Writes are MANDATORY user mode.** Any CREATE/UPDATE on Lark (a `/qa:log-bug` record, a
`/qa:update-board` change) MUST use the **user token** (`useUAT: true`, or `get_write_token()`
in Python) so the record shows WHO did it. The app/tenant token logs the change as the bot —
do NOT use it to write. If no user token is configured, STOP and run `/qa:auth-lark --login`;
never silently fall back to the app token for a write.

Auth requests **FULL** capability (read **and** write scopes) in one consent so you never
re-grant piecemeal; the OAuth redirect defaults to port **3000** (`http://localhost:3000/callback`).

How commands/skills know which to use for READS — they don't need to decide; `lark_read.py`
resolves it. The resolution is recorded so anything can inspect it:
- **env** (`.plugin.env`): `LARK_TOKEN_MODE` (preference: user(default)|auto|tenant), `LARK_READ_MODE`
  (resolved effective mode), `LARK_APP_CAPABILITIES`, `LARK_USER_CAPABILITIES`.
- **state** (`.claude/qa-claude/lark-auth.state.json`): `read_mode`, `read_mode_reason`, and
  `modes.{tenant,user}.capabilities` (per-mode ✅/❌ map).
- **user** preference uses the user token first; **auto** picks the mode with more granted read
  scopes (tie → tenant). Either way `lark_read.py` **falls back** to the other configured mode
  for any doc the chosen one is denied.

If a read returns an auth/permission error, run `/qa:auth-lark` (or `--login` for user mode)
to fix scopes — do NOT hardcode tokens.

## Error codes (both `lark_auth.py` and `lark_read.py` emit these)

Every failure carries a stable `error_code` + a one-line `action`. Relay the `action`; don't
re-derive the fix.

| `error_code` | Cause | One-step fix |
|---|---|---|
| `CREDS_PLACEHOLDER` | `LARK_APP_ID`/`SECRET` still `cli_xxx`/`your_app_secret` | fill real creds + `ENABLE_LARK_APP=true` |
| `APP_DISABLED` | creds real but `ENABLE_LARK_APP=false` | set `ENABLE_LARK_APP=true` |
| `SSL_CERT` | corporate self-signed proxy (CERTIFICATE_VERIFY_FAILED) | set `SSL_CERT_FILE` to a CA bundle, or `pip install truststore` (the output prints the exact command) |
| `REDIRECT_MISMATCH` | OAuth error 20029 | set `LARK_REDIRECT_URI` to a URL registered in the app console |
| `INVALID_PARAM` | Lark 10003 | re-check `LARK_APP_ID`/`SECRET` |
| `SCOPE_DENIED` | token lacks the scope | grant it (console → publish) or add to `LARK_USER_SCOPE` + re-login |
| `DOC_DENIED` | doc not shared | share with app/user, or `--login` for user mode |

Read scopes (`wiki.read`/`docx.read`/`drive.read`) are **probed for real** by `/qa:auth-lark`
— a missing scope shows as denied up front (not an optimistic "declared"). Use
`--probe-doc <url>` (or `LARK_PROBE_DOC`) to test against the exact doc you need.

### SSL behind a corporate proxy
The TLS context honours `SSL_CERT_FILE` (set it in `.plugin.env`) and auto-uses the OS trust
store if `truststore` is installed. `/qa:doctor` also probes HTTPS to Lark and prints the fix
if a self-signed CA blocks it. NEVER disable verification — point at a real CA bundle.

---

## (Optional) Using the Lark MCP instead of Python

The plugin does **NOT bundle** a Lark MCP (it bundles only figma/playwright/appium — see `plugins/qa/.mcp.json`). Lark stays Python because a bundled MCP can only read shell env vars, not `.plugin.env`, and the MCP often hits `99991668`. If you still want the MCP path, add it to **your own project `.mcp.json`** (env from your shell):

```json
{
  "mcpServers": {
    "lark-mcp": {
      "command": "npx",
      "args": ["-y", "@larksuiteoapi/lark-mcp", "mcp",
               "-a", "${LARK_APP_ID}", "-s", "${LARK_APP_SECRET}",
               "--domain", "https://open.larksuite.com", "--token-mode", "auto"]
    }
  }
}
```

Then the `lark-reader` agent can fall back to the `mcp__lark*` tools when the Python helper is unavailable.

### MCP token param
Config `--token-mode auto`; per call `useUAT: true` → User Access Token, `useUAT: false`/omit → Tenant Access Token. Scope list at `.mcp.json` → `_scopes`.

---

## Flow: reading a Wiki Document

### Step 1: Get the wiki node info
```
wiki_v2_space_getNode(token: "<wiki_token_from_url>")  // useUAT: true
```
- Input: the token from the wiki URL (the part after `/wiki/`)
- Output: `obj_token` (document ID), `obj_type` (docx, sheet, ...), `title`

### Step 2: Read the document content
```
// Get all blocks (text, table, image, bullet...)
docx_v1_documentBlock_list(document_id: obj_token, page_size: 500)  // useUAT: true

// Or get plain text
docx_v1_document_rawContent(document_id: obj_token)  // useUAT: true
```

### Step 3: Read comments
```
drive_v1_fileComment_list(file_token: obj_token, file_type: "docx")  // do NOT use useUAT (tenant token)
```

### Step 4: Download inline images
```
// From documentBlock_list, filter blocks with block_type=27, take image.token
drive_v1_media_batchGetTmpDownloadUrl(file_tokens: [image_tokens...], useUAT: true)  // useUAT MANDATORY
// Use curl to download, the Read tool to view the image content
```

---

## Per-API details

### 1. Wiki Node — `wiki_v2_space_getNode`
- **Token**: `useUAT: true`
- **Params**: `token` = wiki token from the URL
- **Result**: `obj_token`, `obj_type`, `title`, `space_id`

### 2. Document Blocks — `docx_v1_documentBlock_list`
- **Token**: `useUAT: true`
- **Params**: `document_id` = `obj_token` from step 1, `page_size` max 500
- **Result**: list of blocks, each block has a `block_type`:
  - `1` = Page, `2` = Text, `3` = Heading1, `4` = Heading2
  - `12` = Bullet, `27` = Image, `31` = Table, `32` = TableCell
- **Image block**: has `token` (image file token), `width`, `height`
- **Comment**: blocks may contain `comment_ids` — use to match a comment with its position in the document

### 3. Document Raw Content — `docx_v1_document_rawContent`
- **Token**: `useUAT: true`
- **Params**: `document_id` = `obj_token`
- **Result**: plain text of the whole document

### 4. Comment List — `drive_v1_fileComment_list`
- **Token**: Tenant token — **do NOT use `useUAT: true`** (will get Access denied)
- **Params**: `file_token` = `obj_token`, `file_type` = `"docx"`, `page_size` max 50
- **Result**: list of comments, each comment has:
  - `comment_id` — matches `comment_ids` in blocks
  - `quote` — the commented text excerpt
  - `reply_list.replies[]` — reply content (may contain `text_run`, `person` mention, `docs_link`)
  - `is_solved` — resolved or not
  - `is_whole` — global comment (true) or local/inline comment (false)

### 5. Comment Get — `drive_v1_fileComment_get`
- **Token**: Tenant token
- **NOTE**: only works with a **global (whole) comment**. A local comment returns a `"not exist"` error.
- **Recommendation**: always use `fileComment_list` instead of `fileComment_get` to get all comments.

### 6. Media Download — `drive_v1_media_batchGetTmpDownloadUrl`
- **Token**: `useUAT: true` — **MUST use a user access token**
- **Params**: `file_tokens` = array of image tokens (from the image block `token` field), max 5 tokens/call
- **Result**: `tmp_download_urls[]` — each item has `file_token` + `tmp_download_url` (valid 24h)
- **Inline image in docx**: WORKS with `useUAT: true`. The tenant token returns an empty array.
- **Image download flow**:
  1. Get image block tokens from `documentBlock_list` (block_type = 27, field `image.token`)
  2. Call `batchGetTmpDownloadUrl(file_tokens: [...], useUAT: true)` — max 5 tokens/call
  3. Use `curl -sL -o <file> <tmp_download_url>` to download
  4. Use the Read tool to view the image content (multimodal)

---

## Example: read wiki + comments

URL: `https://<your-org>.larksuite.com/wiki/<wiki-token>`

```
// 1. Get obj_token
wiki_v2_space_getNode(token: "<wiki_token>", useUAT: true)
// → obj_token: "<obj_token>", obj_type: "docx"

// 2. Read content (run in parallel)
docx_v1_documentBlock_list(document_id: "<obj_token>", useUAT: true)
drive_v1_fileComment_list(file_token: "<obj_token>", file_type: "docx")  // tenant token

// 3. Download inline images (from block_type=27, take image.token)
drive_v1_media_batchGetTmpDownloadUrl(file_tokens: ["<img_token_1>", "<img_token_2>"], useUAT: true)
// → tmp_download_urls[]: use curl to download, the Read tool to view
```

---

## Important notes

1. **Comments always use the tenant token** — the user token lacks the `docs:document.comment:read` scope
2. **Wiki/docx content always uses the user token** — the tenant token lacks the `docx:document:readonly` scope
3. **Inline image download works** with `useUAT: true` — the tenant token returns an empty array
4. **When `has_more: true`** in the response, use the `page_token` from the response to fetch the next page
</content>
