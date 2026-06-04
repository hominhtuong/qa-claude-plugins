# Git Conventions (shared)

Quy ước git dùng chung mọi project automation. Skill `commit-push` enforce phần lớn các luật này.

## Branch
- **KHÔNG** commit/push thẳng `main`/`master`. Luôn tạo branch feature `feat/<slug>` (hoặc `fix/<slug>`, `chore/<slug>`).
- Một PR/MR = một feature. Branch suy slug từ nội dung diff.

## Commit message (Conventional Commits)
- Format: `<type>(<scope>): <mô tả ngắn>` — type ∈ `feat|fix|test|chore|refactor|docs|ci`.
- Ví dụ: `test(order): them smoke flow tao don`, `fix(auth): sua locator nut dang nhap`.
- Kết thúc commit message bằng trailer:
  ```
  Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
  ```

## Push
- `git push -u origin <branch>` — **không** `--force`.
- Chỉ commit/push **khi người dùng yêu cầu**.
- Không add file rác/secret: bỏ `reports/`, token, `.properties` chứa secret (đối chiếu `.gitignore`).

## Cổng trước khi commit
1. `review-audit` sạch Critical/Blocker.
2. `build-verify` xanh (`mvn clean compile test-compile`).
3. Mới tới `commit-push`.
