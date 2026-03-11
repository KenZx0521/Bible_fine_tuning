"""Response-mode routing for inference and evaluation."""

from __future__ import annotations

import re

from src.constants import GENERAL_QA_SYSTEM_PROMPT, LOOKUP_SYSTEM_PROMPT

GENERAL_QA_MODE = "general_qa"
LOOKUP_MODE = "lookup"

_REFERENCE_PATTERN = re.compile(r"第\s*\d+\s*章(?:第\s*[\d-]+\s*節)?|[1-3]?\s*[A-Za-z\u4e00-\u9fff]{1,10}\s*\d+:\d+")
_QUOTED_TEXT_PATTERN = re.compile(r"[「『].+[」』]")

_GENERAL_HINTS = (
    "不用整段引用",
    "不要整段引用",
    "不用逐字",
    "用白話",
    "簡單說",
    "直接回答",
    "重點是什麼",
    "主要想傳達",
    "提醒我們什麼",
    "怎麼理解",
    "如何理解",
    "怎麼看待",
    "如何看待",
    "意思是什麼",
    "在講什麼",
)

_LOOKUP_HINTS = (
    "經文是什麼",
    "請引用",
    "引用經文",
    "幫我查",
    "查一下",
    "查閱",
    "內容為何",
    "寫了什麼",
    "怎麼說的",
    "記載了什麼",
)

_SOURCE_HINTS = (
    "出自聖經哪裏",
    "出自聖經哪裡",
    "出處",
    "哪一卷",
    "哪卷書",
    "哪一章哪一節",
    "這句經文在哪裏",
    "這句經文在哪裡",
)

_REFERENCE_LIST_HINTS = (
    "有哪些關於",
    "列出",
    "相關經文",
    "哪些地方有提到",
)


def select_response_mode(question: str) -> str:
    """Classify a question into a lookup-heavy or answer-first response mode."""
    q = question.strip()

    if any(hint in q for hint in _GENERAL_HINTS):
        return GENERAL_QA_MODE

    if any(hint in q for hint in _SOURCE_HINTS) and _QUOTED_TEXT_PATTERN.search(q):
        return LOOKUP_MODE

    if any(hint in q for hint in _LOOKUP_HINTS):
        return LOOKUP_MODE

    if any(hint in q for hint in _REFERENCE_LIST_HINTS) and "經文" in q:
        return LOOKUP_MODE

    if _REFERENCE_PATTERN.search(q) and "節" in q:
        if any(hint in q for hint in ("上下文", "前後文", "背景", "脈絡", "意思")):
            return GENERAL_QA_MODE
        return LOOKUP_MODE

    return GENERAL_QA_MODE


def get_system_prompt(mode: str) -> str:
    """Return the system prompt for a given response mode."""
    if mode == LOOKUP_MODE:
        return LOOKUP_SYSTEM_PROMPT
    return GENERAL_QA_SYSTEM_PROMPT


def select_system_prompt(question: str) -> str:
    """Return the best-fit system prompt for a question."""
    return get_system_prompt(select_response_mode(question))
