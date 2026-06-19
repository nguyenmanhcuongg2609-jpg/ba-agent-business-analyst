# 📊 CẤU TRÚC SLIDE BẢO VỆ ĐỒ ÁN (Khuyến nghị: 10 - 12 Slide)

Dựa trên toàn bộ quá trình phát triển hệ thống Agentic BA, đây là dàn ý chi tiết từng Slide để bạn thiết kế trên PowerPoint/Canva nhằm đạt điểm tuyệt đối.

---

### Slide 1 – Giới thiệu đề tài
*   **Tiêu đề:** Hệ sinh thái Dual-Agent (BA & QA) sử dụng Agentic RAG.
*   **Nội dung:** 
    *   Bối cảnh.
    *   Bài toán.
    *   Mục tiêu.

### Slide 2 – Vấn đề hiện tại (Nỗi đau của BA)
*   **Nội dung (Bán ý tưởng):**
    *   BA phải đọc tài liệu thủ công $\rightarrow$ Mất thời gian.
    *   Dễ bỏ sót yêu cầu.
    *   Khó chuyển đổi kiến thức thô thành User Story chuẩn.

### Slide 3 – Mục tiêu hệ thống
*   **Hệ thống có thể làm gì?**
    *   Đọc hiểu PDF chuyên ngành / BRD.
    *   Hỏi làm rõ yêu cầu (Clarification) thông minh.
    *   Tra cứu Wikipedia động.
    *   Sinh User Story & Business Rules (BA Mode).
    *   Sinh Test Case & Scenario chuyên nghiệp (QA Mode).
    *   Xuất CSV tương thích Jira và TestRail.

### Slide 4 – Kiến trúc tổng thể (QUAN TRỌNG NHẤT)
*   **Sơ đồ luồng xử lý:**
    ```text
    User
     ↓
    Chế độ (Mode Selection)
     ├── BA Agent Mode
     └── QA/Tester Agent Mode
     ↓
    Tool Selection (PDF RAG / Wiki RAG)
     ↓
    Reasoning & Clarification
     ↓
    Structured Output
     ├── Jira CSV (User Story)
     └── TestRail CSV (Test Case)
    ```

### Slide 5 – Agent Workflow
*   **Nhấn mạnh:** LangGraph ReAct Agent
*   **Quy trình:** `Question` $\rightarrow$ `Reasoning` $\rightarrow$ `Tool Calling` $\rightarrow$ `Observation` $\rightarrow$ `Final Answer`

### Slide 6 – PDF RAG Pipeline
*   **Quy trình chuẩn bị dữ liệu nội bộ:** `PDF` $\rightarrow$ `Chunking` (Section-aware) $\rightarrow$ `Embedding` $\rightarrow$ `ChromaDB` $\rightarrow$ `Hybrid Search` $\rightarrow$ `Re-ranking`

### Slide 7 – Wikipedia RAG Tool
*   **Nhấn mạnh (Điểm Mentor cực kỳ quan tâm):** Không dùng Summary trực tiếp.
*   **Quy trình:** `Wikipedia` $\rightarrow$ `Content` $\rightarrow$ `Chunk` $\rightarrow$ `Embedding` $\rightarrow$ `Temporary Vector Store` $\rightarrow$ `Retrieval`

### Slide 8 – Clarification Mechanism (Cơ chế chống Ảo giác)
*   **Điểm sáng về nghiệp vụ BA:**
    *   *Input:* Xây dựng hệ thống khách sạn.
    *   *Agent phản ứng:* Có thanh toán online không? Có những vai trò nào?

### Slide 9 – Demo Results
*   **Nội dung:** Chèn các ảnh chụp màn hình thực tế (từ Automation Test).
    *   UI chuyển đổi BA / QA Mode.
    *   Clarification Questions.
    *   User Story JSON/Markdown.
    *   Test Case Markdown Table.
    *   CSV Export (Jira & TestRail).

### Slide 10 – Đánh giá (Testing & Automation)
*   **Bảng kết quả Test (Có minh chứng):**
    | Test Case | Automation Result |
    | :--- | :--- |
    | PDF RAG & Wiki Tool | ✅ Pass |
    | BA Clarification & User Story | ✅ Pass |
    | QA Clarification & Test Case | ✅ Pass |
    | CSV Dual-Export | ✅ Pass |
    | Playwright UI Test | ✅ Pass |

### Slide 11 – Hạn chế (Limitations)
*   *(Ghi điểm nhờ sự khách quan, nhìn nhận đúng thực tế)*
    *   Chưa tích hợp Jira API.
    *   Chưa có Traceability 1-1 (User Story map trực tiếp về trang PDF gốc).
    *   Chưa có RAGAS Evaluation liên tục trên pipeline tự động (Do giới hạn API free).
    *   Chưa có Memory dài hạn (Long-term DB).

### Slide 12 – Hướng phát triển (Future Work)
*   Jira & TestRail API Integration.
*   Traceability Mapping (1 User Story -> N Test Cases).
*   Evaluation Framework (Ragas CI/CD).
*   Mở rộng thêm Dev Agent (Sinh code).

---
### 🎤 CÂU CHỐT HẠ KẾT THÚC BÀI THUYẾT TRÌNH:
> *"Hệ thống hiện đã hoàn thành một hệ sinh thái Dual-Mode Agent với khả năng Agentic RAG, Tool Calling, Clarification và sinh Artifacts (User Story, Test Case) đạt chuẩn công nghiệp. Các hướng phát triển tiếp theo của nhóm sẽ tập trung vào API Automation và khả năng hợp tác đa tác tử (Multi-Agent Collaboration) sâu hơn. Em xin cảm ơn hội đồng đã lắng nghe!"*
