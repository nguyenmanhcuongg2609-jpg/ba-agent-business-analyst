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

# Import 2 Agent
from agent_workflow import ba_agent
from test_agent import test_agent

# Import hàm export từ utils tập trung
from export_utils import (
    extract_ba_artifacts_to_csv,
    extract_test_artifacts_to_csv,
    export_chat_to_md,
)

# ==========================================
# CẤU HÌNH
# ==========================================
CHROMA_DIR = "./chroma_db_storage"
UPLOAD_DIR = "./uploaded_papers"
os.makedirs(UPLOAD_DIR, exist_ok=True)
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")


def extract_paper_metadata(docs):
    meta = {"title": "Unknown", "authors": "Unknown", "year": "Unknown"}
    if not docs:
        return meta
    lines = [l.strip() for l in docs[0].page_content.split("\n") if l.strip()]
    for line in lines[:8]:
        if 10 < len(line) < 200 and not re.match(r'^\d+$', line):
            meta["title"] = line
            break
    return meta


# ==========================================
# CẤU HÌNH TRANG
# ==========================================
st.set_page_config(page_title="BA & QA Agent AI", page_icon="🤖", layout="wide")

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:

    # --- CHỌN MODE ---
    st.header("⚙️ Chế độ hoạt động")
    mode = st.radio(
        label="Chọn Agent:",
        options=["🧑💼 Business Analyst Mode", "🕵️ Tester / QA Mode"],
        index=0,
        help="BA Mode sinh User Story & Acceptance Criteria. QA Mode sinh Test Case & Test Scenario."
    )
    is_ba_mode = mode.startswith("🧑")
    active_agent = ba_agent if is_ba_mode else test_agent

    st.markdown("---")

    # --- QUẢN LÝ FILE PDF ---
    st.header("📁 Quản lý Tài liệu PDF")
    if is_ba_mode:
        st.caption("Upload BRD, SRS, tài liệu yêu cầu...")
    else:
        st.caption("Upload BRD, SRS, User Story để sinh Test Case...")

    uploaded_files = st.file_uploader(
        "Tải lên tài liệu PDF", type=["pdf"], accept_multiple_files=True
    )

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

                        if len(chunks) > 20:
                            step = len(chunks) / 20.0
                            chunks = [chunks[int(i * step)] for i in range(20)]
                            st.warning("⚠️ PDF quá dài, hệ thống lấy mẫu 20 đoạn đại diện.")

                        for chunk in chunks:
                            chunk.metadata.update({
                                "source_filename": uploaded_file.name,
                                "title": paper_meta.get("title", "Unknown"),
                            })

                        Chroma.from_documents(
                            documents=chunks, embedding=embeddings,
                            persist_directory=CHROMA_DIR
                        )
                        st.success(f"✅ Đã nạp: {uploaded_file.name} ({len(chunks)} chunks)")
                    except Exception as e:
                        st.error(f"❌ Lỗi xử lý file {uploaded_file.name}: {e}")

    st.markdown("---")
    st.subheader("📚 Tài liệu đã nạp")
    existing_files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".pdf")]
    if existing_files:
        for f in existing_files:
            st.markdown(f"- 📄 `{f}`")
    else:
        st.info("Chưa có tài liệu nào.")

    if st.button("🗑️ Xóa toàn bộ Vector DB"):
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


# ==========================================
# TIÊU ĐỀ TRANG (thay đổi theo mode)
# ==========================================
if is_ba_mode:
    st.title("🧑💼 Business Analyst Agent")
    st.caption("Agent tự động sinh Requirement / User Story / Acceptance Criteria từ tài liệu và yêu cầu.")
else:
    st.title("🕵️ QA / Tester Agent")
    st.caption("Agent tự động sinh Test Scenario / Test Case / Pass-Fail Criteria từ tài liệu spec.")

# ==========================================
# SESSION STATE (tách riêng history cho mỗi mode)
# ==========================================
ba_key   = "ba_history"
test_key = "test_history"

if ba_key   not in st.session_state: st.session_state[ba_key]   = []
if test_key not in st.session_state: st.session_state[test_key] = []

history_key = ba_key if is_ba_mode else test_key

if st.button("🗑️ Xóa lịch sử hội thoại"):
    st.session_state[history_key] = []
    st.rerun()

st.markdown("---")

# ==========================================
# RENDER LỊCH SỬ
# ==========================================
for msg in st.session_state[history_key]:
    content = msg.content
    if isinstance(content, list):
        content = "\n".join(
            b.get("text", "") for b in content
            if isinstance(b, dict) and "text" in b
        )
    if isinstance(msg, HumanMessage):
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    elif isinstance(msg, AIMessage) and content:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(content)

# ==========================================
# Ô NHẬP LIỆU
# ==========================================
placeholder = (
    "Ví dụ: Viết User Story cho chức năng Đăng nhập..."
    if is_ba_mode else
    "Ví dụ: Viết Test Case cho chức năng Đăng nhập hệ thống..."
)

if user_query := st.chat_input(placeholder):
    with st.chat_message("user", avatar="👤"):
        st.write(user_query)

    st.session_state[history_key].append(HumanMessage(content=user_query))

    # Giới hạn 10 tin nhắn gần nhất
    if len(st.session_state[history_key]) > 10:
        st.session_state[history_key] = st.session_state[history_key][-10:]

    with st.chat_message("assistant", avatar="🤖"):
        thinking_label = (
            "🧠 BA Agent đang phân tích yêu cầu..."
            if is_ba_mode else
            "🔍 QA Agent đang phân tích và sinh Test Case..."
        )
        status_box = st.status(thinking_label, expanded=True)

        try:
            inputs = {"messages": st.session_state[history_key]}
            final_answer = ""

            for chunk in active_agent.stream(inputs):
                if "agent" in chunk:
                    agent_msg = chunk["agent"]["messages"][0]
                    if agent_msg.tool_calls:
                        for tc in agent_msg.tool_calls:
                            status_box.write(
                                f"🛠️ Đang gọi: **`{tc['name']}`** — *{tc['args'].get('query', '')}*"
                            )
                    if agent_msg.content:
                        if isinstance(agent_msg.content, list):
                            final_answer = "\n".join(
                                b.get("text", "") for b in agent_msg.content
                                if isinstance(b, dict) and "text" in b
                            )
                        else:
                            final_answer = agent_msg.content

                elif "tools" in chunk:
                    tool_msg = chunk["tools"]["messages"][0]
                    status_box.write(
                        f"✅ Đã trích xuất `{len(tool_msg.content)}` ký tự từ **`{tool_msg.name}`**"
                    )

            status_box.update(label="✅ Hoàn tất!", state="complete", expanded=False)
            st.markdown(final_answer)
            st.session_state[history_key].append(AIMessage(content=final_answer))

        except Exception as e:
            status_box.update(label="❌ Đã xảy ra lỗi!", state="error", expanded=True)
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                st.error("⏳ API Key đã hết quota. Vui lòng thay API Key mới trong file .env và khởi động lại!")
            else:
                st.error(f"Lỗi hệ thống: {e}")


# ==========================================
# EXPORT
# ==========================================
st.markdown("---")
st.subheader("💾 Lưu trữ kết quả")
col1, col2 = st.columns(2)

current_history = st.session_state[history_key]
current_mode_label = "BA" if is_ba_mode else "TEST"

with col1:
    if current_history:
        md_data = export_chat_to_md(current_history, mode=current_mode_label)
        st.download_button(
            label="📝 Tải lịch sử Chat (.md)",
            data=md_data,
            file_name=f"Chat_History_{current_mode_label}.md",
            mime="text/markdown",
        )

with col2:
    if is_ba_mode:
        csv_data = extract_ba_artifacts_to_csv(current_history)
        if csv_data:
            st.download_button(
                label="📥 Tải CSV Jira (User Story)",
                data=csv_data,
                file_name="BA_User_Stories.csv",
                mime="text/csv",
            )
        else:
            st.caption("*(CSV xuất hiện khi Agent sinh ra User Story)*")
    else:
        csv_data = extract_test_artifacts_to_csv(current_history)
        if csv_data:
            st.download_button(
                label="📥 Tải CSV TestRail / Xray (Test Case)",
                data=csv_data,
                file_name="Test_Cases.csv",
                mime="text/csv",
            )
        else:
            st.caption("*(CSV xuất hiện khi Agent sinh ra Test Case)*")
