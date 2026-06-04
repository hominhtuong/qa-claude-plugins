---
name: update-sitemap
description: Logic tái dùng để cập nhật bản đồ màn hình (sitemap) + element catalog khi đụng tới một màn. Dùng khi một command (exploratory, cook) vừa tạo/sửa Screen hoặc discover element qua MCP. Cập nhật elements.json + test-hints.json + sitemap.md rồi regenerate bằng script. plan thì chỉ liệt kê node cần đụng.
---

# Skill: update-sitemap

Năng lực tái dùng: giữ bản đồ điều hướng đồng bộ với code, để AI điều hướng đúng ở lần sau. Hệ thống sitemap: [design-pattern §5](../../rules/design-pattern.md). Chi tiết: `sitemap/README.md`.

## Thủ tục (Auto-Update Rule — sau MCP discovery / đổi element)
1. **`screens/<group>/elements.json`** — thêm/cập nhật locator element mới discover (nguồn cho 3-layer lookup Layer 2).
2. **`screens/<group>/test-hints.json`** — nếu discover form field mới: thêm field metadata, validation, business rule (cho `/plan`, `/cook`).
3. **`sitemap/sitemap.md`** — thêm entry màn mới vào navigation index (screen name, path từ Home, entry points, element đặc trưng). Màn cũ có element mới → cập nhật.
4. **Screenshot** (nếu chụp qua MCP): lưu `sitemap/screenshots/<name>.jpg` (JPG, không PNG; không để ra Desktop).
5. **Regenerate**: `python3 sitemap/scripts/gen_sitemap_v2.py` (sitemap.md) + `python3 sitemap/scripts/gen_test_hints.py` (test-hints.json).

> Ở `/plan`: KHÔNG ghi file — chỉ **liệt kê** node/màn cần tạo/cập nhật (path từ Home, element chính) trong plan để `/cook` thực thi sau.
