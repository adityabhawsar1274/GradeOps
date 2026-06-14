import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Tuple

from app.config import settings


def ensure_upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def parse_rubric(content: str) -> List[Dict[str, Any]]:
    data = json.loads(content)
    if isinstance(data, dict) and "questions" in data:
        return data["questions"]
    if isinstance(data, list):
        return data
    raise ValueError("Invalid rubric format")


def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """Extract text per page. Supports .txt directly; PDFs via OCR."""
    path = Path(pdf_path)
    pages: List[Tuple[int, str]] = []

    # Plain text submissions (manual demo)
    if path.suffix.lower() == ".txt":
        text = path.read_text(encoding="utf-8").strip()
        pages.append((1, text))
        return pages

    try:
        from pdf2image import convert_from_path
        import pytesseract

        images = convert_from_path(pdf_path, dpi=200)
        for idx, image in enumerate(images, start=1):
            text = pytesseract.image_to_string(image)
            pages.append((idx, text.strip()))
    except Exception:
        pages.append((1, f"[OCR placeholder for {path.name}]"))
    return pages


def split_answers_by_rubric(pages: List[Tuple[int, str]], rubric_questions: List[Dict]) -> List[Dict]:
    """Map extracted pages/text to rubric questions (one answer block per question)."""
    combined = "\n".join(text for _, text in pages)
    answers = []
    for q in rubric_questions:
        answers.append(
            {
                "question_id": q["id"],
                "page_number": pages[0][0] if pages else 1,
                "transcription": combined[:2000] if combined else "",
            }
        )
    return answers


def keyword_score(transcription: str, criteria: List[str], max_points: float) -> Tuple[float, str]:
    if not criteria:
        ratio = min(1.0, len(transcription.split()) / 40)
        score = round(max_points * ratio, 2)
        return score, f"Awarded {score}/{max_points} based on answer length and completeness."

    hits = []
    lower = transcription.lower()
    for c in criteria:
        tokens = [t for t in re.split(r"\W+", c.lower()) if len(t) > 3]
        if tokens and all(t in lower for t in tokens[:2]):
            hits.append(c)

    ratio = len(hits) / len(criteria) if criteria else 0
    score = round(max_points * ratio, 2)
    justification = (
        f"Matched {len(hits)}/{len(criteria)} rubric criteria: "
        + ("; ".join(hits) if hits else "none matched")
        + f". Partial credit {score}/{max_points}."
    )
    return score, justification


def compute_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def detect_plagiarism_pairs(answers: List[Dict], threshold: float = 0.82) -> List[Dict]:
    flags = []
    for i in range(len(answers)):
        for j in range(i + 1, len(answers)):
            if answers[i]["question_id"] != answers[j]["question_id"]:
                continue
            sim = compute_similarity(answers[i]["transcription"], answers[j]["transcription"])
            if sim >= threshold:
                flags.append(
                    {
                        "answer_index_a": i,
                        "answer_index_b": j,
                        "similarity_score": round(sim, 3),
                        "reason": "Highly similar logic structure detected across submissions.",
                    }
                )
    return flags
