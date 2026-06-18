import os, time, shutil, json, asyncio, uuid
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, UploadFile, File, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.messages import HumanMessage
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredFileLoader
import wikipedia

from session_db import init_db, create_session, list_sessions, get_session_messages, save_message, delete_session, rename_session
from metadata_extractor import extract_pdf_metadata, section_aware_split

# Lazy loading cross-encoder — không tải khi startup
_cross_encoder = None
_cross_encoder_loaded = False

def get_cross_encoder():
    global _cross_encoder, _cross_encoder_loaded
    if _cross_encoder_loaded:
        return _cross_encoder
    try:
        from sentence_transformers import CrossEncoder
        _cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("✅ Cross-encoder loaded.")
    except Exception as e:
        print(f"⚠️ Cross-encoder không khả dụng: {e}")
        _cross_encoder = None
    _cross_encoder_loaded = True
    return _cross_encoder

wikipedia.set_lang("vi")
load_dotenv(dotenv_path="../.env")

CHROMA_DIR = "../chroma_db_storage"
UPLOAD_DIR = "../uploaded_papers"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
API_KEY = os.getenv("API_KEY", "rag-secret-key-2024")

if not GOOGLE_API_KEY:
    raise RuntimeError("❌ Chưa tìm thấy GOOGLE_API_KEY trong file .env!")

# ── Security ──────────────────────────────────────────────
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key không hợp lệ hoặc thiếu header X-API-Key.")
    return key

# ── AI Models ─────────────────────────────────────────────
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)

vectorstore_cache = None
bm25_retriever_cache = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vectorstore_cache, bm25_retriever_cache
    await init_db()
    print("⏳ Khởi tạo VectorStore và BM25...")
    if os.path.exists(CHROMA_DIR):
        try:
            vectorstore_cache = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
            all_docs_data = vectorstore_cache.get()
            if all_docs_data['documents']:
                all_docs = [Document(page_content=t, metadata=m) for t, m in zip(all_docs_data['documents'], all_docs_data['metadatas'])]
                bm25_retriever_cache = BM25Retriever.from_documents(all_docs)
                bm25_retriever_cache.k = 6
                print(f"✅ Tải {len(all_docs)} chunks thành công.")
        except Exception as e:
            print(f"❌ Lỗi tải VectorStore: {e}")
    yield
    print("🛑 Đóng ứng dụng.")

app = FastAPI(title="RAG Chatbot API v2", version="2.0", lifespan=lifespan)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Pydantic Models ────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []
    use_hyde: bool = False
    session_id: Optional[str] = None
    filter_files: Optional[List[str]] = None

class SourceDocument(BaseModel):
    page: int
    filename: str
    title: str
    authors: str
    year: str
    section: str
    content: str
    confidence_score: float

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    follow_up_questions: List[str]

class SessionCreate(BaseModel):
    title: str = "Phiên mới"

# ── Helpers ───────────────────────────────────────────────
def call_llm_with_retry(model, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return model.invoke(messages)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 15 * (2 ** attempt)
                print(f"⏳ Rate limit — đợi {wait}s (lần {attempt+1})")
                time.sleep(wait)
            else:
                raise e
    raise Exception("Vượt quá số lần retry.")

async def call_llm_async(model, messages, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await model.ainvoke(messages)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                await asyncio.sleep(15 * (2 ** attempt))
            else:
                raise e
    raise Exception("Vượt quá số lần retry.")

def hybrid_search(vectorstore, bm25_retriever, query: str, k: int = 6, filter_files: list = None):
    bm25_docs = bm25_retriever.invoke(query)
    if filter_files:
        chroma_filter = {"source_filename": {"$in": filter_files}}
        vector_docs = vectorstore.similarity_search(query, k=k, filter=chroma_filter)
        bm25_docs = [d for d in bm25_docs if d.metadata.get("source_filename") in filter_files]
    else:
        vector_docs = vectorstore.similarity_search(query, k=k)

    scores = {}
    for rank, doc in enumerate(bm25_docs):
        key = doc.page_content
        scores[key] = scores.get(key, {"doc": doc, "score": 0})
        scores[key]["score"] += 1 / (rank + 60)
    for rank, doc in enumerate(vector_docs):
        key = doc.page_content
        if key not in scores:
            scores[key] = {"doc": doc, "score": 0}
        scores[key]["score"] += 1 / (rank + 60)
    return [item["doc"] for item in sorted(scores.values(), key=lambda x: x["score"], reverse=True)[:k]]

def hyde_search(vectorstore, bm25_retriever, query: str, k: int = 6, filter_files: list = None):
    resp = call_llm_with_retry(llm, [HumanMessage(content=f"Hãy viết một đoạn văn ngắn (3-5 câu) giả định là trích dẫn từ bài báo khoa học trả lời câu hỏi: '{query}'. Chỉ viết đoạn văn.")])
    hypo = resp.content if isinstance(resp.content, str) else resp.content[0].get("text", "")
    return hybrid_search(vectorstore, bm25_retriever, hypo, k=k, filter_files=filter_files)

def get_score_map(vectorstore, query, relevant_docs):
    cross_encoder = get_cross_encoder()
    if cross_encoder and relevant_docs:
        pairs = [[query, doc.page_content] for doc in relevant_docs]
        scores = cross_encoder.predict(pairs)
        scored = sorted(zip(relevant_docs, scores), key=lambda x: x[1], reverse=True)
        relevant_docs[:] = [d for d, _ in scored[:6]]
        return {doc.page_content: min(max(float(s) / 10.0 + 0.5, 0.0), 1.0) for doc, s in scored}
    else:
        score_map = {}
        try:
            scored = vectorstore.similarity_search_with_score(query, k=6)
            for doc, dist in scored:
                score_map[doc.page_content] = min(round(1 / (1 + dist), 2), 1.0)
        except:
            pass
        return score_map

def wikipedia_rag_tool(query: str) -> str:
    try:
        from langchain_community.document_loaders import WikipediaLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        docs = WikipediaLoader(query=query, load_max_docs=1, lang="vi").load()
        if not docs:
            docs = WikipediaLoader(query=query, load_max_docs=1, lang="en").load()
        if not docs:
            return ""
        
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        chunks = splitter.split_documents(docs)
        
        temp_db = Chroma.from_documents(chunks, embeddings)
        results = temp_db.similarity_search(query, k=2)
        
        page_title = docs[0].metadata.get('title', 'Wikipedia')
        context = "\n---\n".join([r.page_content for r in results])
        return f"[WIKIPEDIA - {page_title}]\n{context}"
    except Exception as e:
        print(f"Error in wikipedia_rag_tool: {e}")
        return ""

def trim_history(messages: List[ChatMessage], max_tokens: int = 2000) -> str:
    selected, total = [], 0
    for msg in reversed(messages):
        role = "🧑 Người dùng" if msg.role == "user" else "🤖 Trợ lý"
        line = f"{role}: {msg.content}\n"
        t = len(line) // 4
        if total + t > max_tokens:
            break
        selected.insert(0, line)
        total += t
    return "".join(selected)

def extract_text(response) -> str:
    if isinstance(response.content, list) and response.content:
        return response.content[0].get("text", "")
    return str(response.content)

def build_sources(relevant_docs, score_map, used_wiki=False):
    sources = []
    for doc in relevant_docs:
        sources.append(SourceDocument(
            page=doc.metadata.get("page", 0) + 1,
            filename=doc.metadata.get("source_filename", "Unknown"),
            title=doc.metadata.get("title", "Unknown"),
            authors=doc.metadata.get("authors", "Unknown"),
            year=doc.metadata.get("year", "Unknown"),
            section=doc.metadata.get("section_heading", "Body"),
            content=doc.page_content,
            confidence_score=score_map.get(doc.page_content, 0.0)
        ))
    if used_wiki:
        sources.append(SourceDocument(page=1, filename="Wikipedia", title="Bách khoa toàn thư",
            authors="Wikipedia Contributors", year="2024", section="Summary",
            content="Thông tin từ Wikipedia tiếng Việt.", confidence_score=1.0))
    return sources

def refresh_bm25():
    global bm25_retriever_cache
    all_docs_data = vectorstore_cache.get()
    if all_docs_data["documents"]:
        all_docs = [Document(page_content=t, metadata=m) for t, m in zip(all_docs_data["documents"], all_docs_data["metadatas"])]
        bm25_retriever_cache = BM25Retriever.from_documents(all_docs)
        bm25_retriever_cache.k = 6

# ── RAG Core ──────────────────────────────────────────────
def rag_retrieve(request: ChatRequest):
    if vectorstore_cache is None or bm25_retriever_cache is None:
        raise HTTPException(status_code=400, detail="Chưa có tài liệu nào trong hệ thống.")
    if request.use_hyde:
        docs = hyde_search(vectorstore_cache, bm25_retriever_cache, request.query, filter_files=request.filter_files)
    else:
        docs = hybrid_search(vectorstore_cache, bm25_retriever_cache, request.query, filter_files=request.filter_files)
    score_map = get_score_map(vectorstore_cache, request.query, docs)
    context = "\n\n---\n\n".join([d.page_content for d in docs])
    used_wiki = False
    max_score = max(score_map.values()) if score_map else 0.0
    if max_score < 0.6 or not context.strip():
        wiki = wikipedia_rag_tool(request.query)
        if wiki:
            context = f"{context}\n\n---\n\n{wiki}" if context else wiki
            used_wiki = True
    return docs, score_map, context, used_wiki

def build_prompt(context, history_text, query):
    return (
        "Bạn là một Chuyên viên Phân tích Nghiệp vụ (Business Analyst - BA) AI cấp cao. Hãy suy nghĩ từng bước.\n"
        "Dùng ngữ cảnh và lịch sử bên dưới để phân tích yêu cầu.\n"
        "Hãy xuất ra định dạng JSON chuẩn gồm các trường: use_cases (mảng string), user_stories (mảng string), acceptance_criteria (mảng string).\n"
        "Nếu không tìm thấy thông tin, hãy sinh ra câu hỏi làm rõ (Requirement Clarification).\n\n"
        f"📜 LỊCH SỬ:\n{history_text}\n"
        f"📖 NGỮ CẢNH:\n{context}\n\n"
        f"❓ YÊU CẦU: {query}\n"
        "Hãy trả về CHỈ JSON theo định dạng chuẩn:"
        "{\n"
        "  \"use_cases\": [],\n"
        "  \"user_stories\": [],\n"
        "  \"acceptance_criteria\": []\n"
        "}"
    )

# ── Endpoints: Chat ────────────────────────────────────────
@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat_endpoint(request: ChatRequest):
    try:
        docs, score_map, context, used_wiki = rag_retrieve(request)
        history_text = trim_history(request.history)
        prompt = build_prompt(context, history_text, request.query)
        response = call_llm_with_retry(llm, [HumanMessage(content=prompt)])
        answer = extract_text(response)
        sources = build_sources(docs, score_map, used_wiki)

        follow_up_resp = call_llm_with_retry(llm, [HumanMessage(content=(
            "Sinh đúng 3 câu hỏi ngắn (dưới 15 chữ) để gợi ý người dùng đào sâu thêm. "
            "Mỗi câu bắt đầu bằng (-).\n\n"
            f"Ngữ cảnh: {context[:800]}\nCâu trả lời: {answer[:400]}"
        ))])
        follow_ups = [q.strip("- \n*") for q in extract_text(follow_up_resp).split("\n") if q.strip()][:3]

        if request.session_id:
            await save_message(request.session_id, "user", request.query)
            await save_message(request.session_id, "assistant", answer, [s.dict() for s in sources])

        return ChatResponse(answer=answer, sources=sources, follow_up_questions=follow_ups)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream", dependencies=[Depends(verify_api_key)])
async def stream_chat_endpoint(request: ChatRequest):
    try:
        docs, score_map, context, used_wiki = rag_retrieve(request)
        history_text = trim_history(request.history)
        prompt = build_prompt(context, history_text, request.query)
        sources_dict = [s.dict() for s in build_sources(docs, score_map, used_wiki)]

        async def generate():
            full_answer = ""
            try:
                async for chunk in llm.astream([HumanMessage(content=prompt)]):
                    text = extract_text(chunk) if hasattr(chunk, "content") else str(chunk)
                    if text:
                        full_answer += text
                        yield f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                return

            try:
                fu_resp = await call_llm_async(llm, [HumanMessage(content=(
                    "Sinh đúng 3 câu hỏi ngắn (dưới 15 chữ) gợi ý người dùng. Mỗi câu bắt đầu (-).\n"
                    f"Ngữ cảnh: {context[:800]}\nTrả lời: {full_answer[:400]}"
                ))])
                follow_ups = [q.strip("- \n*") for q in extract_text(fu_resp).split("\n") if q.strip()][:3]
            except:
                follow_ups = []

            if request.session_id:
                await save_message(request.session_id, "user", request.query)
                await save_message(request.session_id, "assistant", full_answer, sources_dict)

            yield f"data: {json.dumps({'type': 'metadata', 'sources': sources_dict, 'follow_up_questions': follow_ups})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Endpoints: Upload & Papers ─────────────────────────────
@app.post("/api/upload", dependencies=[Depends(verify_api_key)])
async def upload_file(file: UploadFile = File(...)):
    global vectorstore_cache
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF.")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    try:
        # Trích xuất metadata
        meta = extract_pdf_metadata(file_path)
        loader = UnstructuredFileLoader(file_path)
        docs = loader.load()
        # Section-aware chunking
        chunks = section_aware_split(docs, chunk_size=1200, chunk_overlap=150)
        for chunk in chunks:
            chunk.metadata["source_filename"] = file.filename
            chunk.metadata["title"] = meta["title"]
            chunk.metadata["authors"] = meta["authors"]
            chunk.metadata["year"] = meta["year"]
        if vectorstore_cache is None:
            vectorstore_cache = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
        vectorstore_cache.add_documents(chunks)
        refresh_bm25()
        return {"message": f"Upload thành công '{file.filename}' ({len(chunks)} chunks).", "metadata": meta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/papers", dependencies=[Depends(verify_api_key)])
async def list_papers():
    if not os.path.exists(UPLOAD_DIR):
        return {"papers": []}
    papers = []
    for fname in os.listdir(UPLOAD_DIR):
        if fname.lower().endswith(".pdf"):
            fpath = os.path.join(UPLOAD_DIR, fname)
            size = os.path.getsize(fpath)
            papers.append({"filename": fname, "title": fname.replace(".pdf", "").replace("_", " "), "size_kb": round(size / 1024, 1)})
    return {"papers": papers}

@app.delete("/api/papers/{filename}", dependencies=[Depends(verify_api_key)])
async def delete_paper(filename: str):
    global vectorstore_cache
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' không tồn tại.")
    try:
        os.remove(file_path)
        if vectorstore_cache:
            all_data = vectorstore_cache.get()
            ids_to_delete = [
                id_ for id_, meta in zip(all_data["ids"], all_data["metadatas"])
                if meta.get("source_filename") == filename
            ]
            if ids_to_delete:
                vectorstore_cache.delete(ids=ids_to_delete)
            refresh_bm25()
        return {"message": f"Đã xoá '{filename}' và {len(ids_to_delete) if vectorstore_cache else 0} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Endpoints: Sessions ────────────────────────────────────
@app.post("/api/sessions", dependencies=[Depends(verify_api_key)])
async def create_new_session(body: SessionCreate):
    session_id = str(uuid.uuid4())
    await create_session(session_id, body.title)
    return {"session_id": session_id, "title": body.title}

@app.get("/api/sessions", dependencies=[Depends(verify_api_key)])
async def get_sessions():
    sessions = await list_sessions()
    return {"sessions": sessions}

@app.get("/api/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
async def get_session(session_id: str):
    msgs = await get_session_messages(session_id)
    return {"session_id": session_id, "messages": msgs}

@app.delete("/api/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
async def remove_session(session_id: str):
    await delete_session(session_id)
    return {"message": f"Đã xoá session {session_id}"}

@app.patch("/api/sessions/{session_id}", dependencies=[Depends(verify_api_key)])
async def update_session_title(session_id: str, body: SessionCreate):
    await rename_session(session_id, body.title)
    return {"message": "Đã cập nhật tiêu đề session."}

# ── Health check (public) ──────────────────────────────────
@app.get("/health")
async def health():
    chunks = 0
    if vectorstore_cache:
        try:
            chunks = len(vectorstore_cache.get()["ids"])
        except:
            pass
    return {"status": "ok", "chunks_loaded": chunks}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
