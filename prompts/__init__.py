from langchain_core.prompts import PromptTemplate

_INSTRUCTION = "JANGAN gunakan kalimat pembuka apapun. Langsung ke konten yang diminta."

INFORMATION_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=f"""{_INSTRUCTION}

Berdasarkan teks skripsi berikut, ekstrak informasi berikut:

📄 Informasi Skripsi
- Judul:
- Penulis:
- Tahun:
- Metode:
- Bidang:

Jika tidak ditemukan, tulis "Tidak disebutkan".

Teks Skripsi:
{{context}}

Informasi Skripsi:
""",
)

SUMMARY_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=f"""{_INSTRUCTION}

Berdasarkan teks skripsi berikut, buat ringkasan dengan struktur:

📝 Ringkasan Eksekutif
- Latar Belakang:
- Tujuan:
- Metodologi:
- Hasil:
- Kesimpulan:

Maksimal 5 kalimat. Gunakan bullet point.

Teks Skripsi:
{{context}}

Ringkasan Eksekutif:
""",
)

EXAMINER_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=f"""{_INSTRUCTION}

Buat 5 pertanyaan sidang beserta jawaban singkatnya berdasarkan teks skripsi berikut.
Pilih pertanyaan yang paling kritis dan sering ditanyakan:

🎓 Pertanyaan Sidang
1. Pertanyaan:
   Jawaban:
2. Pertanyaan:
   Jawaban:
3. Pertanyaan:
   Jawaban:
4. Pertanyaan:
   Jawaban:
5. Pertanyaan:
   Jawaban:

Teks Skripsi:
{{context}}

Pertanyaan Sidang:
""",
)

WEAKNESS_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=f"""{_INSTRUCTION}

Berdasarkan teks skripsi berikut, analisis maksimal 5 kelemahan utama penelitian.
Untuk setiap kelemahan gunakan format:

⚠️ Kelemahan Utama
1. Kelemahan:
   Dampak:
   Saran:

Teks Skripsi:
{{context}}

Kelemahan Utama:
""",
)

LITERATURE_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=f"""{_INSTRUCTION}

Berdasarkan teks skripsi berikut, buat analisis dalam Bahasa Indonesia:

📚 Research Gap & Kontribusi
- Penelitian Sebelumnya:
- Kontribusi Penelitian:
- Kontribusi Praktis:

Teks Skripsi:
{{context}}

Research Gap & Kontribusi:
""",
)

CONCLUSION_PROMPT = PromptTemplate(
    input_variables=["context", "information", "summary", "examiner", "weakness", "literature"],
    template=f"""{_INSTRUCTION}

Berdasarkan hasil analisis berikut, buat kesimpulan dalam Bahasa Indonesia:

📋 Kesimpulan Akhir
- Kelayakan:
- Kualitas Penelitian:
- Potensi Pengembangan:

Informasi Skripsi:
{{information}}

Ringkasan:
{{summary}}

Pertanyaan Sidang:
{{examiner}}

Kelemahan:
{{weakness}}

Research Gap:
{{literature}}

Kesimpulan Akhir:
""",
)

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question", "chat_history", "sources"],
    template=f"""{_INSTRUCTION}

Jawab pertanyaan berdasarkan konteks skripsi di bawah.
Kutip teks asli dari konteks jika diminta.

Konteks dari skripsi:
{{context}}

Riwayat percakapan sebelumnya:
{{chat_history}}

Pertanyaan: {{question}}

Sumber yang tersedia:
{{sources}}

Jawaban:

Sumber:
""",
)
