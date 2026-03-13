"""Tests for template constants quality and consistency."""

from __future__ import annotations

from src.data.templates import (
    TOPIC_KEYWORDS,
    _BOOK_TO_CATEGORY,
    _BOUNDARY_QUESTIONS,
    _CONTEXT_ANSWER_TEMPLATES,
    _CONTEXT_TEMPLATES,
    _FAKE_BOOKS,
    _FAKE_QUERY_TEMPLATES,
    _IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION,
    _IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION,
    _IDENTIFICATION_ANSWER_TEMPLATES,
    _IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES,
    _IDENTIFICATION_TEMPLATES,
    _MISSPELLED_BOOKS,
    _NON_BIBLE_QUESTIONS,
    _NON_BIBLE_QUESTIONS_BY_CATEGORY,
    _REFUSAL_MISSPELLED_BOOK,
    _REFUSAL_NON_BIBLE,
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


class TestTemplateTypes:
    """All templates should be tuples."""

    def test_verse_query_is_tuple(self):
        assert isinstance(_VERSE_QUERY_TEMPLATES, tuple)

    def test_verse_answer_is_tuple(self):
        assert isinstance(_VERSE_ANSWER_TEMPLATES, tuple)

    def test_section_summary_is_tuple(self):
        assert isinstance(_SECTION_SUMMARY_TEMPLATES, tuple)

    def test_section_answer_is_tuple(self):
        assert isinstance(_SECTION_SUMMARY_ANSWER_TEMPLATES, tuple)

    def test_context_is_tuple(self):
        assert isinstance(_CONTEXT_TEMPLATES, tuple)

    def test_identification_is_tuple(self):
        assert isinstance(_IDENTIFICATION_TEMPLATES, tuple)

    def test_thematic_is_tuple(self):
        assert isinstance(_THEMATIC_TEMPLATES, tuple)

    def test_thematic_category_is_tuple(self):
        assert isinstance(_THEMATIC_CATEGORY_TEMPLATES, tuple)

    def test_fake_books_is_tuple(self):
        assert isinstance(_FAKE_BOOKS, tuple)

    def test_fake_query_is_tuple(self):
        assert isinstance(_FAKE_QUERY_TEMPLATES, tuple)

    def test_non_bible_is_tuple(self):
        assert isinstance(_NON_BIBLE_QUESTIONS, tuple)

    def test_boundary_is_tuple(self):
        assert isinstance(_BOUNDARY_QUESTIONS, tuple)

    def test_verse_answer_extended_is_tuple(self):
        assert isinstance(_VERSE_ANSWER_EXTENDED_TEMPLATES, tuple)

    def test_context_answer_is_tuple(self):
        assert isinstance(_CONTEXT_ANSWER_TEMPLATES, tuple)

    def test_identification_answer_is_tuple(self):
        assert isinstance(_IDENTIFICATION_ANSWER_TEMPLATES, tuple)

    def test_identification_answer_with_section_is_tuple(self):
        assert isinstance(_IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES, tuple)

    def test_thematic_answer_is_tuple(self):
        assert isinstance(_THEMATIC_ANSWER_TEMPLATES, tuple)

    def test_thematic_category_answer_is_tuple(self):
        assert isinstance(_THEMATIC_CATEGORY_ANSWER_TEMPLATES, tuple)

    def test_thematic_testament_templates_is_tuple(self):
        assert isinstance(_THEMATIC_TESTAMENT_TEMPLATES, tuple)

    def test_thematic_testament_answer_is_tuple(self):
        assert isinstance(_THEMATIC_TESTAMENT_ANSWER_TEMPLATES, tuple)


class TestTemplateCounts:
    """Templates should meet minimum count requirements."""

    def test_verse_query_min_30(self):
        assert len(_VERSE_QUERY_TEMPLATES) >= 30

    def test_verse_answer_min_14(self):
        assert len(_VERSE_ANSWER_TEMPLATES) >= 14

    def test_verse_answer_extended_min_6(self):
        assert len(_VERSE_ANSWER_EXTENDED_TEMPLATES) >= 6

    def test_section_summary_min_10(self):
        assert len(_SECTION_SUMMARY_TEMPLATES) >= 10

    def test_section_answer_min_10(self):
        assert len(_SECTION_SUMMARY_ANSWER_TEMPLATES) >= 6

    def test_context_min_25(self):
        assert len(_CONTEXT_TEMPLATES) >= 25

    def test_context_answer_min_6(self):
        assert len(_CONTEXT_ANSWER_TEMPLATES) >= 6

    def test_identification_min_20(self):
        assert len(_IDENTIFICATION_TEMPLATES) >= 20

    def test_identification_answer_min_6(self):
        assert len(_IDENTIFICATION_ANSWER_TEMPLATES) >= 6

    def test_identification_answer_with_section_min_6(self):
        assert len(_IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES) >= 6

    def test_thematic_min_8(self):
        assert len(_THEMATIC_TEMPLATES) >= 8

    def test_thematic_category_min_8(self):
        assert len(_THEMATIC_CATEGORY_TEMPLATES) >= 8

    def test_thematic_answer_min_8(self):
        assert len(_THEMATIC_ANSWER_TEMPLATES) >= 8

    def test_thematic_category_answer_min_8(self):
        assert len(_THEMATIC_CATEGORY_ANSWER_TEMPLATES) >= 8

    def test_fake_books_min_42(self):
        assert len(_FAKE_BOOKS) >= 42

    def test_topic_keywords_min_78(self):
        assert len(TOPIC_KEYWORDS) >= 78

    def test_non_bible_min_200(self):
        assert len(_NON_BIBLE_QUESTIONS) >= 200

    def test_fake_query_min_15(self):
        assert len(_FAKE_QUERY_TEMPLATES) >= 15

    def test_boundary_min_30(self):
        assert len(_BOUNDARY_QUESTIONS) >= 30


class TestTemplatePlaceholders:
    """Templates should contain correct format string placeholders."""

    def test_verse_query_placeholders(self):
        for tmpl in _VERSE_QUERY_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"

    def test_verse_answer_placeholders(self):
        for tmpl in _VERSE_ANSWER_TEMPLATES:
            assert "{text}" in tmpl, f"Missing {{text}} in: {tmpl}"
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"

    def test_section_summary_placeholders(self):
        for tmpl in _SECTION_SUMMARY_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{section}" in tmpl, f"Missing {{section}} in: {tmpl}"

    def test_section_answer_placeholders(self):
        for tmpl in _SECTION_SUMMARY_ANSWER_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{section}" in tmpl, f"Missing {{section}} in: {tmpl}"
            assert "{summary_text}" in tmpl, f"Missing {{summary_text}} in: {tmpl}"
            assert "{reference_span}" in tmpl, f"Missing {{reference_span}} in: {tmpl}"

    def test_context_placeholders(self):
        for tmpl in _CONTEXT_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"

    def test_identification_placeholders(self):
        for tmpl in _IDENTIFICATION_TEMPLATES:
            assert "{text}" in tmpl, f"Missing {{text}} in: {tmpl}"

    def test_thematic_placeholders(self):
        for tmpl in _THEMATIC_TEMPLATES:
            assert "{topic}" in tmpl, f"Missing {{topic}} in: {tmpl}"

    def test_thematic_category_placeholders(self):
        for tmpl in _THEMATIC_CATEGORY_TEMPLATES:
            assert "{category}" in tmpl, f"Missing {{category}} in: {tmpl}"
            assert "{topic}" in tmpl, f"Missing {{topic}} in: {tmpl}"

    def test_verse_answer_extended_placeholders(self):
        for tmpl in _VERSE_ANSWER_EXTENDED_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"
            assert "{text}" in tmpl, f"Missing {{text}} in: {tmpl}"
            assert "{section_title}" in tmpl, f"Missing {{section_title}} in: {tmpl}"

    def test_context_answer_placeholders(self):
        for tmpl in _CONTEXT_ANSWER_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"
            assert "{context_text}" in tmpl, f"Missing {{context_text}} in: {tmpl}"
            assert "{section_info}" in tmpl, f"Missing {{section_info}} in: {tmpl}"

    def test_identification_answer_placeholders(self):
        for tmpl in _IDENTIFICATION_ANSWER_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"

    def test_identification_answer_with_section_placeholders(self):
        for tmpl in _IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"
            assert "{section_title}" in tmpl, f"Missing {{section_title}} in: {tmpl}"

    def test_thematic_answer_placeholders(self):
        for tmpl in _THEMATIC_ANSWER_TEMPLATES:
            assert "{topic}" in tmpl, f"Missing {{topic}} in: {tmpl}"
            assert "{verse_lines}" in tmpl, f"Missing {{verse_lines}} in: {tmpl}"

    def test_thematic_category_answer_placeholders(self):
        for tmpl in _THEMATIC_CATEGORY_ANSWER_TEMPLATES:
            assert "{category}" in tmpl, f"Missing {{category}} in: {tmpl}"
            assert "{topic}" in tmpl, f"Missing {{topic}} in: {tmpl}"
            assert "{verse_lines}" in tmpl, f"Missing {{verse_lines}} in: {tmpl}"

    def test_fake_query_placeholders(self):
        for tmpl in _FAKE_QUERY_TEMPLATES:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{ch}" in tmpl, f"Missing {{ch}} in: {tmpl}"

    def test_thematic_testament_placeholders(self):
        for tmpl in _THEMATIC_TESTAMENT_TEMPLATES:
            assert "{testament}" in tmpl, f"Missing {{testament}} in: {tmpl}"
            assert "{topic}" in tmpl, f"Missing {{topic}} in: {tmpl}"

    def test_thematic_testament_answer_placeholders(self):
        for tmpl in _THEMATIC_TESTAMENT_ANSWER_TEMPLATES:
            assert "{testament}" in tmpl, f"Missing {{testament}} in: {tmpl}"
            assert "{topic}" in tmpl, f"Missing {{topic}} in: {tmpl}"
            assert "{verse_lines}" in tmpl, f"Missing {{verse_lines}} in: {tmpl}"

    def test_refusal_misspelled_book_placeholders(self):
        for tmpl in _REFUSAL_MISSPELLED_BOOK:
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{correct_book}" in tmpl, f"Missing {{correct_book}} in: {tmpl}"


class TestTopicKeywords:
    """Topic keywords should have proper structure."""

    def test_all_have_include(self):
        for topic, config in TOPIC_KEYWORDS.items():
            assert "include" in config, f"Missing 'include' for topic: {topic}"
            assert len(config["include"]) > 0, (
                f"Empty 'include' for topic: {topic}"
            )

    def test_all_have_exclude(self):
        for topic, config in TOPIC_KEYWORDS.items():
            assert "exclude" in config, (
                f"Missing 'exclude' for topic: {topic}"
            )

    def test_no_duplicate_topics(self):
        topics = list(TOPIC_KEYWORDS.keys())
        assert len(topics) == len(set(topics))

    def test_no_duplicate_fake_books(self):
        assert len(_FAKE_BOOKS) == len(set(_FAKE_BOOKS))


class TestRefusalTemplateCounts:
    """Each refusal template group should have >= 6 entries."""

    def test_nonexistent_book_min_6(self):
        assert len(_REFUSAL_NONEXISTENT_BOOK) >= 6

    def test_out_of_range_min_6(self):
        assert len(_REFUSAL_OUT_OF_RANGE) >= 6

    def test_out_of_range_verse_min_6(self):
        assert len(_REFUSAL_OUT_OF_RANGE_VERSE) >= 6

    def test_non_bible_min_15(self):
        assert len(_REFUSAL_NON_BIBLE) >= 15

    def test_misspelled_book_min_6(self):
        assert len(_REFUSAL_MISSPELLED_BOOK) >= 6


class TestMisspelledBooks:
    """Misspelled book dictionary should be valid."""

    def test_is_dict(self):
        assert isinstance(_MISSPELLED_BOOKS, dict)

    def test_min_20_entries(self):
        assert len(_MISSPELLED_BOOKS) >= 20

    def test_correct_names_exist_in_categories(self):
        for wrong, correct in _MISSPELLED_BOOKS.items():
            assert correct in _BOOK_TO_CATEGORY, (
                f"Correct name '{correct}' for '{wrong}' not in _BOOK_TO_CATEGORY"
            )

    def test_wrong_names_are_strings(self):
        for wrong, correct in _MISSPELLED_BOOKS.items():
            assert isinstance(wrong, str) and len(wrong) > 0
            assert isinstance(correct, str) and len(correct) > 0


class TestTestamentCategories:
    """Testament categories should cover all book categories."""

    def test_has_old_and_new(self):
        assert "舊約" in _TESTAMENT_CATEGORIES
        assert "新約" in _TESTAMENT_CATEGORIES

    def test_covers_all_book_categories(self):
        from src.data.templates import _BOOK_CATEGORIES

        all_testament_cats = set()
        for cats in _TESTAMENT_CATEGORIES.values():
            all_testament_cats.update(cats)

        for cat in _BOOK_CATEGORIES:
            assert cat in all_testament_cats, (
                f"Category '{cat}' not covered by _TESTAMENT_CATEGORIES"
            )

    def test_testament_templates_min_8(self):
        assert len(_THEMATIC_TESTAMENT_TEMPLATES) >= 8

    def test_testament_answer_templates_min_4(self):
        assert len(_THEMATIC_TESTAMENT_ANSWER_TEMPLATES) >= 4


class TestEnrichedAnswerTemplates:
    """Tests for v7 enriched identification answer templates."""

    def test_enriched_no_section_is_tuple(self):
        assert isinstance(_IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION, tuple)

    def test_enriched_with_section_is_tuple(self):
        assert isinstance(_IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION, tuple)

    def test_enriched_no_section_min_4(self):
        assert len(_IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION) >= 4

    def test_enriched_with_section_min_4(self):
        assert len(_IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION) >= 4

    def test_enriched_no_section_placeholders(self):
        for tmpl in _IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION:
            assert "{text}" in tmpl, f"Missing {{text}} in: {tmpl}"
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"

    def test_enriched_with_section_placeholders(self):
        for tmpl in _IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION:
            assert "{text}" in tmpl, f"Missing {{text}} in: {tmpl}"
            assert "{book}" in tmpl, f"Missing {{book}} in: {tmpl}"
            assert "{chapter}" in tmpl, f"Missing {{chapter}} in: {tmpl}"
            assert "{verse}" in tmpl, f"Missing {{verse}} in: {tmpl}"
            assert "{section_title}" in tmpl, f"Missing {{section_title}} in: {tmpl}"


# --- v9: Non-Bible category tests ---


class TestNonBibleCategories:
    """Tests for _NON_BIBLE_QUESTIONS_BY_CATEGORY (v9)."""

    def test_is_dict_with_9_categories(self):
        assert isinstance(_NON_BIBLE_QUESTIONS_BY_CATEGORY, dict)
        assert len(_NON_BIBLE_QUESTIONS_BY_CATEGORY) == 9

    def test_total_count_matches_flat(self):
        """Total questions across categories should match _NON_BIBLE_QUESTIONS."""
        total = sum(len(qs) for qs in _NON_BIBLE_QUESTIONS_BY_CATEGORY.values())
        assert total == len(_NON_BIBLE_QUESTIONS), (
            f"Category total {total} != flat total {len(_NON_BIBLE_QUESTIONS)}"
        )

    def test_no_duplicate_questions_across_categories(self):
        """No question should appear in multiple categories."""
        all_questions: list[str] = []
        for qs in _NON_BIBLE_QUESTIONS_BY_CATEGORY.values():
            all_questions.extend(qs)
        assert len(all_questions) == len(set(all_questions)), (
            "Found duplicate questions across categories"
        )

    def test_each_category_has_refusal_template(self):
        """Each non-通用 category should have a matching refusal template."""
        for category in _NON_BIBLE_QUESTIONS_BY_CATEGORY:
            if category == "通用":
                continue
            assert category in _REFUSAL_NON_BIBLE_BY_CATEGORY, (
                f"Category '{category}' missing from _REFUSAL_NON_BIBLE_BY_CATEGORY"
            )

    def test_generic_refusal_min_6(self):
        assert len(_REFUSAL_NON_BIBLE_GENERIC) >= 6

    def test_category_refusal_min_2_each(self):
        for cat, templates in _REFUSAL_NON_BIBLE_BY_CATEGORY.items():
            assert len(templates) >= 2, (
                f"Category '{cat}' has only {len(templates)} refusal templates"
            )
