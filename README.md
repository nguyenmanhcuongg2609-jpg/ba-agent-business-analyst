# 🤖 RAG Chatbot - Trợ Lý Nghiên Cứu Khoa Học Thông Minh

Dự án **RAG Chatbot** là một hệ thống hỏi đáp (QA) thông minh dựa trên kiến trúc **Retrieval-Augmented Generation (RAG)**. Ứng dụng cho phép người dùng nạp vào các tài liệu như bài báo khoa học (PDF) hoặc tra cứu trực tiếp từ Wikipedia, sau đó đặt câu hỏi và nhận câu trả lời chính xác có kèm theo trích dẫn nguồn (citation).

Dự án nhằm giải quyết vấn đề "ảo giác" (hallucination) thường gặp ở các LLM truyền thống, bằng cách bắt buộc mô hình phải dựa trên các thông tin đã được trích xuất (retrieved context) từ cơ sở dữ liệu để đưa ra câu trả lời.

---

## 🚀 Các Tính Năng Nổi Bật

1. **Tìm kiếm lai (Hybrid Search)**: Kết hợp tìm kiếm theo từ khóa (BM25) và tìm kiếm theo ngữ nghĩa (Vector Search với Gemini Embeddings). Kỹ thuật **Reciprocal Rank Fusion (RRF)** được sử dụng để kết hợp và xếp hạng lại kết quả, giúp tìm ngữ cảnh chính xác nhất.
2. **Kiểm soát ảo giác (Anti-hallucination)**: LLM được hướng dẫn chặt chẽ qua prompt để từ chối trả lời nếu thông tin không tồn tại trong tài liệu.
3. **Cảnh báo độ tin cậy (Confidence Score)**: Hệ thống tính toán điểm tin cậy dựa trên khoảng cách Vector (L2 distance) và tự động cảnh báo người dùng nếu tài liệu truy xuất có độ tương đồng thấp (<40%).
4. **Theo dõi nguồn gốc (Source Citation)**: Câu trả lời được đính kèm chi tiết nguồn lấy thông tin (trang số mấy, phần nào, tên tác giả, năm xuất bản...).
5. **Gợi ý tự động (Follow-up Questions)**: LLM tự động sinh thêm 3 câu hỏi gợi ý liên quan giúp người dùng đào sâu kiến thức.
6. **Lịch sử ngữ cảnh thông minh (Token-based History)**: Cắt bớt lịch sử trò chuyện linh hoạt theo số token thay vì số lượt (turns) cứng nhắc, tối ưu hóa ngữ cảnh đưa vào model.
7. **Phản hồi người dùng (Feedback Loop)**: Ghi nhận nút "Hữu ích / Không hữu ích" để tiếp tục cải thiện hệ thống.

---

## ⚙️ Cấu Trúc Hệ Thống (5-Layer Architecture)

Kiến trúc hệ thống được chia làm 5 tầng:
1. **Data Ingestion (Nạp dữ liệu)**: Xử lý PDF/Wiki, chia nhỏ (chunking), tạo Embeddings và lưu vào ChromaDB.
2. **Retrieval (Tìm kiếm)**: Nhận câu hỏi, tìm ra top ngữ cảnh liên quan nhất qua Hybrid Search.
3. **Generation (Sinh câu trả lời)**: Đưa ngữ cảnh và câu hỏi vào Gemini 2.5 Flash để sinh câu trả lời.
4. **Accuracy (Kiểm soát chất lượng)**: Tính điểm Confidence Score và xử lý Rate Limit, chặn sinh nội dung bịa đặt.
5. **UX/Trust (Trải nghiệm người dùng)**: Hiển thị kết quả, trích dẫn, gợi ý và ghi nhận đánh giá (Feedback).

*(Xem chi tiết trong tài liệu `Bao_cao_Kien_truc_RAG.md`)*

---

## 🛠️ Cài Đặt Và Chạy Ứng Dụng

### Yêu Cầu Hệ Thống
- Python 3.9 trở lên
- API Key của **Google Gemini** (tạo tại [Google AI Studio](https://aistudio.google.com/))

### Cài Đặt

1. **Clone repository:**
   ```bash
   git clone <repo_url>
   cd RAG_Chatbot
   ```

2. **Cài đặt môi trường:**
   Tạo môi trường ảo (khuyến nghị) và cài các thư viện:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Trên Windows dùng: .venv\Scripts\activate
   pip install -r backend/requirements.txt
   pip install streamlit rank_bm25 wikipedia
   ```

3. **Cấu hình API Key:**
   Tạo file `.env` ở thư mục gốc của dự án và điền thông tin sau:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

### Khởi Chạy Ứng Dụng

Dự án hiện có 2 ứng dụng độc lập dành cho 2 mục đích khác nhau:

#### 1. Chế độ đọc Bài báo nghiên cứu (Research Paper Mode)
Dành cho việc đọc, lưu trữ và phân tích các bài báo chuyên sâu dạng file `.pdf`.
```bash
streamlit run app_streamlit.py
```
> Truy cập tại: `http://localhost:8501`

#### 2. Chế độ tra cứu Wikipedia (Wikipedia Mode)
Dành cho việc truy vấn tự động các bài viết trên Wikipedia mà không cần tải tài liệu lên thủ công.
```bash
streamlit run app_wiki.py
```
> Truy cập tại: `http://localhost:8502`

*(Mẹo: Bạn có thể chạy song song 2 lệnh này trên 2 terminal khác nhau để mở cả hai chế độ).*

---

## 🏗️ Cấu Trúc Thư Mục

```
RAG_Chatbot/
├── app_streamlit.py           # Streamlit App cho Research Papers (PDF)
├── app_wiki.py                # Streamlit App cho Wikipedia
├── chatbot.py                 # File thử nghiệm ban đầu của dự án
├── Bao_cao_Kien_truc_RAG.md   # Tài liệu kiến trúc hệ thống chuyên sâu
├── .env                       # Chứa API keys (Không đẩy lên git)
├── chroma_db_storage/         # Thư mục lưu trữ vector tự động (Paper mode)
├── chroma_wiki_storage/       # Thư mục lưu trữ vector tự động (Wiki mode)
├── uploaded_papers/           # Chứa các file PDF do người dùng tải lên
├── backend/                   # Thư mục API chuẩn bị tích hợp FastAPI
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml         # Dùng để khởi chạy backend bằng Docker
```

---

## 🤝 Tương Lai Phát Triển (Roadmap)
- Xây dựng API độc lập với FastAPI.
- Tích hợp **SemanticChunker** (hiện tại đang dùng RecursiveCharacterTextSplitter để phù hợp với API free-tier).
- Tích hợp **GraphRAG** để xử lý cấu trúc tri thức theo dạng đồ thị thay vì chunk tuyến tính.
- Mở rộng hỗ trợ định dạng file `docx` và `txt`.

---
*Dự án thực tập/nghiên cứu.*
