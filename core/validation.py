"""
Document Validation Agent untuk ThesisMind.

Memeriksa apakah dokumen yang diunggah merupakan skripsi atau bukan
berdasarkan struktur dan konten akademik.
"""

import re
from typing import List, Tuple


# Indikator struktur skripsi
THESIS_INDICATORS = {
    "BAB I": [r"BAB\s+I", r"BAB\s+1"],
    "BAB II": [r"BAB\s+II", r"BAB\s+2"],
    "BAB III": [r"BAB\s+III", r"BAB\s+3"],
    "BAB IV": [r"BAB\s+IV", r"BAB\s+4"],
    "BAB V": [r"BAB\s+V", r"BAB\s+5"],
    "Daftar Pustaka": [r"Daftar\s+Pustaka", r"DAFTAR\s+PUSTAKA"],
    "Abstrak": [r"Abstrak", r"ABSTRAK"],
    "Kata Pengantar": [r"Kata\s+Pengantar", r"KATA\s+PENGANTAR"],
    "Halaman Pengesahan": [r"Pengesahan", r"PENGESAHAN"],
}

# Indikator dokumen non-skripsi
NON_THESIS_INDICATORS = {
    "Jurnal": [r"Jurnal", r"Vol\.\s*\d+", r"No\.\s*\d+", r"ISSN"],
    "Proposal": [r"Proposal", r"Rencana\s+Penelitian", r"Latar\s+Belakang\s+Masalah"],
    "Buku": [r"Bab\s+\d+", r"Penerbit", r"ISBN"],
    "Laporan KP": [r"Laporan\s+Kerja\s+Praktik", r"Laporan\s+PKL", r"Laporan\s+Magang"],
    "Modul": [r"Modul\s+Praktikum", r"Modul\s+Ajar", r"Bahan\s+Ajar"],
}


def scan_text(text: str, patterns: List[str]) -> bool:
    """Cari pola dalam teks, return True jika minimal satu cocok."""
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def detect_non_thesis_type(text: str) -> Tuple[str, int]:
    """Deteksi jenis dokumen non-skripsi.

    Returns:
        Tuple (jenis_dokumen, jumlah_indikator_cocok)
    """
    best_type = "Tidak Diketahui"
    best_count = 0

    for doc_type, patterns in NON_THESIS_INDICATORS.items():
        count = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
        if count > best_count:
            best_count = count
            best_type = doc_type

    return best_type, best_count


def validate_document(full_text: str) -> dict:
    """Validasi apakah dokumen adalah skripsi.

    Args:
        full_text: Teks lengkap dokumen

    Returns:
        dict dengan keys: jenis_dokumen, keyakinan, alasan, status, pesan
    """
    reasons = []
    thesis_matches = 0
    total_indicators = len(THESIS_INDICATORS)

    for name, patterns in THESIS_INDICATORS.items():
        if scan_text(full_text, patterns):
            thesis_matches += 1
            reasons.append(f"Ditemukan: {name}")
        else:
            reasons.append(f"Tidak ditemukan: {name}")

    non_thesis_type, non_thesis_count = detect_non_thesis_type(full_text)

    # Hitung keyakinan
    confidence = int((thesis_matches / total_indicators) * 100)

    # Klasifikasi
    if thesis_matches >= 5:
        doc_type = "Skripsi"
    elif non_thesis_type != "Tidak Diketahui" and non_thesis_count > 0:
        doc_type = non_thesis_type
    elif thesis_matches >= 3:
        doc_type = "Skripsi"
    else:
        doc_type = "Tidak Diketahui"

    # Status
    if doc_type == "Skripsi" and confidence >= 60:
        status = "VALID"
        message = ""
    elif doc_type == "Skripsi" and confidence >= 40:
        status = "WARNING"
        message = (
            "Dokumen tidak terdeteksi sebagai skripsi. "
            "Beberapa fitur seperti Analisis Kelemahan, Pertanyaan Sidang, "
            "dan Research Gap mungkin tidak menghasilkan hasil yang optimal."
        )
    else:
        status = "REJECT"
        message = (
            "ThesisMind dirancang khusus untuk analisis skripsi. "
            "Silakan unggah dokumen skripsi yang valid."
        )

    return {
        "jenis_dokumen": doc_type,
        "keyakinan": confidence,
        "alasan": reasons,
        "status": status,
        "pesan": message,
    }
