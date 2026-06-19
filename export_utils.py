"""
export_utils.py
---------------
Các hàm tiện ích để xuất kết quả từ BA Agent và Test Agent ra file CSV/Markdown.
"""

import re
import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage


# ==========================================
# EXPORT: BA MODE → CSV JIRA FORMAT
# ==========================================
def extract_ba_artifacts_to_csv(chat_history) -> bytes | None:
    """
    Bóc tách User Story + Acceptance Criteria từ lịch sử chat của BA Agent.
    Xuất ra CSV tương thích với Jira.
    """
    latest_msg = ""
    for msg in reversed(chat_history):
        if isinstance(msg, AIMessage):
            content = _get_content(msg)
            if "User Story" in content and "Business Rules" in content:
                latest_msg = content
                break

    if not latest_msg:
        return None

    blocks = re.split(
        r'\n(?=\s*\d+\.\s*(?:Use Case|\*\*Use Case|Yêu cầu|\*\*Yêu cầu|Requirement|\*\*Requirement))',
        "\n" + latest_msg
    )

    data = []
    for block in blocks:
        if not block.strip():
            continue

        uc  = re.search(r'Use Case:?\s*\*?\*?(.*?)(?=\n|$)', block, re.IGNORECASE)
        req = re.search(r'(?:Yêu cầu|Requirement).*?:?\s*\*?\*?(.*?)(?=\n.*User Story)', block, re.IGNORECASE | re.DOTALL)
        us  = re.search(r'User Story:?\s*\*?\*?(.*?)(?=\n.*Business Rules)', block, re.IGNORECASE | re.DOTALL)
        ac  = re.search(r'(?:Business Rules|Quy tắc nghiệp vụ):?\s*\*?\*?(.*)', block, re.IGNORECASE | re.DOTALL)

        if us and ac:
            data.append({
                "Use Case":            uc.group(1).strip()  if uc  else "Chức năng chung",
                "Requirement":         req.group(1).strip() if req else "",
                "User Story":          us.group(1).strip()  if us  else "",
                "Business Rules":      ac.group(1).strip()  if ac  else "",
            })

    if not data:
        return None

    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode("utf-8-sig")


# ==========================================
# EXPORT: TEST MODE → CSV TESTRAIL / XRAY FORMAT
# ==========================================
def extract_test_artifacts_to_csv(chat_history) -> bytes | None:
    """
    Bóc tách Test Case từ lịch sử chat của Test Agent.
    Xuất ra CSV tương thích với TestRail / Xray (Jira).

    Các cột: Test Case ID | Test Scenario | Tên Test Case |
              Precondition | Steps | Expected Result | Priority | Status
    """
    latest_msg = ""
    for msg in reversed(chat_history):
        if isinstance(msg, AIMessage):
            content = _get_content(msg)
            # Nhận dạng output của Test Agent
            if ("TC" in content or "Test Case" in content) and ("Expected" in content or "Kết quả" in content or "mong đợi" in content):
                latest_msg = content
                break

    if not latest_msg:
        return None

    # --- Lấy Test Scenario (tiêu đề chung) ---
    scenario_match = re.search(r'Test Scenario[:\s*#]+(.+?)(?=\n|$)', latest_msg, re.IGNORECASE)
    scenario = scenario_match.group(1).strip() if scenario_match else "General Scenario"

    # --- Bóc tách từng dòng trong bảng Markdown ---
    # Tìm bảng | TC... | ... |
    table_rows = re.findall(
        r'\|\s*(TC[a-zA-Z0-9_]+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|',
        latest_msg
    )

    data = []

    if table_rows:
        for row in table_rows:
            tc_id, name, precond, steps, expected, priority, status = row
            # Bỏ qua dòng header phân cách (---)
            if re.match(r'^[-:]+$', tc_id.strip()):
                continue
            data.append({
                "Test Case ID":    tc_id.strip(),
                "Test Scenario":   scenario,
                "Tên Test Case":   name.strip(),
                "Precondition":    precond.strip(),
                "Steps":           steps.strip().replace("\\n", "\n"),
                "Expected Result": expected.strip(),
                "Priority":        priority.strip(),
                "Status":          status.strip(),
            })

    # --- Fallback: Nếu không có bảng, bóc tách theo block TC ---
    if not data:
        tc_blocks = re.split(r'\n(?=TC[a-zA-Z0-9_]+\b)', latest_msg)
        for block in tc_blocks:
            tc_id_m   = re.match(r'(TC[a-zA-Z0-9_]+)', block)
            name_m    = re.search(r'(?:Tên|Name|Title)[:\s]+(.+?)(?=\n|$)', block, re.IGNORECASE)
            pre_m     = re.search(r'(?:Precondition|Điều kiện)[:\s]+(.+?)(?=\n)', block, re.IGNORECASE)
            steps_m   = re.search(r'(?:Steps|Các bước)[:\s]+(.*?)(?=Expected|Kết quả)', block, re.IGNORECASE | re.DOTALL)
            exp_m     = re.search(r'(?:Expected Result|Kết quả mong đợi)[:\s]+(.+?)(?=\n\n|Priority|Mức độ|$)', block, re.IGNORECASE | re.DOTALL)
            prio_m    = re.search(r'(?:Priority|Mức độ ưu tiên)[:\s]+(.+?)(?=\n|$)', block, re.IGNORECASE)

            if tc_id_m and exp_m:
                data.append({
                    "Test Case ID":    tc_id_m.group(1),
                    "Test Scenario":   scenario,
                    "Tên Test Case":   name_m.group(1).strip()  if name_m  else "",
                    "Precondition":    pre_m.group(1).strip()   if pre_m   else "",
                    "Steps":           steps_m.group(1).strip() if steps_m else "",
                    "Expected Result": exp_m.group(1).strip()   if exp_m   else "",
                    "Priority":        prio_m.group(1).strip()  if prio_m  else "Medium",
                    "Status":          "Pending",
                })

    if not data:
        return None

    df = pd.DataFrame(data, columns=[
        "Test Case ID", "Test Scenario", "Tên Test Case",
        "Precondition", "Steps", "Expected Result", "Priority", "Status"
    ])
    return df.to_csv(index=False).encode("utf-8-sig")


# ==========================================
# EXPORT: CHAT HISTORY → MARKDOWN
# ==========================================
def export_chat_to_md(chat_history, mode: str = "BA") -> bytes:
    """Xuất toàn bộ lịch sử hội thoại ra file Markdown."""
    title = "BA AGENT" if mode == "BA" else "TEST AGENT"
    md = f"# LỊCH SỬ HỘI THOẠI {title}\n\n"
    for msg in chat_history:
        role = "🧑 USER" if isinstance(msg, HumanMessage) else f"🤖 {title}"
        content = _get_content(msg)
        md += f"### {role}\n{content}\n\n---\n\n"
    return md.encode("utf-8")


# ==========================================
# HELPER
# ==========================================
def _get_content(msg) -> str:
    """Chuẩn hoá content từ message (str hoặc list block)."""
    content = msg.content
    if isinstance(content, list):
        return "\n".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and "text" in b
        )
    return content or ""
