"""
rag_utils.py — Shared utilities cho RAG Chatbot
================================================
Module này tập trung tất cả logic dùng chung giữa app_streamlit.py và app_wiki.py,
loại bỏ hoàn toàn việc copy-paste code.

Bao gồm:
  - call_llm_with_retry      : Gọi LLM có exponential backoff khi bị rate limit 429
  - hybrid_search            : BM25 + Vector Search kết hợp bằng Reciprocal Rank Fusion
  - estimate_tokens          : Ước tính số token từ độ dài chuỗi
  - trim_history_by_tokens   : Cắt lịch sử chat theo giới hạn token
  - rewrite_query_with_history : [MỚI] Query rewriting cho multi-turn conversation
  - extract_llm_text         : Trích text từ response Gemini (xử lý list/str)
  - build_rag_prompt         : [MỚI] Prompt có structured output + language detection
"""

import time
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document

# ─────────────────────────────────────────────
# 1. RATE LIMIT HANDLER
# ─────────────────────────────────────────────

def call_llm_with_retry(llm, messages, max_retries: int = 3, toast_fn=None):
    """
    Gọi LLM với tự động retry khi bị 429 RESOURCE_EXHAUSTED.

    Args:
        llm        : LangChain LLM instance
        messages   : list[BaseMessage]
        max_retries: số lần thử lại tối đa
        toast_fn   : hàm hiển thị thông báo (vd: st.toast). None → dùng print.
    """
    notify = toast_fn if toast_fn else lambda msg, **_: print(msg)
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 2 ** attempt * 15  # 15s → 30s → 60s
                notify(
                    f"⏳ Rate limit — đợi {wait}s rồi thử lại... (lần {attempt+1}/{max_retries})",
                    icon="⚠️"
                )
                time.sleep(wait)
            else:
                raise e
    raise Exception("Vượt quá số lần retry. Vui lòng thử lại sau.")


# ─────────────────────────────────────────────
# 2. HYBRID SEARCH VÀ RE-RANKING (BM25 + Vector + CrossEncoder)
# ─────────────────────────────────────────────

cross_encoder_model = None

def get_cross_encoder():
    """Lazy load Cross-encoder để tránh khởi tạo chậm lúc start app"""
    return None  # TẠM TẮT ĐỂ TRÁNH TẢI MÔ HÌNH CHẬM (FIX LỖI LOAD LÂU)

def hybrid_search(vectorstore, bm25_retriever, query: str, k: int = 6) -> list[Document]:
    """
    Gộp kết quả BM25 và Vector Search bằng Reciprocal Rank Fusion (RRF).
    Sau đó áp dụng Cross-Encoder Re-ranking (nếu có thư viện) để đẩy top kết quả lên.
    RRF score = Σ 1/(rank + 60) — hằng số 60 theo paper Cormack et al. 2009.
    """
    bm25_docs   = bm25_retriever.invoke(query)
    
    # BỎ QUA Vector Search vì API Google đang bị hết Quota (Rate Limit) gây treo máy
    # vector_docs = vectorstore.similarity_search(query, k=k)
    vector_docs = []

    scores: dict = {}
    for rank, doc in enumerate(bm25_docs):
        key = doc.page_content
        scores.setdefault(key, {"doc": doc, "score": 0.0})
        scores[key]["score"] += 1 / (rank + 60)
    for rank, doc in enumerate(vector_docs):
        key = doc.page_content
        scores.setdefault(key, {"doc": doc, "score": 0.0})
        scores[key]["score"] += 1 / (rank + 60)

    ranked = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    top_docs = [item["doc"] for item in ranked[:k*2]] # Lấy dư ra (k*2) để rerank

    # --- BƯỚC RE-RANKING BẰNG CROSS-ENCODER ---
    ce = get_cross_encoder()
    if ce is not None and top_docs:
        try:
            pairs = [[query, doc.page_content] for doc in top_docs]
            ce_scores = ce.predict(pairs)
            
            # Gắn điểm mới vào metadata
            for idx, score in enumerate(ce_scores):
                top_docs[idx].metadata["ce_score"] = float(score)
            
            # Sort lại theo điểm của Cross-Encoder
            top_docs_reranked = sorted(zip(top_docs, ce_scores), key=lambda x: x[1], reverse=True)
            return [doc for doc, score in top_docs_reranked[:k]]
        except Exception as e:
            print(f"Lỗi Re-ranking: {e}. Trả về kết quả RRF gốc.")
            
    return top_docs[:k]

# ─────────────────────────────────────────────
# 3. TOKEN-BASED HISTORY
# ─────────────────────────────────────────────

MAX_HISTORY_TOKENS = 2000


def estimate_tokens(text: str) -> int:
    """Ước tính số token (~4 ký tự = 1 token cho tiếng Anh/Việt hỗn hợp)."""
    return len(text) // 4


def trim_history_by_tokens(
    messages: list, max_tokens: int = MAX_HISTORY_TOKENS
) -> str:
    """
    Xây dựng history_text từ các messages gần nhất sao cho tổng token ≤ max_tokens.
    Luôn lấy từ cuối về đầu để giữ context mới nhất.
    """
    selected     = []
    total_tokens = 0
    for msg in reversed(messages[:-1]):  # bỏ câu hiện tại vừa append
        role = "🧑 Người dùng" if isinstance(msg, HumanMessage) else "🤖 Trợ lý"
        line = f"{role}: {msg.content}\n"
        t    = estimate_tokens(line)
        if total_tokens + t > max_tokens:
            break
        selected.insert(0, line)
        total_tokens += t
    return "".join(selected)


# ─────────────────────────────────────────────
# 4. QUERY REWRITING — multi-turn fix  [MỚI]
# ─────────────────────────────────────────────

def rewrite_query_with_history(llm, user_query: str, chat_history: list) -> str:
    """
    Viết lại câu hỏi của user thành câu độc lập (standalone), không phụ thuộc
    vào ngữ cảnh hội thoại trước.

    Vấn đề giải quyết:
        User hỏi "Phương pháp này có tốt hơn BERT không?" sau khi đã nói về
        H-RAG. Nếu embed câu gốc, vector search sẽ không tìm được gì liên quan
        vì "phương pháp này" không có nghĩa khi đứng một mình.

    Nếu không có lịch sử (câu đầu tiên) → trả về câu hỏi gốc ngay, không tốn API.
    """
    # Không có lịch sử → câu đầu tiên, không cần rewrite
    if not chat_history or len(chat_history) < 2:
        return user_query

    # Lấy tối đa 3 lượt gần nhất để làm context cho rewriter (tiết kiệm token)
    recent = chat_history[-6:]  # 3 lượt = 6 messages (human + ai)
    history_snippet = trim_history_by_tokens(recent + [HumanMessage(content=user_query)], max_tokens=800)

    rewrite_prompt = (
        "Bạn là một công cụ viết lại câu hỏi (query rewriter) cho hệ thống RAG.\n"
        "Nhiệm vụ: Dựa vào lịch sử hội thoại bên dưới, hãy viết lại câu hỏi mới nhất "
        "của người dùng thành một câu hỏi ĐỘC LẬP, đầy đủ nghĩa khi đứng một mình, "
        "không dùng đại từ chỉ định mơ hồ (này, đó, nó, phương pháp trên...).\n"
        "Giữ nguyên ngôn ngữ của câu hỏi gốc (tiếng Việt → tiếng Việt, English → English).\n"
        "CHỈ trả về câu hỏi đã viết lại, không giải thích.\n\n"
        f"Lịch sử hội thoại:\n{history_snippet}\n"
        f"Câu hỏi gốc cần viết lại: {user_query}\n"
        "Câu hỏi độc lập:"
    )

    try:
        response = llm.invoke([HumanMessage(content=rewrite_prompt)])
        rewritten = extract_llm_text(response).strip()
        # Fallback nếu rewriter trả về chuỗi rỗng hoặc quá ngắn
        return rewritten if len(rewritten) > 5 else user_query
    except Exception:
        # Nếu rewrite thất bại → dùng câu gốc, không để crash toàn bộ flow
        return user_query


# ─────────────────────────────────────────────
# 5. EXTRACT TEXT từ Gemini response  [helper]
# ─────────────────────────────────────────────

def extract_llm_text(response) -> str:
    """
    Trích nội dung text từ LLM response.
    Gemini đời mới có thể trả về list thay vì string trực tiếp.
    """
    content = response.content
    if isinstance(content, list) and len(content) > 0:
        return content[0].get("text", str(content))
    return str(content)


# ─────────────────────────────────────────────
# 6. BUILD RAG PROMPT — structured output + language detection  [MỚI]
# ─────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Phát hiện ngôn ngữ đơn giản dựa trên tỉ lệ ký tự ASCII.
    ASCII cao → tiếng Anh. Unicode nhiều → tiếng Việt/CJK.
    Đủ dùng cho bài toán này, không cần thư viện ngoài.
    """
    if not text:
        return "Vietnamese"
    ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text)
    return "English" if ascii_ratio > 0.85 else "Vietnamese"


def build_rag_prompt(
    user_query: str,
    context: str,
    history_text: str,
    used_tokens: int,
) -> str:
    """
    Tạo prompt chuẩn cho RAG với:
      1. Language detection → LLM trả lời đúng ngôn ngữ câu hỏi
      2. Structured output → câu trả lời luôn có 3 phần rõ ràng:
            [ANSWER]    : nội dung trả lời chính
            [CITATIONS] : liệt kê nguồn theo số (nếu có)
            [LIMITS]    : giới hạn / điều LLM không chắc chắn
         Cấu trúc này giúp UI parse dễ, đồng thời giảm hallucination vì
         LLM phải khai báo tường minh những gì nó không biết.
      3. Anti-hallucination instruction rõ ràng hơn bản cũ
      4. Chain-of-Thought kích hoạt qua "think step by step"
    """
    lang = detect_language(user_query)
    lang_instruction = (
        "Answer in English." if lang == "English"
        else "Trả lời bằng tiếng Việt."
    )

    prompt = f"""Bạn là một Chuyên viên Phân tích Nghiệp vụ (Business Analyst - BA) AI cấp cao.
{lang_instruction}
Hãy suy nghĩ từng bước (think step by step) trước khi viết câu trả lời.

=== NGUYÊN TẮC BẮT BUỘC ===
1. Khi nhận yêu cầu, phân tích xem thông tin đã ĐỦ để viết Requirement/User Story chưa.
2. Nếu thiếu thông tin (ví dụ yêu cầu chung chung), BẮT BUỘC KHÔNG sinh Use Case/User Story, mà xuất ra các Câu hỏi làm rõ (Requirement Clarification).
3. Chỉ sử dụng thông tin từ [NGỮ CẢNH TÀI LIỆU] bên dưới. TUYỆT ĐỐI không bịa thêm.

=== ĐỊNH DẠNG TRẢ LỜI (Nếu đủ thông tin, xuất JSON chuẩn sau) ===
{{
  "use_cases": ["Danh sách các Use Case"],
  "user_stories": ["Danh sách các User Story theo chuẩn: As a [role], I want [goal] so that [benefit]"],
  "acceptance_criteria": ["Danh sách các tiêu chí chấp nhận"]
}}

Nếu không đủ thông tin, hãy sinh ra danh sách câu hỏi làm rõ (có thể không cần định dạng JSON).


=== DỮ LIỆU ĐẦU VÀO ===
📜 LỊCH SỬ HỘI THOẠI (≈{used_tokens} tokens):
{history_text if history_text else "(Chưa có lịch sử)"}

📖 NGỮ CẢNH TÀI LIỆU TRA CỨU ĐƯỢC:
{context}

❓ CÂU HỎI: {user_query}"""

    return prompt