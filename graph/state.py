from typing import Any, List, Optional, TypedDict


class GraphState(TypedDict):
    action: str
    context: str
    cover_text: str
    retrieved_context: str
    information: str
    summary: str
    examiner: str
    weakness: str
    literature: str
    conclusion: str
    report: str
    question: str
    answer: str
    messages: List[dict]
    pdf_path: str
    chunks: List[Any]
    sources: List[str]
    vectorstore: Optional[Any]
