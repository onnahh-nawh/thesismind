import streamlit as st

from agents import (
    conclusion_agent,
    examiner_agent,
    information_agent,
    literature_agent,
    summary_agent,
    weakness_agent,
)


def _exec_agent(key, fn, result):
    try:
        result[key] = fn()
        return True
    except Exception as e:
        result[key] = "Gagal diproses."
        print(f"[WARN] Agent {key} gagal: {e}")
        return False


def render_analysis_tab():
    if not st.session_state.get("pdf_loaded"):
        st.markdown(
            '<div class="custom-card" style="text-align: center; padding: 3rem 2rem;">'
            '<div style="color: #6B7280; font-size: 1rem; margin-bottom: 0.5rem;">'
            "Belum ada PDF yang dimuat</div>"
            '<p style="color: #9CA3AF; font-size: 0.875rem; margin-bottom: 0;">'
            "Upload PDF skripsi melalui sidebar terlebih dahulu.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    pdf_name = st.session_state.get("pdf_name", "")
    pdf_pages = st.session_state.get("pdf_pages", 0)
    analysis_result = st.session_state.get("analysis_result")

    status_html = (
        '<span class="custom-badge" style="background: #F0FDF4; border-color: #BBF7D0; color: #166534;">'
        "Sudah dianalisis</span>"
        if analysis_result
        else '<span class="custom-badge">Belum dianalisis</span>'
    )

    st.markdown(
        f'<div class="custom-card" style="display: flex; align-items: center; '
        f'justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;">'
        f'<div>'
        f'<div class="custom-card-header" style="margin-bottom: 0.25rem;">{pdf_name}</div>'
        f'<div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">'
        f'<span class="custom-badge">{pdf_pages} halaman</span>'
        f'{status_html}'
        f'</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="custom-card" style="padding: 1rem 1.5rem;">'
        '<div style="font-family: Plus Jakarta Sans; font-weight: 700; font-size: 1rem; '
        'color: #111827;">Analisis Multi-Agent</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    analyze_clicked = st.button(
        "Analisis Skripsi", type="primary", use_container_width=True
    )

    result = None

    if analyze_clicked:
        full_text = st.session_state.full_text
        result = {}

        steps = [
            ("📄 Informasi Skripsi", "information", lambda: information_agent(full_text)),
            ("📝 Ringkasan Eksekutif", "summary", lambda: summary_agent(full_text)),
            ("⚠️ Kelemahan Utama", "weakness", lambda: weakness_agent(full_text)),
            ("🎓 Pertanyaan Sidang", "examiner", lambda: examiner_agent(full_text)),
            ("📚 Research Gap & Kontribusi", "literature", lambda: literature_agent(full_text)),
        ]

        status = st.status("Menganalisis skripsi...", expanded=True)

        for label, key, fn in steps:
            status.update(label=f"⏳ {label}...")
            ok = _exec_agent(key, fn, result)
            with status:
                st.write(f"{'✅' if ok else '❌'} {label}")

        status.update(label="⏳ Kesimpulan Akhir...")
        try:
            result["conclusion"] = conclusion_agent(
                context=full_text,
                information=result.get("information", ""),
                summary=result.get("summary", ""),
                examiner=result.get("examiner", ""),
                weakness=result.get("weakness", ""),
                literature=result.get("literature", ""),
            )
            with status:
                st.write("✅ Kesimpulan Akhir")
            ok = True
        except Exception as e:
            result["conclusion"] = "Gagal diproses."
            with status:
                st.write("❌ Kesimpulan Akhir")
            print(f"[WARN] Agent conclusion gagal: {e}")

        total = len(steps) + 1
        done = sum(1 for k in ["information", "summary", "weakness", "examiner", "literature", "conclusion"] if result.get(k) and result[k] != "Gagal diproses.")

        status.update(
            label=f"✅ Analisis selesai ({done}/{total} berhasil)",
            state="complete",
        )

        result["report"] = "\n\n---\n\n".join(
            result.get(k, "") for k in ["information", "summary", "examiner", "weakness", "literature", "conclusion"]
        )

        st.session_state.analysis_result = result

    if not result:
        result = st.session_state.get("analysis_result")

    if not result:
        st.markdown(
            '<div class="custom-card" style="text-align: center; padding: 2rem;">'
            '<div style="color: #9CA3AF; font-size: 0.875rem;">'
            "Klik tombol Analisis Skripsi untuk memulai.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    tab_ringkasan, tab_kelemahan, tab_sidang, tab_literatur, tab_laporan = st.tabs(
        ["Ringkasan", "Kelemahan", "Pertanyaan Sidang", "Literature Review", "Laporan"]
    )

    def _render_content(content):
        if content and content != "Gagal diproses.":
            st.markdown(content)
        else:
            st.markdown(
                '<div class="custom-card" style="text-align: center; padding: 1.5rem;">'
                '<div style="color: #9CA3AF; font-size: 0.875rem;">Tidak ada data.</div>'
                "</div>",
                unsafe_allow_html=True,
            )

    with tab_ringkasan:
        _render_content(result.get("summary"))

    with tab_kelemahan:
        _render_content(result.get("weakness"))

    with tab_sidang:
        _render_content(result.get("examiner"))

    with tab_literatur:
        _render_content(result.get("literature"))

    with tab_laporan:
        _render_content(result.get("report") or result.get("conclusion"))
