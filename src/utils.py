"""Shared utility helpers for inference and evaluation."""

from __future__ import annotations

import re

_THINK_RE = re.compile(r"^<think>\n?(.*?)\n?</think>\n\n(.+)", re.DOTALL)


def strip_thinking(response: str) -> tuple[str | None, str]:
    """Separate thinking and answer from a response.

    Returns (thinking_text, answer_text). If no <think> tags found,
    returns (None, original_response).
    """
    m = _THINK_RE.match(response)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, response.strip()


def get_stopping_token_ids(tokenizer) -> list[int] | int:
    """Return token IDs that should stop generation.

    Gemma 3 uses ``<end_of_turn>`` as the turn delimiter, but its ID
    differs from ``eos_token_id``.  If the tokenizer knows about
    ``<end_of_turn>`` we return *both* IDs so that ``model.generate``
    stops at whichever comes first.  Otherwise we fall back to the
    plain ``eos_token_id``.
    """
    eos = tokenizer.eos_token_id

    try:
        eot = tokenizer.convert_tokens_to_ids("<end_of_turn>")
    except Exception:
        return eos if eos is not None else 1

    # convert_tokens_to_ids returns the unk_token_id when the token
    # is not in the vocabulary — treat that as "not found".
    unk = getattr(tokenizer, "unk_token_id", None)
    if eot is None or eot == unk:
        return eos if eos is not None else 1

    if eos is None:
        return [eot]

    if eos == eot:
        return eos

    return [eos, eot]
