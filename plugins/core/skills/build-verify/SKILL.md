---
name: build-verify
description: Logic tái dùng làm "cổng xanh" — biên dịch sạch (mvn clean compile test-compile) và (tuỳ chọn) chạy nhanh test của feature vừa đụng. Dùng trước khi kết thúc cook/fix/exploratory và trước khi commit ở push-code/merge-request. Không tăng timeout/workaround để "qua test".
---

# Skill: build-verify

Năng lực tái dùng: đảm bảo code ở trạng thái biên dịch sạch trước khi đi tiếp. Mỏng nhưng là cổng chặn (không vá để qua).

## Thủ tục
1. `mvn clean compile test-compile` — phải **xanh**. Đỏ → sửa qua skill `fix-by-layer` tới khi xanh; vẫn đỏ → **DỪNG**, báo lỗi, **không** đi tiếp (không commit/không push).
2. **Tuỳ chọn** chạy nhanh test feature vừa làm qua script (tự check device): `./scripts/run-android.sh` / `./scripts/run-ios.sh`, hoặc `mvn test -DsuiteXmlFile=testng/<suite>.xml`. Nhớ TestNG XML có `GoToHomeTest` là `<test>` đầu.
3. **Không** tăng timeout bừa, không `Thread.sleep`, không nới điều kiện chỉ để "qua test" — đó là che lỗi, vi phạm coding-rules.

> Timeout/capabilities lấy tập trung từ `configurations/`, không rải số ma trong code. `MobileFindFieldDecorator` đã lo polling.
