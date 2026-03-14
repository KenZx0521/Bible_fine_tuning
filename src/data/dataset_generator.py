"""Training sample generators for Bible QA fine-tuning.

Generates 8 types of QA samples (A-H) in TRL SFT messages format:
  A: Verse lookup — query specific verse text (with downsampling)
  B: Section summary — summarize a section (filtered & truncated)
  C: Thematic verses — find verses by topic keyword (multi-faceted)
  D: Context understanding — provide verse context
  E: Verse identification — identify verse source from quote
  F: Refusal — reject out-of-scope or non-existent queries
  G: General Bible QA — answer first, cite as support
  H: Citation-light QA — explicitly avoid quote-dumping
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass

from src.constants import (
    GENERAL_QA_SYSTEM_PROMPT,
    GENERAL_QA_SYSTEM_PROMPT_VARIANTS,
    LOOKUP_SYSTEM_PROMPT_VARIANTS,
)
from src.data.parser import Book, Chapter, Verse
from src.data.templates import (
    TOPIC_KEYWORDS,
    _BOOK_TO_CATEGORY,
    _BOUNDARY_QUESTIONS,
    _CONTEXT_ANSWER_TEMPLATES,
    _CONTEXT_EXPLANATION_TEMPLATES,
    _CONTEXT_TEMPLATES,
    _FAKE_BOOKS,
    _FAKE_QUERY_TEMPLATES,
    _GENERAL_SECTION_ANSWER_TEMPLATES,
    _GENERAL_SECTION_QA_TEMPLATES,
    _GENERAL_TOPIC_ANSWER_TEMPLATES,
    _GENERAL_TOPIC_QA_TEMPLATES,
    _IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION,
    _IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION,
    _IDENTIFICATION_ANSWER_TEMPLATES,
    _IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES,
    _IDENTIFICATION_TEMPLATES,
    _MISSPELLED_BOOKS,
    _NO_QUOTE_ANSWER_TEMPLATES,
    _NO_QUOTE_SECTION_QA_TEMPLATES,
    _NO_QUOTE_TOPIC_QA_TEMPLATES,
    _NON_BIBLE_QUESTIONS_BY_CATEGORY,
    _REFUSAL_MISSPELLED_BOOK,
    _REFUSAL_NON_BIBLE_BY_CATEGORY,
    _REFUSAL_NON_BIBLE_GENERIC,
    _REFUSAL_NONEXISTENT_BOOK,
    _REFUSAL_OUT_OF_RANGE,
    _REFUSAL_OUT_OF_RANGE_VERSE,
    _SECTION_SUMMARY_ANSWER_TEMPLATES,
    _SECTION_SUMMARY_TEMPLATES,
    _TESTAMENT_CATEGORIES,
    _THEMATIC_ANSWER_TEMPLATES,
    _THEMATIC_CATEGORY_ANSWER_TEMPLATES,
    _THEMATIC_CATEGORY_TEMPLATES,
    _THEMATIC_TEMPLATES,
    _THEMATIC_TESTAMENT_ANSWER_TEMPLATES,
    _THEMATIC_TESTAMENT_TEMPLATES,
    _VERSE_ANSWER_EXTENDED_TEMPLATES,
    _VERSE_ANSWER_TEMPLATES,
    _VERSE_QUERY_TEMPLATES,
)

_MIN_SAMPLES_PER_BOOK = 30
_REBALANCE_CAPS = {
    "A": 3500,
    "D": 2200,
    "E": 1800,
}


@dataclass(frozen=True)
class Sample:
    """A single training sample."""

    sample_type: str  # A, B, C, D, E, F, G, H
    messages: tuple[dict[str, str], ...]


def _make_messages(
    question: str,
    answer: str,
    system_prompt: str = GENERAL_QA_SYSTEM_PROMPT,
) -> tuple[dict[str, str], ...]:
    """Create a messages tuple in TRL SFT format."""
    return (
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    )


def _collect_all_verses(books: list[Book]) -> list[Verse]:
    """Flatten all verses from all books."""
    return [
        v
        for book in books
        for chapter in book.chapters
        for section in chapter.sections
        for v in section.verses
    ]


def _build_chapter_verse_list(chapter: Chapter) -> list[Verse]:
    """Get all verses in a chapter in order."""
    return [v for s in chapter.sections for v in s.verses]


def _lookup_prompt(rng: random.Random) -> str:
    """Sample a prompt variant for explicit lookup tasks."""
    return rng.choice(LOOKUP_SYSTEM_PROMPT_VARIANTS)


def _general_prompt(rng: random.Random) -> str:
    """Sample a prompt variant for answer-first QA tasks."""
    return rng.choice(GENERAL_QA_SYSTEM_PROMPT_VARIANTS)


def _make_reference(verse: Verse) -> str:
    """Format a verse reference."""
    return f"{verse.book}第{verse.chapter}章第{verse.verse_number}節"


def _join_references(verses: list[Verse]) -> str:
    """Join verse references into concise Traditional Chinese text."""
    refs = [_make_reference(v) for v in verses]
    if not refs:
        return "相關經文"
    if len(refs) == 1:
        return refs[0]
    return "、".join(refs[:-1]) + "與" + refs[-1]


def _make_snippet(text: str) -> str:
    """Extract a meaningful snippet from verse text for summaries."""
    snippet = _prepare_verse_text(text)
    if len(snippet) > 36:
        for sep in ("。", "；", "，"):
            pos = snippet.find(sep, 14)
            if pos != -1:
                snippet = snippet[: pos + 1]
                break
        else:
            snippet = snippet[:36] + "……"
    return snippet


def _make_support_point(text: str, max_chars: int = 50) -> str:
    """Compress verse text into a meaningful support point for answer-first QA."""
    point = _prepare_verse_text(text)
    for token in ("「", "」", "『", "』", "\n"):
        point = point.replace(token, "")
    point = point.strip("。；，：、 ")
    # Try to find a natural break point after at least 12 chars
    for sep in ("。", "；"):
        pos = point.find(sep, 12)
        if pos != -1 and pos <= max_chars:
            point = point[:pos]
            break
    else:
        # If no sentence break, try comma after 20 chars
        for sep in ("，", "："):
            pos = point.find(sep, 20)
            if pos != -1 and pos <= max_chars:
                point = point[:pos]
                break
    if len(point) > max_chars:
        point = point[:max_chars].rstrip("；，：、 ")
    return point or "這段重點"


def _pick_support_verses(verses: list[Verse], max_picks: int = 3) -> list[Verse]:
    """Pick up to *max_picks* representative verses for concise support.

    Strategy: sort by text length (longer verses tend to be richer),
    then pick the top candidates, preferring spread across the section.
    """
    if not verses:
        return []
    if len(verses) == 1:
        return [verses[0]]
    if len(verses) <= max_picks:
        return list(verses)
    # Sort by text length descending; pick the richest verses
    ranked = sorted(enumerate(verses), key=lambda iv: len(iv[1].text), reverse=True)
    # Take top candidates but keep them in original order
    chosen_indices = sorted(idx for idx, _ in ranked[:max_picks])
    return [verses[i] for i in chosen_indices]


def _support_points(verses: list[Verse]) -> tuple[str, ...]:
    """Build up to three support points from representative verses."""
    supports = _pick_support_verses(verses)
    if not supports:
        return ("這段內容需要回到上下文理解",)

    points = [_make_support_point(v.text) for v in supports]
    return tuple(points)


def _make_reference_span(verses: list[Verse]) -> str:
    """Format a contiguous verse span for a section-level reference."""
    if not verses:
        return "相關段落"

    first = verses[0]
    last = verses[-1]
    if (
        first.book == last.book
        and first.chapter == last.chapter
        and first.verse_number == last.verse_number
    ):
        return _make_reference(first)

    if first.book == last.book and first.chapter == last.chapter:
        return (
            f"{first.book}第{first.chapter}章"
            f"第{first.verse_number}節至第{last.verse_number}節"
        )

    return f"{_make_reference(first)}至{_make_reference(last)}"


_FLOW_PREV_PHRASES = ("前文提到", "前一節記載", "在這之前，經文談到")
_FLOW_CURR_PHRASES = ("本節則說到", "本節的重點是", "這節經文說的是")
_FLOW_NEXT_PHRASES = ("後文又接著", "接下來提到", "下一節則延續到")


def _build_context_flow(
    prev: Verse | None, verse: Verse, nxt: Verse | None,
    rng: random.Random | None = None,
) -> str:
    """Convert surrounding verses into a concise contextual summary."""
    if rng is None:
        rng = random.Random()
    parts = []
    if prev:
        parts.append(f"{rng.choice(_FLOW_PREV_PHRASES)}{_make_snippet(prev.text)}")
    parts.append(f"{rng.choice(_FLOW_CURR_PHRASES)}{_make_snippet(verse.text)}")
    if nxt:
        parts.append(f"{rng.choice(_FLOW_NEXT_PHRASES)}{_make_snippet(nxt.text)}")
    return "；".join(parts) + "。"


_SECTION_SUMMARY_TEXT_TEMPLATES = (
    "核心在於{point1}，並進一步說明{point2}",
    "從{point1}開始，逐步帶出{point2}的主題",
    "主要描述{point1}，其中特別強調{point2}",
    "圍繞{point1}展開，透過{point2}來深化主旨",
    "以{point1}為起點，引導讀者理解{point2}",
    "先談到{point1}，再延伸到{point2}，兩者互相呼應",
    "{point1}是這段的基礎，接著{point2}進一步展開",
    "重點在於{point1}，同時也提到{point2}",
)

_SECTION_SUMMARY_TEXT_TEMPLATES_3 = (
    "核心在於{point1}，並進一步說明{point2}，最終帶出{point3}",
    "從{point1}開始，經過{point2}，最後聚焦在{point3}",
    "主要描述{point1}，其中{point2}和{point3}是兩個重要面向",
    "以{point1}為起點，透過{point2}過渡到{point3}",
    "這段的脈絡是{point1}、{point2}，最終歸結到{point3}",
    "{point1}是基礎，{point2}是展開，{point3}是總結",
)


def _build_section_summary_text(
    section_title: str, verses: list[Verse], rng: random.Random | None = None
) -> str:
    """Build a diverse summary text for a titled section."""
    points = _support_points(verses)
    if len(points) == 1:
        return f"主要圍繞{points[0]}"
    if rng is None:
        rng = random.Random()
    if len(points) >= 3:
        tmpl = rng.choice(_SECTION_SUMMARY_TEXT_TEMPLATES_3)
        return tmpl.format(point1=points[0], point2=points[1], point3=points[2])
    tmpl = rng.choice(_SECTION_SUMMARY_TEXT_TEMPLATES)
    return tmpl.format(point1=points[0], point2=points[1])


_TOPIC_SUMMARY_TEXT_TEMPLATES = (
    "從{point1}和{point2}這些角度來呈現",
    "透過{point1}以及{point2}來傳達核心信息",
    "反覆強調{point1}，同時也指向{point2}",
    "一方面談到{point1}，另一方面也涉及{point2}",
    "以{point1}為核心，延伸出{point2}的教導",
    "{point1}是重要面向，{point2}則是另一個層次的呈現",
    "多處提到{point1}，並且與{point2}相互連結",
    "不同經卷從{point1}和{point2}兩個方向闡述",
)


def _build_topic_summary_text(
    topic: str, verses: list[Verse], rng: random.Random | None = None
) -> str:
    """Build a diverse summary text for a thematic QA sample."""
    points = _support_points(verses)
    if len(points) == 1:
        return f"常用{points[0]}這類內容幫助人理解"
    if rng is None:
        rng = random.Random()
    tmpl = rng.choice(_TOPIC_SUMMARY_TEXT_TEMPLATES)
    return tmpl.format(point1=points[0], point2=points[1])


def _rebalance_samples(samples: list[Sample], seed: int) -> list[Sample]:
    """Downsample retrieval-heavy tasks so answer-first QA is not drowned out."""
    indexed_groups: dict[str, list[tuple[int, Sample]]] = defaultdict(list)
    for idx, sample in enumerate(samples):
        indexed_groups[sample.sample_type].append((idx, sample))

    rng = random.Random(seed + 1000)
    keep_indices: set[int] = set()
    for sample_type, grouped in indexed_groups.items():
        cap = _REBALANCE_CAPS.get(sample_type)
        if cap is None or len(grouped) <= cap:
            keep_indices.update(idx for idx, _ in grouped)
            continue
        chosen = rng.sample(grouped, cap)
        keep_indices.update(idx for idx, _ in chosen)

    return [sample for idx, sample in enumerate(samples) if idx in keep_indices]


# --- Type A: Verse Lookup (with downsampling + book floor) ---


def generate_type_a(books: list[Book], rng: random.Random) -> list[Sample]:
    """Generate verse lookup samples with progressive downsampling.

    v6 changes:
    - More aggressive downsampling: 8%/18%/30% (from 15%/35%/50%)
    - Book floor: each book gets at least _MIN_SAMPLES_PER_BOOK samples
    """
    # Phase 1: Collect eligible verses per book
    eligible_per_book: dict[str, list[Verse]] = {}
    for book in books:
        book_verses = []
        for chapter in book.chapters:
            for section in chapter.sections:
                for v in section.verses:
                    if len(v.text) >= 15:
                        book_verses.append(v)
        if book_verses:
            eligible_per_book[book.name] = book_verses

    # Phase 2: Downsampling
    sampled_per_book: dict[str, list[Verse]] = {}
    for book_name, verses in eligible_per_book.items():
        sampled = []
        for verse in verses:
            text_len = len(verse.text)
            if text_len <= 25 and rng.random() > 0.08:
                continue
            elif 25 < text_len <= 40 and rng.random() > 0.18:
                continue
            elif text_len > 40 and rng.random() > 0.30:
                continue
            sampled.append(verse)
        sampled_per_book[book_name] = sampled

    # Phase 3: Book floor — ensure minimum samples per book
    for book_name, sampled in sampled_per_book.items():
        if len(sampled) < _MIN_SAMPLES_PER_BOOK:
            eligible = eligible_per_book[book_name]
            if len(eligible) <= _MIN_SAMPLES_PER_BOOK:
                sampled_per_book[book_name] = list(eligible)
            else:
                already = set(id(v) for v in sampled)
                remaining = [v for v in eligible if id(v) not in already]
                need = _MIN_SAMPLES_PER_BOOK - len(sampled)
                extra = rng.sample(remaining, min(need, len(remaining)))
                sampled_per_book[book_name] = sampled + extra

    # Phase 4: Generate samples
    samples = []
    for verses in sampled_per_book.values():
        for verse in verses:
            sys_prompt = _lookup_prompt(rng)
            template = rng.choice(_VERSE_QUERY_TEMPLATES)
            question = template.format(
                book=verse.book,
                chapter=verse.chapter,
                verse=verse.verse_number,
            )

            # 60% chance to use extended template (with section context)
            use_extended = (
                verse.section_title
                and rng.random() < 0.60
            )
            if use_extended:
                answer_template = rng.choice(_VERSE_ANSWER_EXTENDED_TEMPLATES)
                answer = answer_template.format(
                    book=verse.book,
                    chapter=verse.chapter,
                    verse=verse.verse_number,
                    text=_prepare_verse_text(verse.text),
                    section_title=verse.section_title,
                )
            else:
                answer_template = rng.choice(_VERSE_ANSWER_TEMPLATES)
                answer = answer_template.format(
                    book=verse.book,
                    chapter=verse.chapter,
                    verse=verse.verse_number,
                    text=_prepare_verse_text(verse.text),
                )
            samples.append(
                Sample(
                    sample_type="A",
                    messages=_make_messages(question, answer, sys_prompt),
                )
            )
    return samples


# --- Type B: Section Summary (filtered & truncated) ---


def generate_type_b(books: list[Book], rng: random.Random) -> list[Sample]:
    """Generate section summary samples.

    Filters:
    - Skip sections with empty title
    - Answer with concise summary + reference span instead of verse dump
    """
    samples = []
    for book in books:
        for chapter in book.chapters:
            for section in chapter.sections:
                if not section.verses:
                    continue
                if not section.title:
                    continue  # Skip empty section titles

                sys_prompt = _general_prompt(rng)
                template = rng.choice(_SECTION_SUMMARY_TEMPLATES)
                question = template.format(
                    book=book.name,
                    chapter=chapter.number,
                    section=section.title,
                )
                answer_template = rng.choice(_SECTION_SUMMARY_ANSWER_TEMPLATES)
                answer = answer_template.format(
                    book=book.name,
                    chapter=chapter.number,
                    section=section.title,
                    summary_text=_build_section_summary_text(
                        section.title, list(section.verses), rng
                    ),
                    reference_span=_make_reference_span(list(section.verses)),
                    key_verse_ref=_make_reference(
                        _pick_support_verses(list(section.verses))[0]
                    ),
                    key_verse_snippet=_make_snippet(
                        _pick_support_verses(list(section.verses))[0].text
                    ),
                )
                samples.append(
                    Sample(
                        sample_type="B",
                        messages=_make_messages(question, answer, sys_prompt),
                    )
                )
    return samples


# --- Type C: Thematic Verses (multi-faceted) ---


def _match_topic(verse_text: str, topic_config: dict) -> bool:
    """Check if a verse matches a topic with include/exclude rules."""
    includes = topic_config["include"]
    excludes = topic_config["exclude"]

    # Must match at least one include keyword
    if not any(kw in verse_text for kw in includes):
        return False

    # Must not match any exclude keyword
    if excludes and any(kw in verse_text for kw in excludes):
        return False

    return True


def _build_topic_index(
    books: list[Book],
) -> dict[str, list[Verse]]:
    """Build an index of verses by topic keyword with exclusion rules."""
    index: dict[str, list[Verse]] = {topic: [] for topic in TOPIC_KEYWORDS}
    for verse in _collect_all_verses(books):
        for topic, config in TOPIC_KEYWORDS.items():
            if _match_topic(verse.text, config):
                index[topic].append(verse)
    return index


def _get_testament_for_category(category: str) -> str | None:
    """Return the testament ('舊約' or '新約') for a book category."""
    for testament, categories in _TESTAMENT_CATEGORIES.items():
        if category in categories:
            return testament
    return None


def generate_type_c(
    books: list[Book], rng: random.Random, verses_per_sample: int = 6
) -> list[Sample]:
    """Generate thematic verse samples with multi-faceted generation.

    For each topic:
    - Group matching verses by book category
    - Generate one sample per category that has enough verses
    - Generate up to 3 overall samples
    - Generate testament-level samples (舊約/新約)
    """
    index = _build_topic_index(books)
    samples = []

    for topic, all_verses in index.items():
        if len(all_verses) < 3:
            continue

        # v7: Track used verses within this topic to avoid overlap
        used_verse_ids: set[int] = set()

        # Group by book category
        category_verses: dict[str, list[Verse]] = {}
        for v in all_verses:
            cat = _BOOK_TO_CATEGORY.get(v.book, "其他")
            category_verses.setdefault(cat, []).append(v)

        # Generate per-category samples (lowered threshold from 2 to 1)
        for cat, cat_verses in category_verses.items():
            if len(cat_verses) < 1:
                continue

            available = [v for v in cat_verses if id(v) not in used_verse_ids]
            if not available:
                continue

            sys_prompt = _lookup_prompt(rng)
            n_show = min(len(available), verses_per_sample)
            selected = rng.sample(available, n_show)
            used_verse_ids.update(id(v) for v in selected)

            template = rng.choice(_THEMATIC_CATEGORY_TEMPLATES)
            question = template.format(category=cat, topic=topic)

            verse_lines_text = "\n".join(
                f"- {v.book}第{v.chapter}章第{v.verse_number}節：「{_prepare_verse_text(v.text)}」"
                for v in selected
            )
            answer_template = rng.choice(_THEMATIC_CATEGORY_ANSWER_TEMPLATES)
            answer = answer_template.format(
                category=cat, topic=topic, verse_lines=verse_lines_text,
            )
            samples.append(
                Sample(
                    sample_type="C",
                    messages=_make_messages(question, answer, sys_prompt),
                )
            )

        # Generate overall samples (mixed categories) — up to 3
        for overall_idx in range(3):
            if overall_idx == 0:
                pass  # always generate first
            elif overall_idx == 1 and len(all_verses) < verses_per_sample * 2:
                break
            elif overall_idx == 2 and len(all_verses) < verses_per_sample * 3:
                break

            available = [v for v in all_verses if id(v) not in used_verse_ids]
            if len(available) < 1:
                break

            sys_prompt = _lookup_prompt(rng)
            n_show = min(len(available), verses_per_sample)
            selected = rng.sample(available, n_show)
            used_verse_ids.update(id(v) for v in selected)

            template = rng.choice(_THEMATIC_TEMPLATES)
            question = template.format(topic=topic)

            verse_lines_text = "\n".join(
                f"- {v.book}第{v.chapter}章第{v.verse_number}節：「{_prepare_verse_text(v.text)}」"
                for v in selected
            )
            answer_template = rng.choice(_THEMATIC_ANSWER_TEMPLATES)
            answer = answer_template.format(
                topic=topic, verse_lines=verse_lines_text,
            )
            samples.append(
                Sample(
                    sample_type="C",
                    messages=_make_messages(question, answer, sys_prompt),
                )
            )

        # Generate testament-level samples (舊約/新約)
        testament_verses: dict[str, list[Verse]] = {}
        for v in all_verses:
            cat = _BOOK_TO_CATEGORY.get(v.book)
            if cat:
                testament = _get_testament_for_category(cat)
                if testament:
                    testament_verses.setdefault(testament, []).append(v)

        for testament, t_verses in testament_verses.items():
            available = [v for v in t_verses if id(v) not in used_verse_ids]
            if len(available) < 2:
                continue

            sys_prompt = _lookup_prompt(rng)
            n_show = min(len(available), verses_per_sample)
            selected = rng.sample(available, n_show)
            used_verse_ids.update(id(v) for v in selected)

            template = rng.choice(_THEMATIC_TESTAMENT_TEMPLATES)
            question = template.format(testament=testament, topic=topic)

            verse_lines_text = "\n".join(
                f"- {v.book}第{v.chapter}章第{v.verse_number}節：「{_prepare_verse_text(v.text)}」"
                for v in selected
            )
            answer_template = rng.choice(_THEMATIC_TESTAMENT_ANSWER_TEMPLATES)
            answer = answer_template.format(
                testament=testament, topic=topic,
                verse_lines=verse_lines_text,
            )
            samples.append(
                Sample(
                    sample_type="C",
                    messages=_make_messages(question, answer, sys_prompt),
                )
            )

    return samples


# --- Type D: Context Understanding ---


def generate_type_d(
    books: list[Book], rng: random.Random, sample_ratio: float = 0.18
) -> list[Sample]:
    """Generate context understanding samples (subset of verses)."""
    samples = []
    for book in books:
        for chapter in book.chapters:
            all_verses = _build_chapter_verse_list(chapter)
            if len(all_verses) < 3:
                continue
            # Sample a subset of verses
            n_samples = max(1, int(len(all_verses) * sample_ratio))
            selected_indices = rng.sample(range(len(all_verses)), n_samples)

            for idx in selected_indices:
                verse = all_verses[idx]
                sys_prompt = _lookup_prompt(rng)
                template = rng.choice(_CONTEXT_TEMPLATES)
                question = template.format(
                    book=verse.book,
                    chapter=verse.chapter,
                    verse=verse.verse_number,
                )

                # Build context: previous, current, next verses
                prev = all_verses[idx - 1] if idx > 0 else None
                nxt = all_verses[idx + 1] if idx < len(all_verses) - 1 else None

                parts = []
                if idx > 0:
                    parts.append(
                        f"前文（第{prev.verse_number}節）：「{_prepare_verse_text(prev.text)}」"
                    )

                parts.append(
                    f"本節（第{verse.verse_number}節）：「{_prepare_verse_text(verse.text)}」"
                )

                if idx < len(all_verses) - 1:
                    parts.append(
                        f"後文（第{nxt.verse_number}節）：「{_prepare_verse_text(nxt.text)}」"
                    )

                if rng.random() < 0.60:
                    references = [v for v in (prev, verse, nxt) if v is not None]
                    answer_template = rng.choice(_CONTEXT_EXPLANATION_TEMPLATES)
                    answer = answer_template.format(
                        flow_text=_build_context_flow(prev, verse, nxt, rng),
                        references_text=_join_references(references),
                    )
                else:
                    context_text = "\n".join(parts)
                    section_info = (
                        f"\n\n這節經文位於「{verse.section_title}」段落中。"
                        if verse.section_title
                        else ""
                    )
                    answer_template = rng.choice(_CONTEXT_ANSWER_TEMPLATES)
                    answer = answer_template.format(
                        book=verse.book,
                        chapter=verse.chapter,
                        verse=verse.verse_number,
                        context_text=context_text,
                        section_info=section_info,
                    )
                samples.append(
                    Sample(
                        sample_type="D",
                        messages=_make_messages(question, answer, sys_prompt),
                    )
                )
    return samples


# --- Type E: Verse Identification ---


def _normalize_inner_quotes(text: str) -> str:
    """Convert inner 「」 to 『』 to avoid nested 「「...」」 when wrapped by templates."""
    return text.replace("「", "『").replace("」", "』")


def _fix_quote_pairing(text: str) -> str:
    """Fix unpaired quotes in text (e.g. after snippet truncation).

    Counts 「/」 and 『/』 pairs and appends missing closing or
    prepends missing opening quotes.
    """
    for open_q, close_q in (("「", "」"), ("『", "』")):
        n_open = text.count(open_q)
        n_close = text.count(close_q)
        if n_open > n_close:
            text = text + close_q * (n_open - n_close)
        elif n_close > n_open:
            text = open_q * (n_close - n_open) + text
    return text


def _prepare_verse_text(text: str) -> str:
    """Normalize inner quotes and fix pairing for verse text."""
    return _fix_quote_pairing(_normalize_inner_quotes(text))


def generate_type_e(
    books: list[Book], rng: random.Random, sample_ratio: float = 0.15
) -> list[Sample]:
    """Generate verse identification samples (subset of verses).

    v7 changes:
    - Raised eligible threshold: 15 → 25 chars
    - Extract _make_snippet helper
    - Deduplicate snippets
    - 4-tier answer enrichment with echo snippets
    """
    all_verses = _collect_all_verses(books)
    # v7: raised threshold from 15 to 25
    eligible = [v for v in all_verses if len(v.text) >= 25]
    n_target = max(1, int(len(eligible) * sample_ratio))

    # Over-sample then deduplicate snippets
    n_candidates = min(int(n_target * 1.15), len(eligible))
    candidates = rng.sample(eligible, n_candidates)

    seen_snippets: set[str] = set()
    selected: list[Verse] = []
    for verse in candidates:
        snippet = _make_snippet(verse.text)
        if snippet in seen_snippets:
            continue
        seen_snippets.add(snippet)
        selected.append(verse)
        if len(selected) >= n_target:
            break

    samples = []
    for verse in selected:
        sys_prompt = _lookup_prompt(rng)
        text_snippet = _make_snippet(verse.text)

        # v7: Ensure minimum snippet length
        if len(text_snippet) < 20:
            text_snippet = verse.text

        # v8: Fix quote pairing (after truncation) and normalize inner quotes
        text_snippet = _fix_quote_pairing(text_snippet)
        text_snippet = _normalize_inner_quotes(text_snippet)

        template = rng.choice(_IDENTIFICATION_TEMPLATES)
        question = template.format(text=text_snippet)

        # v8: 4-tier answer enrichment (adjusted for richer answers)
        roll = rng.random()
        if verse.section_title and roll < 0.30:
            # 30% enriched with section
            answer_template = rng.choice(
                _IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION
            )
            answer = answer_template.format(
                text=text_snippet,
                book=verse.book,
                chapter=verse.chapter,
                verse=verse.verse_number,
                section_title=verse.section_title,
            )
        elif roll < 0.55:
            # 25% enriched without section
            answer_template = rng.choice(
                _IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION
            )
            answer = answer_template.format(
                text=text_snippet,
                book=verse.book,
                chapter=verse.chapter,
                verse=verse.verse_number,
            )
        elif verse.section_title and roll < 0.80:
            # 25% existing with section
            answer_template = rng.choice(
                _IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES
            )
            answer = answer_template.format(
                book=verse.book,
                chapter=verse.chapter,
                verse=verse.verse_number,
                section_title=verse.section_title,
            )
        else:
            # 20% existing plain
            answer_template = rng.choice(_IDENTIFICATION_ANSWER_TEMPLATES)
            answer = answer_template.format(
                book=verse.book,
                chapter=verse.chapter,
                verse=verse.verse_number,
            )
        samples.append(
            Sample(
                sample_type="E",
                messages=_make_messages(question, answer, sys_prompt),
            )
        )
    return samples


# --- Type G: General Bible QA ---


def _pad_points(points: tuple[str, ...], n: int = 2) -> tuple[str, ...]:
    """Ensure at least *n* support points, repeating the last if needed."""
    if not points:
        return ("這段重點",) * n
    while len(points) < n:
        points = points + (points[-1],)
    return points


def generate_type_g(books: list[Book], rng: random.Random) -> list[Sample]:
    """Generate answer-first Bible QA samples with supporting references."""
    samples = []

    for book in books:
        for chapter in book.chapters:
            for section in chapter.sections:
                if not section.title or not section.verses:
                    continue

                points = _pad_points(_support_points(list(section.verses)))
                key_verse = _pick_support_verses(list(section.verses))[0]
                sys_prompt = _general_prompt(rng)
                question = rng.choice(_GENERAL_SECTION_QA_TEMPLATES).format(
                    book=book.name,
                    chapter=chapter.number,
                    section=section.title,
                )
                reference_span = _make_reference_span(list(section.verses))
                answer = rng.choice(_GENERAL_SECTION_ANSWER_TEMPLATES).format(
                    section=section.title,
                    point1=points[0],
                    point2=points[1],
                    references_text=reference_span,
                    key_verse_ref=_make_reference(key_verse),
                    key_verse_snippet=_make_snippet(key_verse.text),
                )
                samples.append(
                    Sample(
                        sample_type="G",
                        messages=_make_messages(question, answer, sys_prompt),
                    )
                )

    topic_index = _build_topic_index(books)
    for topic, verses in topic_index.items():
        if len(verses) < 2:
            continue

        support_verses = rng.sample(verses, min(2, len(verses)))
        points = _pad_points(_support_points(support_verses))
        key_verse = support_verses[0]
        sys_prompt = _general_prompt(rng)
        question = rng.choice(_GENERAL_TOPIC_QA_TEMPLATES).format(topic=topic)
        answer = rng.choice(_GENERAL_TOPIC_ANSWER_TEMPLATES).format(
            topic=topic,
            point1=points[0],
            point2=points[1],
            references_text=_join_references(support_verses),
            key_verse_ref=_make_reference(key_verse),
            key_verse_snippet=_make_snippet(key_verse.text),
        )
        samples.append(
            Sample(
                sample_type="G",
                messages=_make_messages(question, answer, sys_prompt),
            )
        )

    return samples


# --- Type H: Citation-light Bible QA ---


def generate_type_h(books: list[Book], rng: random.Random) -> list[Sample]:
    """Generate samples that explicitly prefer concise answers over quote dumps."""
    samples = []

    for book in books:
        for chapter in book.chapters:
            for section in chapter.sections:
                if not section.title or not section.verses:
                    continue

                sys_prompt = _general_prompt(rng)
                question = rng.choice(_NO_QUOTE_SECTION_QA_TEMPLATES).format(
                    book=book.name,
                    chapter=chapter.number,
                    section=section.title,
                )
                reference_span = _make_reference_span(list(section.verses))
                answer = rng.choice(_NO_QUOTE_ANSWER_TEMPLATES).format(
                    summary_text=_build_section_summary_text(
                        section.title, list(section.verses), rng
                    ),
                    references_text=reference_span,
                )
                samples.append(
                    Sample(
                        sample_type="H",
                        messages=_make_messages(question, answer, sys_prompt),
                    )
                )

    topic_index = _build_topic_index(books)
    for topic, verses in topic_index.items():
        if len(verses) < 2:
            continue

        support_verses = rng.sample(verses, min(2, len(verses)))
        sys_prompt = _general_prompt(rng)
        question = rng.choice(_NO_QUOTE_TOPIC_QA_TEMPLATES).format(topic=topic)
        answer = rng.choice(_NO_QUOTE_ANSWER_TEMPLATES).format(
            summary_text=_build_topic_summary_text(topic, support_verses, rng),
            references_text=_join_references(support_verses),
        )
        samples.append(
            Sample(
                sample_type="H",
                messages=_make_messages(question, answer, sys_prompt),
            )
        )

    return samples


# --- Type F: Refusal / Out-of-scope ---


def generate_type_f(
    books: list[Book], rng: random.Random
) -> list[Sample]:
    """Generate refusal samples for out-of-scope or non-existent queries."""
    samples = []

    # Build max chapter map for real books
    max_chapters: dict[str, int] = {}
    for book in books:
        if book.chapters:
            max_chapters[book.name] = max(c.number for c in book.chapters)

    # --- F1: Non-existent books (42 books x 5 = 210) ---
    for fake_book in _FAKE_BOOKS:
        for ch in rng.sample(range(1, 11), 5):
            v = rng.randint(1, 20)
            sys_prompt = _general_prompt(rng)
            template = rng.choice(_FAKE_QUERY_TEMPLATES)
            question = template.format(book=fake_book, ch=ch, v=v)
            answer = rng.choice(_REFUSAL_NONEXISTENT_BOOK).format(
                book=fake_book
            )
            samples.append(
                Sample(
                    sample_type="F",
                    messages=_make_messages(question, answer, sys_prompt),
                )
            )

    # --- F2: Out-of-range chapters (280) ---
    real_books = list(max_chapters.keys())
    for _ in range(280):
        book_name = rng.choice(real_books)
        max_ch = max_chapters[book_name]
        fake_ch = max_ch + rng.randint(1, 50)
        v = rng.randint(1, 30)
        sys_prompt = _general_prompt(rng)
        template = rng.choice(_FAKE_QUERY_TEMPLATES)
        question = template.format(book=book_name, ch=fake_ch, v=v)
        answer = rng.choice(_REFUSAL_OUT_OF_RANGE).format(
            book=book_name, max_ch=max_ch, ch=fake_ch
        )
        samples.append(
            Sample(
                sample_type="F",
                messages=_make_messages(question, answer, sys_prompt),
            )
        )

    # --- F2b: Out-of-range verses (220) ---
    max_verses_per_chapter: dict[str, dict[int, int]] = {}
    for book in books:
        book_verses: dict[int, int] = {}
        for chapter in book.chapters:
            verse_count = sum(len(s.verses) for s in chapter.sections)
            if verse_count > 0:
                book_verses[chapter.number] = verse_count
        if book_verses:
            max_verses_per_chapter[book.name] = book_verses

    for _ in range(220):
        book_name = rng.choice(list(max_verses_per_chapter.keys()))
        ch_map = max_verses_per_chapter[book_name]
        ch = rng.choice(list(ch_map.keys()))
        max_v = ch_map[ch]
        fake_v = max_v + rng.randint(1, 30)
        sys_prompt = _general_prompt(rng)
        template = rng.choice(_FAKE_QUERY_TEMPLATES)
        question = template.format(book=book_name, ch=ch, v=fake_v)
        answer = rng.choice(_REFUSAL_OUT_OF_RANGE_VERSE).format(
            book=book_name, ch=ch, max_v=max_v, v=fake_v
        )
        samples.append(
            Sample(
                sample_type="F",
                messages=_make_messages(question, answer, sys_prompt),
            )
        )

    # --- F3: Non-Bible questions (category-aware refusal) ---
    for category, questions in _NON_BIBLE_QUESTIONS_BY_CATEGORY.items():
        cat_templates = _REFUSAL_NON_BIBLE_BY_CATEGORY.get(category)
        for question in questions:
            sys_prompt = _general_prompt(rng)
            if cat_templates and rng.random() < 0.60:
                answer = rng.choice(cat_templates)
            else:
                answer = rng.choice(_REFUSAL_NON_BIBLE_GENERIC)
            samples.append(
                Sample(
                    sample_type="F",
                    messages=_make_messages(question, answer, sys_prompt),
                )
            )

    # --- F4: Ambiguous boundary questions (30) ---
    for question, answer in _BOUNDARY_QUESTIONS:
        sys_prompt = _general_prompt(rng)
        samples.append(
            Sample(
                sample_type="F",
                messages=_make_messages(question, answer, sys_prompt),
            )
        )

    # --- F5: Misspelled book names (20 x 5 = 100) ---
    for wrong_name, correct_name in _MISSPELLED_BOOKS.items():
        for _ in range(5):
            ch = rng.randint(1, 10)
            v = rng.randint(1, 20)
            sys_prompt = _general_prompt(rng)
            template = rng.choice(_FAKE_QUERY_TEMPLATES)
            question = template.format(book=wrong_name, ch=ch, v=v)
            answer = rng.choice(_REFUSAL_MISSPELLED_BOOK).format(
                book=wrong_name, correct_book=correct_name,
            )
            samples.append(
                Sample(
                    sample_type="F",
                    messages=_make_messages(question, answer, sys_prompt),
                )
            )

    return samples


# --- Main generator ---


def generate_all_samples(
    books: list[Book], seed: int = 42
) -> list[Sample]:
    """Generate all training samples from parsed Bible books.

    Returns a list of Sample objects with all 8 types combined.
    """
    rng = random.Random(seed)

    samples: list[Sample] = []
    samples.extend(generate_type_a(books, rng))
    samples.extend(generate_type_b(books, rng))
    samples.extend(generate_type_c(books, rng))
    samples.extend(generate_type_d(books, rng))
    samples.extend(generate_type_e(books, rng))
    samples.extend(generate_type_g(books, rng))
    samples.extend(generate_type_h(books, rng))
    samples.extend(generate_type_f(books, rng))

    return _rebalance_samples(samples, seed)
