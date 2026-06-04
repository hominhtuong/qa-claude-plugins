---
name: commit-push
description: Logic tái dùng để commit & push an toàn — không bao giờ push thẳng main/master (tự tạo branch feat/<slug>), commit theo Conventional Commits kèm trailer Co-Authored-By, push -u không force. Dùng bởi push-code và merge-request sau khi code đã sạch + build xanh. Chỉ chạy khi người dùng yêu cầu.
---

# Skill: commit-push

Năng lực tái dùng: đưa thay đổi đã sạch lên origin một cách an toàn. Chỉ chạy **sau** khi `review-audit` sạch Critical và `build-verify` xanh, và **chỉ khi người dùng yêu cầu**.

## Thủ tục
1. **Xác định branch**: `git branch --show-current`.
   - Đang ở **default branch** (`main`/`master`) → **KHÔNG push thẳng**. Tạo branch feature `feat/<slug>` (suy từ diff, hoặc hỏi tên nếu không rõ) → `git switch -c <branch>`.
   - Branch khác → giữ nguyên.
2. **Stage**: `git add` file trong phạm vi; tránh add file rác/secret (đối chiếu `.gitignore` — không add `reports/`, token, `.properties` chứa secret).
3. **Commit message**: dùng tham số nếu có; trống → tự sinh Conventional Commit ngắn từ diff (vd `test(order): them smoke flow tao don`). Kết thúc bằng dòng:
   `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`
4. **Push**: `git push -u origin <branch>`. Remote từ chối (branch sau remote) → `git fetch` + báo người dùng, **KHÔNG** force-push.
5. **Báo**: file đã commit, tên branch, kết quả push (URL branch nếu remote in ra).

> Chỉ commit/push khi người dùng yêu cầu (qua command `/push-code` hoặc `/merge-request`). Không tự ý.
