# BÁO CÁO TỔNG KẾT DỰ ÁN: TỪ RAG CHATBOT ĐẾN AI BUSINESS ANALYST AGENT

Dưới đây là tài liệu tổng hợp toàn bộ kiến trúc, luồng xử lý và các tính năng cốt lõi của dự án. Tài liệu này được thiết kế theo đúng chuẩn đánh giá của Mentor, sẵn sàng để đưa vào Slide báo cáo cuối khóa.

---

## 1. TỔNG QUAN KIẾN TRÚC (ARCHITECTURE OVERVIEW)
Dự án đã có một bước chuyển mình mạnh mẽ từ một hệ thống **QA RAG thông thường** (hỏi - đáp tuyến tính) trở thành một **AI Agent tự trị** (tự suy luận, ra quyết định và sử dụng công cụ).

**Sự khác biệt cốt lõi:**
*   **Hệ cũ (RAG):** User Question $\rightarrow$ Vector Database Retrieval $\rightarrow$ LLM $\rightarrow$ Answer.
*   **Hệ mới (AI Agent):** User Request $\rightarrow$ **Reasoning (Agent)** $\rightarrow$ **Requirement Completeness Check** $\rightarrow$ **Tool Selection** $\rightarrow$ Execute Tool $\rightarrow$ Tổng hợp $\rightarrow$ **Structured BA Output**.

---

## 2. CẤU TRÚC TỆP TIN & VAI TRÒ CHÍNH (KEY COMPONENTS)

### 🧠 `agent_workflow.py` (Bộ não trung tâm - LangGraph ReAct)
*   **Chức năng:** Định nghĩa tư duy của Agent thông qua `System Prompt` nâng cao. Thay vì trả lời ngay, Agent được lập trình để lập kế hoạch (Plan) và đưa ra quyết định.
*   **Quản lý Tool:** Tích hợp 2 công cụ song song để Agent tự do lựa chọn:
    *   `wikipedia_rag_tool`: Dùng để tra cứu các khái niệm nền tảng mở (Scrum, Agile, v.v.).
    *   `pdf_research_tool`: Dùng để tìm kiếm thông tin chuyên sâu trong bộ Vector Database chứa tài liệu nội bộ.
*   **Điểm nhấn (Sprint 3):** Tích hợp logic *Clarification Questions*. Agent sẽ từ chối sinh User Story nếu yêu cầu quá mơ hồ, buộc người dùng phải làm rõ các Actor, luồng quy trình, và ràng buộc hệ thống.

### ⚙️ `rag_utils.py` & `metadata_extractor.py` (Động cơ RAG - Retrieval-Augmented Generation)
*   **Chức năng:** Cung cấp hạ tầng xử lý dữ liệu PDF mạnh mẽ.
*   **Điểm nhấn:** Không cắt chuỗi (chunk) một cách mù quáng, hệ thống áp dụng kỹ thuật **Section-aware Splitting** (nhận diện các chương/mục trong bài báo khoa học) để bảo toàn ngữ cảnh. Sử dụng mô hình `gemini-embedding-2` để nhúng (embed) vào ChromaDB.

### 🖥️ `app_agent.py` (Giao diện người dùng - Streamlit UI)
*   **Chức năng:** Cung cấp trải nghiệm tương tác trực quan cho người dùng cuối.
*   **Điểm nhấn (Sprint 4):** 
    *   **Thinking Box (Hộp tư duy):** Hiển thị trực tiếp (Real-time) các bước suy luận và việc gọi Tool của Agent.
    *   **PDF Upload Sidebar:** Cho phép nạp tài liệu động ngay trên giao diện web.
    *   **Export to CSV:** Bóc tách kết quả Markdown và chuyển thành file `.csv` chuẩn định dạng, cho phép Import trực tiếp vào Jira hoặc Excel bằng Pandas.

---

## 3. LUỒNG XỬ LÝ NGHIỆP VỤ (BUSINESS WORKFLOW)

1. **Nạp dữ liệu (Ingestion):** Người dùng upload file tài liệu (PDF). File được băm nhỏ (chunking), tạo Vector và lưu vào kho lưu trữ (ChromaDB) một cách tự động.
2. **Tiếp nhận Yêu cầu (Request):** Người dùng nhập một yêu cầu nghiệp vụ (VD: *"Phân tích hệ thống mượn trả sách"*).
3. **Đánh giá mức độ đầy đủ (Completeness Check):** 
    *   Nếu thiếu thông tin: Agent sẽ đặt câu hỏi làm rõ (VD: *"Hệ thống có quản lý phạt trễ hạn không? Actor là ai?"*).
    *   Nếu đủ thông tin: Agent bước sang quá trình thực thi.
4. **Gọi Công cụ (Tool Calling):** Agent sử dụng `pdf_research_tool` để quét tài liệu vừa nạp, tìm các quy trình cốt lõi để thu thập dữ kiện.
5. **Định dạng Đầu ra (Structured Output):** LLM (Gemini 2.5 Flash) xào nấu dữ liệu và xuất ra theo đúng format ngành BA:
    *   *Yêu cầu (Requirement)*
    *   *User Story (As a... I want... so that...)*
    *   *Acceptance Criteria (Tiêu chí nghiệm thu)*
6. **Trích xuất (Export):** Người dùng click một chạm để tải xuống file CSV.

---

## 4. ĐÁNH GIÁ CHẤT LƯỢNG & XỬ LÝ NGOẠI LỆ (EVALUATION & ERROR HANDLING)

### 🛡️ `evaluate.py` (Chấm điểm tự động với Ragas)
*   **Tích hợp Ragas (v0.4.x):** Xây dựng pipeline đánh giá độc lập để đo lường chất lượng của bộ máy RAG dựa trên các chỉ số khoa học: *Faithfulness* (độ trung thực của câu trả lời) và *Answer Relevancy* (mức độ bám sát câu hỏi).
*   **Cơ chế chống Rate Limit (Auto-Retry):** Các hệ thống gọi LLM liên tục (như Agent hay Ragas) rất dễ gặp lỗi quá tải API (429 Resource Exhausted) của Google Gemini. Toàn bộ dự án (`agent_workflow.py` và `evaluate.py`) đã được thiết lập khối `try...except` bắt lỗi 429 thông minh: Hệ thống sẽ in ra cảnh báo thân thiện, tự động tạm ngưng (sleep) 15-30s và thử lại thay vì crash, đảm bảo tính ổn định tuyệt đối (Robustness) trên môi trường thực tế.

---

## 5. BẢNG MAPPING THEO TIÊU CHÍ CỦA MENTOR

| Mốc đánh giá của Mentor | Hiện trạng Hệ thống dự án | Đánh giá |
| :--- | :--- | :--- |
| **Sprint 1: Agent + Tool Calling** | Agent đã tự động nhận diện và gọi song song `Wiki Tool` và `PDF Tool` dựa trên ngữ nghĩa câu hỏi. | Hoàn thành xuất sắc |
| **Sprint 2: BA Output** | Xóa bỏ format trả lời Q&A dài dòng. 100% output định dạng chuẩn: Requirement, User Story, Acceptance Criteria. | Hoàn thành xuất sắc |
| **Sprint 3: Clarification Questions** | Agent tự động ngăn chặn ảo giác (hallucination) bằng cách hỏi vặn lại người dùng nếu yêu cầu quá mập mờ (Missing Info). | Điểm sáng dự án |
| **Sprint 4: Export** | Tích hợp thành công bộ Parser Regex & Pandas để xuất data thô ra định dạng CSV tương thích với Jira / Excel. | Điểm cộng kỹ thuật |

---
**🏆 TỔNG KẾT:**
Dự án đã vượt qua khỏi ranh giới của một hệ thống Chatbot Hỏi - Đáp thông thường để trở thành một "Đồng sự" đích thực (BA AI Assistant). Có khả năng làm chủ luồng hội thoại, ra quyết định chọn tài nguyên và tạo ra giá trị nghiệp vụ (Business Value) có thể mang đi sử dụng ngay lập tức trong môi trường phát triển phần mềm thực tế.

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
