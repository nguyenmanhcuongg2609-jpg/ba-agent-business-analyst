import os
import warnings
warnings.filterwarnings("ignore")
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Import tools dùng lại từ BA Agent (không tạo lại)
from agent_workflow import wikipedia_rag_tool, pdf_research_tool

load_dotenv(override=True)

# ==========================================
# SYSTEM PROMPT CHUYÊN BIỆT CHO QA / TESTER
# ==========================================
test_system_prompt = """Bạn là một QA Engineer / Software Tester AI cấp cao, chuyên về kiểm thử phần mềm.
Bạn có khả năng đọc tài liệu yêu cầu (BRD, SRS, User Story) và sinh ra Test Case chi tiết, chuyên nghiệp.

QUY TRÌNH SUY NGHĨ (REASONING & CLARIFICATION):
1. Khi nhận yêu cầu, hãy đánh giá xem thông tin đã ĐỦ để viết Test Case chưa.
2. [MISSING INFO? - QUAN TRỌNG NHẤT]: Nếu yêu cầu quá chung chung, BẮT BUỘC đặt câu hỏi làm rõ:
   - Loại test nào? (Functional / Regression / UAT / Smoke / API / Performance?)
   - Môi trường test? (Dev / Staging / Production?)
   - Người dùng thực hiện hành động là ai? (Role/Actor)
   - Cần kiểm tra happy path, negative case, hay edge case?
   - Có tích hợp hệ thống ngoài không? (Payment, Email, API 3rd party...)
3. Dùng `pdf_research_tool` khi người dùng nhắc tới tài liệu spec/BRD/SRS đã upload.
4. Dùng `wikipedia_rag_tool` khi cần tra cứu khái niệm testing (ví dụ: Boundary Value Analysis, Equivalence Partitioning...).
5. Chỉ xuất Test Case khi đã có ĐỦ thông tin.

ĐỊNH DẠNG ĐẦU RA (Chỉ xuất khi đủ thông tin):

## Test Scenario: [Tên kịch bản tổng quát]
**Mô tả**: [Mô tả ngắn gọn kịch bản]
**Loại test**: [Functional / Regression / UAT / ...]
**Actor**: [Người thực hiện]

### Test Cases:

| Test Case ID | Tên Test Case | Điều kiện tiên quyết | Các bước thực hiện | Kết quả mong đợi | Mức độ ưu tiên | Trạng thái |
|---|---|---|---|---|---|---|
| TC001 | [Tên] | [Precondition] | 1. Bước 1\n2. Bước 2 | [Expected Result] | High/Medium/Low | Pass/Fail/Pending |

### Edge Cases & Negative Cases:
- [Mô tả các trường hợp biên và trường hợp sai]

### Acceptance Criteria (Pass/Fail):
- ✅ PASS khi: [Điều kiện pass]
- ❌ FAIL khi: [Điều kiện fail]

Nếu yêu cầu chưa rõ, chỉ xuất danh sách câu hỏi làm rõ, KHÔNG sinh Test Case."""

# ==========================================
# KHỞI TẠO TEST AGENT
# ==========================================
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, max_retries=3)

tools = [wikipedia_rag_tool, pdf_research_tool]

test_agent = create_react_agent(llm, tools, prompt=test_system_prompt)


def run_test_agent(query: str):
    """Hàm chạy Test Agent độc lập (dùng để test trực tiếp từ terminal)."""
    print(f"\n" + "="*60)
    print(f"🧑 USER: {query}")
    print("="*60)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = test_agent.invoke({"messages": [("user", query)]})
            print("\n" + "="*60)
            print("🤖 TEST AGENT TRẢ LỜI:")
            print("="*60)
            content = result["messages"][-1].content
            if isinstance(content, list):
                content = "\n".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
            print(content)
            print("="*60)
            return
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"⏳ Rate Limit. Đang đợi 15s... (lần {attempt+1}/{max_retries})")
                time.sleep(15)
            else:
                raise e
    print("❌ Vượt quá số lần thử lại.")


if __name__ == "__main__":
    print("🚀 ĐANG KHỞI ĐỘNG TEST AGENT...")

    # Test 1: Functional Test cho tính năng Login
    run_test_agent(
        "Viết Test Case cho chức năng Đăng nhập hệ thống. "
        "Actor: Người dùng cuối. Có 2 loại tài khoản: Admin và User thường. "
        "Yêu cầu: Đăng nhập bằng email + mật khẩu, có giới hạn 5 lần sai."
    )

    print("\n⏳ Đợi 15s để tránh Rate Limit...")
    time.sleep(15)

    # Test 2: Đọc từ tài liệu PDF đã upload
    run_test_agent(
        "Dựa vào tài liệu spec đã upload, hãy viết Test Case "
        "cho chức năng quan trọng nhất trong tài liệu."
    )
