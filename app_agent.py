import streamlit as st
import time
import os
import shutil
import re
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from backend.metadata_extractor import section_aware_split
from agent_workflow import ba_agent  # Import bộ não Agent đã tạo

# Cấu hình đường dẫn lưu trữ
CHROMA_DIR = "./chroma_db_storage"
UPLOAD_DIR = "./uploaded_papers"
os.makedirs(UPLOAD_DIR, exist_ok=True)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")

def extract_paper_metadata(docs):
    from collections import Counter
    meta = {"title": "Unknown", "authors": "Unknown", "year": "Unknown"}
    if not docs: return meta
    lines = [l.strip() for l in docs[0].page_content.split("\n") if l.strip()]
    for line in lines[:8]:
        if 10 < len(line) < 200 and not re.match(r'^\d+$', line):
            meta["title"] = line
            break
    return meta


# Cấu hình trang
st.set_page_config(page_title="BA Agent AI (Pro)", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ Business Analyst Agent (Tool Calling)")
st.caption("Agent tự động lập kế hoạch, chọn Tool (Wikipedia RAG / PDF Search), và xuất ra Requirement / User Story.")

# Khởi tạo lịch sử chat
if "agent_history" not in st.session_state:
    st.session_state.agent_history = []

# Nút xóa lịch sử
if st.button("🗑️ Xóa lịch sử hội thoại"):
    st.session_state.agent_history = []
    st.rerun()

st.markdown("---")

# --- SIDEBAR: QUẢN LÝ FILE VÀ VECTOR DATABASE ---
with st.sidebar:
    st.header("📁 Quản lý Tài liệu PDF")
    uploaded_files = st.file_uploader("Tải lên tài liệu hoặc bài báo nghiên cứu (PDF)", type=["pdf"], accept_multiple_files=True)
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                with st.spinner(f"🔄 Đang phân tích PDF: {uploaded_file.name}..."):
                    try:
                        loader = PyPDFLoader(file_path)
                        docs = loader.load()
                        paper_meta = extract_paper_metadata(docs)
                        chunks = section_aware_split(docs, chunk_size=1200, chunk_overlap=150)
                        
                        # Lấy mẫu đại diện (stratified sampling) thay vì chỉ lấy 20 đoạn đầu
                        # để tránh dính Rate Limit (chờ quá lâu) của tài khoản Free
                        if len(chunks) > 20:
                            step = len(chunks) / 20.0
                            chunks = [chunks[int(i * step)] for i in range(20)]
                            st.warning(f"⚠️ PDF quá dài, hệ thống đã lấy mẫu 20 đoạn đại diện từ toàn bộ tài liệu (tránh lỗi Rate Limit).")
                        
                        for chunk in chunks:
                            chunk.metadata.update({
                                "source_filename": uploaded_file.name,
                                "title": paper_meta.get("title", "Unknown"),
                            })

                        Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=CHROMA_DIR)
                        st.success(f"✅ Đã nạp thành công: {uploaded_file.name} ({len(chunks)} chunks)")
                    except Exception as e:
                        st.error(f"❌ Lỗi xử lý file {uploaded_file.name}: {e}")
                
    st.markdown("---")
    st.subheader("📚 Tài liệu đã nạp (Trong DB)")
    existing_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.pdf')]
    if existing_files:
        for f in existing_files:
            st.markdown(f"- 📄 `{f}`")
    else:
        st.info("Chưa có tài liệu nào trong hệ thống.")

    if st.button("🗑️ Xóa toàn bộ dữ liệu Vector DB"):
        import gc
        gc.collect()
        try:
            if os.path.exists(CHROMA_DIR):
                shutil.rmtree(CHROMA_DIR, ignore_errors=True)
            if os.path.exists(UPLOAD_DIR):
                shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
                os.makedirs(UPLOAD_DIR, exist_ok=True)
            st.success("💥 Đã xóa sạch DB! Hãy F5 reload lại trang.")
        except Exception as e:
            st.error(f"❌ Lỗi: {e}")

# Render lịch sử
for msg in st.session_state.agent_history:
    content = msg.content
    if isinstance(content, list):
        content = "\n".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
        
    if isinstance(msg, HumanMessage):
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(content)
    elif isinstance(msg, AIMessage) and content:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(content)

# Ô nhập liệu
if user_query := st.chat_input("Ví dụ: Tra cứu Wiki khái niệm Scrum và viết 1 User Story..."):
    # 1. Hiển thị câu hỏi của user
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(user_query)
    
    # Lưu vào lịch sử (tạm thời giới hạn lưu 10 tin nhắn gần nhất để tránh tràn Token)
    st.session_state.agent_history.append(HumanMessage(content=user_query))
    if len(st.session_state.agent_history) > 10:
        st.session_state.agent_history = st.session_state.agent_history[-10:]
        
    # 2. Xử lý Agent
    with st.chat_message("assistant", avatar="🤖"):
        # Dùng st.status để làm UI hiển thị các bước "Suy nghĩ" (như ChatGPT)
        status_box = st.status("🧠 Agent đang phân tích yêu cầu và lập kế hoạch...", expanded=True)
        
        try:
            inputs = {"messages": st.session_state.agent_history}
            final_answer = ""
            
            # Chạy Stream để lấy log từng bước của Tool
            for chunk in ba_agent.stream(inputs):
                if "agent" in chunk:
                    agent_msg = chunk["agent"]["messages"][0]
                    # Nếu Agent quyết định dùng tool
                    if agent_msg.tool_calls:
                        for tc in agent_msg.tool_calls:
                            status_box.write(f"🛠️ Đang gọi công cụ: **`{tc['name']}`** với từ khóa: *{tc['args'].get('query', '')}*")
                    
                    # Nếu Agent có câu trả lời cuối cùng
                    if agent_msg.content:
                        if isinstance(agent_msg.content, list):
                            final_answer = "\n".join([b.get("text", "") for b in agent_msg.content if isinstance(b, dict) and "text" in b])
                        else:
                            final_answer = agent_msg.content
                        
                elif "tools" in chunk:
                    # Khi Tool chạy xong và trả về kết quả
                    tool_msg = chunk["tools"]["messages"][0]
                    status_box.write(f"✅ Đã trích xuất được `{len(tool_msg.content)}` ký tự từ **`{tool_msg.name}`**")
            
            status_box.update(label="Hoàn tất quy trình phân tích!", state="complete", expanded=False)
            
            # Hiển thị kết quả cuối cùng ra màn hình
            st.markdown(final_answer)
            st.session_state.agent_history.append(AIMessage(content=final_answer))
            
        except Exception as e:
            status_box.update(label="Đã xảy ra lỗi!", state="error", expanded=True)
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                st.error("⏳ API Key đã hết giới hạn (Quota) trong ngày. Vui lòng thay API Key mới trong file .env và khởi động lại!")
            else:
                st.error(f"Lỗi hệ thống: {e}")

# --- SPRINT 4: EXPORT TO CSV (JIRA/EXCEL FORMAT) ---
import pandas as pd
import re

def extract_ba_artifacts_to_csv(chat_history):
    latest_msg = ""
    for msg in reversed(chat_history):
        if isinstance(msg, AIMessage):
            content = msg.content
            if isinstance(content, list):
                content = "\n".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
            if "User Story" in content and "Acceptance Criteria" in content:
                latest_msg = content
                break
                
    if not latest_msg: return None
    
    # Chia thành các block
    blocks = re.split(r'\n(?=\s*\d+\.\s*(?:Use Case|\*\*Use Case|Yêu cầu|\*\*Yêu cầu|Requirement|\*\*Requirement))', "\n" + latest_msg)
    
    data = []
    for block in blocks:
        if not block.strip(): continue
        
        # Regex cực kỳ linh hoạt bỏ qua mọi loại dấu chấm tròn (◦), gạch đầu dòng, ký tự đặc biệt
        uc = re.search(r'Use Case:?\s*\*?\*?(.*?)(?=\n|$)', block, re.IGNORECASE)
        req = re.search(r'(?:Yêu cầu|Requirement).*?:?\s*\*?\*?(.*?)(?=\n.*User Story)', block, re.IGNORECASE | re.DOTALL)
        us = re.search(r'User Story:?\s*\*?\*?(.*?)(?=\n.*Acceptance Criteria)', block, re.IGNORECASE | re.DOTALL)
        ac = re.search(r'Acceptance Criteria:?\s*\*?\*?(.*)', block, re.IGNORECASE | re.DOTALL)
        
        # Fix: Vẫn lưu vào data ngay cả khi không có Use Case (vì Agent thường bỏ qua)
        if us and ac:
            data.append({
                "Use Case": uc.group(1).strip() if uc else "Chức năng chung",
                "Requirement": req.group(1).strip() if req else "",
                "User Story": us.group(1).strip() if us else "",
                "Acceptance Criteria": ac.group(1).strip() if ac else ""
            })
            
    if data:
        import pandas as pd
        df = pd.DataFrame(data)
        return df.to_csv(index=False).encode('utf-8-sig')
    return None

def export_chat_to_md(chat_history):
    md_content = "# LỊCH SỬ HỘI THOẠI AGENTIC BA\n\n"
    for msg in chat_history:
        role = "🧑 USER" if isinstance(msg, HumanMessage) else "🤖 BA AGENT"
        content = msg.content
        if isinstance(content, list):
            content = "\n".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
        md_content += f"### {role}\n{content}\n\n---\n\n"
    return md_content.encode('utf-8')

st.markdown("---")
st.subheader("💾 LƯU TRỮ KẾT QUẢ")
col1, col2 = st.columns(2)

with col1:
    md_data = export_chat_to_md(st.session_state.agent_history)
    if len(st.session_state.agent_history) > 0:
        st.download_button(
            label="📝 Tải toàn bộ Lịch sử Chat (.md)",
            data=md_data,
            file_name="Chat_History.md",
            mime="text/markdown",
            help="Tải đoạn chat hiện tại để đưa vào báo cáo Anti-hallucination"
        )

with col2:
    csv_data = extract_ba_artifacts_to_csv(st.session_state.agent_history)
    if csv_data:
        st.download_button(
            label="📥 Tải file CSV (Excel / Jira)",
            data=csv_data,
            file_name="BA_User_Stories.csv",
            mime="text/csv"
        )
    else:
        st.caption("*(File CSV chỉ hiện khi Agent có tạo ra User Story)*")
