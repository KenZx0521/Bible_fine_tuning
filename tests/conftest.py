"""Shared test fixtures for Bible fine-tuning tests."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.data.parser import Book, Chapter, Section, Verse


@pytest.fixture
def sample_markdown(tmp_path: Path) -> Path:
    """Create a minimal Bible markdown file for testing."""
    content = textwrap.dedent("""\
        # 測試書

        ## 第 1 章

        ### 段落一

        **1** 這是第一節經文。

        **2** 這是第二節經文，比較長一些。

        **3** 這是第三節經文。

        ### 段落二

        **4** 這是第四節。

        **5** 這是第五節。

        ## 第 2 章

        ### 另一個段落

        **1** 第二章的第一節。

        **2** 第二章的第二節。
    """)
    filepath = tmp_path / "測試書.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


@pytest.fixture
def psalm_markdown(tmp_path: Path) -> Path:
    """Create a Psalms-like markdown with multi-line poetry and edge cases."""
    content = textwrap.dedent("""\
        # 測試詩篇

        ## 第 1 章

        ### 真福

        **1** 不從惡人的計謀，
        不站罪人的道路，
        不坐褻慢人的座位，

        **2** 惟喜愛耶和華的律法，
        晝夜思想，
        這人便為有福！

        ## 第 2 章

        ### 上帝所揀選的君王

        **1** 外邦為甚麼爭鬧？

        ### （細拉）

        **2** 世上的君王一齊起來。

        ## 第 3 章

        **1** 你們將我的尊榮變為羞辱要到幾

        ### 時呢？

        ### （細拉）

        **2** 第三章第二節。
    """)
    filepath = tmp_path / "測試詩篇.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


@pytest.fixture
def cross_ref_markdown(tmp_path: Path) -> Path:
    """Create markdown with cross-references."""
    content = textwrap.dedent("""\
        # 測試書卷

        ## 第 1 章

        ### 開篇

        **1** 第一節。

        ### （出20‧1－17）

        **2** 第二節。

        **3** 第三節。
    """)
    filepath = tmp_path / "測試書卷.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


@pytest.fixture
def footnote_markdown(tmp_path: Path) -> Path:
    """Create markdown with footnote blocks at end of chapters."""
    content = textwrap.dedent("""\
        # 測試註腳書

        ## 第 1 章

        ### 段落一

        **1** 第一章第一節經文。

        **2** 第一章第二節經文。

        ---
        **註腳：**
        - 1:1: 或譯：「初始之時」。
        - 1:2: 希伯來文：ruach。

        ## 第 2 章

        ### 段落二

        **1** 第二章第一節經文。

        **2** 第二章第二節經文。

        ---
        **註腳：**
        - 2:1: 古譯本作「聖所」。
    """)
    filepath = tmp_path / "測試註腳書.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


@pytest.fixture
def parallel_ref_markdown(tmp_path: Path) -> Path:
    """Create markdown with incomplete parenthetical and asterisk references."""
    content = textwrap.dedent("""\
        # 測試平行書

        ## 第 1 章

        ### 最後的晚餐

        **1** 第一節經文。

        ### （太26‧20－25；可14‧17－21；路

        **2** 第二節經文。

        ### *王下18‧13－37*

        **3** 第三節經文。

        ### （太26‧69－70；可14‧66－68；路22‧55－57)

        **4** 第四節經文。

        ### 以利沙和便‧哈達王

        **5** 第五節經文。
    """)
    filepath = tmp_path / "測試平行書.md"
    filepath.write_text(content, encoding="utf-8")
    return filepath


@pytest.fixture
def sample_books() -> list[Book]:
    """Create sample Book objects for testing generators."""
    verses_s1 = (
        Verse("創世記", 1, "1", "起初，上帝創造天地。地是空虛混沌，淵面黑暗；上帝的靈運行在水面上。", "上帝的創造"),
        Verse("創世記", 1, "2", "上帝說：「要有光」，就有了光。上帝看光是好的，就把光暗分開了。", "上帝的創造"),
        Verse("創世記", 1, "3", "上帝稱光為「晝」，稱暗為「夜」。有晚上，有早晨，這是頭一日。", "上帝的創造"),
    )
    verses_s2 = (
        Verse("創世記", 1, "4", "上帝說：「諸水之間要有空氣，將水分為上下。」上帝就造出空氣，將空氣以下的水、空氣以上的水分開了。事就這樣成了。", "光暗分開"),
        Verse("創世記", 1, "5", "上帝稱空氣為「天」。有晚上，有早晨，是第二日。", "光暗分開"),
    )
    section1 = Section("上帝的創造", verses_s1)
    section2 = Section("光暗分開", verses_s2)
    chapter1 = Chapter("創世記", 1, (section1, section2))

    verses_ch2 = (
        Verse("創世記", 2, "1", "天地萬物都造齊了。", "第七日安息"),  # 9 chars — tests filtering
    )
    section_ch2 = Section("第七日安息", verses_ch2)
    chapter2 = Chapter("創世記", 2, (section_ch2,))

    book = Book("創世記", (chapter1, chapter2))
    return [book]
