"""Tests for response routing between lookup and general QA modes."""

from __future__ import annotations

from src.constants import GENERAL_QA_SYSTEM_PROMPT, LOOKUP_SYSTEM_PROMPT
from src.response_policy import GENERAL_QA_MODE, LOOKUP_MODE, select_response_mode, select_system_prompt


class TestSelectResponseMode:
    """Tests for question routing."""

    def test_routes_exact_verse_lookup_to_lookup_mode(self):
        question = "創世記第1章第1節的經文是什麼？"
        assert select_response_mode(question) == LOOKUP_MODE

    def test_routes_quoted_source_question_to_lookup_mode(self):
        question = "「起初，上帝創造天地。」這句經文出自聖經哪裏？"
        assert select_response_mode(question) == LOOKUP_MODE

    def test_routes_general_qa_to_general_mode(self):
        question = "請用簡單的話回答：聖經如何看待信心？"
        assert select_response_mode(question) == GENERAL_QA_MODE

    def test_routes_context_explanation_to_general_mode(self):
        question = "創世記第1章第1節的意思是什麼？請先直接回答。"
        assert select_response_mode(question) == GENERAL_QA_MODE


class TestSelectSystemPrompt:
    """Tests for mode-specific prompt selection."""

    def test_lookup_question_uses_lookup_prompt(self):
        prompt = select_system_prompt("請引用約翰福音第3章第16節。")
        assert prompt == LOOKUP_SYSTEM_PROMPT

    def test_general_question_uses_answer_first_prompt(self):
        prompt = select_system_prompt("不要整段貼經文，請解釋聖經如何看待盼望。")
        assert prompt == GENERAL_QA_SYSTEM_PROMPT
