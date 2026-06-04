# Lark MCP Usage Guide

Hướng dẫn sử dụng Lark MCP để đọc tài liệu, comment, và media từ Lark/Feishu.

## Token Mode

MCP config dùng `--token-mode auto`. Mỗi API call có thể override bằng param `useUAT`:
- `useUAT: true` → User Access Token (scopes trong `user` section của `.mcp.json`)
- `useUAT: false` hoặc **omit** → Tenant Access Token (scopes trong `tenant` section)

Xem danh sách scopes tại `.mcp.json` → `_scopes`.

---

## Flow đọc Wiki Document

### Step 1: Lấy thông tin wiki node
```
wiki_v2_space_getNode(token: "<wiki_token_from_url>")  // useUAT: true
```
- Input: token từ URL wiki (phần sau `/wiki/`)
- Output: `obj_token` (document ID), `obj_type` (docx, sheet, ...), `title`

### Step 2: Đọc nội dung document
```
// Lấy tất cả blocks (text, table, image, bullet...)
docx_v1_documentBlock_list(document_id: obj_token, page_size: 500)  // useUAT: true

// Hoặc lấy plain text
docx_v1_document_rawContent(document_id: obj_token)  // useUAT: true
```

### Step 3: Đọc comments
```
drive_v1_fileComment_list(file_token: obj_token, file_type: "docx")  // KHÔNG dùng useUAT (tenant token)
```

### Step 4: Download inline images
```
// Từ documentBlock_list, lọc blocks có block_type=27, lấy image.token
drive_v1_media_batchGetTmpDownloadUrl(file_tokens: [image_tokens...], useUAT: true)  // BẮT BUỘC useUAT
// Dùng curl tải về, Read tool để xem nội dung hình ảnh
```

---

## Chi tiết từng API

### 1. Wiki Node — `wiki_v2_space_getNode`
- **Token**: `useUAT: true`
- **Params**: `token` = wiki token từ URL
- **Kết quả**: `obj_token`, `obj_type`, `title`, `space_id`

### 2. Document Blocks — `docx_v1_documentBlock_list`
- **Token**: `useUAT: true`
- **Params**: `document_id` = `obj_token` từ step 1, `page_size` tối đa 500
- **Kết quả**: danh sách blocks, mỗi block có `block_type`:
  - `1` = Page, `2` = Text, `3` = Heading1, `4` = Heading2
  - `12` = Bullet, `27` = Image, `31` = Table, `32` = TableCell
- **Image block**: có `token` (image file token), `width`, `height`
- **Comment**: blocks có thể chứa `comment_ids` — dùng để match comment với vị trí trong document

### 3. Document Raw Content — `docx_v1_document_rawContent`
- **Token**: `useUAT: true`
- **Params**: `document_id` = `obj_token`
- **Kết quả**: plain text toàn bộ document

### 4. Comment List — `drive_v1_fileComment_list`
- **Token**: Tenant token — **KHÔNG dùng `useUAT: true`** (sẽ bị Access denied)
- **Params**: `file_token` = `obj_token`, `file_type` = `"docx"`, `page_size` tối đa 50
- **Kết quả**: danh sách comments, mỗi comment có:
  - `comment_id` — match với `comment_ids` trong blocks
  - `quote` — đoạn text được comment
  - `reply_list.replies[]` — nội dung replies (có thể chứa `text_run`, `person` mention, `docs_link`)
  - `is_solved` — đã resolved hay chưa
  - `is_whole` — global comment (true) hay local/inline comment (false)

### 5. Comment Get — `drive_v1_fileComment_get`
- **Token**: Tenant token
- **CHÚ Ý**: Chỉ hoạt động với **global (whole) comment**. Local comment sẽ trả lỗi `"not exist"`.
- **Khuyến nghị**: Luôn dùng `fileComment_list` thay vì `fileComment_get` để lấy tất cả comments.

### 6. Media Download — `drive_v1_media_batchGetTmpDownloadUrl`
- **Token**: `useUAT: true` — **BẮT BUỘC dùng user access token**
- **Params**: `file_tokens` = array of image tokens (lấy từ image block `token` field), tối đa 5 tokens/lần
- **Kết quả**: `tmp_download_urls[]` — mỗi item có `file_token` + `tmp_download_url` (valid 24h)
- **Inline image trong docx**: HOẠT ĐỘNG với `useUAT: true`. Tenant token trả về mảng rỗng.
- **Flow download image**:
  1. Lấy image block tokens từ `documentBlock_list` (block_type = 27, field `image.token`)
  2. Gọi `batchGetTmpDownloadUrl(file_tokens: [...], useUAT: true)` — tối đa 5 tokens/lần
  3. Dùng `curl -sL -o <file> <tmp_download_url>` để tải về
  4. Dùng Read tool để xem nội dung hình ảnh (multimodal)

---

## Ví dụ: Đọc wiki + comments

URL: `https://sobanhang.sg.larksuite.com/wiki/BrOZwhai1ifbcokUavil2VQ0gcd`

```
// 1. Lấy obj_token
wiki_v2_space_getNode(token: "BrOZwhai1ifbcokUavil2VQ0gcd", useUAT: true)
// → obj_token: "EV4tdqrWLo8tWyxg4s1luUCDgYe", obj_type: "docx"

// 2. Đọc nội dung (chạy song song)
docx_v1_documentBlock_list(document_id: "EV4tdqrWLo8tWyxg4s1luUCDgYe", useUAT: true)
drive_v1_fileComment_list(file_token: "EV4tdqrWLo8tWyxg4s1luUCDgYe", file_type: "docx")  // tenant token

// 3. Download inline images (từ block_type=27, lấy image.token)
drive_v1_media_batchGetTmpDownloadUrl(file_tokens: ["T58ob...", "K9Gob..."], useUAT: true)
// → tmp_download_urls[]: dùng curl để tải, Read tool để xem
```

---

## Lưu ý quan trọng

1. **Comment luôn dùng tenant token** — user token thiếu scope `docs:document.comment:read`
2. **Wiki/docx content luôn dùng user token** — tenant token thiếu scope `docx:document:readonly`
3. **Inline image download được** với `useUAT: true` — tenant token trả về mảng rỗng
4. **Khi `has_more: true`** trong response, dùng `page_token` từ response để lấy trang tiếp theo
