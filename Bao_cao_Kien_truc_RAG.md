# Báo cáo Kiến trúc RAG Chatbot
## Hệ thống Trợ lý Nghiên cứu Khoa học Thông minh

---

## 1. Tổng quan hệ thống

**RAG Chatbot** (Retrieval-Augmented Generation) là hệ thống hỏi-đáp thông minh kết hợp:
- **Tìm kiếm ngữ cảnh** từ tài liệu thực (PDF hoặc Wikipedia)
- **Sinh câu trả lời** bằng mô hình ngôn ngữ lớn (LLM)

> Khác với chatbot thông thường chỉ dựa vào dữ liệu huấn luyện sẵn, RAG Chatbot **trả lời dựa trên tài liệu được cung cấp** — giảm thiểu hiện tượng "ảo giác" (hallucination) của AI.

---

## 2. Kiến trúc 5 Tầng (5-Layer Architecture)

```text
┌─────────────────────────────────────────────────────────┐
│              NGƯỜI DÙNG nhập câu hỏi                    │
└─────────────────────┬───────────────────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  TẦNG 1: DATA INGESTION│  ← Nạp & xử lý tài liệu
          │  (Khi upload tài liệu) │
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │  TẦNG 2: RETRIEVAL    │  ← Tìm kiếm ngữ cảnh
          │  (Mỗi khi người dùng  │
          │   gửi câu hỏi)        │
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │  TẦNG 3: GENERATION   │  ← Sinh câu trả lời
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │  TẦNG 4: ACCURACY     │  ← Kiểm soát chất lượng
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │  TẦNG 5: UX/TRUST     │  ← Hiển thị & tương tác
          └───────────────────────┘
```

---

## 3. Chi tiết từng Tầng

### 🟢 Tầng 1 — Data Ingestion (Nạp dữ liệu)

**Mục đích:** Đọc tài liệu, cắt nhỏ và lưu vào cơ sở dữ liệu vector.

**Quy trình:**
```text
Tài liệu đầu vào (PDF / Wikipedia)
        ↓
[Trích xuất văn bản]  ← PyPDFLoader / wikipedia library
        ↓
[Cắt nhỏ thành Chunks]  ← RecursiveCharacterTextSplitter
   chunk_size = 1000 ký tự
   chunk_overlap = 200 ký tự
   separators: đoạn văn → dòng → câu
        ↓
[Gắn Metadata cho từng chunk]
   • title: tên bài báo / tên bài Wikipedia
   • authors: tên tác giả
   • year: năm xuất bản
   • section_heading: Abstract / Introduction / Results...
   • source_filename: tên file gốc
        ↓
[Tạo Vector Embedding]  ← Google Gemini Embedding API
        ↓
[Lưu vào ChromaDB]  ← Cơ sở dữ liệu vector cục bộ
```

**Kết quả:** Mỗi chunk là một đoạn văn có nghĩa + metadata đầy đủ, sẵn sàng để tìm kiếm.

---

### 🔵 Tầng 2 — Retrieval (Tìm kiếm ngữ cảnh)

**Mục đích:** Tìm những đoạn văn liên quan nhất với câu hỏi của người dùng.

**Kỹ thuật: Hybrid Search = BM25 + Vector + RRF**

```text
Câu hỏi người dùng
        │
        ├──► [BM25 Search]          ← Tìm theo từ khóa chính xác
        │    (tốt với thuật ngữ kỹ  
        │     thuật: "F1=0.94",     
        │     "ablation study")     
        │
        ├──► [Vector Search]        ← Tìm theo ngữ nghĩa
        │    (tốt với câu hỏi       
        │     ngữ nghĩa: "phương    
        │     pháp tiếp cận")       
        │
        └──► [Reciprocal Rank Fusion (RRF)]
             Gộp và sắp xếp lại kết quả
             Score = 1/(rank + 60)
                     ↓
             Top-6 chunks liên quan nhất
```

> **Tại sao Hybrid?** Vector search đôi khi bỏ qua từ kỹ thuật cụ thể. BM25 không hiểu ngữ nghĩa. Kết hợp cả hai cho kết quả tốt nhất.

---

### 🟡 Tầng 3 — Generation (Sinh câu trả lời)

**Mục đích:** Dùng LLM để tổng hợp câu trả lời từ ngữ cảnh đã tìm được.

**Cấu trúc Prompt:**
```text
[Vai trò]
Bạn là trợ lý AI chuyên phân tích bài báo nghiên cứu.
Hãy suy nghĩ từng bước (Chain-of-Thought).

[Quy tắc Anti-hallucination]
QUAN TRỌNG: Chỉ trả lời từ NGỮ CẢNH bên dưới.
Nếu không có thông tin → "Tôi không tìm thấy trong tài liệu."

[Lịch sử hội thoại — Token-based]
≈ 2000 tokens gần nhất (thay vì cắt cứng 5 lượt)
🧑 Người dùng: ...
🤖 Trợ lý: ...

[Ngữ cảnh tài liệu]
(6 chunks liên quan nhất từ Tầng 2)

[Câu hỏi hiện tại]
```

**LLM sử dụng:** Google Gemini 2.5 Flash

---

### 🔴 Tầng 4 — Accuracy (Kiểm soát chất lượng)

**Mục đích:** Đảm bảo câu trả lời đáng tin cậy, không bịa đặt.

| Cơ chế | Hoạt động |
|--------|-----------|
| **Anti-hallucination** | Prompt cứng: chỉ trả lời từ ngữ cảnh |
| **Fallback Block** | Nếu chưa upload tài liệu → chặn hoàn toàn, không gọi LLM |
| **Confidence Score** | Tính từ L2 distance: `score = 1 / (1 + distance)` |
| **Confidence Warning** | Nếu score < 40% → hiện cảnh báo cho người dùng |
| **Retry Logic** | Tự động đợi và thử lại khi bị Rate Limit (429) |

**Công thức Confidence Score:**
```text
Vector Distance (L2) → Confidence Score
distance = 0.2  →  score = 83%  🟢
distance = 1.5  →  score = 40%  🟡  
distance = 3.0  →  score = 25%  🔴
```

---

### 🟣 Tầng 5 — UX/Trust (Giao diện & Độ tin cậy)

**Mục đích:** Giúp người dùng hiểu và tin tưởng vào câu trả lời.

**Các thành phần:**

```text
Câu trả lời của AI
        │
        ├── [Confidence Warning]   ← Banner vàng nếu score thấp
        │
        ├── [🔍 Nguồn trích dẫn]   ← Expander hiển thị:
        │    • 🟢/🟡/🔴 Độ liên quan: 75%
        │    • Tên file / URL Wikipedia
        │    • 📰 Tiêu đề bài báo
        │    • 👤 Tác giả (Năm)
        │    • 📑 Section: abstract / results
        │    • Đoạn văn gốc
        │
        ├── [💡 Gợi ý câu hỏi tiếp]  ← LLM tự sinh 3 câu
        │    👉 Ablation study kết quả ra sao?
        │    👉 Dataset được xây dựng thế nào?
        │
        └── [📊 Feedback]
             👍 Hữu ích → ghi vào feedback_log.json
             👎 Không hữu ích → ghi để cải thiện sau
```

---

## 4. Hai chế độ hoạt động

### 📄 Chế độ 1: Research Paper Mode (`app_streamlit.py`)
- **Nguồn:** File PDF bài báo nghiên cứu (upload thủ công)
- **Phù hợp:** Phân tích bài báo cụ thể, trích dẫn chính xác
- **Port:** `http://localhost:8501`

### 🌐 Chế độ 2: Wikipedia Mode (`app_wiki.py`)
- **Nguồn:** Wikipedia API (fetch real-time theo chủ đề)
- **Phù hợp:** Tra cứu kiến thức rộng, không cần upload file
- **Port:** `http://localhost:8502`

---

## 5. Luồng dữ liệu đầy đủ

```text
[Người dùng]
     │
     │  "H-RAG cải thiện bao nhiêu % so với baseline?"
     ▼
[Streamlit UI]
     │
     ▼
[Tầng 2: Hybrid Search]
     │  BM25 → ["H-RAG improved 8-12%...", ...]  (rank 1,2,3)
     │  Vector → ["flat RAG pipeline...", ...]    (rank 1,2,3)
     │  RRF → Top 6 chunks kết hợp
     ▼
[Tầng 4: Confidence Score]
     │  Chunk 1: score = 0.78 🟢
     │  Chunk 2: score = 0.65 🟢
     │  Chunk 3: score = 0.43 🟡
     ▼
[Tầng 3: LLM (Gemini 2.5 Flash)]
     │  Input: Prompt + 6 chunks + history (≈2000 tokens)
     │  Output: Câu trả lời chi tiết, có Chain-of-Thought
     ▼
[Tầng 5: UI Response]
     │  ✅ Câu trả lời hiển thị
     │  🔍 Nguồn: H-RAG paper Trang 4, Section: results, 🟢 78%
     │  💡 Gợi ý: "MuSiQue dataset là gì?", ...
     │  📊 Feedback: 👍 / 👎
     ▼
[feedback_log.json]  ← Lưu để phân tích và cải thiện
```

---

## 6. Stack kỹ thuật

| Thành phần | Công nghệ |
|-----------|-----------|
| Frontend UI | Streamlit |
| Backend API | FastAPI (sẵn sàng tích hợp) |
| LLM | Google Gemini 2.5 Flash |
| Embedding | Google Gemini Embedding 2 |
| Vector DB | ChromaDB (local persistent) |
| Keyword Search | BM25 (rank-bm25) |
| PDF Loader | PyPDFLoader (LangChain) |
| Wiki Loader | wikipedia library |
| Framework | LangChain |

---

## 7. Điểm mạnh so với RAG thông thường

| Tiêu chí | RAG cơ bản | RAG Chatbot này |
|----------|-----------|-----------------|
| Tìm kiếm | Vector only | **Hybrid: BM25 + Vector + RRF** |
| Metadata | Chỉ có page | **title, authors, year, section** |
| Hallucination | Không kiểm soát | **Chặn hoàn toàn khi không có ngữ cảnh** |
| Confidence | Không có | **Score 🟢🟡🔴 + cảnh báo** |
| Context window | Cắt cứng N turns | **Token-based dynamic trimming** |
| Nguồn dữ liệu | 1 loại | **PDF + Wikipedia real-time** |
| Feedback | Không có | **👍👎 + JSON logging** |

---

## 8. Hướng phát triển tiếp theo

1. **SemanticChunker** — Cắt chunk theo ngữ nghĩa (cần API Paid Tier)
2. **HyDE** — Tăng độ chính xác retrieval (đã có, cần bật toggle)
3. **RAGAS Evaluation** — Đo Faithfulness & Answer Relevancy tự động
4. **GraphRAG** — Xây dựng knowledge graph thay vì chunk tuyến tính
5. **Multi-document Comparison** — Filter retrieval theo từng file riêng biệt
