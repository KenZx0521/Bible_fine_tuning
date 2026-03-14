"""Tests for src.utils — stopping token helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.utils import get_stopping_token_ids


class TestGetStoppingTokenIds:
    """Tests for get_stopping_token_ids."""

    def test_returns_list_for_gemma3(self):
        """When <end_of_turn> exists and differs from eos, return a list."""
        tok = MagicMock()
        tok.eos_token_id = 1
        tok.unk_token_id = 0
        tok.convert_tokens_to_ids.return_value = 107

        result = get_stopping_token_ids(tok)

        assert isinstance(result, list)
        assert 1 in result
        assert 107 in result
        assert len(result) == 2

    def test_returns_int_when_end_of_turn_missing(self):
        """When <end_of_turn> resolves to unk, fall back to eos_token_id."""
        tok = MagicMock()
        tok.eos_token_id = 1
        tok.unk_token_id = 0
        tok.convert_tokens_to_ids.return_value = 0  # same as unk

        result = get_stopping_token_ids(tok)

        assert result == 1

    def test_handles_tokenizer_exception(self):
        """If convert_tokens_to_ids raises, fall back gracefully."""
        tok = MagicMock()
        tok.eos_token_id = 2
        tok.convert_tokens_to_ids.side_effect = KeyError("not found")

        result = get_stopping_token_ids(tok)

        assert result == 2

    def test_none_eos_token_id(self):
        """If eos_token_id is None and <end_of_turn> exists, return list."""
        tok = MagicMock()
        tok.eos_token_id = None
        tok.unk_token_id = 0
        tok.convert_tokens_to_ids.return_value = 107

        result = get_stopping_token_ids(tok)

        assert isinstance(result, list)
        assert result == [107]

    def test_none_eos_and_no_end_of_turn(self):
        """If both eos and <end_of_turn> are unavailable, return 1."""
        tok = MagicMock()
        tok.eos_token_id = None
        tok.unk_token_id = 0
        tok.convert_tokens_to_ids.return_value = 0  # same as unk

        result = get_stopping_token_ids(tok)

        assert result == 1

    def test_same_eos_and_eot(self):
        """If eos_token_id == end_of_turn_id, return int (not list)."""
        tok = MagicMock()
        tok.eos_token_id = 107
        tok.unk_token_id = 0
        tok.convert_tokens_to_ids.return_value = 107

        result = get_stopping_token_ids(tok)

        assert result == 107
        assert isinstance(result, int)
