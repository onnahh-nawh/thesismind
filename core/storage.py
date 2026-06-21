import hashlib
import os
import pickle
import sqlite3
import shutil
from datetime import datetime
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

DB_PATH = "data/thesismind.db"
FAISS_DIR = "data/faiss"
TEXTS_DIR = "data/texts"


def get_pdf_id(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()[:12]


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pdfs (
            pdf_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            pages INTEGER DEFAULT 0,
            chars INTEGER DEFAULT 0,
            uploaded_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pdf_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_pdf ON chat_messages(pdf_id)"
    )
    conn.commit()
    conn.close()


def save_pdf_metadata(pdf_id: str, filename: str, pages: int, chars: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR REPLACE INTO pdfs (pdf_id, filename, pages, chars, uploaded_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (pdf_id, filename, pages, chars, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_pdf_metadata(pdf_id: str) -> Optional[dict]:
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT pdf_id, filename, pages, chars, uploaded_at FROM pdfs WHERE pdf_id = ?",
            (pdf_id,),
        ).fetchone()
        conn.close()
        if row:
            return {
                "pdf_id": row[0],
                "filename": row[1],
                "pages": row[2],
                "chars": row[3],
                "uploaded_at": row[4],
            }
    except sqlite3.Error:
        pass
    return None


def get_stored_pdfs() -> list:
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT pdf_id, filename, pages, chars, uploaded_at "
            "FROM pdfs ORDER BY uploaded_at DESC"
        ).fetchall()
        conn.close()
        return [
            {
                "pdf_id": r[0],
                "filename": r[1],
                "pages": r[2],
                "chars": r[3],
                "uploaded_at": r[4],
            }
            for r in rows
        ]
    except sqlite3.Error:
        return []


def save_vectorstore(vectorstore, pdf_id: str):
    path = os.path.join(FAISS_DIR, pdf_id)
    os.makedirs(path, exist_ok=True)
    vectorstore.save_local(path)


def load_vectorstore(pdf_id: str) -> Optional[FAISS]:
    path = os.path.join(FAISS_DIR, pdf_id)
    if not os.path.exists(path):
        return None
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)


def save_chunks(pdf_id: str, chunks: list):
    os.makedirs(TEXTS_DIR, exist_ok=True)
    with open(os.path.join(TEXTS_DIR, f"{pdf_id}_chunks.pkl"), "wb") as f:
        pickle.dump(chunks, f)


def load_chunks(pdf_id: str) -> list:
    path = os.path.join(TEXTS_DIR, f"{pdf_id}_chunks.pkl")
    if not os.path.exists(path):
        return []
    with open(path, "rb") as f:
        return pickle.load(f)


def save_text(pdf_id: str, name: str, content: str):
    os.makedirs(TEXTS_DIR, exist_ok=True)
    with open(os.path.join(TEXTS_DIR, f"{pdf_id}_{name}.txt"), "w", encoding="utf-8") as f:
        f.write(content)


def load_text(pdf_id: str, name: str) -> str:
    path = os.path.join(TEXTS_DIR, f"{pdf_id}_{name}.txt")
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_chat_message(pdf_id: str, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO chat_messages (pdf_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (pdf_id, role, content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def load_chat_history(pdf_id: str) -> list:
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE pdf_id = ? ORDER BY id",
            (pdf_id,),
        ).fetchall()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in rows]
    except sqlite3.Error:
        return []


def pdf_exists(pdf_id: str) -> bool:
    return os.path.exists(os.path.join(FAISS_DIR, pdf_id))


def clear_chat_history(pdf_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM chat_messages WHERE pdf_id = ?", (pdf_id,))
    conn.commit()
    conn.close()


def remove_pdf(pdf_id: str):
    shutil.rmtree(os.path.join(FAISS_DIR, pdf_id), ignore_errors=True)
    for fname in [f"{pdf_id}_full.txt", f"{pdf_id}_cover.txt", f"{pdf_id}_chunks.pkl"]:
        path = os.path.join(TEXTS_DIR, fname)
        if os.path.exists(path):
            os.remove(path)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM pdfs WHERE pdf_id = ?", (pdf_id,))
    conn.execute("DELETE FROM chat_messages WHERE pdf_id = ?", (pdf_id,))
    conn.commit()
    conn.close()
