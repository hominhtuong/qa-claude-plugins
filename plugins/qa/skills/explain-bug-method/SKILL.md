---
name: explain-bug-method
description: Reusable logic to "translate" a poorly-written bug into a clear, structured summary so the reader instantly understands it. Handles raw pasted text (incl. no-diacritics Vietnamese / messy / vague), a screenshot, a Bug ID, or a full Lark record link — reading the record + comments + history from the Lark Bitable board via scripts/lark_bitable.py. Always includes a Severity/Priority reasonableness check per severity-priority-framework.md. Replies in-conversation (no file). Reusable core behind the explain-bug command.
---

# Skill: explain-bug-method

Reusable capability: take a confusing bug report and produce a crisp, structured explanation — summary, reproduction steps, actual vs expected, a preliminary severity, and a Severity/Priority sanity check. Keep the reporter's intent; don't invent a new bug.

> 🧭 Tone: neutral and helpful — never criticize how the bug was written. Where you must guess context, say so ("đang suy luận"), don't present it as fact.

## Input modes
1. **Pasted text** — raw description, possibly no diacritics ("khong hien thi" → "không hiển thị"), abbreviations, mixed steps/actual/expected, vague ("nó bị lỗi"). Interpret best-effort.
2. **Screenshot attached** — read it (you are multimodal) and fold the visual context into the explanation.
3. **Bug ID** — `BId-000427`, `427`, or `#427`. Extract the number → look it up on the board:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --bug-id 427 --with-comments
   ```
4. **Full Lark record link** — contains `?record=recXXX` → extract the record id:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lark_bitable.py" --record-id recXXXXXX --with-comments
   ```
   **Short link `/record/XXX` is NOT supported** (it's an internal sharing token, not a `recXXX` id, and won't resolve via API) → ask the user for the Bug ID or a full `?record=recXXX` link.

## Procedure
1. **Detect the mode** from the input. For board modes, run `lark_bitable.py` (relay the `action` verbatim on `ok:false`; never invent record content). Read ALL logical fields + `comments` + created/modified history.
2. **Interpret** the content into the output structure. Multiple bugs / multiple links → explain each separately.
3. **Assess Severity/Priority** per `../../rules/severity-priority-framework.md` — ALWAYS include the reasonableness block. If the user gave a level that doesn't fit the evidence, say so and suggest a better one.
4. **Reply in-conversation** (no file).

## Output structure
```
--- Giải thích Bug ---
**Tóm tắt**: [1 câu bug là gì]
**Màn hình / Tính năng**: [feature/screen]
**Các bước tái hiện**: 1. … 2. … 3. …
**Thực tế xảy ra**: [actual, diễn giải rõ]
**Kỳ vọng đúng**: [expected, suy luận từ context]
**Mức độ nghiêm trọng (sơ bộ)**: [Critical/High/Medium/Low] — [lý do]
**Đánh giá Severity/Priority có hợp lý không**:
- Kết luận: [Hợp lý / Chưa hợp lý / Chưa đủ dữ liệu]
- Severity đề xuất: … | Priority đề xuất: … | Lý do: … | Khuyến nghị: …
```
**For a Lark record**, also add:
```
**Thông tin record**: Người tạo/ngày · Sửa gần nhất · Status · Dev PIC · Sprint · Version · Bug ID · link đầy đủ
**Comments & Thảo luận** (nếu có): [người] ([khi]): [tóm tắt] → Tóm tắt: [đã consensus chưa / info bổ sung]
```
Always add when relevant: **Lưu ý** (contradictions/missing logic), **Câu hỏi cần làm rõ** (if too vague), **Suy luận** (flag guesses).

## Rules
- Keep the reporter's intent — never add/remove a bug. Too short/vague → still explain best-effort + list clarifying questions.
- Screenshot → describe what's visible and tie it to the text.
- ALWAYS include the Severity/Priority reasonableness block (per the framework).
- Read-only — never create/edit a record. Never print tokens.
- **LANGUAGE**: reply in the configured output language (default Vietnamese with diacritics; technical terms in English) — see `../../rules/output-language.md`.
