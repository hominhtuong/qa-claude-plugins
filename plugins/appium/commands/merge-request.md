---
description: Review → fix → tích hợp main mới nhất qua branch tạm (merge an toàn) → push → tạo Merge Request trên GitLab (glab)
argument-hint: [tiêu đề MR tuỳ chọn] [--target <branch đích, mặc định main>]
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# /merge-request — Tạo MR sạch (không conflict, không mất code)

Input: **$ARGUMENTS** (tiêu đề MR tuỳ chọn; target mặc định `main`).

Remote dự án: **GitLab** `code.finan.one/finan-qa/sbh-auto-apps`. Mục tiêu: tạo MR cho branch hiện tại, **không conflict với target & không mất dòng code nào** — tích hợp sẵn `main` mới nhất qua **branch tạm** trước khi push.

## Quy trình (làm đúng thứ tự)

### 1. Cổng chất lượng — skill `review-audit` + `fix-by-layer` + `build-verify`
Như bước 1–3 của `/push-code`: `review-audit` → tự fix Critical rõ ràng qua `fix-by-layer` / DỪNG nếu cần quyết định → `build-verify` xanh. Chưa sạch + xanh thì **không** tạo MR.

### 2. Chốt branch & commit — skill `commit-push` (chỉ branch + commit)
Xác định `FEATURE` (đang ở `main` → tạo `feat/<slug>`, không bao giờ MR main→main). Commit hết thay đổi đang dở (message `$ARGUMENTS` nếu có + trailer Co-Authored-By). **Chưa push**. Xác định `TARGET` (mặc định `main` hoặc `--target`).

### 3. Lấy target mới nhất
`git fetch origin --prune`. Tham chiếu `origin/<TARGET>`.

### 4. Tích hợp qua branch tạm (an toàn)
1. `git switch -c tmp/mr-<FEATURE> origin/<TARGET>` → `git merge --no-ff FEATURE`.
2. Conflict → giải theo **Rule merge thông minh** dưới. Giải xong: không còn marker (`grep` kiểm) **và** `build-verify` xanh.

### 5. Đưa kết quả về FEATURE (fast-forward, không mất code)
- `git switch FEATURE` → `git merge --ff-only tmp/mr-<FEATURE>` → `git branch -D tmp/mr-<FEATURE>`.
- (4)/(5) thất bại không cứu an toàn được → `git merge --abort`, xoá branch tạm, **DỪNG** + báo danh sách file conflict cần quyết định. Tuyệt đối không bỏ code.

### 6. Push & tạo MR
- `git push -u origin FEATURE` (không force).
- **glab** (đã `glab auth login --hostname code.finan.one`):
  ```bash
  glab mr create --source-branch FEATURE --target-branch <TARGET> \
    --title "<tiêu đề>" --description "<mô tả>" --remove-source-branch=false --yes
  ```
- glab chưa auth → fallback GitLab API (token `GITLAB_PAT`, project encoded `finan-qa%2Fsbh-auto-apps`, host `code.finan.one`). KHÔNG in token. Tiêu đề `$ARGUMENTS` hoặc sinh từ diff; mô tả = tóm tắt thay đổi + kết quả review + "đã tích hợp `origin/<TARGET>`, build xanh".
- Sau khi tạo: xác nhận MR **mergeable** (`glab mr view <iid>` / API `has_conflicts`). Target nhảy → lặp bước 3–5.

## Rule merge thông minh (khi có conflict)
Nguyên tắc: **không mất code, không đoán bừa.**
1. KHÔNG `-X ours`/`-X theirs` toàn cục. Giải từng hunk sau khi hiểu cả hai phía.
2. Thay đổi cộng dồn khác vị trí (method/field/import/key config) → **GIỮ CẢ HAI** (đa số conflict repo *package-by-feature* thuộc loại này).
3. `configurations/*.properties` → union key cả hai phía. `elements.json`/`test-hints.json`/`sitemap` member-owned → union node/field.
4. Semantic conflict (cùng method/logic sửa khác nhau) → **KHÔNG tự quyết**: ghi file + 2 phía, `git merge --abort`, DỪNG, hỏi người dùng.
5. File dùng chung (`base`/`utils`/`actions`) → ưu tiên giữ cả hai; mâu thuẫn API thật → như (4).
6. Sau mỗi lần giải: grep marker rỗng **và** `build-verify` xanh mới đi tiếp.

## Báo cáo cuối
Tóm tắt review (finding & fix), kết quả tích hợp target (conflict file nào, giải ra sao), branch nguồn/đích, link MR, trạng thái mergeable. Dừng → lý do + quyết định cần người dùng.
