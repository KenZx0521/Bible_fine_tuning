"""Tests for Bible markdown parser."""

from __future__ import annotations

from pathlib import Path

from src.data.parser import (
    _is_broken_h3,
    _is_cross_ref_or_annotation,
    count_stats,
    parse_all_books,
    parse_book,
)


class TestIsBrokenH3:
    """Tests for broken H3 detection."""

    def test_broken_h3_short_punctuation(self):
        assert _is_broken_h3("### 的君」。", "政權必擔在他的肩頭上")

    def test_broken_h3_exclamation(self):
        assert _is_broken_h3("### 頭！", "求你救我脫離說謊的嘴唇和詭詐的舌")

    def test_broken_h3_question_mark(self):
        assert _is_broken_h3("### 時呢？", "你們將我的尊榮變為羞辱要到幾")

    def test_broken_h3_comma(self):
        assert _is_broken_h3("### 風，", "看哪，他駕雲降臨")

    def test_real_section_title_not_broken(self):
        # Real section title — previous line ends with proper punctuation
        assert not _is_broken_h3("### 這是基督嗎？", "你們也不向他說甚麼。")

    def test_long_title_not_broken(self):
        assert not _is_broken_h3("### 上帝的創造", "")

    def test_normal_title_not_broken(self):
        assert not _is_broken_h3("### 真福", "")

    def test_not_h3_at_all(self):
        assert not _is_broken_h3("**1** 經文", "")


class TestParseBook:
    """Tests for single book parsing."""

    def test_basic_parsing(self, sample_markdown: Path):
        book = parse_book(sample_markdown)

        assert book.name == "測試書"
        assert len(book.chapters) == 2

    def test_chapter_one_structure(self, sample_markdown: Path):
        book = parse_book(sample_markdown)
        ch1 = book.chapters[0]

        assert ch1.number == 1
        assert len(ch1.sections) == 2
        assert ch1.sections[0].title == "段落一"
        assert ch1.sections[1].title == "段落二"

    def test_verse_content(self, sample_markdown: Path):
        book = parse_book(sample_markdown)
        ch1 = book.chapters[0]
        s1 = ch1.sections[0]

        assert len(s1.verses) == 3
        assert s1.verses[0].verse_number == "1"
        assert s1.verses[0].text == "這是第一節經文。"
        assert s1.verses[0].book == "測試書"
        assert s1.verses[0].chapter == 1
        assert s1.verses[0].section_title == "段落一"

    def test_chapter_two(self, sample_markdown: Path):
        book = parse_book(sample_markdown)
        ch2 = book.chapters[1]

        assert ch2.number == 2
        assert len(ch2.sections) == 1
        assert len(ch2.sections[0].verses) == 2

    def test_multi_line_poetry(self, psalm_markdown: Path):
        book = parse_book(psalm_markdown)
        ch1 = book.chapters[0]
        s1 = ch1.sections[0]

        # Verse 1 should have multi-line content
        assert "不從惡人的計謀" in s1.verses[0].text
        assert "不站罪人的道路" in s1.verses[0].text
        assert "不坐褻慢人的座位" in s1.verses[0].text

    def test_sela_skipped(self, psalm_markdown: Path):
        book = parse_book(psalm_markdown)
        ch2 = book.chapters[1]

        # （細拉） should not create a section
        section_titles = [s.title for s in ch2.sections]
        assert "（細拉）" not in section_titles

    def test_broken_h3_appended(self, psalm_markdown: Path):
        book = parse_book(psalm_markdown)
        ch3 = book.chapters[2]

        # "時呢？" should be appended to verse 1
        verse1 = ch3.sections[0].verses[0]
        assert "時呢？" in verse1.text
        assert "要到幾" in verse1.text

    def test_cross_reference_skipped(self, cross_ref_markdown: Path):
        book = parse_book(cross_ref_markdown)
        ch1 = book.chapters[0]

        # Cross reference should not create a separate section
        section_titles = [s.title for s in ch1.sections]
        assert "（出20‧1－17）" not in section_titles


class TestFootnoteFiltering:
    """Tests for footnote block filtering in parser."""

    def test_footnote_marker_not_in_verse_text(self, footnote_markdown: Path):
        book = parse_book(footnote_markdown)
        for ch in book.chapters:
            for sec in ch.sections:
                for v in sec.verses:
                    assert "註腳" not in v.text, (
                        f"Footnote marker leaked into {v.book} {v.chapter}:{v.verse_number}"
                    )

    def test_horizontal_rule_not_in_verse_text(self, footnote_markdown: Path):
        book = parse_book(footnote_markdown)
        for ch in book.chapters:
            for sec in ch.sections:
                for v in sec.verses:
                    assert "---" not in v.text, (
                        f"Horizontal rule leaked into {v.book} {v.chapter}:{v.verse_number}"
                    )

    def test_footnote_entry_not_in_verse_text(self, footnote_markdown: Path):
        book = parse_book(footnote_markdown)
        for ch in book.chapters:
            for sec in ch.sections:
                for v in sec.verses:
                    assert "1:1:" not in v.text
                    assert "ruach" not in v.text
                    assert "古譯本" not in v.text

    def test_verses_preserved_before_footnote(self, footnote_markdown: Path):
        book = parse_book(footnote_markdown)
        ch1 = book.chapters[0]
        verses = ch1.sections[0].verses
        assert len(verses) == 2
        assert "第一章第一節經文" in verses[0].text
        assert "第一章第二節經文" in verses[1].text

    def test_chapter_after_footnote_parses_correctly(self, footnote_markdown: Path):
        book = parse_book(footnote_markdown)
        assert len(book.chapters) == 2
        ch2 = book.chapters[1]
        assert ch2.number == 2
        verses = ch2.sections[0].verses
        assert len(verses) == 2
        assert "第二章第一節經文" in verses[0].text


class TestIsCrossRef:
    """Tests for cross-reference detection (expanded)."""

    def test_cross_reference(self):
        assert _is_cross_ref_or_annotation("### （路3‧23－38）")

    def test_sela(self):
        assert _is_cross_ref_or_annotation("### （細拉）")

    def test_psalm_reference(self):
        assert _is_cross_ref_or_annotation("### （詩53）")

    def test_normal_title(self):
        assert not _is_cross_ref_or_annotation("### 上帝的創造")

    def test_incomplete_parenthetical_is_cross_ref(self):
        assert _is_cross_ref_or_annotation("### （太26‧20－25；可14‧17－21；路")

    def test_asterisk_wrapped_is_cross_ref(self):
        assert _is_cross_ref_or_annotation("### *王下18‧13－37*")

    def test_half_width_closing_paren(self):
        assert _is_cross_ref_or_annotation("### （太26‧69－70；可14‧66－68；路22‧55－57)")

    def test_place_name_with_dot_preserved(self):
        assert not _is_cross_ref_or_annotation("### 以利沙和便‧哈達王")

    def test_place_name_kiryat_yearim_preserved(self):
        assert not _is_cross_ref_or_annotation("### 基列‧耶琳")

    def test_place_name_adoni_bezek_preserved(self):
        assert not _is_cross_ref_or_annotation("### 亞多尼‧比色")


class TestParallelRefParsing:
    """Integration tests for parallel reference filtering."""

    def test_incomplete_ref_no_section(self, parallel_ref_markdown: Path):
        book = parse_book(parallel_ref_markdown)
        titles = [s.title for ch in book.chapters for s in ch.sections]
        assert not any("太26" in t for t in titles)

    def test_asterisk_ref_no_section(self, parallel_ref_markdown: Path):
        book = parse_book(parallel_ref_markdown)
        titles = [s.title for ch in book.chapters for s in ch.sections]
        assert not any("王下18" in t for t in titles)

    def test_place_name_section_preserved(self, parallel_ref_markdown: Path):
        book = parse_book(parallel_ref_markdown)
        titles = [s.title for ch in book.chapters for s in ch.sections]
        assert "以利沙和便‧哈達王" in titles


class TestParseAllBooks:
    """Tests for parsing all books."""

    def test_parse_directory(self, sample_markdown: Path, psalm_markdown: Path):
        data_dir = sample_markdown.parent
        books = parse_all_books(data_dir)

        assert len(books) >= 2

    def test_empty_directory(self, tmp_path: Path):
        import pytest

        with pytest.raises(FileNotFoundError):
            parse_all_books(tmp_path)


class TestCountStats:
    """Tests for counting statistics."""

    def test_count(self, sample_books):
        stats = count_stats(sample_books)

        assert stats["books"] == 1
        assert stats["chapters"] == 2
        assert stats["sections"] == 3
        assert stats["verses"] == 6
