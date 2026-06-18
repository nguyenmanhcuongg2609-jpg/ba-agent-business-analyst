# 📊 CẤU TRÚC SLIDE BẢO VỆ ĐỒ ÁN (Khuyến nghị: 10 - 12 Slide)

Dựa trên toàn bộ quá trình phát triển hệ thống Agentic BA, đây là dàn ý chi tiết từng Slide để bạn thiết kế trên PowerPoint/Canva nhằm đạt điểm tuyệt đối.

---

### Slide 1 – Giới thiệu đề tài
*   **Tiêu đề:** BA Agent sử dụng Agentic RAG và Wikipedia Knowledge Base.
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
    *   Đọc hiểu PDF chuyên ngành.
    *   Hỏi làm rõ yêu cầu (Elicitation / Clarification).
    *   Tra cứu Wikipedia động.
    *   Sinh User Story & Acceptance Criteria.
    *   Xuất CSV tương thích Jira.

### Slide 4 – Kiến trúc tổng thể (QUAN TRỌNG NHẤT)
*   **Sơ đồ luồng xử lý:**
    ```text
    User
     ↓
    BA Agent
     ↓
    Tool Selection
     ├── PDF RAG Tool
     └── Wikipedia RAG Tool
     ↓
    Reasoning
     ↓
    Structured Output
     ↓
    CSV Export
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
*   **Nội dung:** Chèn các ảnh chụp màn hình thực tế (Hoặc quay Video nhúng vào Slide).
    *   Tool Calling.
    *   Clarification.
    *   User Story JSON/Markdown.
    *   CSV Export.

### Slide 10 – Đánh giá
*   **Bảng kết quả Test (Có minh chứng):**
    | Test Case | Kết quả |
    | :--- | :--- |
    | PDF QA | ✅ Pass |
    | Wiki Retrieval | ✅ Pass |
    | Clarification | ✅ Pass |
    | User Story | ✅ Pass |
    | CSV Export | ✅ Pass |

### Slide 11 – Hạn chế (Limitations)
*   *(Ghi điểm nhờ sự khách quan, nhìn nhận đúng thực tế)*
    *   Chưa tích hợp Jira API.
    *   Chưa có Traceability 1-1 (User Story map trực tiếp về trang PDF gốc).
    *   Chưa có RAGAS Evaluation liên tục trên pipeline tự động (Do giới hạn API free).
    *   Chưa có Memory dài hạn (Long-term DB).

### Slide 12 – Hướng phát triển (Future Work)
*   Jira Integration.
*   Confluence Integration.
*   Traceability Mapping.
*   Evaluation Framework.
*   Multi-Agent Collaboration (Thêm Dev Agent, Tester Agent).

---
### 🎤 CÂU CHỐT HẠ KẾT THÚC BÀI THUYẾT TRÌNH:
> *"Hệ thống hiện đã hoàn thành MVP của một Business Analyst Agent với khả năng Agentic RAG, Tool Calling, Clarification Questions và Structured Artifact Generation. Các hướng phát triển tiếp theo của nhóm sẽ tập trung vào Traceability, Evaluation Framework và tích hợp trực tiếp với các công cụ BA như Jira và Confluence. Em xin cảm ơn hội đồng đã lắng nghe!"*
