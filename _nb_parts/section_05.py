# Section 5: Sample Generator
cells.append(md("""---
## Section 5: 樣本生成器

根據解析後的聖經結構與模板系統，生成 6 種類型的訓練樣本。

### 生成策略

| 類型 | 策略 |
|------|------|
| A | 漸進式降採樣（8%/18%/30%）+ 書卷最低保證（30 筆） |
| B | 過濾空標題段落 + 長段落截斷（>1500 字元取前 8 節） |
| C | 主題關鍵字匹配 + 類別/整體/新舊約 多面向生成 |
| D | 18% 章節取樣 + 前後文組裝 |
| E | 25 字元門檻 + snippet 去重 + 4 層回答豐富化 |
| F | 假書/超範圍/非聖經/邊界/錯字 五類拒絕樣本 |"""))

cells.append(code("""# ── Sample dataclass 與輔助函式 ──

_MIN_SAMPLES_PER_BOOK = 30


@dataclass(frozen=True)
class Sample:
    \"\"\"單一訓練樣本。\"\"\"
    sample_type: str  # A, B, C, D, E, F
    messages: tuple[dict[str, str], ...]


def _make_messages(
    question: str, answer: str, system_prompt: str = SYSTEM_PROMPT
) -> tuple[dict[str, str], ...]:
    \"\"\"建立 TRL SFT 格式的 messages tuple。\"\"\"
    return (
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    )


def _collect_all_verses(books: list[Book]) -> list[Verse]:
    \"\"\"展平所有書卷的經文。\"\"\"
    return [
        v for book in books for chapter in book.chapters
        for section in chapter.sections for v in section.verses
    ]


def _build_chapter_verse_list(chapter: Chapter) -> list[Verse]:
    \"\"\"取得章內所有經文（按順序）。\"\"\"
    return [v for s in chapter.sections for v in s.verses]


def _normalize_inner_quotes(text: str) -> str:
    \"\"\"將內層「」轉為『』，避免模板包裹後產生巢狀引號。\"\"\"
    return text.replace("「", "『").replace("」", "』")


def _fix_quote_pairing(text: str) -> str:
    \"\"\"修復不成對的引號（截斷後可能產生）。\"\"\"
    for open_q, close_q in (("「", "」"), ("『", "』")):
        n_open = text.count(open_q)
        n_close = text.count(close_q)
        if n_open > n_close:
            text = text + close_q * (n_open - n_close)
        elif n_close > n_open:
            text = open_q * (n_close - n_open) + text
    return text


def _prepare_verse_text(text: str) -> str:
    \"\"\"正規化內層引號並修復配對。\"\"\"
    return _fix_quote_pairing(_normalize_inner_quotes(text))


def _make_snippet(text: str) -> str:
    \"\"\"從經文中擷取有意義的片段用於辨識。\"\"\"
    snippet = text
    if len(snippet) > 50:
        for sep in ("。", "；", "，"):
            pos = snippet.find(sep, 20)
            if pos != -1:
                snippet = snippet[:pos + 1]
                break
        else:
            snippet = snippet[:50] + "……"
    return snippet"""))

cells.append(code("""# ── Type A, B, C 生成器 ──

def generate_type_a(books: list[Book], rng: random.Random) -> list[Sample]:
    \"\"\"經文查詢樣本（漸進式降採樣 + 書卷最低保證）。\"\"\"
    eligible_per_book: dict[str, list[Verse]] = {}
    for book in books:
        book_verses = [
            v for ch in book.chapters for sec in ch.sections
            for v in sec.verses if len(v.text) >= 15
        ]
        if book_verses:
            eligible_per_book[book.name] = book_verses

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

    samples = []
    for verses in sampled_per_book.values():
        for verse in verses:
            sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
            template = rng.choice(_VERSE_QUERY_TEMPLATES)
            question = template.format(
                book=verse.book, chapter=verse.chapter, verse=verse.verse_number,
            )
            use_extended = verse.section_title and rng.random() < 0.60
            if use_extended:
                answer_template = rng.choice(_VERSE_ANSWER_EXTENDED_TEMPLATES)
                answer = answer_template.format(
                    book=verse.book, chapter=verse.chapter,
                    verse=verse.verse_number, text=_prepare_verse_text(verse.text),
                    section_title=verse.section_title,
                )
            else:
                answer_template = rng.choice(_VERSE_ANSWER_TEMPLATES)
                answer = answer_template.format(
                    book=verse.book, chapter=verse.chapter,
                    verse=verse.verse_number, text=_prepare_verse_text(verse.text),
                )
            samples.append(Sample(sample_type="A", messages=_make_messages(question, answer, sys_prompt)))
    return samples


def generate_type_b(books: list[Book], rng: random.Random) -> list[Sample]:
    \"\"\"段落摘要樣本（過濾空標題 + 長段落截斷）。\"\"\"
    samples = []
    for book in books:
        for chapter in book.chapters:
            for section in chapter.sections:
                if not section.verses or not section.title:
                    continue
                sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
                template = rng.choice(_SECTION_SUMMARY_TEMPLATES)
                question = template.format(
                    book=book.name, chapter=chapter.number, section=section.title,
                )
                full_text = "\\n".join(
                    f"第{v.verse_number}節：{_fix_quote_pairing(v.text)}" for v in section.verses
                )
                if len(full_text) <= _MAX_SECTION_ANSWER_CHARS:
                    verses_text = full_text
                else:
                    shown = section.verses[:8]
                    verses_text = "\\n".join(
                        f"第{v.verse_number}節：{_fix_quote_pairing(v.text)}" for v in shown
                    )
                    verses_text += (
                        f"\\n\\n（本段共{len(section.verses)}節經文，"
                        f"以上列出前{len(shown)}節）"
                    )
                answer_template = rng.choice(_SECTION_ANSWER_TEMPLATES)
                answer = answer_template.format(
                    book=book.name, chapter=chapter.number,
                    section=section.title, verses_text=verses_text,
                )
                samples.append(Sample(sample_type="B", messages=_make_messages(question, answer, sys_prompt)))
    return samples


def _match_topic(verse_text: str, topic_config: dict) -> bool:
    \"\"\"檢查經文是否匹配主題（含排除規則）。\"\"\"
    includes = topic_config["include"]
    excludes = topic_config["exclude"]
    if not any(kw in verse_text for kw in includes):
        return False
    if excludes and any(kw in verse_text for kw in excludes):
        return False
    return True


def _build_topic_index(books: list[Book]) -> dict[str, list[Verse]]:
    \"\"\"建立主題 → 經文索引。\"\"\"
    index: dict[str, list[Verse]] = {topic: [] for topic in TOPIC_KEYWORDS}
    for verse in _collect_all_verses(books):
        for topic, config in TOPIC_KEYWORDS.items():
            if _match_topic(verse.text, config):
                index[topic].append(verse)
    return index


def _get_testament_for_category(category: str) -> str | None:
    for testament, categories in _TESTAMENT_CATEGORIES.items():
        if category in categories:
            return testament
    return None


def generate_type_c(books: list[Book], rng: random.Random, verses_per_sample: int = 6) -> list[Sample]:
    \"\"\"主題經文樣本（多面向生成）。\"\"\"
    index = _build_topic_index(books)
    samples = []
    for topic, all_verses in index.items():
        if len(all_verses) < 3:
            continue
        used_verse_ids: set[int] = set()
        category_verses: dict[str, list[Verse]] = {}
        for v in all_verses:
            cat = _BOOK_TO_CATEGORY.get(v.book, "其他")
            category_verses.setdefault(cat, []).append(v)

        for cat, cat_verses in category_verses.items():
            if len(cat_verses) < 1:
                continue
            available = [v for v in cat_verses if id(v) not in used_verse_ids]
            if not available:
                continue
            sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
            n_show = min(len(available), verses_per_sample)
            selected = rng.sample(available, n_show)
            used_verse_ids.update(id(v) for v in selected)
            template = rng.choice(_THEMATIC_CATEGORY_TEMPLATES)
            question = template.format(category=cat, topic=topic)
            verse_lines_text = "\\n".join(
                f"- {v.book}第{v.chapter}章第{v.verse_number}節：「{_prepare_verse_text(v.text)}」"
                for v in selected
            )
            answer_template = rng.choice(_THEMATIC_CATEGORY_ANSWER_TEMPLATES)
            answer = answer_template.format(category=cat, topic=topic, verse_lines=verse_lines_text)
            samples.append(Sample(sample_type="C", messages=_make_messages(question, answer, sys_prompt)))

        for overall_idx in range(3):
            if overall_idx == 1 and len(all_verses) < verses_per_sample * 2:
                break
            elif overall_idx == 2 and len(all_verses) < verses_per_sample * 3:
                break
            available = [v for v in all_verses if id(v) not in used_verse_ids]
            if len(available) < 1:
                break
            sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
            n_show = min(len(available), verses_per_sample)
            selected = rng.sample(available, n_show)
            used_verse_ids.update(id(v) for v in selected)
            template = rng.choice(_THEMATIC_TEMPLATES)
            question = template.format(topic=topic)
            verse_lines_text = "\\n".join(
                f"- {v.book}第{v.chapter}章第{v.verse_number}節：「{_prepare_verse_text(v.text)}」"
                for v in selected
            )
            answer_template = rng.choice(_THEMATIC_ANSWER_TEMPLATES)
            answer = answer_template.format(topic=topic, verse_lines=verse_lines_text)
            samples.append(Sample(sample_type="C", messages=_make_messages(question, answer, sys_prompt)))

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
            sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
            n_show = min(len(available), verses_per_sample)
            selected = rng.sample(available, n_show)
            used_verse_ids.update(id(v) for v in selected)
            template = rng.choice(_THEMATIC_TESTAMENT_TEMPLATES)
            question = template.format(testament=testament, topic=topic)
            verse_lines_text = "\\n".join(
                f"- {v.book}第{v.chapter}章第{v.verse_number}節：「{_prepare_verse_text(v.text)}」"
                for v in selected
            )
            answer_template = rng.choice(_THEMATIC_TESTAMENT_ANSWER_TEMPLATES)
            answer = answer_template.format(testament=testament, topic=topic, verse_lines=verse_lines_text)
            samples.append(Sample(sample_type="C", messages=_make_messages(question, answer, sys_prompt)))
    return samples"""))

cells.append(code("""# ── Type D, E, F 生成器 ──

def generate_type_d(books: list[Book], rng: random.Random, sample_ratio: float = 0.18) -> list[Sample]:
    \"\"\"上下文理解樣本。\"\"\"
    samples = []
    for book in books:
        for chapter in book.chapters:
            all_verses = _build_chapter_verse_list(chapter)
            if len(all_verses) < 3:
                continue
            n_samples = max(1, int(len(all_verses) * sample_ratio))
            selected_indices = rng.sample(range(len(all_verses)), n_samples)
            for idx in selected_indices:
                verse = all_verses[idx]
                sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
                template = rng.choice(_CONTEXT_TEMPLATES)
                question = template.format(book=verse.book, chapter=verse.chapter, verse=verse.verse_number)
                parts = []
                if idx > 0:
                    prev = all_verses[idx - 1]
                    parts.append(f"前文（第{prev.verse_number}節）：「{_prepare_verse_text(prev.text)}」")
                parts.append(f"本節（第{verse.verse_number}節）：「{_prepare_verse_text(verse.text)}」")
                if idx < len(all_verses) - 1:
                    nxt = all_verses[idx + 1]
                    parts.append(f"後文（第{nxt.verse_number}節）：「{_prepare_verse_text(nxt.text)}」")
                context_text = "\\n".join(parts)
                section_info = (
                    f"\\n\\n這節經文位於「{verse.section_title}」段落中。"
                    if verse.section_title else ""
                )
                answer_template = rng.choice(_CONTEXT_ANSWER_TEMPLATES)
                answer = answer_template.format(
                    book=verse.book, chapter=verse.chapter, verse=verse.verse_number,
                    context_text=context_text, section_info=section_info,
                )
                samples.append(Sample(sample_type="D", messages=_make_messages(question, answer, sys_prompt)))
    return samples


def generate_type_e(books: list[Book], rng: random.Random, sample_ratio: float = 0.15) -> list[Sample]:
    \"\"\"經文辨識樣本（snippet 去重 + 4 層回答豐富化）。\"\"\"
    all_verses = _collect_all_verses(books)
    eligible = [v for v in all_verses if len(v.text) >= 25]
    n_target = max(1, int(len(eligible) * sample_ratio))
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
        sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
        text_snippet = _make_snippet(verse.text)
        if len(text_snippet) < 20:
            text_snippet = verse.text
        text_snippet = _fix_quote_pairing(text_snippet)
        text_snippet = _normalize_inner_quotes(text_snippet)
        template = rng.choice(_IDENTIFICATION_TEMPLATES)
        question = template.format(text=text_snippet)
        roll = rng.random()
        if verse.section_title and roll < 0.30:
            answer_template = rng.choice(_IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION)
            answer = answer_template.format(
                text=text_snippet, book=verse.book, chapter=verse.chapter,
                verse=verse.verse_number, section_title=verse.section_title,
            )
        elif roll < 0.55:
            answer_template = rng.choice(_IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION)
            answer = answer_template.format(
                text=text_snippet, book=verse.book, chapter=verse.chapter, verse=verse.verse_number,
            )
        elif verse.section_title and roll < 0.80:
            answer_template = rng.choice(_IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES)
            answer = answer_template.format(
                book=verse.book, chapter=verse.chapter,
                verse=verse.verse_number, section_title=verse.section_title,
            )
        else:
            answer_template = rng.choice(_IDENTIFICATION_ANSWER_TEMPLATES)
            answer = answer_template.format(book=verse.book, chapter=verse.chapter, verse=verse.verse_number)
        samples.append(Sample(sample_type="E", messages=_make_messages(question, answer, sys_prompt)))
    return samples


def generate_type_f(books: list[Book], rng: random.Random) -> list[Sample]:
    \"\"\"拒絕樣本（5 類）。\"\"\"
    samples = []
    max_chapters: dict[str, int] = {}
    for book in books:
        if book.chapters:
            max_chapters[book.name] = max(c.number for c in book.chapters)

    # F1: 假書
    for fake_book in _FAKE_BOOKS:
        for ch in rng.sample(range(1, 11), 5):
            v = rng.randint(1, 20)
            sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
            template = rng.choice(_FAKE_QUERY_TEMPLATES)
            question = template.format(book=fake_book, ch=ch, v=v)
            answer = rng.choice(_REFUSAL_NONEXISTENT_BOOK).format(book=fake_book)
            samples.append(Sample(sample_type="F", messages=_make_messages(question, answer, sys_prompt)))

    # F2: 超出章數範圍
    real_books = list(max_chapters.keys())
    for _ in range(280):
        book_name = rng.choice(real_books)
        max_ch = max_chapters[book_name]
        fake_ch = max_ch + rng.randint(1, 50)
        v = rng.randint(1, 30)
        sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
        template = rng.choice(_FAKE_QUERY_TEMPLATES)
        question = template.format(book=book_name, ch=fake_ch, v=v)
        answer = rng.choice(_REFUSAL_OUT_OF_RANGE).format(book=book_name, max_ch=max_ch, ch=fake_ch)
        samples.append(Sample(sample_type="F", messages=_make_messages(question, answer, sys_prompt)))

    # F2b: 超出節數範圍
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
        sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
        template = rng.choice(_FAKE_QUERY_TEMPLATES)
        question = template.format(book=book_name, ch=ch, v=fake_v)
        answer = rng.choice(_REFUSAL_OUT_OF_RANGE_VERSE).format(book=book_name, ch=ch, max_v=max_v, v=fake_v)
        samples.append(Sample(sample_type="F", messages=_make_messages(question, answer, sys_prompt)))

    # F3: 非聖經問題（類別感知拒絕）
    for category, questions in _NON_BIBLE_QUESTIONS_BY_CATEGORY.items():
        cat_templates = _REFUSAL_NON_BIBLE_BY_CATEGORY.get(category)
        for question in questions:
            sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
            if cat_templates and rng.random() < 0.60:
                answer = rng.choice(cat_templates)
            else:
                answer = rng.choice(_REFUSAL_NON_BIBLE_GENERIC)
            samples.append(Sample(sample_type="F", messages=_make_messages(question, answer, sys_prompt)))

    # F4: 邊界問題
    for question, answer in _BOUNDARY_QUESTIONS:
        sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
        samples.append(Sample(sample_type="F", messages=_make_messages(question, answer, sys_prompt)))

    # F5: 書名錯字
    for wrong_name, correct_name in _MISSPELLED_BOOKS.items():
        for _ in range(5):
            ch = rng.randint(1, 10)
            v = rng.randint(1, 20)
            sys_prompt = rng.choice(SYSTEM_PROMPT_VARIANTS)
            template = rng.choice(_FAKE_QUERY_TEMPLATES)
            question = template.format(book=wrong_name, ch=ch, v=v)
            answer = rng.choice(_REFUSAL_MISSPELLED_BOOK).format(book=wrong_name, correct_book=correct_name)
            samples.append(Sample(sample_type="F", messages=_make_messages(question, answer, sys_prompt)))
    return samples"""))

cells.append(code("""# ── 總指揮 ──

def generate_all_samples(books: list[Book], seed: int = 42) -> list[Sample]:
    \"\"\"生成所有訓練樣本（6 種類型）。\"\"\"
    rng = random.Random(seed)
    samples: list[Sample] = []
    samples.extend(generate_type_a(books, rng))
    samples.extend(generate_type_b(books, rng))
    samples.extend(generate_type_c(books, rng))
    samples.extend(generate_type_d(books, rng))
    samples.extend(generate_type_e(books, rng))
    samples.extend(generate_type_f(books, rng))
    return samples"""))
