# Báo cáo Nâng cấp: Từ RAG Chatbot lên BA AI Agent

Tài liệu này tổng hợp các hạng mục đã hoàn thành trong quá trình nâng cấp hệ thống theo chuẩn **Agentic Workflow** và các yêu cầu khắt khe dành cho một AI Agent chuyên nghiệp trong lĩnh vực Phân tích nghiệp vụ (Business Analysis).

## 1. Trở thành một AI Agent thực thụ (Agentic Workflow)
Thay vì quy trình xử lý tuyến tính `User -> VectorDB -> LLM -> Answer`, hệ thống đã được tái cấu trúc hoàn toàn bằng **LangGraph (ReAct Framework)**:
- **Tự động lập kế hoạch (Reasoning):** Agent có khả năng phân tích câu hỏi để tự quyết định xem cần tìm kiếm thông tin ở đâu.
- **Tự động gọi công cụ (Tool Calling):** Hệ thống không còn bị giới hạn trong 1 cơ sở dữ liệu duy nhất. Nó có thể gọi đồng thời 2 công cụ chuyên biệt để tổng hợp thông tin.

## 2. Nâng cấp Wikipedia Search thành Wikipedia RAG
Khắc phục điểm yếu "chỉ lấy tóm tắt 1500 ký tự đầu tiên":
- **Quy trình chuẩn:** Thay vì chỉ lấy đoạn Summary, công cụ `wikipedia_rag_tool` nay tải toàn bộ bài báo Wikipedia (ưu tiên tiếng Việt, fallback tiếng Anh).
- **Chunking & VectorDB tạm thời:** Hệ thống lập tức chia nhỏ bài viết thành các chunk (1000 ký tự) và tạo một VectorDB trên RAM (in-memory ChromaDB) để tiến hành RAG nội bộ bài viết, giúp trích xuất chính xác đoạn định nghĩa mấu chốt.

## 3. Khả năng Multi-document Reasoning (Suy luận Đa nguồn)
Agent có thể thực hiện những tác vụ phức tạp như "So sánh":
- Nó tự động gọi `wikipedia_rag_tool` để hiểu "khái niệm A là gì".
- Nó tiếp tục gọi `pdf_research_tool` để tìm xem "trong tài liệu đang mô tả B như thế nào".
- Cuối cùng, tổng hợp và đối chiếu 2 nguồn dữ liệu này để đưa ra câu trả lời logic.

## 4. Structured Output dành riêng cho BA
Hệ thống không còn trả lời dưới dạng đoạn văn text thông thường (Text QA). Khi được yêu cầu phân tích tính năng, Agent bắt buộc tuân theo System Prompt nghiêm ngặt để xuất ra chuẩn đầu ra của BA:
- **Requirement:** Yêu cầu nghiệp vụ chi tiết.
- **User Story:** Định dạng chuẩn `As a [role], I want [goal] so that [benefit]`.
- **Acceptance Criteria:** Các tiêu chí nghiệm thu rõ ràng.

## 5. UI Trực quan & Xử lý lỗi hệ thống (Auto-retry)
- **Giao diện `app_agent.py`:** Mang lại trải nghiệm giống hệt ChatGPT, có **Hộp Suy nghĩ (Thinking box)** hiển thị rõ ràng từng bước Agent đang làm (vd: "Đang gọi công cụ Wikipedia", "Đã lấy được dữ liệu").
- **Auto-retry LLM:** Hệ thống được cấu hình `max_retries` để tự động "ngủ đông" và thử lại ngầm khi gặp sự cố 429 Rate Limit từ Google, tránh tình trạng ứng dụng bị văng đột ngột.
