from core import get_llm
from prompts import (
    CONCLUSION_PROMPT,
    EXAMINER_PROMPT,
    INFORMATION_PROMPT,
    LITERATURE_PROMPT,
    QA_PROMPT,
    SUMMARY_PROMPT,
    WEAKNESS_PROMPT,
)

CONTEXT_LARGE = 100000
CONTEXT_SMALL = 50000


def _run_agent(prompt, **inputs):
    llm = get_llm()
    return (prompt | llm).invoke(inputs).content


def information_agent(context: str) -> str:
    return _run_agent(INFORMATION_PROMPT, context=context[:CONTEXT_SMALL])


def summary_agent(context: str) -> str:
    return _run_agent(SUMMARY_PROMPT, context=context[:CONTEXT_LARGE])


def examiner_agent(context: str) -> str:
    return _run_agent(EXAMINER_PROMPT, context=context[:CONTEXT_LARGE])


def weakness_agent(context: str) -> str:
    return _run_agent(WEAKNESS_PROMPT, context=context[:CONTEXT_LARGE])


def literature_agent(context: str) -> str:
    return _run_agent(LITERATURE_PROMPT, context=context[:CONTEXT_LARGE])


def conclusion_agent(
    context: str,
    information: str,
    summary: str,
    examiner: str,
    weakness: str,
    literature: str,
) -> str:
    return _run_agent(
        CONCLUSION_PROMPT,
        context=context[:CONTEXT_SMALL],
        information=information,
        summary=summary,
        examiner=examiner,
        weakness=weakness,
        literature=literature,
    )


def qa_agent(question: str, context: str, chat_history: str, sources: str = "") -> str:
    return _run_agent(
        QA_PROMPT,
        question=question,
        context=context,
        chat_history=chat_history,
        sources=sources,
    )
