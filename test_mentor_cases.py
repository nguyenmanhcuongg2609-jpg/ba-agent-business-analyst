"""
test_mentor_cases.py
--------------------
Bộ kiểm tra tự động (Automation Test) cho cả BA Agent và QA/Test Agent.
Mục đích: Tạo log terminal đẹp để đưa vào báo cáo / demo với Mentor.
"""

import time
import sys
import warnings
from langchain_core.messages import HumanMessage
from agent_workflow import ba_agent
from test_agent import test_agent

sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

# ==========================================
# HELPER
# ==========================================
DIVIDER     = "=" * 70
SUBDIV      = "-" * 50

def print_header(title: str):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)

def run_case(agent, case: dict, idx: int, total: int):
    print(f"\n[{case['id']}] {case['name']}")
    print(f"🧑 USER INPUT: {case['query']}")
    print(SUBDIV)

    try:
        result = agent.invoke({"messages": [("user", case["query"])]})
        content = result["messages"][-1].content

        if isinstance(content, list):
            content = "\n".join(
                b.get("text", "") for b in content
                if isinstance(b, dict) and "text" in b
            )

        print(f"🤖 AGENT OUTPUT:\n{content}\n")

        # Liệt kê tools đã gọi
        tool_calls = []
        for msg in result["messages"]:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for t in msg.tool_calls:
                    tool_calls.append(t["name"])
        if tool_calls:
            print(f"🛠️  CÔNG CỤ ĐÃ DÙNG: {', '.join(tool_calls)}\n")
        else:
            print("🛠️  CÔNG CỤ ĐÃ DÙNG: (không cần tool)\n")

    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            print("⏳ [Cảnh báo] Hết Quota API Google. Vui lòng đợi 1 phút rồi chạy lại.\n")
        else:
            print(f"❌ LỖI: {e}\n")

    print(DIVIDER)

    # Nghỉ 15s giữa các case (trừ case cuối)
    if idx < total - 1:
        print("⏳ Đợi 15 giây để tránh Rate Limit...\n")
        time.sleep(15)


# ==========================================
# PHẦN 1: BA AGENT TEST CASES
# ==========================================
ba_test_cases = [
    {
        "id": "BA-01",
        "name": "Tool Calling — Hỏi khái niệm ngoài tài liệu (Wikipedia RAG)",
        "query": "Khái niệm OAuth 2.0 là gì?",
    },
    {
        "id": "BA-02",
        "name": "Clarification Questions — Chống ảo giác (yêu cầu mập mờ)",
        "query": "Tôi muốn xây dựng hệ thống quản lý khách sạn. Hãy viết User Story.",
    },
    {
        "id": "BA-03",
        "name": "Structured Output — Yêu cầu đầy đủ thông tin",
        "query": (
            "Hệ thống quản lý khách sạn. Actors: Lễ tân, Quản lý. "
            "Có thanh toán online qua VNPay. Hãy viết User Story và Acceptance Criteria."
        ),
    },
]

# ==========================================
# PHẦN 2: QA / TEST AGENT TEST CASES
# ==========================================
qa_test_cases = [
    {
        "id": "QA-01",
        "name": "Clarification Questions — Yêu cầu thiếu thông tin loại test",
        "query": "Viết Test Case cho chức năng Đăng nhập.",
    },
    {
        "id": "QA-02",
        "name": "Functional Test — Happy Path & Negative Case",
        "query": (
            "Viết Test Case cho chức năng Đăng nhập hệ thống. "
            "Actor: Người dùng cuối. "
            "Loại test: Functional. "
            "Yêu cầu: Đăng nhập bằng email + mật khẩu, khoá tài khoản sau 5 lần sai. "
            "Cần cả happy path và negative case."
        ),
    },
    {
        "id": "QA-03",
        "name": "Edge Case — Kiểm tra khái niệm Boundary Value Analysis",
        "query": (
            "Tra cứu Wikipedia khái niệm Boundary Value Analysis "
            "và viết Test Case áp dụng kỹ thuật này cho ô nhập mật khẩu "
            "(yêu cầu: tối thiểu 8 ký tự, tối đa 32 ký tự)."
        ),
    },
]


# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":

    # --- BA AGENT ---
    print_header("🧑💼 PHẦN 1/2 — BA AGENT EVALUATION TEST")
    print("Mục tiêu: Kiểm tra Tool Calling, Chống ảo giác, Structured Output\n")

    for i, case in enumerate(ba_test_cases):
        run_case(ba_agent, case, i, len(ba_test_cases))

    print("\n⏳ Nghỉ 20 giây trước khi chạy QA Agent...\n")
    time.sleep(20)

    # --- QA / TEST AGENT ---
    print_header("🕵️  PHẦN 2/2 — QA / TEST AGENT EVALUATION TEST")
    print("Mục tiêu: Kiểm tra Clarification, Test Case Generation, Edge Case\n")

    for i, case in enumerate(qa_test_cases):
        run_case(test_agent, case, i, len(qa_test_cases))

    # --- KẾT QUẢ ---
    print_header("✅ KIỂM TRA HOÀN TẤT!")
    print(f"  BA Agent  : {len(ba_test_cases)} test cases")
    print(f"  QA Agent  : {len(qa_test_cases)} test cases")
    print(f"  Tổng cộng : {len(ba_test_cases) + len(qa_test_cases)} test cases\n")
    print("📁 Log đầy đủ đã sẵn sàng để đưa vào báo cáo!")
    print(DIVIDER)
