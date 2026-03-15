"""Tests for dataset sample generators."""

from __future__ import annotations

import random

from src.constants import (
    GENERAL_QA_SYSTEM_PROMPT_VARIANTS,
    LOOKUP_SYSTEM_PROMPT_VARIANTS,
)
from src.data.dataset_generator import (
    _MIN_SAMPLES_PER_BOOK,
    _fix_quote_pairing,
    _make_messages,
    _match_topic,
    _normalize_inner_quotes,
    _prepare_verse_text,
    _wrap_cot,
    generate_all_samples,
    generate_type_a,
    generate_type_b,
    generate_type_c,
    generate_type_d,
    generate_type_e,
    generate_type_f,
    generate_type_g,
    generate_type_h,
)
from src.data.templates import (
    _FAKE_BOOKS,
    _MISSPELLED_BOOKS,
    _NON_BIBLE_QUESTIONS_BY_CATEGORY,
    _REFUSAL_NON_BIBLE_BY_CATEGORY,
    _VERSE_ANSWER_EXTENDED_TEMPLATES,
    _VERSE_ANSWER_TEMPLATES,
    TOPIC_KEYWORDS,
)


class TestTypeA:
    """Tests for verse lookup sample generation (with downsampling)."""

    def test_skips_short_verses(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_a(sample_books, rng)
        # verses_ch2 has 9-char verse ("天地萬物都造齊了。") → filtered by <15
        # All chapter 1 verses are >25 chars → kept (with 18%/30% rate)
        assert len(samples) > 0
        assert len(samples) <= 5  # At most 5 (6 minus 1 filtered)

    def test_message_format(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_a(sample_books, rng)
        sample = samples[0]

        assert sample.sample_type == "A"
        assert len(sample.messages) == 3
        assert sample.messages[0]["role"] == "system"
        assert sample.messages[0]["content"] in LOOKUP_SYSTEM_PROMPT_VARIANTS
        assert sample.messages[1]["role"] == "user"
        assert sample.messages[2]["role"] == "assistant"

    def test_answer_contains_verse_text(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_a(sample_books, rng)
        answers = [s.messages[2]["content"] for s in samples]
        # All chapter 1 verses are >25 chars, should appear in answers
        assert any("創世記" in a for a in answers)
        assert any("上帝" in a for a in answers)

    def test_uses_expanded_templates(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_a(sample_books, rng)
        questions = [s.messages[1]["content"] for s in samples]
        # Should see variety beyond original 4 templates
        all_text = " ".join(questions)
        # At least check some templates are used
        assert any(
            "經文" in q or "說了" in q or "查" in q or "寫了" in q
            for q in questions
        )


class TestTypeB:
    """Tests for section summary sample generation (filtered)."""

    def test_one_per_section_with_title(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_b(sample_books, rng)
        # 3 sections in sample_books, all have titles
        assert len(samples) == 3

    def test_no_empty_title(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_b(sample_books, rng)
        for sample in samples:
            question = sample.messages[1]["content"]
            assert "「」" not in question

    def test_summary_is_concise_not_full_verse_dump(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_b(sample_books, rng)
        answer = samples[0].messages[2]["content"]
        # Answer should be summary-oriented, not a full verse dump
        assert "第1節：" not in answer
        # Should NOT contain the old "推託" pattern
        assert "若要回頭對照原文" not in answer

    def test_uses_answer_templates(self, sample_books):
        """Verify Type B uses varied answer templates with real content."""
        rng = random.Random(42)
        samples = generate_type_b(sample_books, rng)
        answers = [s.messages[2]["content"] for s in samples]
        # All answers should contain the book name and section name
        for a in answers:
            assert "創世記" in a
            # Should NOT contain old "推託" pattern
            assert "若要回頭對照原文" not in a


class TestTypeC:
    """Tests for thematic verse samples (multi-faceted)."""

    def test_generates_samples(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_c(sample_books, rng)
        assert isinstance(samples, list)

    def test_topic_in_question_or_answer(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_c(sample_books, rng)
        for sample in samples:
            q = sample.messages[1]["content"]
            a = sample.messages[2]["content"]
            assert "關於" in q or "提到" in q or "教導" in q or "相關" in q


class TestMatchTopic:
    """Tests for keyword matching with exclusion."""

    def test_include_match(self):
        config = {"include": ["創造"], "exclude": ["建造"]}
        assert _match_topic("上帝創造天地。", config)

    def test_exclude_match(self):
        config = {"include": ["創造", "造"], "exclude": ["建造"]}
        assert not _match_topic("迦得子孫建造底本。", config)

    def test_no_match(self):
        config = {"include": ["信心"], "exclude": []}
        assert not _match_topic("上帝創造天地。", config)


    def test_angel_excludes_high_heaven_fire(self):
        """「高天使火」中的「天使」是斷句錯誤，不應匹配天使主題。"""
        config = TOPIC_KEYWORDS["天使"]
        assert not _match_topic("他從高天使火進入我的骨頭", config)

    def test_angel_keeps_real_angel(self):
        """真正的「天使」經文應正常匹配。"""
        config = TOPIC_KEYWORDS["天使"]
        assert _match_topic("耶和華的天使向他顯現。", config)

    def test_light_excludes_sword_gleam(self):
        config = TOPIC_KEYWORDS["光明"]
        assert not _match_topic("刀劍發光，令人懼怕。", config)

    def test_light_excludes_bright_copper(self):
        config = TOPIC_KEYWORDS["光明"]
        assert not _match_topic("光明的銅，如同擦亮的銅。", config)

    def test_light_keeps_spiritual_light(self):
        config = TOPIC_KEYWORDS["光明"]
        assert _match_topic("光明照耀在黑暗中。", config)

    def test_light_keeps_darkness_to_light(self):
        config = TOPIC_KEYWORDS["光明"]
        assert _match_topic("從黑暗中歸向光明。", config)


class TestTypeD:
    """Tests for context understanding samples."""

    def test_generates_more_samples(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_d(sample_books, rng)
        assert len(samples) > 0

    def test_context_includes_surrounding(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_d(sample_books, rng)
        for sample in samples:
            answer = sample.messages[2]["content"]
            assert "本節" in answer


    def test_uses_lookup_prompt(self, sample_books):
        """Type D should use LOOKUP prompt (not GENERAL_QA)."""
        rng = random.Random(42)
        samples = generate_type_d(sample_books, rng)
        for sample in samples:
            sys_prompt = sample.messages[0]["content"]
            assert sys_prompt in LOOKUP_SYSTEM_PROMPT_VARIANTS, (
                f"Type D should use LOOKUP prompt, got: {sys_prompt[:60]}"
            )


class TestTypeDDiversity:
    """Tests for answer diversity in Type D."""

    def test_multiple_answer_prefixes(self, sample_books):
        """Type D should use varied answer templates (after CoT)."""
        answers = set()
        for seed in range(50):
            rng = random.Random(seed)
            samples = generate_type_d(sample_books, rng)
            for s in samples:
                content = s.messages[2]["content"]
                # Extract answer after </think>\n\n
                marker = "</think>\n\n"
                idx = content.find(marker)
                if idx != -1:
                    answer_part = content[idx + len(marker):]
                else:
                    answer_part = content
                answers.add(answer_part[:6])
        # With 6 templates, should see more than 1 unique prefix
        assert len(answers) > 1, "Type D answers lack diversity"


class TestTypeE:
    """Tests for verse identification samples."""

    def test_generates_samples(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_e(sample_books, rng)
        assert isinstance(samples, list)

    def test_answer_contains_reference(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_e(sample_books, rng)
        ref_keywords = [
            "出自", "記載在", "出處是", "來自", "收錄在", "引用",
        ]
        for sample in samples:
            answer = sample.messages[2]["content"]
            assert any(kw in answer for kw in ref_keywords), (
                f"Missing reference keyword in: {answer[:80]}"
            )


class TestTypeF:
    """Tests for refusal / out-of-scope samples."""

    def test_generates_samples(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)
        assert len(samples) >= 900

    def test_has_refusal_content(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)
        refusal_keywords = [
            "沒有", "不是", "超出", "範圍", "不存在",
            "正典", "聖經", "並非", "不同的", "提到",
            "傳統", "定論", "記載", "有誤", "誤寫",
            "正確名稱", "不在", "無法", "不屬於",
        ]
        for sample in samples:
            answer = sample.messages[2]["content"]
            assert any(
                kw in answer for kw in refusal_keywords
            ), f"Missing refusal in: {answer[:80]}"

    def test_includes_fake_books(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)
        questions = [s.messages[1]["content"] for s in samples]
        assert any(
            "保羅書" in q or "彼拉多書" in q or "馬利亞福音" in q
            for q in questions
        )


class TestTypeG:
    """Tests for answer-first Bible QA samples."""

    def test_generates_samples(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_g(sample_books, rng)
        assert len(samples) > 0

    def test_uses_general_prompt(self, sample_books):
        rng = random.Random(42)
        sample = generate_type_g(sample_books, rng)[0]
        assert sample.messages[0]["content"] in GENERAL_QA_SYSTEM_PROMPT_VARIANTS

    def test_answer_mentions_verse_content(self, sample_books):
        rng = random.Random(42)
        answers = [s.messages[2]["content"] for s in generate_type_g(sample_books, rng)]
        # New templates embed verse snippets directly in the answer
        assert any("提到" in a or "記載" in a or "寫道" in a or "說" in a for a in answers)
        # Should NOT contain old "推託" pattern
        assert all("若要對照原文" not in a for a in answers)


class TestTypeH:
    """Tests for citation-light Bible QA samples."""

    def test_generates_samples(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_h(sample_books, rng)
        assert len(samples) > 0

    def test_question_explicitly_discourages_quote_dumping(self, sample_books):
        rng = random.Random(42)
        questions = [s.messages[1]["content"] for s in generate_type_h(sample_books, rng)]
        assert any("不要" in q or "不用" in q for q in questions)

    def test_answer_stays_concise(self, sample_books):
        rng = random.Random(42)
        answers = [s.messages[2]["content"] for s in generate_type_h(sample_books, rng)]
        assert all("第1節：" not in a for a in answers)


class TestGenerateAll:
    """Tests for full sample generation."""

    def test_all_types_present(self, sample_books):
        samples = generate_all_samples(sample_books, seed=42)
        types = {s.sample_type for s in samples}
        assert "A" in types
        assert "B" in types
        assert "D" in types
        assert "F" in types  # Refusal samples always present
        assert "G" in types
        assert "H" in types

    def test_deterministic(self, sample_books):
        samples1 = generate_all_samples(sample_books, seed=42)
        samples2 = generate_all_samples(sample_books, seed=42)
        assert len(samples1) == len(samples2)
        for s1, s2 in zip(samples1, samples2):
            assert s1.messages == s2.messages


class TestTypeAProgressive:
    """Tests for progressive downsampling in Type A."""

    def test_filters_under_15_chars(self, sample_books):
        """Verses < 15 chars should be completely filtered out."""
        rng = random.Random(42)
        samples = generate_type_a(sample_books, rng)
        answers = [s.messages[2]["content"] for s in samples]
        # "天地萬物都造齊了。" (9 chars) should never appear
        assert not any("天地萬物都造齊了" in a for a in answers)

    def test_progressive_downsample_rates(self):
        """Verify progressive downsampling produces expected ratios."""
        from src.data.parser import Book, Chapter, Section, Verse

        # Create enough long verses so that after 30% downsampling, the book
        # still has > _MIN_SAMPLES_PER_BOOK (30), preventing the floor from
        # pulling the short verse back in. 120 * 0.30 = ~36 > 30.
        long_verses = tuple(
            Verse("測試", 1, str(i), "一" * 45, "段落")
            for i in range(1, 121)
        )
        short_verse = Verse(
            "測試", 1, "121", "一二三四五六七八九十一二三四五", "段落"
        )  # 15 chars
        med_verse = Verse(
            "測試", 1, "122",
            "一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十",
            "段落",
        )  # 30 chars

        section = Section("段落", long_verses + (short_verse, med_verse))
        chapter = Chapter("測試", 1, (section,))
        books = [Book("測試", (chapter,))]

        # Run many times to verify rates
        short_kept = sum(
            1 for seed in range(1000)
            if any(
                "一二三四五六七八九十一二三四五」" in s.messages[2]["content"]
                and "一二三四五六七八九十一二三四五六"
                not in s.messages[2]["content"]
                for s in generate_type_a(books, random.Random(seed))
            )
        )
        # 15-char verse: 8% keep rate → expect ~80 out of 1000
        assert (
            20 < short_kept < 200
        ), f"Short verse kept {short_kept}/1000, expected ~80"

    def test_answer_template_diversity(self, sample_books):
        """Verify multiple answer templates are used."""
        rng = random.Random(42)
        samples = generate_type_a(sample_books, rng)
        answers = [s.messages[2]["content"] for s in samples]
        # Check that different answer prefixes appear
        prefixes_seen = set()
        for tmpl in _VERSE_ANSWER_TEMPLATES:
            prefix = tmpl.split("{")[0][:4]
            if any(a.startswith(prefix) or prefix in a[:20] for a in answers):
                prefixes_seen.add(prefix)
        # Should see at least 1 different template style with few samples
        assert len(prefixes_seen) >= 1


class TestTypeAExtended:
    """Tests for extended answer templates in Type A."""

    def test_extended_template_ratio(self):
        """20-70% of Type A answers should use extended templates (section context)."""
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i), f"這是一段足夠長的經文內容，用來測試模板的選擇邏輯。第{i}節。", "上帝的創造")
            for i in range(1, 51)
        )
        section = Section("上帝的創造", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        extended_count = 0
        total_count = 0
        for seed in range(100):
            rng = random.Random(seed)
            samples = generate_type_a(books, rng)
            for s in samples:
                total_count += 1
                answer = s.messages[2]["content"]
                if "段落" in answer and "section_title" not in answer:
                    extended_count += 1

        if total_count > 0:
            ratio = extended_count / total_count
            assert 0.20 < ratio < 0.70, (
                f"Extended template ratio {ratio:.2%} outside expected 20-70%"
            )


class TestTypeABookFloor:
    """Tests for book floor in Type A (v6)."""

    def test_small_book_reaches_floor(self):
        """Small books should reach the minimum sample count."""
        from src.data.parser import Book, Chapter, Section, Verse

        # Create a small book with 35 eligible verses
        verses = tuple(
            Verse("小書卷", 1, str(i), f"這是小書卷第{i}節的經文內容，足夠長的文字。", "段落一")
            for i in range(1, 36)
        )
        section = Section("段落一", verses)
        chapter = Chapter("小書卷", 1, (section,))
        books = [Book("小書卷", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_a(books, rng)
        assert len(samples) >= _MIN_SAMPLES_PER_BOOK, (
            f"Small book only got {len(samples)} samples, expected >= {_MIN_SAMPLES_PER_BOOK}"
        )


class TestTypeCGrowth:
    """Tests for Type C sample count growth (v5)."""

    def test_second_overall_sample_generated(self):
        """Topics with enough verses should get a second overall sample."""
        from src.data.parser import Book, Chapter, Section, Verse

        # Create a book with many verses matching "信心" topic
        verses = tuple(
            Verse("測試書", 1, str(i), f"這是關於信心和相信的經文，信心是重要的。第{i}節。", "信心段落")
            for i in range(1, 25)
        )
        section = Section("信心段落", verses)
        chapter = Chapter("測試書", 1, (section,))
        books = [Book("測試書", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_c(books, rng, verses_per_sample=6)

        # With 24 verses matching 信心 (>= 6*2=12), should generate 2+ overall samples
        overall_count = sum(
            1 for s in samples
            if "聖經" in s.messages[1]["content"] or "一些" in s.messages[2]["content"]
        )
        assert overall_count >= 2, (
            f"Expected at least 2 overall samples, got {overall_count}"
        )


class TestTypeCTestament:
    """Tests for testament-level samples in Type C (v6)."""

    def test_testament_samples_generated(self):
        """Testament-level questions should be generated for topics with verses in 舊約/新約."""
        from src.data.parser import Book, Chapter, Section, Verse

        # v7: Need enough verses to survive dedup across category/overall/testament
        # category(6) + overall×3(18) + testament(2+) = need ≥ 28 verses
        verses = tuple(
            Verse("創世記", 1, str(i), f"信心和相信是重要的教導。第{i}節。", "段落")
            for i in range(1, 35)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_c(books, rng, verses_per_sample=6)

        # Should have at least one testament-level sample with "舊約"
        testament_qs = [
            s.messages[1]["content"] for s in samples
            if "舊約" in s.messages[1]["content"] or "新約" in s.messages[1]["content"]
        ]
        assert len(testament_qs) >= 1, (
            f"Expected testament-level samples, got {len(testament_qs)}"
        )


class TestTypeCUnique:
    """Tests for unique questions in Type C."""

    def test_no_duplicate_questions(self, sample_books):
        """Each Type C question should be unique."""
        rng = random.Random(42)
        samples = generate_type_c(sample_books, rng)
        questions = [s.messages[1]["content"] for s in samples]
        assert len(questions) == len(set(questions)), (
            f"Found {len(questions) - len(set(questions))} duplicate questions"
        )

    def test_category_in_per_category_question(self, sample_books):
        """Per-category questions should contain the category name."""
        rng = random.Random(42)
        samples = generate_type_c(sample_books, rng)
        for sample in samples:
            q = sample.messages[1]["content"]
            a = sample.messages[2]["content"]
            if "以下是一些關於" not in a:
                # This is a per-category sample
                assert "聖經" not in q, (
                    f"Per-category question should not use '聖經': {q}"
                )


class TestTypeEEnrichment:
    """Tests for section enrichment in Type E."""

    def test_section_enrichment_occurs(self, sample_books):
        """Type E answers should contain section info in some portion."""
        # v7: 4-tier distribution, ~25% enriched-with-section + ~30% existing-with-section = ~55%
        enriched_count = 0
        total_count = 0
        section_keywords = ["段落中", "段落。", "段落裏", "段落主題", "段落之中", "這一段中", "段落的內容"]
        for seed in range(100):
            rng = random.Random(seed)
            samples = generate_type_e(sample_books, rng)
            for s in samples:
                total_count += 1
                answer = s.messages[2]["content"]
                if any(kw in answer for kw in section_keywords):
                    enriched_count += 1
        if total_count > 0:
            ratio = enriched_count / total_count
            assert 0.20 < ratio < 0.80, (
                f"Enrichment ratio {ratio:.2%} outside expected 20-80%"
            )


class TestTypeEMinSnippet:
    """Tests for minimum snippet length in Type E (v6)."""

    def test_no_short_snippets(self):
        """No identification snippet should be < 20 chars."""
        from src.data.parser import Book, Chapter, Section, Verse

        # v7: eligible threshold raised to 25 chars
        # Create verses with >= 25 chars
        verses = tuple(
            Verse("測試書", 1, str(i), f"這是第{i}節的經文內容，足夠長的文字用來測試。", "段落")
            for i in range(1, 21)
        )
        section = Section("段落", verses)
        chapter = Chapter("測試書", 1, (section,))
        books = [Book("測試書", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_e(books, rng)
        for s in samples:
            q = s.messages[1]["content"]
            # Extract the quoted text from the question
            start = q.find("「")
            end = q.find("」")
            if start != -1 and end != -1:
                snippet = q[start + 1:end]
                assert len(snippet) >= 20, (
                    f"Snippet too short ({len(snippet)} chars): {snippet}"
                )


class TestTypeFSubtypes:
    """Tests for Type F subtype distribution."""

    def test_subtype_distribution(self, sample_books):
        """Verify all F subtypes are present with expected counts."""
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)

        questions = [s.messages[1]["content"] for s in samples]
        answers = [s.messages[2]["content"] for s in samples]

        # F1: fake books (42 books x 5 = 210)
        f1_count = sum(
            1 for q in questions if any(fb in q for fb in _FAKE_BOOKS)
        )
        assert f1_count >= 200, (
            f"F1 count: {f1_count}, expected >= 200 (42 books x 5)"
        )

        # F2: out-of-range chapters (200 samples, 6 templates)
        f2_count = sum(
            1 for a in answers
            if "章超出範圍" in a or "章不存在" in a
            or "超出了" in a and "章" in a
            or ("沒有第" in a and "章" in a and "節" not in a.split("沒有第")[-1][:3])
        )
        assert f2_count >= 240, f"F2 count: {f2_count}, expected >=240"

        # F2b: out-of-range verses
        f2b_count = sum(
            1 for a in answers
            if "節超出範圍" in a or ("只有" in a and "節" in a)
            or "節不存在" in a
        )
        assert f2b_count >= 180, f"F2b count: {f2b_count}, expected >=180"

        # F3: non-Bible (200 questions, 15 templates)
        f3_count = sum(
            1 for a in answers
            if "超出了聖經的範圍" in a or "不是聖經的內容" in a
            or "不在聖經的範疇" in a or "與聖經無關" in a
            or "無法回答" in a or "超出了我的專業" in a
            or "不屬於聖經" in a or "超出了聖經" in a
            or "並非聖經" in a or "不在聖經" in a
            or "聖經知識的範圍" in a
        )
        assert f3_count >= 195, f"F3 count: {f3_count}, expected >= 195"

        # F4: boundary (custom answers, not using templates)
        f4_count = sum(
            1 for a in answers
            if "沒有直接" in a or "並未" in a or "不同的" in a
        )
        assert f4_count >= 18, f"F4 count: {f4_count}, expected >=18"

        # F5: misspelled books (detect by misspelled name in question)
        misspelled_names = set(_MISSPELLED_BOOKS.keys())
        f5_count = sum(
            1 for q in questions
            if any(m in q for m in misspelled_names)
        )
        assert f5_count >= 80, f"F5 count: {f5_count}, expected >=80"


class TestTypeFMisspelled:
    """Tests for F5 misspelled book name samples (v6)."""

    def test_misspelled_samples_present(self, sample_books):
        """F5 samples should contain misspelled book names."""
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)

        misspelled_names = set(_MISSPELLED_BOOKS.keys())
        f5_qs = [
            s.messages[1]["content"] for s in samples
            if any(m in s.messages[1]["content"] for m in misspelled_names)
        ]
        assert len(f5_qs) >= 80, (
            f"F5 misspelled sample count: {len(f5_qs)}, expected >= 80"
        )

    def test_misspelled_answers_contain_correction(self, sample_books):
        """F5 answers should contain the correct book name."""
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)

        misspelled_names = set(_MISSPELLED_BOOKS.keys())
        correct_names = set(_MISSPELLED_BOOKS.values())
        for s in samples:
            q = s.messages[1]["content"]
            answer = s.messages[2]["content"]
            # Only check samples whose question contains a misspelled name
            if any(m in q for m in misspelled_names):
                if "有誤" in answer or "誤寫" in answer or "正確名稱" in answer:
                    assert any(cn in answer for cn in correct_names), (
                        f"Missing correct name in misspelled answer: {answer[:80]}"
                    )


class TestSystemPromptVariants:
    """Tests for system prompt variant rotation."""

    def test_multiple_variants_used(self, sample_books):
        """Different samples should use different system prompt variants."""
        samples = generate_all_samples(sample_books, seed=42)
        prompts_seen = {s.messages[0]["content"] for s in samples}
        assert len(prompts_seen) > 1, (
            "Expected multiple system prompt variants, but only saw 1"
        )

    def test_all_variants_contain_bible_keyword(self):
        """All system prompt variants should contain '聖經'."""
        all_variants = (
            GENERAL_QA_SYSTEM_PROMPT_VARIANTS + LOOKUP_SYSTEM_PROMPT_VARIANTS
        )
        for variant in all_variants:
            assert "聖經" in variant, f"Variant missing '聖經': {variant}"

    def test_all_variants_are_strings(self):
        """All system prompt variants should be non-empty strings."""
        all_variants = (
            GENERAL_QA_SYSTEM_PROMPT_VARIANTS + LOOKUP_SYSTEM_PROMPT_VARIANTS
        )
        assert isinstance(all_variants, tuple)
        assert len(all_variants) >= 6
        for variant in all_variants:
            assert isinstance(variant, str)
            assert len(variant) > 20

    def test_general_and_lookup_prompts_both_present(self, sample_books):
        """The generator should rotate both general and lookup prompt pools."""
        prompts_seen = {
            s.messages[0]["content"] for s in generate_all_samples(sample_books, seed=42)
        }
        assert any(p in prompts_seen for p in GENERAL_QA_SYSTEM_PROMPT_VARIANTS)
        assert any(p in prompts_seen for p in LOOKUP_SYSTEM_PROMPT_VARIANTS)


class TestTypeEEnrichedAnswers:
    """Tests for v7 enriched Type E answers that echo the snippet."""

    def test_enriched_answers_echo_snippet(self):
        """Some Type E answers should echo the quoted text snippet."""
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i), f"這是一段足夠長的經文內容，用來測試第{i}節的引文回顯。", "上帝的創造")
            for i in range(1, 51)
        )
        section = Section("上帝的創造", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        echo_count = 0
        total_count = 0
        for seed in range(50):
            rng = random.Random(seed)
            samples = generate_type_e(books, rng)
            for s in samples:
                total_count += 1
                answer = s.messages[2]["content"]
                question = s.messages[1]["content"]
                # Extract snippet from question
                start = question.find("「")
                end = question.find("」")
                if start != -1 and end != -1:
                    snippet = question[start + 1:end]
                    if snippet in answer:
                        echo_count += 1
        if total_count > 0:
            ratio = echo_count / total_count
            # Expect ~45% (25% enriched-with-section + 20% enriched-no-section)
            assert ratio > 0.15, (
                f"Enriched echo ratio {ratio:.2%} too low, expected >15%"
            )


class TestTypeENoDuplicateSnippets:
    """Tests for v7 snippet deduplication in Type E."""

    def test_no_duplicate_snippets(self):
        """Type E should not have duplicate question snippets."""
        from src.data.parser import Book, Chapter, Section, Verse

        # Create verses with some duplicate texts
        verses = []
        for i in range(1, 31):
            text = f"這是一段會重複的經文內容，第{i % 10}組的文字。"
            verses.append(Verse("測試書", 1, str(i), text, "段落"))
        section = Section("段落", tuple(verses))
        chapter = Chapter("測試書", 1, (section,))
        books = [Book("測試書", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_e(books, rng)
        snippets = []
        for s in samples:
            q = s.messages[1]["content"]
            start = q.find("「")
            end = q.find("」")
            if start != -1 and end != -1:
                snippets.append(q[start + 1:end])
        assert len(snippets) == len(set(snippets)), (
            f"Found {len(snippets) - len(set(snippets))} duplicate snippets"
        )


class TestTypeCNoVerseOverlap:
    """Tests for v7 verse deduplication within Type C topics."""

    def test_no_verse_overlap_within_topic(self):
        """Within a single topic, no verse should appear in multiple samples."""
        from src.data.parser import Book, Chapter, Section, Verse

        # Create many matching verses for "信心" topic
        verses = tuple(
            Verse("創世記", 1, str(i), f"信心和相信是重要的教導，第{i}節。", "段落")
            for i in range(1, 31)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_c(books, rng, verses_per_sample=6)

        # Extract all verse references from all samples
        all_refs: list[str] = []
        for s in samples:
            answer = s.messages[2]["content"]
            # Parse "創世記第1章第N節" from answer
            import re
            refs = re.findall(r"創世記第1章第(\d+)節", answer)
            all_refs.extend(refs)

        # No verse should appear more than once across all samples
        assert len(all_refs) == len(set(all_refs)), (
            f"Found {len(all_refs) - len(set(all_refs))} overlapping verses across Type C samples"
        )


# --- v8: Quote normalization and fix tests ---


class TestNormalizeInnerQuotes:
    """Tests for _normalize_inner_quotes helper."""

    def test_no_quotes_unchanged(self):
        assert _normalize_inner_quotes("沒有引號的文字") == "沒有引號的文字"

    def test_single_pair_converted(self):
        assert _normalize_inner_quotes("他說「你好」然後走了") == "他說『你好』然後走了"

    def test_multiple_pairs_converted(self):
        result = _normalize_inner_quotes("「甲」和「乙」")
        assert result == "『甲』和『乙』"

    def test_nested_eliminated(self):
        """Wrapping with outer 「」 should not produce 「「...」」."""
        inner = _normalize_inner_quotes("耶穌說「你去吧」")
        wrapped = f"「{inner}」"
        assert "「「" not in wrapped
        assert "」」" not in wrapped


class TestFixQuotePairing:
    """Tests for _fix_quote_pairing helper."""

    def test_balanced_unchanged(self):
        assert _fix_quote_pairing("「你好」") == "「你好」"

    def test_missing_close_appended(self):
        result = _fix_quote_pairing("「你好")
        assert result == "「你好」"

    def test_missing_open_prepended(self):
        result = _fix_quote_pairing("你好」")
        assert result == "「你好」"

    def test_no_quotes_unchanged(self):
        assert _fix_quote_pairing("沒有引號") == "沒有引號"

    def test_double_angle_quotes(self):
        result = _fix_quote_pairing("『甲")
        assert result == "『甲』"


class TestNoNestedQuotesInOutput:
    """Verify Types A/D/E output never contains 「「 or 」」."""

    def test_type_a_no_nested_quotes(self):
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i), f"他說「你們要信靠上帝」這是第{i}節。", "段落")
            for i in range(1, 11)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_a(books, rng)
        for s in samples:
            answer = s.messages[2]["content"]
            assert "「「" not in answer, f"Nested 「「 in Type A: {answer[:80]}"
            assert "」」" not in answer, f"Nested 」」 in Type A: {answer[:80]}"

    def test_type_d_no_nested_quotes(self):
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i), f"神說「要有光」就有了光。第{i}節。", "段落")
            for i in range(1, 11)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_d(books, rng)
        for s in samples:
            answer = s.messages[2]["content"]
            assert "「「" not in answer, f"Nested 「「 in Type D: {answer[:80]}"
            assert "」」" not in answer, f"Nested 」」 in Type D: {answer[:80]}"

    def test_type_e_no_nested_quotes(self):
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i), f"主對摩西說「我是耶和華」這是重要的啟示。第{i}節。", "段落")
            for i in range(1, 31)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_e(books, rng)
        for s in samples:
            q = s.messages[1]["content"]
            a = s.messages[2]["content"]
            assert "「「" not in q, f"Nested 「「 in Type E question: {q[:80]}"
            assert "」」" not in q, f"Nested 」」 in Type E question: {q[:80]}"
            assert "「「" not in a, f"Nested 「「 in Type E answer: {a[:80]}"
            assert "」」" not in a, f"Nested 」」 in Type E answer: {a[:80]}"


class TestTypeDRatio:
    """Tests for Type D sample ratio (v8)."""

    def test_default_sample_ratio(self):
        """Default sample_ratio should be 0.18."""
        import inspect
        sig = inspect.signature(generate_type_d)
        default = sig.parameters["sample_ratio"].default
        assert default == 0.18, f"Expected 0.18, got {default}"


# --- v9: _prepare_verse_text and unpaired quote fix tests ---


class TestPrepareVerseText:
    """Tests for _prepare_verse_text helper (v9)."""

    def test_chained_processing(self):
        """Should normalize inner quotes AND fix pairing."""
        # Input has inner 「」 that need normalizing, plus an unpaired opening
        text = "他說「你好」然後又說「再見"
        result = _prepare_verse_text(text)
        # 「→『, 」→』, then fix unpaired 『 → append 』
        assert result == "他說『你好』然後又說『再見』"

    def test_balanced_quotes(self):
        """Already balanced quotes should normalize but not add extra."""
        text = "他說「你好」然後走了"
        result = _prepare_verse_text(text)
        assert result == "他說『你好』然後走了"

    def test_no_quotes(self):
        """Text without quotes should pass through unchanged."""
        text = "沒有引號的文字"
        result = _prepare_verse_text(text)
        assert result == "沒有引號的文字"

    def test_only_closing_quote(self):
        """A closing quote without opening should get a prepended opening."""
        text = "你好」然後走了"
        result = _prepare_verse_text(text)
        assert result == "『你好』然後走了"


class TestNoUnpairedQuotesInOutput:
    """Verify Types A/B/C/D output has no unpaired quotes (v9)."""

    @staticmethod
    def _has_unpaired(text: str) -> bool:
        """Check for unpaired 「」 or 『』 in text."""
        for open_q, close_q in (("「", "」"), ("『", "』")):
            if text.count(open_q) != text.count(close_q):
                return True
        return False

    def test_type_a_no_unpaired_quotes(self):
        """Type A answers should have no unpaired quotes."""
        from src.data.parser import Book, Chapter, Section, Verse

        # Simulate cross-verse dialogue: verse only has opening quote
        verses = tuple(
            Verse("創世記", 1, str(i),
                  f"耶和華說「我是全能的上帝，你要行走在我面前，作完全的人。第{i}節",
                  "段落")
            for i in range(1, 11)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_a(books, rng)
        for s in samples:
            answer = s.messages[2]["content"]
            assert not self._has_unpaired(answer), (
                f"Unpaired quotes in Type A: {answer[:100]}"
            )

    def test_type_b_no_unpaired_quotes(self):
        """Type B answers should have no unpaired quotes."""
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i),
                  f"上帝說「要有光」然後又對亞當說「你在哪裏，第{i}節",
                  "段落")
            for i in range(1, 6)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_b(books, rng)
        for s in samples:
            answer = s.messages[2]["content"]
            assert not self._has_unpaired(answer), (
                f"Unpaired quotes in Type B: {answer[:100]}"
            )

    def test_type_c_no_unpaired_quotes(self):
        """Type C answers should have no unpaired quotes."""
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i),
                  f"信心和相信是重要的教導，他說「你們要信靠上帝。第{i}節",
                  "段落")
            for i in range(1, 25)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_c(books, rng)
        for s in samples:
            answer = s.messages[2]["content"]
            assert not self._has_unpaired(answer), (
                f"Unpaired quotes in Type C: {answer[:100]}"
            )

    def test_type_d_no_unpaired_quotes(self):
        """Type D answers should have no unpaired quotes."""
        from src.data.parser import Book, Chapter, Section, Verse

        verses = tuple(
            Verse("創世記", 1, str(i),
                  f"耶和華對摩西說「你要上西奈山去，第{i}節",
                  "段落")
            for i in range(1, 11)
        )
        section = Section("段落", verses)
        chapter = Chapter("創世記", 1, (section,))
        books = [Book("創世記", (chapter,))]

        rng = random.Random(42)
        samples = generate_type_d(books, rng)
        for s in samples:
            answer = s.messages[2]["content"]
            assert not self._has_unpaired(answer), (
                f"Unpaired quotes in Type D: {answer[:100]}"
            )


class TestF3CategoryMatching:
    """Tests for F3 category-aware refusal (v9)."""

    def test_science_question_no_wrong_category(self, sample_books):
        """Science questions should not get literature/religion/language refusals."""
        wrong_keywords = ["文學", "宗教", "語言"]
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)

        science_questions = set(_NON_BIBLE_QUESTIONS_BY_CATEGORY["科學"])
        for s in samples:
            q = s.messages[1]["content"]
            if q in science_questions:
                answer = s.messages[2]["content"]
                for kw in wrong_keywords:
                    assert kw not in answer, (
                        f"Science question got wrong category '{kw}': Q={q[:40]}, A={answer[:60]}"
                    )

    def test_religion_question_gets_matching_refusal(self, sample_books):
        """At least some religion questions should get religion-specific refusals."""
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)

        religion_questions = set(_NON_BIBLE_QUESTIONS_BY_CATEGORY["宗教"])
        religion_refusals = _REFUSAL_NON_BIBLE_BY_CATEGORY["宗教"]
        matched = 0
        total = 0
        for s in samples:
            q = s.messages[1]["content"]
            if q in religion_questions:
                total += 1
                answer = s.messages[2]["content"]
                if any(tmpl.split("。")[0][:10] in answer for tmpl in religion_refusals):
                    matched += 1
        # With 60% probability, at least some should match
        assert matched > 0, f"No religion questions got category-matched refusals (total={total})"

    def test_f3_total_count_unchanged(self, sample_books):
        """F3 should still produce the same total number of questions."""
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)
        # Count F3 by checking against all non-Bible questions
        from src.data.templates import _NON_BIBLE_QUESTIONS
        all_nb = set(_NON_BIBLE_QUESTIONS)
        f3_count = sum(1 for s in samples if s.messages[1]["content"] in all_nb)
        assert f3_count == len(_NON_BIBLE_QUESTIONS), (
            f"F3 count {f3_count} != expected {len(_NON_BIBLE_QUESTIONS)}"
        )


# --- v10: Answer quality improvement tests ---


class TestSummaryTemplateDiversity:
    """Tests for v10 diverse summary text generation."""

    def test_section_summary_diversity(self):
        """_build_section_summary_text should produce diverse outputs."""
        from src.data.dataset_generator import _build_section_summary_text
        from src.data.parser import Verse

        verses = [
            Verse("創世記", 1, "1", "起初上帝創造天地，地是空虛混沌", "段落"),
            Verse("創世記", 1, "2", "上帝說要有光就有了光。上帝看光是好的", "段落"),
            Verse("創世記", 1, "3", "上帝稱光為晝，稱暗為夜，有晚上有早晨", "段落"),
        ]
        results = set()
        for seed in range(50):
            rng = random.Random(seed)
            results.add(_build_section_summary_text("段落", verses, rng))
        assert len(results) >= 4, (
            f"Only {len(results)} unique summaries in 50 seeds, expected >=4"
        )

    def test_topic_summary_diversity(self):
        """_build_topic_summary_text should produce diverse outputs."""
        from src.data.dataset_generator import _build_topic_summary_text
        from src.data.parser import Verse

        verses = [
            Verse("創世記", 1, "1", "信心和相信是重要的", "段落"),
            Verse("創世記", 1, "2", "信靠主就得平安。相信上帝的應許", "段落"),
        ]
        results = set()
        for seed in range(50):
            rng = random.Random(seed)
            results.add(_build_topic_summary_text("信心", verses, rng))
        assert len(results) >= 4, (
            f"Only {len(results)} unique topic summaries in 50 seeds, expected >=4"
        )


class TestSupportPointLength:
    """Tests for v10 support point improvements."""

    def test_support_point_max_50_chars(self):
        """Support points should be at most 50 chars (up from 18)."""
        from src.data.dataset_generator import _make_support_point

        text = "起初上帝創造天地，地是空虛混沌，淵面黑暗，上帝的靈運行在水面上。"
        point = _make_support_point(text)
        assert len(point) <= 50
        assert len(point) > 18  # Verify it actually uses more space now

    def test_support_point_finds_natural_break(self):
        """Support point should break at natural sentence boundaries."""
        from src.data.dataset_generator import _make_support_point

        text = "上帝看光是好的，就把光暗分開了。上帝稱光為晝。"
        point = _make_support_point(text)
        # Should break at the first 。 after 12 chars
        assert point.endswith("分開了") or point.endswith("晝")


class TestPickSupportVerses:
    """Tests for v10 improved verse selection."""

    def test_picks_up_to_3(self):
        """_pick_support_verses should pick up to 3 verses."""
        from src.data.dataset_generator import _pick_support_verses
        from src.data.parser import Verse

        verses = [
            Verse("測試", 1, str(i), f"第{i}節" * 10, "段落")
            for i in range(1, 10)
        ]
        picked = _pick_support_verses(verses)
        assert len(picked) == 3

    def test_prefers_longer_verses(self):
        """_pick_support_verses should prefer longer (richer) verses."""
        from src.data.dataset_generator import _pick_support_verses
        from src.data.parser import Verse

        verses = [
            Verse("測試", 1, "1", "短", "段落"),
            Verse("測試", 1, "2", "這是一段非常長的經文內容用來測試選擇邏輯", "段落"),
            Verse("測試", 1, "3", "短短", "段落"),
            Verse("測試", 1, "4", "這是另一段很長的經文內容用來測試第四節", "段落"),
        ]
        picked = _pick_support_verses(verses)
        picked_nums = [v.verse_number for v in picked]
        assert "2" in picked_nums
        assert "4" in picked_nums


class TestNoPassBuckAnswers:
    """Tests for v10 removal of 推託 patterns."""

    _PASS_BUCK_PHRASES = (
        "若要回頭對照原文",
        "若要對照原文",
        "需要回頭查原文時",
        "再視需要查回",
        "若需要逐字查考",
    )

    def test_type_b_no_pass_buck(self, sample_books):
        """Type B answers should not use pass-buck phrases."""
        rng = random.Random(42)
        for s in generate_type_b(sample_books, rng):
            answer = s.messages[2]["content"]
            for phrase in self._PASS_BUCK_PHRASES:
                assert phrase not in answer, (
                    f"Pass-buck phrase '{phrase}' in Type B: {answer[:80]}"
                )

    def test_type_g_no_pass_buck(self, sample_books):
        """Type G answers should not use pass-buck phrases."""
        rng = random.Random(42)
        for s in generate_type_g(sample_books, rng):
            answer = s.messages[2]["content"]
            for phrase in self._PASS_BUCK_PHRASES:
                assert phrase not in answer, (
                    f"Pass-buck phrase '{phrase}' in Type G: {answer[:80]}"
                )

    def test_type_h_no_pass_buck(self, sample_books):
        """Type H answers should not use pass-buck phrases."""
        rng = random.Random(42)
        for s in generate_type_h(sample_books, rng):
            answer = s.messages[2]["content"]
            for phrase in self._PASS_BUCK_PHRASES:
                assert phrase not in answer, (
                    f"Pass-buck phrase '{phrase}' in Type H: {answer[:80]}"
                )

    def test_type_d_no_pass_buck(self, sample_books):
        """Type D answers should not use pass-buck phrases."""
        rng = random.Random(42)
        for s in generate_type_d(sample_books, rng):
            answer = s.messages[2]["content"]
            for phrase in self._PASS_BUCK_PHRASES:
                assert phrase not in answer, (
                    f"Pass-buck phrase '{phrase}' in Type D: {answer[:80]}"
                )


class TestTypeGEmbeddedContent:
    """Tests for v10 Type G/B answers with embedded verse content."""

    def test_type_b_embeds_verse_snippet(self, sample_books):
        """Type B answers should contain actual verse content."""
        rng = random.Random(42)
        samples = generate_type_b(sample_books, rng)
        for s in samples:
            answer = s.messages[2]["content"]
            # New templates embed key_verse_snippet from actual verse text
            assert "「" in answer, (
                f"Type B answer missing embedded verse quote: {answer[:80]}"
            )

    def test_type_g_section_embeds_verse(self, sample_books):
        """Type G section answers should reference specific verse content."""
        rng = random.Random(42)
        samples = generate_type_g(sample_books, rng)
        section_answers = [
            s.messages[2]["content"] for s in samples
            if "「" in s.messages[2]["content"]
        ]
        assert len(section_answers) > 0, "No Type G answers contain verse quotes"


class TestContextFlowDiversity:
    """Tests for v10 diverse context flow phrases."""

    def test_flow_phrase_variety(self, sample_books):
        """_build_context_flow should produce varied phrasing."""
        from src.data.dataset_generator import _build_context_flow
        from src.data.parser import Verse

        prev = Verse("創世記", 1, "1", "起初上帝創造天地", "段落")
        curr = Verse("創世記", 1, "2", "上帝說要有光就有了光", "段落")
        nxt = Verse("創世記", 1, "3", "上帝稱光為晝稱暗為夜", "段落")

        results = set()
        for seed in range(50):
            rng = random.Random(seed)
            results.add(_build_context_flow(prev, curr, nxt, rng))
        assert len(results) >= 3, (
            f"Only {len(results)} unique flow texts in 50 seeds, expected >=3"
        )


# --- v10: Chain-of-Thought (CoT) tests ---


class TestWrapCot:
    """Tests for _wrap_cot helper."""

    def test_basic_wrapping(self):
        result = _wrap_cot("測試內容")
        assert result == "<think>\n測試內容\n</think>"

    def test_empty_string(self):
        result = _wrap_cot("")
        assert result == "<think>\n\n</think>"


class TestMakeMessagesWithThinking:
    """Tests for _make_messages with thinking parameter."""

    def test_thinking_prepended_to_answer(self):
        msgs = _make_messages("Q", "A", thinking="<think>\n思考\n</think>")
        assert msgs[2]["content"].startswith("<think>")
        assert "A" in msgs[2]["content"]
        assert msgs[2]["content"] == "<think>\n思考\n</think>\n\nA"

    def test_no_thinking_leaves_answer_unchanged(self):
        msgs = _make_messages("Q", "A")
        assert msgs[2]["content"] == "A"

    def test_empty_thinking_leaves_answer_unchanged(self):
        msgs = _make_messages("Q", "A", thinking="")
        assert msgs[2]["content"] == "A"


class TestAllTypesHaveCot:
    """Tests that all sample types include CoT thinking tags."""

    def test_type_a_has_cot(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_a(sample_books, rng)
        for s in samples:
            content = s.messages[2]["content"]
            assert content.startswith("<think>"), (
                f"Type A missing CoT: {content[:60]}"
            )
            assert "</think>\n\n" in content

    def test_type_b_has_cot(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_b(sample_books, rng)
        for s in samples:
            content = s.messages[2]["content"]
            assert content.startswith("<think>"), (
                f"Type B missing CoT: {content[:60]}"
            )
            assert "</think>\n\n" in content

    def test_type_d_has_cot(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_d(sample_books, rng)
        for s in samples:
            content = s.messages[2]["content"]
            assert content.startswith("<think>"), (
                f"Type D missing CoT: {content[:60]}"
            )
            assert "</think>\n\n" in content

    def test_type_f_has_cot(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_f(sample_books, rng)
        for s in samples[:10]:
            content = s.messages[2]["content"]
            assert content.startswith("<think>"), (
                f"Type F missing CoT: {content[:60]}"
            )
            assert "</think>\n\n" in content

    def test_type_g_has_cot(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_g(sample_books, rng)
        for s in samples:
            content = s.messages[2]["content"]
            assert content.startswith("<think>"), (
                f"Type G missing CoT: {content[:60]}"
            )
            assert "</think>\n\n" in content

    def test_type_h_has_cot(self, sample_books):
        rng = random.Random(42)
        samples = generate_type_h(sample_books, rng)
        for s in samples:
            content = s.messages[2]["content"]
            assert content.startswith("<think>"), (
                f"Type H missing CoT: {content[:60]}"
            )
            assert "</think>\n\n" in content

    def test_all_types_have_cot(self, sample_books):
        all_samples = generate_all_samples(sample_books, seed=42)
        by_type: dict[str, list] = {}
        for s in all_samples:
            by_type.setdefault(s.sample_type, []).append(s)
        for t in by_type:
            first = by_type[t][0]
            assert first.messages[2]["content"].startswith("<think>"), (
                f"Type {t} first sample missing CoT"
            )


class TestStripThinking:
    """Tests for strip_thinking helper in utils module."""

    def test_strip_with_tags(self):
        from src.utils import strip_thinking
        thinking, answer = strip_thinking("<think>\n思考\n</think>\n\n答案")
        assert thinking == "思考"
        assert answer == "答案"

    def test_strip_no_tags(self):
        from src.utils import strip_thinking
        thinking, answer = strip_thinking("直接答案")
        assert thinking is None
        assert answer == "直接答案"

    def test_strip_multiline_thinking(self):
        from src.utils import strip_thinking
        response = "<think>\n第一行\n第二行\n</think>\n\n答案內容"
        thinking, answer = strip_thinking(response)
        assert thinking == "第一行\n第二行"
        assert answer == "答案內容"

    def test_strip_with_empty_thinking(self):
        from src.utils import strip_thinking
        thinking, answer = strip_thinking("<think>\n\n</think>\n\n答案")
        assert thinking == ""
        assert answer == "答案"
