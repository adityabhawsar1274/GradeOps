"""Agentic LLM grading pipeline (LangGraph when available, deterministic fallback otherwise)."""

import json
from typing import Any, Dict, List

from app.config import settings
from app.services.ocr_service import keyword_score


def _grade_with_rubric(question: Dict[str, Any], transcription: str) -> Dict[str, Any]:
    criteria = question.get("criteria", [])
    max_points = float(question.get("max_points", 10))
    score, justification = keyword_score(transcription, criteria, max_points)
    return {
        "ai_score": score,
        "ai_max_score": max_points,
        "ai_justification": justification,
    }


def _llm_refine(question: Dict[str, Any], transcription: str, graded: Dict[str, Any]) -> Dict[str, Any]:
    if settings.use_mock_ai or not settings.openai_api_key:
        graded["ai_justification"] += " [Agent: structured rubric evaluation complete.]"
        return graded

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key, temperature=0)
        prompt = f"""
You are an exam grader. Given rubric and student answer, refine score and write concise justification.

Rubric question: {json.dumps(question)}
Student answer: {transcription}
Current score: {graded['ai_score']}/{graded['ai_max_score']}

Respond JSON: {{"score": number, "justification": "..."}}
"""
        resp = llm.invoke(
            [
                SystemMessage(content="Return valid JSON only."),
                HumanMessage(content=prompt),
            ]
        )
        data = json.loads(resp.content)
        graded["ai_score"] = float(data.get("score", graded["ai_score"]))
        graded["ai_justification"] = str(data.get("justification", graded["ai_justification"]))
    except Exception as exc:
        graded["ai_justification"] += f" [LLM refine skipped: {exc}]"
    return graded


def grade_answer(question: Dict[str, Any], transcription: str) -> Dict[str, Any]:
    """Two-step agentic pipeline: rubric check → optional LLM refine."""
    graded = _grade_with_rubric(question, transcription)
    return _llm_refine(question, transcription, graded)


def grade_batch(questions: List[Dict[str, Any]], transcriptions: List[str]) -> List[Dict[str, Any]]:
    return [grade_answer(q, t) for q, t in zip(questions, transcriptions)]
