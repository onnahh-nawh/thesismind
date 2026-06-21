"""
Core module for document processing, embedding, and retrieval.

Komponen:
- PyPDFLoader: Membaca PDF halaman per halaman dengan metadata page number
- RecursiveCharacterTextSplitter: Memecah teks jadi chunks dengan overlap
- GoogleGenerativeAIEmbeddings: Membuat vector embedding dari teks
- FAISS: Vector database untuk similarity search
"""

import os
import re
import tempfile
from typing import List, Tuple

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


CHAPTER_PATTERN = re.compile(r'BAB\s+([IVX\d]+)', re.IGNORECASE)

ROMAN_MAP = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI"}

CHAPTER_KEYWORDS = {
    "pendahuluan": "BAB I",
    "latar belakang": "BAB I",
    "tinjauan": "BAB II",
    "kajian": "BAB II",
    "landasan": "BAB II",
    "teori": "BAB II",
    "metode": "BAB III",
    "metodologi": "BAB III",
    "hasil": "BAB IV",
    "pembahasan": "BAB IV",
    "implementasi": "BAB IV",
    "pengujian": "BAB IV",
    "kesimpulan": "BAB V",
    "saran": "BAB V",
    "penutup": "BAB V",
}


def normalize_chapter_num(num: str) -> str:
    """Normalisasi angka bab: 1 -> I, 2 -> II, dst."""
    cleaned = num.upper().strip().rstrip(".:-")
    if cleaned in ROMAN_MAP:
        return ROMAN_MAP[cleaned]
    return cleaned


def extract_chapter_from_question(question: str) -> str | None:
    """Deteksi apakah pertanyaan meminta bab tertentu.

    Contoh: "Apa isi Bab 1?" -> "BAB I"
            "Ringkas Bab II" -> "BAB II"
            "Apa kesimpulannya?" -> "BAB V"
    """
    q = question.lower()
    m = re.search(r'(?:bab|chapter)\s+([IVX\d]+)', q, re.IGNORECASE)
    if m:
        num = normalize_chapter_num(m.group(1))
        return f"BAB {num}"
    for keyword, chapter in CHAPTER_KEYWORDS.items():
        if keyword in q:
            return chapter
    return None


def add_chapter_metadata_to_docs(documents: List[Document], full_text: str = "") -> None:
    """Tambahkan metadata chapter ke setiap dokumen (in-place).

    Hanya mendeteksi heading BAB yang muncul di 200 karakter
    pertama setiap halaman. Halaman yang mengandung referensi
    ke banyak BAB (seperti Daftar Isi) dilewati.
    Halaman setelah heading dianggap bagian dari bab tersebut
    sampai ditemukan heading bab berikutnya.
    """
    current_ch = None
    for doc in documents:
        first_part = doc.page_content[:200].upper()
        m = CHAPTER_PATTERN.search(first_part)
        if m:
            page_upper = doc.page_content.upper()
            bab_matches = CHAPTER_PATTERN.findall(page_upper)
            unique_babs = set(normalize_chapter_num(b) for b in bab_matches)
            if len(unique_babs) <= 2:
                current_ch = f"BAB {normalize_chapter_num(m.group(1))}"
        doc.metadata["chapter"] = current_ch


def get_llm():
    """Inisialisasi LLM via KoboldLLM (OpenAI-compatible)."""
    return ChatOpenAI(
        model="gemini-2.5-flash",
        base_url=os.getenv("BASE_URL_API"),
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.3,
        timeout=120,
        max_retries=2,
    )


def load_pdf(uploaded_file) -> Tuple[List[Document], str]:
    """Load PDF dari uploaded file Streamlit.

    Args:
        uploaded_file: File PDF dari st.file_uploader

    Returns:
        Tuple berisi (list dokumen, path file sementara)
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    loader = PyPDFLoader(tmp_path)
    documents = loader.load()

    return documents, tmp_path


def split_documents(documents: List[Document]) -> List[Document]:
    """Memecah dokumen menjadi chunks dengan RecursiveCharacterTextSplitter.

    Args:
        documents: List dokumen dari PDF loader

    Returns:
        List chunk dokumen dengan metadata page number
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = text_splitter.split_documents(documents)
    return chunks


def create_vectorstore(chunks: List[Document]) -> FAISS:
    """Membuat FAISS vector store dari document chunks.

    GoogleGenerativeAIEmbeddings mengubah teks menjadi vector 768-dimensi
    yang disimpan di FAISS untuk similarity search.

    Args:
        chunks: List chunk dokumen

    Returns:
        FAISS vector store
    """
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore


def format_docs_with_citation(documents: List[Document]) -> str:
    """Format dokumen dengan informasi citation (halaman + bab).

    Setiap chunk menyertakan nomor halaman asal untuk citation.

    Args:
        documents: List dokumen hasil retrieval

    Returns:
        String terformat dengan citation
    """
    formatted = []
    for doc in documents:
        page = doc.metadata.get("page", "N/A")
        chapter = doc.metadata.get("chapter", "-")
        source = doc.metadata.get("source", "Unknown")
        text = doc.page_content.strip()
        formatted.append(
            f"[Halaman {page} | {chapter} dari {source}]\n{text}"
        )
    return "\n\n---\n\n".join(formatted)


def format_chapter_docs(documents: List[Document]) -> tuple[str, list[int]]:
    """Format seluruh chunk dari satu bab untuk konteks LLM.

    Returns:
        Tuple (teks terkumpul, daftar halaman unik)
    """
    pages = set()
    parts = []
    for doc in documents:
        page = doc.metadata.get("page", "N/A")
        pages.add(page)
        parts.append(
            f"[Halaman {page}]\n{doc.page_content.strip()}"
        )
    return "\n\n".join(parts), sorted(pages)


def get_full_text(documents: List[Document]) -> str:
    """Mendapatkan teks lengkap dari semua dokumen.

    Args:
        documents: List dokumen

    Returns:
        String teks lengkap
    """
    return "\n\n".join([doc.page_content for doc in documents])


def extract_cover_text(documents: List[Document], max_chars: int = 1500) -> str:
    """Mengambil teks halaman pertama (cover) sebagai konteks judul.

    Args:
        documents: List dokumen hasil PDF load
        max_chars: Maksimal karakter yang diambil

    Returns:
        Teks cover page
    """
    if not documents:
        return ""
    return documents[0].page_content[:max_chars]


def process_uploaded_pdf(uploaded_file) -> Tuple[List[Document], FAISS, str, str, List[Document]]:
    """Pipeline lengkap: upload -> load -> split -> embed -> vectorstore.

    Args:
        uploaded_file: File PDF dari user

    Returns:
        Tuple berisi (documents, vectorstore, full_text, cover_text, chunks)
    """
    documents, tmp_path = load_pdf(uploaded_file)
    try:
        full_text = get_full_text(documents)

        add_chapter_metadata_to_docs(documents, full_text)

        chunks = split_documents(documents)
        vectorstore = create_vectorstore(chunks)
        cover_text = extract_cover_text(documents)
    finally:
        os.unlink(tmp_path)

    return documents, vectorstore, full_text, cover_text, chunks
