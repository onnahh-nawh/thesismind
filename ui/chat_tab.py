import streamlit as st

from core.storage import clear_chat_history, save_chat_message
from graph import run_chat


def render_chat_tab():
    if not st.session_state.get("pdf_loaded"):
        st.info("Upload PDF skripsi melalui sidebar terlebih dahulu.")
        return

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Tanyakan tentang skripsi..."):
        pdf_id = st.session_state.get("pdf_id", "")

        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        save_chat_message(pdf_id, "user", prompt)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Mencari jawaban..."):
            try:
                result = run_chat(
                    question=prompt,
                    messages=st.session_state.chat_messages,
                    vectorstore=st.session_state.get("vectorstore"),
                    cover_text=st.session_state.get("cover_text", ""),
                    chunks=st.session_state.get("chunks", []),
                )
                answer = result.get("answer", "Maaf, tidak dapat menemukan jawaban.")
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": answer}
                )
                save_chat_message(pdf_id, "assistant", answer)
                with st.chat_message("assistant"):
                    st.markdown(answer)
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                with st.chat_message("assistant"):
                    st.error(error_msg)

        st.rerun()

    if st.session_state.chat_messages:
        st.divider()
        if st.button("Hapus percakapan", type="secondary"):
            pdf_id = st.session_state.get("pdf_id", "")
            if pdf_id:
                clear_chat_history(pdf_id)
            st.session_state.chat_messages = []
            st.rerun()
