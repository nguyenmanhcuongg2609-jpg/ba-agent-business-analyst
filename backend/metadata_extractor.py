"""
metadata_extractor.py — Trích xuất metadata (title, authors, year) từ PDF
Ưu tiên: 1) PDF metadata sẵn có  2) Phân tích text trang đầu bằng regex
"""
import re
from pypdf import PdfReader


def extract_pdf_metadata(file_path: str) -> dict:
    """
    Trả về dict: { title, authors, year }
    """
    meta = {"title": "", "authors": "", "year": ""}

    try:
        reader = PdfReader(file_path)

        # --- 1. Lấy từ PDF metadata ---
        info = reader.metadata or {}
        raw_title = info.get("/Title", "") or ""
        raw_author = info.get("/Author", "") or ""
        raw_date = info.get("/CreationDate", "") or ""

        if raw_title.strip():
            meta["title"] = raw_title.strip()
        if raw_author.strip():
            meta["authors"] = raw_author.strip()

        # Parse năm từ PDF date string (D:20230512...)
        year_match = re.search(r"D:(\d{4})", raw_date)
        if year_match:
            meta["year"] = year_match.group(1)

        # --- 2. Dùng text trang đầu nếu metadata trống ---
        if not meta["title"] or not meta["authors"]:
            first_page_text = ""
            if reader.pages:
                first_page_text = reader.pages[0].extract_text() or ""

            lines = [l.strip() for l in first_page_text.split("\n") if l.strip()]

            # Tìm title: dòng dài nhất trong 5 dòng đầu (heuristic)
            if not meta["title"] and lines:
                candidates = sorted(lines[:8], key=len, reverse=True)
                meta["title"] = candidates[0] if candidates else lines[0]

            # Tìm year: 4 chữ số 19xx hoặc 20xx
            if not meta["year"]:
                year_m = re.search(r"\b(19|20)\d{2}\b", first_page_text)
                if year_m:
                    meta["year"] = year_m.group(0)

            # Tìm authors: dòng có "," hoặc "and" ở gần đầu
            if not meta["authors"] and len(lines) > 1:
                for line in lines[1:6]:
                    if "," in line or " and " in line.lower():
                        # Bỏ qua dòng quá dài (không phải tên người)
                        if len(line) < 200:
                            meta["authors"] = line
                            break

    except Exception as e:
        print(f"⚠️ metadata_extractor lỗi: {e}")

    # Fallback
    if not meta["title"]:
        meta["title"] = "Unknown Title"
    if not meta["authors"]:
        meta["authors"] = "Unknown Authors"
    if not meta["year"]:
        meta["year"] = "Unknown"

    return meta


def detect_section(text: str) -> str:
    """
    Phát hiện heading section từ text chunk.
    Trả về tên section hoặc 'Body'.
    """
    patterns = [
        (r"\babstract\b", "Abstract"),
        (r"\bintroduction\b", "Introduction"),
        (r"\brelated work\b|\bliterature review\b", "Related Work"),
        (r"\bmethod(ology|s)?\b|\bapproach\b|\bproposed\b", "Methods"),
        (r"\bexperiment(s|al)?\b|\bsetup\b|\bimplementation\b", "Experiments"),
        (r"\bresult(s)?\b|\bevaluation\b|\bperformance\b", "Results"),
        (r"\bdiscussion\b", "Discussion"),
        (r"\bconclusion\b|\bfuture work\b|\bsummary\b", "Conclusion"),
        (r"\breference(s)?\b|\bbibliograph", "References"),
    ]
    text_lower = text[:500].lower()
    for pattern, section_name in patterns:
        if re.search(pattern, text_lower):
            return section_name
    return "Body"


def section_aware_split(docs: list, chunk_size: int = 1200, chunk_overlap: int = 150) -> list:
    """
    Chia tài liệu theo section trước, sau đó chunk theo ký tự.
    Mỗi chunk được gán metadata section_heading.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    section_headers = [
        "Abstract", "Introduction", "Related Work", "Literature Review",
        "Method", "Approach", "Experiment", "Results", "Evaluation",
        "Discussion", "Conclusion", "References", "Acknowledgment"
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    result_chunks = []
    for doc in docs:
        chunks = splitter.split_documents([doc])
        for chunk in chunks:
            section = detect_section(chunk.page_content)
            chunk.metadata["section_heading"] = section
        result_chunks.extend(chunks)

    return result_chunks
