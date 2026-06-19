# 🤖 Dual-Mode AI Agent: Business Analyst & QA Assistant

Dual-Mode AI Agent (BA & QA) with Agentic RAG là một hệ sinh thái **Multi-Agent** tự trị đóng vai trò là Business Analyst (BA) và Quality Assurance (QA) ảo. Khác với các hệ thống RAG Hỏi - Đáp thông thường, hệ thống này được cung cấp khả năng tư duy (Reasoning) và sử dụng bộ công cụ (Tool Calling) để:
1. Đọc hiểu tài liệu chuyên ngành (BRD, PDF) và bóc tách thông tin cốt lõi.
2. Tư duy chống "Ảo giác" (Hallucination) bằng cách chủ động đặt câu hỏi làm rõ (Clarification Questions) nếu yêu cầu mập mờ.
3. **BA Mode:** Tự động sinh ra *User Story, Business Rules*.
4. **QA Mode:** Tự động sinh ra *Test Case, Test Scenario*.
5. Định dạng đầu ra trực tiếp thành các file **CSV chuẩn Jira / TestRail** để đưa ngay vào Workflow thực tế.

---

## 🌟 TÍNH NĂNG NỔI BẬT

1. **Agentic Workflow (LangGraph):** Hệ thống tự động quyết định khi nào cần tra cứu Wikipedia, khi nào cần tìm trong tài liệu PDF nội bộ để hoàn thành yêu cầu của người dùng.
2. **Clarification Questions (Chống Ảo giác):** Khi người dùng cung cấp yêu cầu mập mờ, Agent sẽ từ chối sinh kết quả và đặt câu hỏi ngược lại (Ví dụ: "Hệ thống có quản lý thanh toán không?", "Có những Role nào?") để thu thập đủ thông tin.
3. **Structured Output:** 
   - **BA Mode:** Tự động sinh ra `Business Requirements`, `Use Case`, `User Story`, và `Business Rules` chuẩn quy trình BA.
   - **QA Mode:** Tự động sinh ra `Test Cases`, `Test Steps`, `Expected Results` phục vụ kiểm thử.
4. **Jira & TestRail CSV Export:** Bóc tách kết quả phân tích và xuất ra file CSV tương thích 100% với Jira/Excel/TestRail chỉ bằng một cú click.

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

Dự án là sự kết hợp hoàn hảo giữa LLM tiên tiến và kiến trúc Hybrid RAG:

*   **Brain (Bộ não):** LangGraph ReAct Agent tích hợp Gemini 2.5 Flash.
*   **Tool 1 - Wikipedia RAG:** Tìm kiếm khái niệm mở (Agile, Scrum, OAuth 2.0...) trên Wikipedia, chunking, embed và search để lấy ngữ cảnh.
*   **Tool 2 - PDF RAG:** Tìm kiếm tài liệu chuyên ngành bằng kỹ thuật Hybrid Search (BM25 + Vector Search) với `section_aware_split` (cắt theo cấu trúc văn bản).
*   **UI/UX:** Streamlit. Hiển thị "Thinking Box" trực quan tiến trình suy luận của Agent.

```text
User Request
   ↓
LangGraph ReAct Agent
   ↓
[ Tool Selection ] ──> Wiki Tool / PDF Tool
   ↓
[ Clarification / Reasoning ]
   ↓
Structured JSON (User Story)
   ↓
Export to CSV
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT VÀ CHẠY DỰ ÁN

### 1. Chuẩn bị môi trường
Yêu cầu: Python 3.12+
```bash
# Clone dự án về máy
git clone <your-repo-url>
cd RAG_Chatbot

# Kích hoạt môi trường ảo (đã tạo sẵn)
.\venv_312\Scripts\activate
```

### 2. Cấu hình API Key
Tạo file `.env` ở thư mục gốc (hoặc copy từ `.env.example`) và điền API Key của Google:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Khởi chạy Giao diện
```bash
streamlit run app_agent.py
```
Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ: `http://localhost:8501`

---

## 📸 DEMO SẢN PHẨM

*(Bạn hãy thay thế các link ảnh dưới đây bằng ảnh chụp màn hình thực tế của bạn bằng cách copy ảnh vào dự án)*

### 1. Khả năng gọi Tool (Tool Calling)
![Tool Calling Demo](link_anh_tool_calling.png)
*Agent tự động nhận diện từ khóa và gọi Wikipedia Tool.*

### 2. Khả năng Elicitation (Hỏi làm rõ yêu cầu)
![Clarification Demo](link_anh_clarification.png)
*Agent vặn hỏi lại người dùng khi Input bị thiếu dữ kiện.*

### 3. Xuất Artifacts và CSV
![CSV Export Demo](link_anh_csv_export.png)
*Giao diện xuất file CSV để import thẳng vào Jira Sprint Backlog.*

---
**🏆 Project Status:** Completed (Dual-Mode Ready). 
**👉 Future Work:** Tích hợp Jira & TestRail API trực tiếp, mở rộng Traceability Mapping và thêm Dev Agent.
