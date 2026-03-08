# Section 3: Parser
cells.append(md("""---
## Section 3: 聖經解析器

將 66 卷聖經 Markdown 檔案解析為結構化 Python 物件（`Book → Chapter → Section → Verse`）。

### Markdown 格式規則

```
# 創世記           ← H1: 書卷名稱
## 第 1 章          ← H2: 章號
### 上帝創造天地    ← H3: 段落標題
**1** 起初⋯⋯       ← 粗體數字: 節號 + 經文
```

### 邊界案例處理

| 案例 | 說明 | 處理方式 |
|------|------|----------|
| Broken H3 | `### 的君」。` | 偵測短文＋非句尾前行 → 合併至前一節 |
| 交叉引用 | `### （路3‧23-38）` | regex 過濾 |
| 音樂註記 | `（細拉）` | 過濾 |
| 多行詩歌 | 詩篇跨行經文 | 累積至下一節號 |
| 合併節號 | `**1-2**` | verse_number 以 str 儲存 |
| 註腳區塊 | `---` + `**註腳**` | 跳過後續行 |"""))

cells.append(code("""# ── 資料結構（frozen dataclass）與 Regex ──

@dataclass(frozen=True)
class Verse:
    book: str
    chapter: int
    verse_number: str  # str 以支援 "1-2" 合併節
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


# Regex 模式
_RE_H1 = re.compile(r"^# (.+)$")
_RE_H2 = re.compile(r"^## 第 (\\d+) 章$")
_RE_H3 = re.compile(r"^### (.+)$")
_RE_VERSE = re.compile(r"^\\*\\*(\\d+(?:-\\d+)?)\\*\\*\\s*(.*)$")
_RE_BROKEN_H3 = re.compile(r"^### .{1,6}[。！？，」）]$")
_RE_CROSS_REF = re.compile(r"^### （.+）$")
_RE_HORIZONTAL_RULE = re.compile(r"^-{3,}$")
_RE_FOOTNOTE_MARKER = re.compile(r"^\\*\\*註腳")
_RE_CHAPTER_VERSE_REF = re.compile(r"\\d+‧\\d+")


def _is_broken_h3(line: str, prev_line: str) -> bool:
    \"\"\"偵測因行寬截斷產生的假 H3 標題。\"\"\"
    if not _RE_BROKEN_H3.match(line):
        return False
    stripped = prev_line.rstrip()
    if not stripped:
        return True
    return stripped[-1] not in "。！？」）；：\\n"


def _is_cross_ref_or_annotation(line: str) -> bool:
    \"\"\"偵測交叉引用與音樂註記。\"\"\"
    if _RE_CROSS_REF.match(line):
        return True
    if not line.startswith("### "):
        return False
    content = line[4:]
    if content.startswith("（") and _RE_CHAPTER_VERSE_REF.search(content):
        return True
    if content.startswith("*") and _RE_CHAPTER_VERSE_REF.search(content):
        return True
    return False"""))

cells.append(code("""# ── 解析函式 ──

def parse_book(filepath: str) -> Book:
    \"\"\"解析單卷聖經 Markdown 檔案為 Book dataclass。\"\"\"
    with open(filepath, "r", encoding="utf-8") as _f:
        text = _f.read()
    lines = text.split("\\n")

    book_name = ""
    chapters: list[Chapter] = []
    current_chapter_num = 0
    current_section_title = ""
    current_sections: list[Section] = []
    current_verses: list[Verse] = []
    current_verse_num = ""
    current_verse_lines: list[str] = []
    prev_content_line = ""
    in_footnote = False

    def _flush_verse() -> None:
        nonlocal current_verse_num, current_verse_lines
        if current_verse_num and current_verse_lines:
            verse_text = "\\n".join(current_verse_lines).strip()
            if verse_text:
                current_verses.append(
                    Verse(book=book_name, chapter=current_chapter_num,
                          verse_number=current_verse_num, text=verse_text,
                          section_title=current_section_title)
                )
        current_verse_num = ""
        current_verse_lines = []

    def _flush_section() -> None:
        nonlocal current_verses
        _flush_verse()
        if current_verses:
            current_sections.append(
                Section(title=current_section_title, verses=tuple(current_verses))
            )
            current_verses = []

    def _flush_chapter() -> None:
        nonlocal current_sections
        _flush_section()
        if current_sections and current_chapter_num > 0:
            chapters.append(
                Chapter(book=book_name, number=current_chapter_num,
                        sections=tuple(current_sections))
            )
            current_sections = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _RE_HORIZONTAL_RULE.match(stripped):
            _flush_verse()
            continue
        h1_match = _RE_H1.match(stripped)
        if h1_match:
            book_name = h1_match.group(1)
            continue
        h2_match = _RE_H2.match(stripped)
        if h2_match:
            _flush_chapter()
            current_chapter_num = int(h2_match.group(1))
            current_section_title = ""
            in_footnote = False
            continue
        h3_match = _RE_H3.match(stripped)
        if h3_match:
            if _is_cross_ref_or_annotation(stripped):
                continue
            if _is_broken_h3(stripped, prev_content_line):
                broken_text = h3_match.group(1)
                if current_verse_lines:
                    current_verse_lines.append(broken_text)
                elif current_verses:
                    last = current_verses[-1]
                    current_verses[-1] = Verse(
                        book=last.book, chapter=last.chapter,
                        verse_number=last.verse_number,
                        text=last.text + broken_text,
                        section_title=last.section_title,
                    )
                prev_content_line = broken_text
                continue
            _flush_section()
            current_section_title = h3_match.group(1)
            continue
        verse_match = _RE_VERSE.match(stripped)
        if verse_match:
            _flush_verse()
            current_verse_num = verse_match.group(1)
            verse_text = verse_match.group(2).strip()
            current_verse_lines = [verse_text] if verse_text else []
            prev_content_line = stripped
            continue
        if _RE_FOOTNOTE_MARKER.match(stripped):
            _flush_verse()
            in_footnote = True
            continue
        if in_footnote:
            continue
        if current_verse_num:
            current_verse_lines.append(stripped)
            prev_content_line = stripped
            continue
        prev_content_line = stripped

    _flush_chapter()
    return Book(name=book_name, chapters=tuple(chapters))


def parse_all_books(data_dir: str) -> list[Book]:
    \"\"\"解析目錄下所有聖經 Markdown 檔案，依檔名排序。\"\"\"
    md_files = sorted(glob.glob(os.path.join(data_dir, "*.md")))
    if not md_files:
        raise FileNotFoundError(f"No markdown files found in {data_dir}")
    books = []
    for filepath in md_files:
        book = parse_book(filepath)
        if book.chapters:
            books.append(book)
    return books


def count_stats(books: list[Book]) -> dict[str, int]:
    \"\"\"統計解析結果。\"\"\"
    return {
        "books": len(books),
        "chapters": sum(len(b.chapters) for b in books),
        "sections": sum(len(c.sections) for b in books for c in b.chapters),
        "verses": sum(
            len(s.verses) for b in books for c in b.chapters for s in c.sections
        ),
    }"""))
