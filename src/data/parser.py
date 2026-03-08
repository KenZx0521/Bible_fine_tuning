"""Markdown parser for Traditional Chinese Bible files.

Handles edge cases:
- Broken H3: verse text broken into fake H3 headings
- Cross-references: ### （路3‧23－38） — skipped
- （細拉）: musical notation in Psalms — skipped
- Multi-line poetry: Psalms verses spanning multiple lines
- Merged verses: **1-2** combined verse numbers
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# --- Data structures (frozen) ---


@dataclass(frozen=True)
class Verse:
    book: str
    chapter: int
    verse_number: str  # str to support "1-2" merged verses
    text: str
    section_title: str


@dataclass(frozen=True)
class Section:
    title: str
    verses: tuple[Verse, ...]


@dataclass(frozen=True)
class Chapter:
    book: str
    number: int
    sections: tuple[Section, ...]


@dataclass(frozen=True)
class Book:
    name: str
    chapters: tuple[Chapter, ...]


# --- Regex patterns ---

_RE_H1 = re.compile(r"^# (.+)$")
_RE_H2 = re.compile(r"^## 第 (\d+) 章$")
_RE_H3 = re.compile(r"^### (.+)$")
_RE_VERSE = re.compile(r"^\*\*(\d+(?:-\d+)?)\*\*\s*(.*)$")

# Broken H3: short text (1-6 chars) ending with sentence punctuation
# e.g., "### 的君」。", "### 頭！", "### 時呢？", "### 風，"
_RE_BROKEN_H3 = re.compile(r"^### .{1,6}[。！？，」）]$")

# Cross-reference or musical notation: "### （...）"
_RE_CROSS_REF = re.compile(r"^### （.+）$")

# Horizontal rule (footnote separator)
_RE_HORIZONTAL_RULE = re.compile(r"^-{3,}$")

# Footnote marker: "**註腳：**" or similar
_RE_FOOTNOTE_MARKER = re.compile(r"^\*\*註腳")

# Chapter-verse reference pattern: digits‧digits (e.g., 26‧20)
_RE_CHAPTER_VERSE_REF = re.compile(r"\d+‧\d+")


def _is_broken_h3(line: str, prev_line: str) -> bool:
    """Detect broken H3 headers caused by line-width wrapping.

    A broken H3 is a short line that looks like a heading but is actually
    a continuation of the previous verse text. Two conditions:
    1. Matches the broken H3 pattern (short text with terminal punctuation)
    2. The previous non-empty line does NOT end with terminal punctuation,
       indicating mid-sentence truncation.
    """
    if not _RE_BROKEN_H3.match(line):
        return False

    stripped = prev_line.rstrip()
    if not stripped:
        return True  # No previous text to check — treat as broken

    # If previous line ends without sentence-ending punctuation, it's broken
    return stripped[-1] not in "。！？」）；：\n"


def _is_cross_ref_or_annotation(line: str) -> bool:
    """Detect cross-references and annotations like （細拉）.

    Handles:
    - Complete parenthetical refs: ### （路3‧23－38）
    - Incomplete parenthetical refs: ### （太26‧20－25；...路
    - Asterisk-wrapped refs: ### *王下18‧13－37*
    - Half-width closing paren: ### （...22‧55－57)

    Does NOT filter legitimate place names like 便‧哈達王 (no digit‧digit pattern).
    """
    if _RE_CROSS_REF.match(line):
        return True
    if not line.startswith("### "):
        return False
    content = line[4:]
    # Incomplete parenthetical + chapter‧verse reference
    if content.startswith("（") and _RE_CHAPTER_VERSE_REF.search(content):
        return True
    # Asterisk-wrapped + chapter‧verse reference
    if content.startswith("*") and _RE_CHAPTER_VERSE_REF.search(content):
        return True
    return False


def parse_book(filepath: Path) -> Book:
    """Parse a single Bible book markdown file into a Book dataclass."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    book_name = ""
    chapters: list[Chapter] = []

    # Current state
    current_chapter_num = 0
    current_section_title = ""
    current_sections: list[Section] = []
    current_verses: list[Verse] = []
    current_verse_num = ""
    current_verse_lines: list[str] = []
    prev_content_line = ""  # Last non-empty, non-heading line
    # Footnote state: horizontal rules at chapter ends precede footnote blocks.
    # Once a footnote marker is seen, all lines are skipped until the next H2 chapter.
    in_footnote = False

    def _flush_verse() -> None:
        """Flush accumulated verse lines into current_verses."""
        nonlocal current_verse_num, current_verse_lines
        if current_verse_num and current_verse_lines:
            verse_text = "\n".join(current_verse_lines).strip()
            if verse_text:
                current_verses.append(
                    Verse(
                        book=book_name,
                        chapter=current_chapter_num,
                        verse_number=current_verse_num,
                        text=verse_text,
                        section_title=current_section_title,
                    )
                )
        current_verse_num = ""
        current_verse_lines = []

    def _flush_section() -> None:
        """Flush current verses into a section."""
        nonlocal current_verses
        _flush_verse()
        if current_verses:
            current_sections.append(
                Section(title=current_section_title, verses=tuple(current_verses))
            )
            current_verses = []

    def _flush_chapter() -> None:
        """Flush current sections into a chapter."""
        nonlocal current_sections
        _flush_section()
        if current_sections and current_chapter_num > 0:
            chapters.append(
                Chapter(
                    book=book_name,
                    number=current_chapter_num,
                    sections=tuple(current_sections),
                )
            )
            current_sections = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Horizontal rule: flush current verse and skip
        if _RE_HORIZONTAL_RULE.match(stripped):
            _flush_verse()
            continue

        # H1: Book name
        h1_match = _RE_H1.match(stripped)
        if h1_match:
            book_name = h1_match.group(1)
            continue

        # H2: Chapter number
        h2_match = _RE_H2.match(stripped)
        if h2_match:
            _flush_chapter()
            current_chapter_num = int(h2_match.group(1))
            current_section_title = ""
            in_footnote = False
            continue

        # H3: Section title, cross-reference, or broken H3
        h3_match = _RE_H3.match(stripped)
        if h3_match:
            # Skip cross-references and annotations
            if _is_cross_ref_or_annotation(stripped):
                continue

            # Handle broken H3: append to previous verse text
            if _is_broken_h3(stripped, prev_content_line):
                broken_text = h3_match.group(1)
                if current_verse_lines:
                    current_verse_lines.append(broken_text)
                elif current_verses:
                    # Append to the last completed verse
                    last = current_verses[-1]
                    current_verses[-1] = Verse(
                        book=last.book,
                        chapter=last.chapter,
                        verse_number=last.verse_number,
                        text=last.text + broken_text,
                        section_title=last.section_title,
                    )
                prev_content_line = broken_text
                continue

            # Real section title
            _flush_section()
            current_section_title = h3_match.group(1)
            continue

        # Verse start: **N** or **N-M**
        verse_match = _RE_VERSE.match(stripped)
        if verse_match:
            _flush_verse()
            current_verse_num = verse_match.group(1)
            verse_text = verse_match.group(2).strip()
            current_verse_lines = [verse_text] if verse_text else []
            prev_content_line = stripped
            continue

        # Footnote marker detection: enter footnote block
        if _RE_FOOTNOTE_MARKER.match(stripped):
            _flush_verse()
            in_footnote = True
            continue

        # Skip all lines inside a footnote block
        if in_footnote:
            continue

        # Continuation line (multi-line poetry or long verse)
        if current_verse_num:
            current_verse_lines.append(stripped)
            prev_content_line = stripped
            continue

        # Any other content line
        prev_content_line = stripped

    # Flush remaining
    _flush_chapter()

    return Book(name=book_name, chapters=tuple(chapters))


def parse_all_books(data_dir: Path) -> list[Book]:
    """Parse all Bible book markdown files from a directory.

    Returns books sorted by filename for deterministic ordering.
    """
    md_files = sorted(data_dir.glob("*.md"))
    if not md_files:
        msg = f"No markdown files found in {data_dir}"
        raise FileNotFoundError(msg)

    books = []
    for filepath in md_files:
        book = parse_book(filepath)
        if book.chapters:
            books.append(book)

    return books


def count_stats(books: list[Book]) -> dict[str, int]:
    """Count parsing statistics for validation."""
    total_books = len(books)
    total_chapters = sum(len(b.chapters) for b in books)
    total_sections = sum(
        len(c.sections) for b in books for c in b.chapters
    )
    total_verses = sum(
        len(s.verses) for b in books for c in b.chapters for s in c.sections
    )
    return {
        "books": total_books,
        "chapters": total_chapters,
        "sections": total_sections,
        "verses": total_verses,
    }
