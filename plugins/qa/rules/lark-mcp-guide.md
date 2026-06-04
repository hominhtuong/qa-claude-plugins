# Lark MCP Usage Guide

Guide for using Lark MCP to read documents, comments, and media from Lark/Feishu.

## Token Mode

The MCP config uses `--token-mode auto`. Each API call can override via the `useUAT` param:
- `useUAT: true` → User Access Token (scopes in the `user` section of `.mcp.json`)
- `useUAT: false` or **omit** → Tenant Access Token (scopes in the `tenant` section)

See the scope list at `.mcp.json` → `_scopes`.

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
wiki_v2_space_getNode(token: "BrOZwhai1ifbcokUavil2VQ0gcd", useUAT: true)
// → obj_token: "EV4tdqrWLo8tWyxg4s1luUCDgYe", obj_type: "docx"

// 2. Read content (run in parallel)
docx_v1_documentBlock_list(document_id: "EV4tdqrWLo8tWyxg4s1luUCDgYe", useUAT: true)
drive_v1_fileComment_list(file_token: "EV4tdqrWLo8tWyxg4s1luUCDgYe", file_type: "docx")  // tenant token

// 3. Download inline images (from block_type=27, take image.token)
drive_v1_media_batchGetTmpDownloadUrl(file_tokens: ["T58ob...", "K9Gob..."], useUAT: true)
// → tmp_download_urls[]: use curl to download, the Read tool to view
```

---

## Important notes

1. **Comments always use the tenant token** — the user token lacks the `docs:document.comment:read` scope
2. **Wiki/docx content always uses the user token** — the tenant token lacks the `docx:document:readonly` scope
3. **Inline image download works** with `useUAT: true` — the tenant token returns an empty array
4. **When `has_more: true`** in the response, use the `page_token` from the response to fetch the next page
</content>
