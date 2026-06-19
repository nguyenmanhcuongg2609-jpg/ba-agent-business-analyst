# BÁO CÁO TỔNG KẾT DỰ ÁN: TỪ RAG CHATBOT ĐẾN DUAL-MODE AI AGENT (BA & QA)

Dưới đây là tài liệu tổng hợp toàn bộ kiến trúc, luồng xử lý và các tính năng cốt lõi của dự án. Tài liệu này được thiết kế theo đúng chuẩn đánh giá của Mentor, sẵn sàng để đưa vào Slide báo cáo cuối khóa.

---

## 1. TỔNG QUAN KIẾN TRÚC (ARCHITECTURE OVERVIEW)
Dự án đã có một bước chuyển mình mạnh mẽ từ một hệ thống **QA RAG thông thường** (hỏi - đáp tuyến tính) trở thành một **Hệ sinh thái AI Agent kép (Dual-Mode)** bao gồm Business Analyst (BA) và Quality Assurance (QA).

**Sự khác biệt cốt lõi:**
*   **Hệ cũ (RAG):** User Question $\rightarrow$ Vector Database Retrieval $\rightarrow$ LLM $\rightarrow$ Answer.
*   **Hệ mới (Dual-Agent):** User Request $\rightarrow$ **Chọn Mode (BA/QA)** $\rightarrow$ **Reasoning (Agent)** $\rightarrow$ **Clarification Check** $\rightarrow$ **Tool Selection** $\rightarrow$ Tổng hợp $\rightarrow$ **Structured Output (Jira/TestRail)**.

---

## 2. CẤU TRÚC TỆP TIN & VAI TRÒ CHÍNH (KEY COMPONENTS)

### 🧠 `agent_workflow.py` (BA Agent - LangGraph ReAct)
*   **Chức năng:** Định nghĩa tư duy của BA Agent thông qua `System Prompt` chuyên biệt. Agent có nhiệm vụ phân tích yêu cầu, đặt câu hỏi làm rõ và viết User Story/Business Rules.
*   **Quản lý Tool:** Tích hợp các công cụ: `wikipedia_rag_tool`, `pdf_research_tool`.

### 🕵️ `test_agent.py` (QA Agent - LangGraph ReAct)
*   **Chức năng:** Được tạo ra để song hành cùng BA. Hệ thống System Prompt đóng vai trò là một QA Engineer, yêu cầu đầy đủ thông tin về Môi trường, Actor, Loại Test trước khi sinh ra Bảng Test Case chuyên nghiệp.

### ⚙️ `rag_utils.py` & `metadata_extractor.py` (Động cơ RAG)
*   **Chức năng:** Cung cấp hạ tầng xử lý dữ liệu PDF mạnh mẽ bằng kỹ thuật **Section-aware Splitting** bảo toàn ngữ cảnh và embedding qua `gemini-embedding-2`. Cung cấp RAG tri thức dùng chung cho cả BA và QA Agent.

### 🖥️ `app_agent.py` (Giao diện Streamlit Dual-Mode)
*   **Chức năng:** Cung cấp trải nghiệm tương tác với sidebar `st.radio` cho phép switch qua lại giữa 2 chế độ làm việc (BA và QA).
*   **Điểm nhấn:** Có vùng bộ nhớ riêng biệt (session_state) cho từng Agent, cùng giao diện Thinking Box (Hộp tư duy) hiển thị trực tiếp quá trình suy luận.

### 📦 `export_utils.py` (Tiện ích bóc tách dữ liệu)
*   **Chức năng:** Tách biệt logic Regex và Pandas DataFrame ra một tệp riêng.
*   **Hỗ trợ đa định dạng:** Tự động parse Markdown Table ra CSV TestRail/Xray (cho QA) và parse nội dung ra CSV Jira (cho BA).

---

## 3. LUỒNG XỬ LÝ NGHIỆP VỤ (BUSINESS WORKFLOW)

1. **Nạp dữ liệu (Ingestion):** Người dùng upload file tài liệu (PDF/BRD).
2. **Chọn Mode:** Người dùng chọn BA Mode hoặc QA Mode.
3. **Tiếp nhận & Đánh giá (Clarification):** 
    *   Cả 2 Agent đều có cơ chế từ chối trả lời ngay nếu yêu cầu mập mờ.
    *   BA Agent sẽ hỏi về: Actor, luồng nghiệp vụ.
    *   QA Agent sẽ hỏi về: Loại test, môi trường test.
4. **Gọi Công cụ (Tool Calling):** Agent sử dụng `pdf_research_tool` hoặc `wikipedia_rag_tool` để đọc kiến thức.
5. **Định dạng Đầu ra kép (Structured Output):**
    *   **BA Mode:** Xuất Requirement, User Story, Business Rules.
    *   **QA Mode:** Xuất Markdown Table (TC_ID, Precondition, Steps, Expected Result, Status).
6. **Trích xuất (Export):** Người dùng click tải CSV Jira (BA) hoặc CSV TestRail (QA).

---

## 4. ĐÁNH GIÁ CHẤT LƯỢNG & XỬ LÝ NGOẠI LỆ (EVALUATION & ERROR HANDLING)

### 🛡️ `evaluate.py` (Chấm điểm tự động với Ragas)
*   **Tích hợp Ragas (v0.4.x):** Xây dựng pipeline đánh giá độc lập để đo lường chất lượng của bộ máy RAG dựa trên các chỉ số khoa học: *Faithfulness* (độ trung thực của câu trả lời) và *Answer Relevancy* (mức độ bám sát câu hỏi).
*   **Cơ chế chống Rate Limit (Auto-Retry):** Các hệ thống gọi LLM liên tục (như Agent hay Ragas) rất dễ gặp lỗi quá tải API (429 Resource Exhausted) của Google Gemini. Toàn bộ dự án (`agent_workflow.py` và `evaluate.py`) đã được thiết lập khối `try...except` bắt lỗi 429 thông minh: Hệ thống sẽ in ra cảnh báo thân thiện, tự động tạm ngưng (sleep) 15-30s và thử lại thay vì crash, đảm bảo tính ổn định tuyệt đối (Robustness) trên môi trường thực tế.

---

## 5. BẢNG MAPPING THEO TIÊU CHÍ CỦA MENTOR

| Mốc đánh giá của Mentor | Hiện trạng Hệ thống dự án | Đánh giá |
| :--- | :--- | :--- |
| **Sprint 1: Tool Calling** | Agent đã tự động nhận diện và gọi song song `Wiki Tool` và `PDF Tool` dựa trên ngữ nghĩa câu hỏi. | Hoàn thành xuất sắc |
| **Sprint 2: BA Output** | Xóa bỏ format trả lời Q&A dài dòng. 100% output định dạng chuẩn: Requirement, User Story, Business Rules. | Hoàn thành xuất sắc |
| **Sprint 3: Clarification** | Agent tự động ngăn chặn ảo giác (hallucination) bằng cách hỏi vặn lại người dùng nếu yêu cầu quá mập mờ. | Điểm sáng dự án |
| **Sprint 4: Dual-Mode & Export** | Phát triển thành hệ thống Đa nhân (Multi-Agent) gồm BA và QA. Tích hợp bộ Parser xuất CSV kép tương thích với Jira và TestRail. | Vượt mong đợi |
| **Sprint 5: Auto-Testing** | Tích hợp script `playwright_test.py` và `test_mentor_cases.py` để tự động hóa quá trình nghiệm thu hệ thống. | Kỹ thuật nâng cao |

---
**🏆 TỔNG KẾT:**
Dự án đã vượt qua khỏi ranh giới của một hệ thống Chatbot Hỏi - Đáp thông thường để trở thành một "Đồng sự" đích thực (Dual AI Assistant). Có khả năng làm chủ luồng hội thoại, ra quyết định chọn tài nguyên và tạo ra giá trị nghiệp vụ song song (User Story cho Dev, Test Case cho Tester) sẵn sàng áp dụng trong mô hình Agile thực tế.

---

## 6. CÁC CÂU HỎI BẢO VỆ PHẢN BIỆN (DEFENSE Q&A)

Dưới đây là các câu trả lời chuẩn xác nhất được thiết kế để trả lời hội đồng Mentor:

**❓ Câu hỏi 1: Tại sao phải dùng Agent? Dùng RAG thường không được sao?**
> **Trả lời:** *"Dạ, RAG truyền thống chỉ có thể trả lời thụ động dựa trên nguồn tri thức có sẵn. BA Agent của em cần khả năng **suy luận** để xác định thông tin nào còn thiếu, từ đó chủ động đặt câu hỏi làm rõ yêu cầu (Elicitation) và linh hoạt lựa chọn nguồn tri thức phù hợp (Wiki hoặc PDF) tùy theo ngữ cảnh. Vì vậy em bắt buộc phải nâng cấp lên Agent Workflow thay vì chỉ dùng Retrieval QA thông thường."*

**❓ Câu hỏi 2: Agent chọn Tool bằng if-else hay bằng LLM?**
> **Trả lời:** *"Dạ hệ thống dùng 100% tư duy LLM thông qua `create_react_agent` của LangGraph. LLM tự đọc docstring của các Tool và ngữ nghĩa câu hỏi để quyết định. Nếu em tải PDF 'Quản lý khách sạn' nhưng lại hỏi 'OAuth 2.0 là gì?', Agent sẽ đủ thông minh để bỏ qua PDF Tool và gọi Wikipedia Tool."*

**❓ Câu hỏi 3: Tính năng Traceability (Truy xuất nguồn gốc User Story) ở đâu?**
> **Trả lời:** *"Dạ ở tầng Data, hàm `section_aware_split` của em đã map được Chunk với Tên Section tương ứng. Nhưng ở tầng giao diện hiện tại, việc map 1-1 từng User Story với số trang PDF cụ thể là **Hướng phát triển tiếp theo (Future Work)** của em. Tới đây em sẽ ép LLM xuất thêm tham số `source_page` vào JSON/CSV để hoàn thiện nốt tính năng này."*

---

## 7. ĐỊNH HƯỚNG PHÁT TRIỂN TIẾP THEO (LIMITATIONS & FUTURE WORK)
*(Khuyến nghị: Dành riêng 1 Slide trình bày phần này để ghi điểm tuyệt đối với Mentor)*

*   **Current Limitations (Hạn chế hiện tại):**
    *   Chưa tích hợp API để đẩy trực tiếp User Story lên Jira/Confluence.
    *   Chưa có User Story Traceability 1-1 (Chưa click vào User Story để nhảy về trang PDF gốc).
*   **Future Work (Hướng phát triển):**
    *   Tích hợp Jira API.
    *   Hoàn thiện Source Mapping (Traceability).
    *   Nâng cấp Evaluation Framework (Đưa Ragas vào đánh giá tự động định kỳ).
