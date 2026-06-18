import os
import warnings
warnings.filterwarnings("ignore")
import time
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langgraph.prebuilt import create_react_agent

# Ép hệ thống luôn lấy Key mới nhất từ file .env (ghi đè Key cũ đang kẹt trong bộ nhớ Terminal)
load_dotenv(override=True)

# ==========================================
# 1. TOOL 1: WIKIPEDIA RAG ()
# ==========================================
@tool
def wikipedia_rag_tool(query: str) -> str:
    """
    Sử dụng công cụ này để tra cứu Wikipedia khi người dùng hỏi các kiến thức nền tảng (ví dụ: Scrum, Kanban, Agile là gì).
    Công cụ này sẽ tải bài báo Wikipedia, chia chunk, nhúng vào VectorDB tạm thời và trích xuất ngữ cảnh liên quan nhất.
    """
    print(f"\n[Tool Execution] Đang chạy Wikipedia RAG cho từ khóa: '{query}'...")
    from langchain_community.document_loaders import WikipediaLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    
    try:
        # 1. Lấy nguyên bài Wikipedia (ưu tiên tiếng Việt, backup tiếng Anh)
        docs = WikipediaLoader(query=query, load_max_docs=1, lang="vi").load()
        if not docs:
            docs = WikipediaLoader(query=query, load_max_docs=1, lang="en").load()
        
        if not docs:
            return f"Không tìm thấy bài viết Wikipedia nào cho từ khóa: {query}"
            
        print(f"  -> Đã tải bài viết: {docs[0].metadata.get('title')}")
        
        # 2. Chunking
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs)
        
        # 3. Embedding & VectorDB (Tạm thời trên RAM)
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
        temp_db = Chroma.from_documents(chunks, embeddings)
        
        # 4. Retrieval
        results = temp_db.similarity_search(query, k=2)
        context = "\n---\n".join([r.page_content for r in results])
        print(f"  -> Trích xuất được {len(context)} ký tự làm context từ Wikipedia.")
        return context
    except Exception as e:
        return f"Lỗi khi tra cứu Wikipedia: {e}"


# ==========================================
# 2. TOOL 2: PDF RESEARCH RAG
# ==========================================
@tool
def pdf_research_tool(query: str) -> str:
    """
    Sử dụng công cụ này để tìm kiếm thông tin chuyên sâu từ các bài báo, tài liệu PDF do người dùng upload.
    BẮT BUỘC dùng khi người dùng nhắc tới 'bài báo', 'tài liệu trên hệ thống', hoặc 'file vừa nạp'.
    Nếu người dùng chỉ nói "đọc file" hoặc "tóm tắt" mà không có câu hỏi cụ thể, hãy tự động gọi công cụ này với query là "tóm tắt nội dung chính và mục đích của tài liệu".
    """
    print(f"\n[Tool Execution] Đang quét VectorDB (PDF) cho từ khóa: '{query}'...")
    from langchain_chroma import Chroma
    from rag_utils import hybrid_search
    from langchain_community.retrievers import BM25Retriever
    
    CHROMA_DIR = "./chroma_db_storage"
    if not os.path.exists(CHROMA_DIR):
        return "Hiện chưa có tài liệu PDF nào trong cơ sở dữ liệu."
        
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
    
    # Tạo BM25 (đơn giản hoá cho script test)
    all_docs_data = vectorstore.get()
    if not all_docs_data["documents"]:
         return "Cơ sở dữ liệu đang trống."
         
    all_docs = [Document(page_content=t, metadata=m) for t, m in zip(all_docs_data["documents"], all_docs_data["metadatas"])]
    bm25 = BM25Retriever.from_documents(all_docs)
    bm25.k = 6
    
    # Gọi Hybrid Search + Cross Encoder
    results = hybrid_search(vectorstore, bm25, query, k=3)
    context = "\n---\n".join([r.page_content for r in results])
    print(f"  -> Trích xuất được {len(context)} ký tự từ PDF cục bộ.")
    return context


# ==========================================
# 3. KHỞI TẠO BA AGENT WORKFLOW
# ==========================================

# Khởi tạo LLM (Agent cần khả năng reasoning mạnh)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, max_retries=3)

# Định nghĩa System Prompt cho BA Agent (Cập nhật SPRINT 3: Clarification Questions)
ba_system_prompt = """Bạn là một Chuyên viên Phân tích Nghiệp vụ (Business Analyst - BA) AI cấp cao.
Bạn có khả năng suy luận đa tài liệu (Multi-document Reasoning) và tư duy logic phản biện.

QUY TRÌNH SUY NGHĨ (REASONING & CLARIFICATION):
1. Khi nhận câu hỏi hoặc yêu cầu, hãy lập kế hoạch (Plan) xem thông tin người dùng cung cấp đã ĐỦ để viết Requirement/User Story chưa.
2. [MISSING INFO? - QUAN TRỌNG NHẤT]: Nếu yêu cầu quá chung chung (Ví dụ: "Xây dựng hệ thống bán hàng", "Làm app khách sạn"), bạn BẮT BUỘC KHÔNG ĐƯỢC sinh ra Use Case hay User Story ngay lập tức. Bạn phải đặt ra các Câu hỏi làm rõ (Clarification Questions) cho người dùng. Ví dụ:
   - Có những loại người dùng (Actor) nào? (Admin, Khách hàng, Lễ tân...)
   - Quy trình cụ thể như thế nào?
   - Có tính năng thanh toán/vận chuyển không?
3. Dùng công cụ `wikipedia_rag_tool` để tìm khái niệm nền tảng nếu cần.
4. Dùng công cụ `pdf_research_tool` để đọc tài liệu nội bộ nếu người dùng nhắc đến file.
5. Chỉ khi có ĐỦ thông tin hoặc được yêu cầu rõ ràng, bạn mới xuất ra kết quả.

ĐỊNH DẠNG ĐẦU RA (STRUCTURED OUTPUT) - (Chỉ xuất ra khi đã có đủ thông tin):
Nếu có đủ thông tin, HÃY XUẤT CÂU TRẢ LỜI THEO ĐÚNG FORMAT SAU:
1. **Yêu cầu (Requirement)**: [Mô tả yêu cầu hệ thống]
2. **User Story**: As a [role], I want [goal] so that [benefit].
3. **Acceptance Criteria**: [Các tiêu chí chấp nhận]

Nếu yêu cầu chưa rõ, chỉ cần xuất ra danh sách câu hỏi làm rõ."""

# Gộp các tools
tools = [wikipedia_rag_tool, pdf_research_tool]

# Tạo ReAct Agent bằng LangGraph Prebuilt
from langgraph.prebuilt import create_react_agent
ba_agent = create_react_agent(llm, tools, prompt=ba_system_prompt)

def run_agent(query: str):
    print(f"\n" + "="*60)
    print(f"🧑 USER: {query}")
    print("="*60)
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Gọi Agent chạy
            result = ba_agent.invoke({"messages": [("user", query)]})
            
            print("\n" + "="*60)
            print("🤖 BA AGENT TRẢ LỜI:")
            print("="*60)
            # Tin nhắn cuối cùng luôn là câu trả lời của LLM sau khi đã chạy xong các Tools
            content = result["messages"][-1].content
            if isinstance(content, list):
                content = "\n".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
            print(content)
            print("="*60)
            return
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"⏳ Lỗi Rate Limit của Google (quá 20 lượt/phút). Đang tự động đợi 15s... (lần {attempt+1}/{max_retries})")
                time.sleep(15)
            else:
                raise e
    print("❌ Vượt quá số lần tự động thử lại do Rate Limit.")

if __name__ == "__main__":
    print("🚀 ĐANG KHỞI ĐỘNG BA AGENT WORKFLOW...")
    
    # Test 1: Khái niệm Wiki + Structured Output
    run_agent("Hãy tra cứu Wikipedia khái niệm Scrum và viết cho tôi 1 User Story mẫu về tính năng 'Lên kế hoạch Sprint'.")
    
    # Test 2: Multi-document Reasoning (Wiki + PDF)
    print("\n⏳ Đợi 15s để tránh Rate Limit API...")
    time.sleep(15)
    run_agent("So sánh phương pháp cắt token trong AgriViT (dùng PDF) với khái niệm Attention Mechanism (tìm trên Wikipedia).")
