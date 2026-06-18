# 🎯 KỊCH BẢN DEMO BẢO VỆ ĐỒ ÁN (AGENTIC BA)

Tài liệu này chứa các kịch bản demo **"có chủ đích"** được thiết kế riêng để chứng minh 4 năng lực cốt lõi của hệ thống trước hội đồng Mentor: `Tool Calling`, `Clarification`, `Structured Output`, và `CSV Export`.

Bạn chỉ cần Copy -> Paste các câu hỏi này vào giao diện Streamlit khi thuyết trình.

---

## DEMO 1: Khả năng tự chọn Tool (Wiki Tool vs PDF Tool)
**Mục tiêu:** Chứng minh Agent tự đọc ngữ nghĩa câu hỏi và quyết định dùng Tool nào mà không cần lệnh `if/else` cứng.

### Kịch bản 1A: Gọi Wikipedia Tool
*   **Hành động:** Bạn (không cần tải PDF nào) nhập câu hỏi:
    > *"Tra cứu Wikipedia khái niệm OAuth 2.0 là gì và viết cho tôi 1 User Story về việc Đăng nhập bằng Google."*
*   **Giải thích cho Mentor:** *"Dạ anh/chị nhìn vào Thinking Box, Agent tự biết 'OAuth' là khái niệm chung nên nó đã chủ động gọi `wikipedia_rag_tool` để kéo kiến thức về."*

### Kịch bản 1B: Gọi PDF Tool
*   **Hành động:** Bạn tải 1 file PDF bất kỳ (ví dụ báo cáo H-RAG) và nhập:
    > *"Dựa vào tài liệu PDF vừa tải lên, hãy tóm tắt nội dung chính và mục đích của tài liệu."*
*   **Giải thích cho Mentor:** *"Ở câu này, Agent tự động bẻ lái sang gọi `pdf_research_tool` để quét Vector Database nội bộ thay vì ra ngoài Internet."*

---

## DEMO 2: Tư duy BA - Clarification Questions (Chống ảo giác Requirement)
**Mục tiêu:** Chứng minh Agent không "nhắm mắt làm bừa", nó biết phân biệt giữa Yêu cầu mập mờ và Yêu cầu đầy đủ.

### Kịch bản 2A: Yêu cầu thiếu thông tin (Missing Input)
*   **Hành động:** Bạn nhập một yêu cầu cực kỳ chung chung:
    > *"Tôi muốn làm một hệ thống quản lý khách sạn. Hãy viết Requirement và User Story cho tôi."*
*   **Kết quả kỳ vọng:** Agent từ chối viết User Story ngay. Nó sẽ hỏi vặn lại: *"Hệ thống phục vụ ai (Lễ tân, Quản lý, Khách)? Có tích hợp thanh toán online không?..."*
*   **Giải thích cho Mentor:** *"Đây là tính năng Clarification. Agent hành xử như một BA thực thụ, phát hiện ra requirement mập mờ và tiến hành Elicitation (Khai thác yêu cầu) để chống ảo giác."*

### Kịch bản 2B: Yêu cầu đầy đủ thông tin (Complete Input)
*   **Hành động:** Bạn cung cấp đủ dữ kiện như BA chuyên nghiệp:
    > *"Hệ thống quản lý khách sạn. Actors gồm: Lễ tân và Quản lý. Có yêu cầu tính năng thanh toán online qua VNPay. Hãy viết User Story."*
*   **Kết quả kỳ vọng:** Agent không hỏi lại nữa mà đi thẳng vào việc lập bảng JSON/Markdown chuẩn form chứa `Use Case`, `User Story` và `Acceptance Criteria`.

---

## DEMO 3: Tính năng Export Artifacts thực tiễn (CSV Export)
**Mục tiêu:** Ghi điểm cộng về tính thực tiễn của dự án (Tích hợp Jira/Excel).

*   **Hành động:** Ngay sau khi Demo 2B chạy xong và xuất ra User Story. Bạn cuộn xuống dưới cùng và click vào nút **"📥 Tải file CSV (Excel / Jira)"**.
*   **Giải thích cho Mentor:** *"Dạ thưa anh/chị, BA không làm việc bằng đoạn Chat. Mọi kết quả cuối cùng của Agent đều được hệ thống Parser của em bóc tách và xuất ra file CSV chuẩn, có thể Import thẳng bằng 1 click vào Jira Sprint Backlog của đội Dev."*

---

## CÂU HỎI PHÒNG THỦ: Traceability (Truy xuất nguồn gốc)
Nếu Mentor hỏi: *"User Story này sinh ra từ trang nào của tài liệu?"*
*   **Cách trả lời:** *"Dạ ở tầng Data, hàm `section_aware_split` của em đã map được Chunk với Tên Section tương ứng. Nhưng ở tầng giao diện hiện tại, việc map 1-1 từng User Story với số trang PDF là **Hướng phát triển tiếp theo (Future Work)** của dự án. Tiếp tới em sẽ ép LLM xuất thêm tham số `source_page` vào file CSV để hoàn thiện nốt tính năng này."*
