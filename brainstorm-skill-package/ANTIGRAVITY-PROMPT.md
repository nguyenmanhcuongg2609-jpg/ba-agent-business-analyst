# Prompt cho Antigravity (hoặc IDE AI khác) — Re-build /brainstorm workflow

> Copy nguyên block bên dưới vào Antigravity chat. AI sẽ đọc các file đính kèm và setup lại skill `/brainstorm` (hoặc tương đương) trong workflow engine của họ.

---

## PROMPT (copy từ đây)

Tôi gửi kèm 1 skill package cho Claude Code tên `/brainstorm`. Mục tiêu: **port skill này sang workflow engine, skills, rules của Antigravity** (giữ nguyên hành vi, output structure, và nguyên tắc IT-BA).

### Context

`/brainstorm` là skill dành cho **IT Business Analyst** (không phải developer). Skill expand 1 raw idea thành structured brainstorm doc qua **7-section deep interview**, chạy **từng section một** (không dồn batch), output file MD 13 section với ASCII flow diagram, scenario matrix, state-transitions, interrupted-tx, exact error/success/info wording.

### Files đính kèm (đọc theo thứ tự)

1. `.claude/skills/brainstorm/SKILL.md` — **entry point**. Định nghĩa Goal, Constraints, Inputs, Approach (Phase A→E), Gotchas.
2. `.claude/rules/ba-conventions.md` — owner resolution, no-re-ask, IT-BA framing, VN typography, L1-cho-BA.
3. `.claude/rules/approval-gate.md` — L1 plan / L2 diff / L3 iterate convention (HITL gates).
4. `.claude/rules/resolve-oqs.md` — Phase E: collect → prompt → loop 1-by-1 → cascade scan side-effect → changelog.
5. `.claude/rules/naming-conventions.md` — slug rules, file paths, frontmatter v2, ID conventions.
6. `.claude/rules/keyword-detection.md` — trigger phrases VN+EN cho decision/blocker/action extraction.
7. `.claude/rules/changelog.md` — YAML changelog list frontmatter format.
8. `_templates/brainstorm.md` — 13-section output template skill render từ đây.
9. `.claude/skills/brainstorm/references/example-brainstorm.md` — ví dụ output đã chuẩn.

### Yêu cầu re-build

1. **Đọc hết 9 file** trước khi đề xuất implementation.
2. **Mapping**: skill này dùng Claude Code primitives (slash command, frontmatter `allowed-tools`, `@<path>` reference). Map sang primitives Antigravity (workflow node, tool binding, file include).
3. **Bảo toàn cứng** các thuộc tính sau (KHÔNG được lược bỏ):
   - **7-section sequential interview** — 1 section/lần, wait reply, KHÔNG dồn batch.
   - **Complexity auto-detection** trigger mandatory artifacts (ASCII flow / interrupted-tx / scenario matrix / state transitions).
   - **IT-BA framing** — cấm hỏi DB schema / function name / SDK / endpoint. Chỉ business language.
   - **No-re-ask** — scan context + existing doc trước mỗi câu hỏi.
   - **Push exact values** — re-ask 1 lần khi vague, sau đó TBD + open question.
   - **L1 plan preview prose tự nhiên** — không bảng `# | path | action`, không tag flag, không jargon.
   - **L3 iterate cho ASCII diagram** max 3 vòng; **KHÔNG iterate L3 cho mermaid** (mermaid không render trong chat).
   - **Phase E resolve OQs sau Write** — loop 1-by-1, cascade scan toàn bộ doc + downstream docs khi 1 OQ được resolved.
   - **Frontmatter v2** với `changelog:` YAML list (newest on top).
4. **Output**: cho tôi
   - File định nghĩa skill/workflow (format của Antigravity)
   - File rules tương đương 6 rule MD đã đính kèm
   - File template brainstorm output
   - 1 doc Markdown mô tả mapping primitives Claude Code → Antigravity (để tôi review).
5. **Hỏi tôi** nếu Antigravity thiếu primitive nào (vd "không có L3 iterate cho creative output — bạn muốn em fallback sang single-shot rồi user edit manual?").

### Test case

Sau khi build xong, simulate scenario:
```
User: /brainstorm đăng nhập email + Google OAuth
```
Skill phải:
- Auto-derive feature=`user-login`, idea=`email-google-oauth`.
- Detect `has_external_redirect=true` → mandate ASCII flow + interrupted-tx matrix.
- Hỏi Section 1 (Overview) trước → wait reply → mới hỏi Section 2.
- KHÔNG hỏi "dùng JWT hay session", "OAuth SDK nào", "DB column user_id type gì".
- L1 preview viết: "Em sẽ tạo file ... với luồng đăng nhập email + OAuth, bảng xử lý browser đóng giữa OAuth callback, wording mẫu khi link verify expire..." — KHÔNG viết "has_external_redirect=Y, Quality checklist 9/11".

Nếu output đạt test case → port thành công.

---

(end of prompt)
