# /brainstorm — Skill Package (Claude Code)

> Skill BA giúp **capture raw idea** và clarify đủ thông tin (7-section deep interview + ASCII flow + scenario matrix + state transitions + interrupted-tx + exact wording) trước khi viết URD/PRD/SRS. Phục vụ IT Business Analyst, không phải developer.

## 1. Package có gì

```
brainstorm-skill-package/
├── README.md                       ← file này (hướng dẫn TV)
├── ANTIGRAVITY-PROMPT.md           ← prompt copy sang Antigravity để re-build
├── .claude/
│   ├── skills/brainstorm/
│   │   ├── SKILL.md                ← entry point của /brainstorm
│   │   └── references/
│   │       └── example-brainstorm.md
│   └── rules/                      ← 6 rule file SKILL.md tham chiếu
│       ├── ba-conventions.md
│       ├── approval-gate.md
│       ├── naming-conventions.md
│       ├── keyword-detection.md
│       ├── resolve-oqs.md
│       └── changelog.md
└── _templates/
    └── brainstrom.md               ← template output (skill render từ đây)
```

Tất cả 9 file đều cần thiết. Không thiếu file nào skill sẽ chạy được nhưng output thiếu structure.

## 2. Cài đặt vào project của bạn

Giả sử project của bạn ở `/path/to/your-project/`.

### Bước 1 — Copy structure

```bash
cd /path/to/your-project

# Copy skill + rules vào .claude/
cp -R brainstorm-skill-package/.claude/skills/brainstorm  .claude/skills/
cp -n brainstorm-skill-package/.claude/rules/*.md         .claude/rules/

# Copy template ra root project
mkdir -p _templates
cp -n brainstorm-skill-package/_templates/brainstorm.md   _templates/
```

> `cp -n` = không overwrite nếu file đã có. Nếu rule file bạn đã có version riêng → review diff trước khi merge.

### Bước 2 — Kiểm tra structure

```bash
ls .claude/skills/brainstorm/SKILL.md
ls .claude/rules/{ba-conventions,approval-gate,naming-conventions,keyword-detection,resolve-oqs,changelog}.md
ls _templates/brainstorm.md
```

5 lệnh trên phải in ra path, không "No such file".

### Bước 3 — Setup folder docs/

Skill sẽ ghi output vào `docs/{feature}/brainstorms/{idea-slug}.md`. Folder `docs/` tự tạo khi skill chạy lần đầu.

### Bước 4 — Reload Claude Code

Mở Claude Code trong project. Gõ `/` và scroll → thấy `/brainstorm` trong danh sách = OK.

---

### Cách nhanh hơn — Copy prompt sau dán vào Claude Code

Nếu lười chạy `cp` tay, mở Claude Code **ngay tại project của bạn**, paste nguyên block dưới đây vào chat. Claude sẽ tự copy file + verify + báo cáo:

```
Tôi vừa giải nén skill package `/brainstorm` vào folder `<PASTE_ABSOLUTE_PATH_TO_brainstorm-skill-package>` (sửa path này trước khi gửi).

Cài skill vào project hiện tại theo các bước sau, đừng tự ý làm thêm gì khác:

1. Verify source: kiểm tra folder tôi đưa có đủ 9 file:
   - `.claude/skills/brainstorm/SKILL.md`
   - `.claude/skills/brainstorm/references/example-brainstorm.md`
   - `.claude/rules/{ba-conventions,approval-gate,naming-conventions,keyword-detection,resolve-oqs,changelog}.md`
   - `_templates/brainstorm.md`
   Thiếu file nào → dừng, báo tôi.

2. Verify destination: kiểm tra cwd là project root (có file `CLAUDE.md` hoặc `.git/` hoặc `package.json` hoặc tôi xác nhận). Không phải → hỏi tôi confirm path.

3. Copy file:
   - `mkdir -p .claude/skills .claude/rules _templates`
   - `cp -R <src>/.claude/skills/brainstorm .claude/skills/`
   - Với mỗi rule file trong `<src>/.claude/rules/`:
     - Nếu đích `.claude/rules/<name>.md` đã tồn tại → KHÔNG overwrite, in diff ngắn (<10 dòng đầu khác nhau) và hỏi tôi: skip / overwrite / rename source thành `<name>.from-brainstorm.md`.
     - Nếu chưa tồn tại → copy trực tiếp.
   - `_templates/brainstorm.md`: cùng logic conflict như rule.

4. Verify install: `ls` 9 path đích → tất cả phải tồn tại. Liệt kê path nào missing.

5. Báo cáo cuối:
   - Số file copied / skipped / conflicted
   - 1 dòng hướng dẫn restart Claude Code + gõ `/brainstorm` để test
   - KHÔNG suggest chạy `/brainstorm` ngay — chờ tôi restart trước.

Yêu cầu thêm:
- KHÔNG sửa nội dung bất kỳ file nào (chỉ copy nguyên).
- KHÔNG commit git.
- KHÔNG tạo doc/folder ngoài 9 path trên.
- Mọi conflict đều hỏi tôi, không tự quyết.
```

> Thay `<PASTE_ABSOLUTE_PATH_TO_brainstorm-skill-package>` bằng path thật (vd `/Users/me/Downloads/brainstorm-skill-package`). Claude sẽ chạy 5 bước, dừng hỏi khi có conflict.

---

## 3. Cách sử dụng

### Cách dùng cơ bản

```
/brainstorm                                  # interactive — skill hỏi idea
/brainstorm <idea text>                      # paste idea inline
/brainstorm @notes/idea-2026.md              # tag file làm source
/brainstorm <idea text> --shallow            # fast mode, single batch
/brainstorm <idea text> --lang en            # output English (default vi)
```

### Ví dụ

```
/brainstorm thêm spaced repetition cho vocabulary trainer
/brainstorm đăng nhập email + Google OAuth
/brainstorm dark mode toggle --shallow
```

### Skill sẽ làm gì

1. **Phase A** — auto-derive feature slug + idea slug từ idea content, detect complexity (external redirect, multi-role, state machine, throttle...).
2. **Phase B** — phỏng vấn 7 section, **mỗi lần 1 section** (không dồn batch):
   - Section 1: Overview
   - Section 2: Users & Access
   - Section 3: Core Flow (Happy Path)
   - Section 4: Deep Dive (chỉ chạy nếu detect complexity) — system actions, decision points, state transitions, interrupted transactions, **ASCII flow diagram** (iterate max 3 vòng), scenario matrix
   - Section 5: Validation, Limits & **Exact wording** (error/success/info messages)
   - Section 6: System Context (business-level only — KHÔNG hỏi DB/SDK/endpoint)
   - Section 7: Edge cases, Risks, Open Questions
3. **Phase C** — synthesize + self-check 10-item quality checklist.
4. **Phase D** — L1 approval preview (ngôn ngữ BA) → Write file.
5. **Phase E** — loop resolve Open Questions từng câu một, cascade scan side-effect.

### Output

`docs/{feature}/brainstorms/{idea-slug}.md` — 13 section, có ASCII diagram, scenario matrix, state-transition table, interrupted-tx table, exact wording tables, IT-BA framing risks, open questions có ID.

## 4. Nguyên tắc skill tuân thủ

- **IT-BA framing**: KHÔNG hỏi DB column, SDK name, function name, JWT vs session, endpoint. Chỉ hỏi business: "lưu thông tin gì", "system làm gì", "dịch vụ ngoài nào".
- **No-re-ask**: skill scan context + existing doc trước mỗi vòng. KHÔNG hỏi lại câu user đã trả lời.
- **Push exact values**: "rate limit bao nhiêu/phút", "câu error chính xác là gì". Vague → re-ask 1 lần → vẫn vague → TBD + open question.
- **L1 approval preview** dùng prose tự nhiên BA, KHÔNG bảng tag/flag/checklist kiểu dev.
- **Vietnamese-first**, không dùng ký hiệu `§` (dùng "Mục N").

## 5. Troubleshooting

| Triệu chứng                                        | Nguyên nhân                       | Cách fix                                                                   |
| ---------------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------- |
| `/brainstorm` không hiện trong slash menu        | Claude Code chưa reload            | Restart Claude Code; check `.claude/skills/brainstorm/SKILL.md` tồn tại |
| Skill output thiếu structure (ít hơn 13 section)  | Thiếu `_templates/brainstorm.md` | Copy lại file template về `_templates/` root                            |
| Skill hỏi câu coding (DB column, endpoint)         | Thiếu rule `ba-conventions.md`   | Copy rule về `.claude/rules/`                                            |
| L1 preview dùng bảng `#                            | path                                | action`                                                                     |
| Open Questions không được loop resolve sau Write | Thiếu rule `resolve-oqs.md`      | Copy lại rule                                                              |
