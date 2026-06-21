import streamlit as st

from core import process_uploaded_pdf
from core.storage import (
    get_pdf_id,
    get_stored_pdfs,
    load_chat_history,
    load_chunks,
    load_text,
    load_vectorstore,
    pdf_exists,
    get_pdf_metadata,
    save_chunks,
    save_pdf_metadata,
    save_text,
    save_vectorstore,
)
from core.validation import validate_document


def _set_pdf_session(pdf_id, vectorstore, full_text, cover_text, chunks, filename, pages):
    st.session_state.pdf_id = pdf_id
    st.session_state.vectorstore = vectorstore
    st.session_state.full_text = full_text
    st.session_state.cover_text = cover_text
    st.session_state.chunks = chunks
    st.session_state.pdf_name = filename
    st.session_state.pdf_pages = pages
    st.session_state.pdf_loaded = True
    st.session_state.analysis_result = None
    st.session_state.chat_messages = load_chat_history(pdf_id)
    st.session_state.validation_result = validate_document(full_text)


def _load_pdf_from_storage(pdf_id):
    vectorstore = load_vectorstore(pdf_id)
    full_text = load_text(pdf_id, "full")
    cover_text = load_text(pdf_id, "cover")
    chunks = load_chunks(pdf_id)
    metadata = get_pdf_metadata(pdf_id)

    if vectorstore is None or metadata is None:
        st.error("Gagal memuat PDF dari penyimpanan.")
        return

    _set_pdf_session(
        pdf_id=pdf_id,
        vectorstore=vectorstore,
        full_text=full_text,
        cover_text=cover_text,
        chunks=chunks,
        filename=metadata["filename"],
        pages=metadata["pages"],
    )


def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="display: flex; align-items: center; gap: 0.5rem; '
            "margin-bottom: 2rem;\">"
            '<div style="width: 36px; height: 36px; background: linear-gradient(135deg, #8B5CF6, #7C3AED); '
            "border-radius: 10px; display: flex; align-items: center; justify-content: center; "
            'font-family: Plus Jakarta Sans; font-weight: 800; font-size: 1rem; color: white;">T</div>'
            '<div style="font-family: Plus Jakarta Sans; font-weight: 800; font-size: 1.2rem; '
            "color: #111827; letter-spacing: -0.03em;\">"
            '<span style="color: #8B5CF6;">Thesis</span>Mind</div>'
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="sidebar-section-title">Upload PDF</div>',
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Upload PDF Skripsi", type=["pdf"], label_visibility="collapsed"
        )

        if uploaded_file is not None:
            if uploaded_file.name != st.session_state.get("pdf_name", ""):
                st.session_state.analysis_result = None

            pdf_id = get_pdf_id(uploaded_file.getvalue())

            if pdf_exists(pdf_id):
                st.info("PDF sudah pernah diproses. Memuat dari penyimpanan...")
                _load_pdf_from_storage(pdf_id)
            else:
                with st.spinner("Memproses PDF..."):
                    try:
                        documents, vectorstore, full_text, cover_text, chunks = process_uploaded_pdf(
                            uploaded_file
                        )

                        save_vectorstore(vectorstore, pdf_id)
                        save_chunks(pdf_id, chunks)
                        save_text(pdf_id, "full", full_text)
                        save_text(pdf_id, "cover", cover_text)
                        save_pdf_metadata(
                            pdf_id, uploaded_file.name, len(documents), len(full_text)
                        )

                        _set_pdf_session(
                            pdf_id=pdf_id,
                            vectorstore=vectorstore,
                            full_text=full_text,
                            cover_text=cover_text,
                            chunks=chunks,
                            filename=uploaded_file.name,
                            pages=len(documents),
                        )

                        st.success(
                            f"PDF berhasil dimuat\n\n{uploaded_file.name}\n\n"
                            f"{len(documents)} halaman · {len(full_text):,} karakter"
                        )

                        validation = st.session_state.validation_result
                        if validation["status"] == "VALID":
                            st.markdown(
                                f'<div style="background: #F0FDF4; border: 1px solid #BBF7D0; '
                                f'border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.5rem;">'
                                f'<div style="color: #166534; font-weight: 600; font-size: 0.875rem;">'
                                f"{validation['jenis_dokumen']} terdeteksi</div>"
                                f'<div style="color: #6B7280; font-size: 0.8rem; margin-top: 0.15rem;">'
                                f"Keyakinan: {validation['keyakinan']}%</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        elif validation["status"] == "WARNING":
                            st.markdown(
                                f'<div style="background: #FFFBEB; border: 1px solid #FDE68A; '
                                f'border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.5rem;">'
                                f'<div style="color: #92400E; font-weight: 600; font-size: 0.875rem;">'
                                f"Terdeteksi: {validation['jenis_dokumen']}</div>"
                                f'<div style="color: #92400E; font-size: 0.8rem; margin-top: 0.15rem;">'
                                f"{validation['pesan']}</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                f'<div style="background: #FEF2F2; border: 1px solid #FECACA; '
                                f'border-radius: 10px; padding: 0.75rem 1rem; margin-top: 0.5rem;">'
                                f'<div style="color: #991B1B; font-weight: 600; font-size: 0.875rem;">'
                                f"Dokumen tidak dikenali</div>"
                                f'<div style="color: #991B1B; font-size: 0.8rem; margin-top: 0.15rem;">'
                                f"{validation['pesan']}</div>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

                    except Exception as e:
                        st.error(f"Gagal memproses PDF: {str(e)}")
                        st.session_state.pdf_loaded = False
        else:
            if st.session_state.get("pdf_loaded"):
                st.success(
                    f"PDF siap digunakan\n\n{st.session_state.pdf_name}\n\n"
                    f"{st.session_state.pdf_pages} halaman · "
                    f"{len(st.session_state.full_text):,} karakter"
                )
            else:
                st.markdown(
                    '<div style="border: 2px dashed #C4B5FD; border-radius: 12px; '
                    "padding: 1.25rem 1rem; text-align: center; "
                    'background: #F5F3FF; margin-top: 0.5rem;">'
                    '<div style="font-family: Plus Jakarta Sans; font-weight: 600; '
                    'font-size: 0.9rem; color: #7C3AED; margin-bottom: 0.25rem;">'
                    "Pilih file PDF</div>"
                    '<div style="color: #8B5CF6; font-size: 0.8rem;">'
                    "Klik tombol di atas untuk upload skripsi</div>"
                    "</div>",
                    unsafe_allow_html=True,
                )

        st.markdown('<hr style="margin: 1.5rem 0;">', unsafe_allow_html=True)

        stored = get_stored_pdfs()
        if stored:
            st.markdown(
                '<div class="sidebar-section-title">PDF Tersimpan</div>',
                unsafe_allow_html=True,
            )
            for pdf in stored:
                active = pdf["pdf_id"] == st.session_state.get("pdf_id", "")
                btn = st.button(
                    f"{'📄' if active else '📁'} {pdf['filename']} ({pdf['pages']} hlm)",
                    key=f"pdf_{pdf['pdf_id']}",
                    disabled=active,
                    use_container_width=True,
                )
                if btn:
                    _load_pdf_from_storage(pdf["pdf_id"])
                    st.rerun()

        st.markdown('<hr style="margin: 1.5rem 0;">', unsafe_allow_html=True)

        st.markdown(
            '<div class="sidebar-section-title">Informasi</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="custom-card" style="padding: 1rem;">'
            '<div style="font-size: 0.875rem; color: #111827; font-weight: 500;">'
            "ThesisMind</div>"
            '<div style="font-size: 0.75rem; color: #6B7280; margin-top: 0.25rem;">'
            "AI Thesis Companion</div>"
            '<div style="font-size: 0.75rem; color: #9CA3AF; margin-top: 0.5rem;">'
            "NLP UAS Project</div>"
            "</div>",
            unsafe_allow_html=True,
        )
