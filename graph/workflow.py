import os
from langgraph.graph import END, StateGraph

from agents import (
    conclusion_agent,
    examiner_agent,
    information_agent,
    literature_agent,
    qa_agent,
    summary_agent,
    weakness_agent,
)
from core import (
    extract_chapter_from_question,
    format_chapter_docs,
    format_docs_with_citation,
)
from graph.state import GraphState

DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def router_node(state: GraphState) -> dict:
    return {"action": state["action"]}


def route_condition(state: GraphState) -> str:
    if state["action"] == "analyze":
        return "analyze"
    return "chat"


def _safe_agent(fn, key, fallback="Gagal diproses."):
    try:
        return {key: fn()}
    except Exception as e:
        print(f"[WARN] Agent {key} gagal: {e}")
        return {key: fallback}


def information_node(state: GraphState) -> dict:
    return _safe_agent(
        lambda: information_agent(state["context"]), "information"
    )


def summary_node(state: GraphState) -> dict:
    return _safe_agent(
        lambda: summary_agent(state["context"]), "summary"
    )


def examiner_node(state: GraphState) -> dict:
    return _safe_agent(
        lambda: examiner_agent(state["context"]), "examiner"
    )


def weakness_node(state: GraphState) -> dict:
    return _safe_agent(
        lambda: weakness_agent(state["context"]), "weakness"
    )


def literature_node(state: GraphState) -> dict:
    return _safe_agent(
        lambda: literature_agent(state["context"]), "literature"
    )


def conclusion_node(state: GraphState) -> dict:
    return _safe_agent(
        lambda: conclusion_agent(
            context=state["context"],
            information=state.get("information", ""),
            summary=state.get("summary", ""),
            examiner=state.get("examiner", ""),
            weakness=state.get("weakness", ""),
            literature=state.get("literature", ""),
        ),
        "conclusion",
    )


def report_node(state: GraphState) -> dict:
    report = f"""
# THESIS ANALYSIS REPORT

---
{state["information"]}
---
{state["summary"]}
---
{state["examiner"]}
---
{state["weakness"]}
---
{state["literature"]}
---
{state["conclusion"]}
"""
    return {"report": report}


def retrieve_node(state: GraphState) -> dict:
    question = state["question"]
    chapter = extract_chapter_from_question(question)

    if chapter:
        chunks = state.get("chunks") or []
        chapter_chunks = [
            c for c in chunks
            if c.metadata.get("chapter") == chapter
        ]

        if chapter_chunks:
            context, pages = format_chapter_docs(chapter_chunks)
            cover = state.get("cover_text", "")
            if cover:
                context = f"[COVER PAGE]\n{cover}\n\n---\n\n{context}"

            sources = [f"Halaman {p}" for p in pages]

            if DEBUG:
                print(f"[DEBUG] Chapter-aware retrieval: {chapter}")
                for i, c in enumerate(chapter_chunks[:5]):
                    print(
                        f"  Chunk {i+1} | Page: {c.metadata.get('page')} "
                        f"| Chapter: {c.metadata.get('chapter')}"
                    )
                if len(chapter_chunks) > 5:
                    print(f"  ... dan {len(chapter_chunks) - 5} chunk lainnya")

            return {"retrieved_context": context, "sources": sources}

    vectorstore = state.get("vectorstore")
    if vectorstore is None:
        return {
            "retrieved_context": state.get("context", ""),
            "sources": [],
        }

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 15, "fetch_k": 30, "lambda_mult": 0.6},
    )
    docs = retriever.invoke(question)
    retrieved = format_docs_with_citation(docs)

    cover = state.get("cover_text", "")
    if cover:
        retrieved = f"[COVER PAGE]\n{cover}\n\n---\n\n{retrieved}"

    sources = list({
        f"Halaman {d.metadata.get('page', '?')}"
        for d in docs
    })

    if DEBUG:
        print("[DEBUG] FAISS MMR retrieval (k=15, fetch_k=30)")
        for i, d in enumerate(docs):
            print(
                f"  Chunk {i+1} | Page: {d.metadata.get('page')} "
                f"| Chapter: {d.metadata.get('chapter', '-')}"
            )

    return {"retrieved_context": retrieved, "sources": sources}


def qa_node(state: GraphState) -> dict:
    context = state.get("retrieved_context") or state.get("context", "")
    messages = state.get("messages", [])
    sources = state.get("sources", [])

    history_str = "\n".join(
        [f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages[-6:]]
    )

    sources_str = "\n".join(f"- {s}" for s in sources) if sources else ""

    return _safe_agent(
        lambda: qa_agent(
            question=state["question"],
            context=context,
            chat_history=history_str,
            sources=sources_str,
        ),
        "answer",
        fallback="Maaf, terjadi kesalahan saat menjawab pertanyaan.",
    )


def build_workflow() -> StateGraph:
    workflow = StateGraph(GraphState)

    workflow.add_node("router", router_node)
    workflow.add_node("information", information_node)
    workflow.add_node("summary", summary_node)
    workflow.add_node("examiner", examiner_node)
    workflow.add_node("weakness", weakness_node)
    workflow.add_node("literature", literature_node)
    workflow.add_node("conclusion", conclusion_node)
    workflow.add_node("report", report_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("qa", qa_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_condition,
        {"analyze": "information", "chat": "retrieve"},
    )

    workflow.add_edge("information", "summary")
    workflow.add_edge("summary", "examiner")
    workflow.add_edge("examiner", "weakness")
    workflow.add_edge("weakness", "literature")
    workflow.add_edge("literature", "conclusion")
    workflow.add_edge("conclusion", "report")
    workflow.add_edge("report", END)

    workflow.add_edge("retrieve", "qa")
    workflow.add_edge("qa", END)

    return workflow.compile()


def run_analysis(full_text: str, cover_text: str = "") -> dict:
    graph = build_workflow()
    initial_state: GraphState = {
        "action": "analyze",
        "context": full_text,
        "cover_text": cover_text,
        "retrieved_context": "",
        "information": "",
        "summary": "",
        "examiner": "",
        "weakness": "",
        "literature": "",
        "conclusion": "",
        "report": "",
        "question": "",
        "answer": "",
        "messages": [],
        "pdf_path": "",
        "chunks": [],
        "sources": [],
        "vectorstore": None,
    }
    return graph.invoke(initial_state)


def run_chat(
    question: str,
    messages: list,
    vectorstore=None,
    cover_text: str = "",
    chunks: list = None,
) -> dict:
    graph = build_workflow()
    initial_state: GraphState = {
        "action": "chat",
        "context": "",
        "cover_text": cover_text,
        "retrieved_context": "",
        "information": "",
        "summary": "",
        "examiner": "",
        "weakness": "",
        "literature": "",
        "conclusion": "",
        "report": "",
        "question": question,
        "answer": "",
        "messages": messages,
        "pdf_path": "",
        "chunks": chunks or [],
        "sources": [],
        "vectorstore": vectorstore,
    }
    return graph.invoke(initial_state)
