# Section 4: Templates (split into 4 code cells)
cells.append(md("""---
## Section 4: 模板系統

定義 6 種樣本類型的問答模板、主題關鍵字、書卷分類與拒絕回應。

| 類型 | 名稱 | 說明 | 佔比 |
|------|------|------|------|
| A | 經文查詢 | 查詢特定經文內容 | ~30% |
| B | 段落摘要 | 概述段落內容 | ~13% |
| C | 主題經文 | 按主題搜尋經文 | ~6% |
| D | 上下文理解 | 提供經文前後文 | ~27% |
| E | 經文辨識 | 辨識經文出處 | ~17% |
| F | 拒絕回應 | 拒答超出範圍的問題 | ~5% |"""))

# Cell 4.2: Type A + B templates
cells.append(code("""# ── Type A: 經文查詢模板 ──

_VERSE_QUERY_TEMPLATES = (
    "{book}第{chapter}章第{verse}節的經文是什麼？",
    "請問{book}第{chapter}章第{verse}節說了什麼？",
    "請引用{book}第{chapter}章第{verse}節的經文。",
    "聖經{book}第{chapter}章{verse}節的內容為何？",
    "幫我查一下{book}第{chapter}章第{verse}節。",
    "{book}第{chapter}章第{verse}節寫了什麼？",
    "請告訴我{book}第{chapter}章第{verse}節的經文。",
    "我想知道{book}{chapter}章{verse}節的經文內容。",
    "{book}{chapter}章{verse}節是怎麼說的？",
    "{book}第{chapter}章第{verse}節記載了什麼？",
    "可以幫我看一下{book}第{chapter}章第{verse}節嗎？",
    "想請教{book}第{chapter}章第{verse}節的經文內容。",
    "我想查{book}{chapter}章{verse}節。",
    "{book}{chapter}:{verse}這段經文是什麼？",
    "請問聖經{book}第{chapter}章第{verse}節是怎麼記載的？",
    "{book}裏面{chapter}章{verse}節怎麼說的？",
    "查經文：{book}第{chapter}章第{verse}節。",
    "關於{book}第{chapter}章第{verse}節，那段經文怎麼寫的？",
    "請查閱{book}第{chapter}章第{verse}節的經文內容。",
    "可以告訴我{book}第{chapter}章第{verse}節的內容嗎？",
    "{book}第{chapter}章第{verse}節的經文內容為何？",
    "我想看{book}第{chapter}章第{verse}節的經文。",
    "麻煩幫我查{book}第{chapter}章第{verse}節。",
    "{book}第{chapter}章第{verse}節說了些什麼？",
    "請問{book}第{chapter}章{verse}節那段經文的內容？",
    "想知道{book}第{chapter}章第{verse}節的記載。",
    "{book}第{chapter}章第{verse}節有什麼經文？",
    "關於{book}{chapter}章{verse}節，聖經是怎麼說的？",
    "請幫我看{book}第{chapter}章第{verse}節的經文。",
    "想了解{book}第{chapter}章第{verse}節記載的內容。",
)

_VERSE_ANSWER_TEMPLATES = (
    "{book}第{chapter}章第{verse}節的經文是：\\n\\n「{text}」",
    "根據{book}第{chapter}章第{verse}節：\\n\\n「{text}」",
    "{book}第{chapter}章第{verse}節記載：\\n\\n「{text}」",
    "以下是{book}第{chapter}章第{verse}節的內容：\\n\\n「{text}」",
    "這段經文記載的是：\\n\\n「{text}」\\n\\n出自{book}第{chapter}章第{verse}節。",
    "好的，{book}第{chapter}章第{verse}節的經文如下：\\n\\n「{text}」",
    "{book}{chapter}章{verse}節寫道：\\n\\n「{text}」",
    "在{book}第{chapter}章第{verse}節中記載：\\n\\n「{text}」",
    "您所詢問的{book}第{chapter}章第{verse}節內容為：\\n\\n「{text}」",
    "這節經文是這樣的：\\n\\n「{text}」\\n\\n——{book}第{chapter}章第{verse}節",
    "查閱{book}第{chapter}章第{verse}節，經文內容為：\\n\\n「{text}」",
    "讓我為您引用{book}第{chapter}章第{verse}節：\\n\\n「{text}」",
    "{book}第{chapter}章第{verse}節是這樣說的：\\n\\n「{text}」",
    "關於{book}第{chapter}章第{verse}節，經文寫道：\\n\\n「{text}」",
)

_VERSE_ANSWER_EXTENDED_TEMPLATES = (
    "這節經文位於{book}第{chapter}章「{section_title}」段落中，第{verse}節記載：\\n\\n「{text}」",
    "{book}第{chapter}章第{verse}節，屬於「{section_title}」這一段的內容：\\n\\n「{text}」",
    "在{book}第{chapter}章的「{section_title}」段落裏，第{verse}節寫道：\\n\\n「{text}」",
    "好的，這段經文出自{book}第{chapter}章「{section_title}」段落：\\n\\n第{verse}節：「{text}」",
    "{book}第{chapter}章第{verse}節的經文如下：\\n\\n「{text}」\\n\\n這節位於「{section_title}」段落之中。",
    "根據{book}第{chapter}章第{verse}節：\\n\\n「{text}」\\n\\n此經文屬於「{section_title}」段落。",
)

# ── Type B: 段落摘要模板 ──

_SECTION_SUMMARY_TEMPLATES = (
    "請概述{book}第{chapter}章「{section}」這段的內容。",
    "{book}第{chapter}章中「{section}」這段經文在講什麼？",
    "請說明{book}第{chapter}章「{section}」段落的主要內容。",
    "請簡單介紹{book}第{chapter}章「{section}」的內容。",
    "聖經{book}第{chapter}章有一段叫「{section}」，這段在講什麼？",
    "{book}第{chapter}章「{section}」的重點是什麼？",
    "可以幫我整理{book}第{chapter}章「{section}」的內容嗎？",
    "「{section}」是{book}第{chapter}章的哪一段？這段在說什麼？",
    "{book}第{chapter}章中「{section}」這個段落包含哪些經文？",
    "請幫我歸納{book}第{chapter}章「{section}」段落的重點。",
)

_SECTION_ANSWER_TEMPLATES = (
    "{book}第{chapter}章「{section}」這段的內容如下：\\n\\n{verses_text}",
    "在{book}第{chapter}章中，「{section}」這段經文記載了以下內容：\\n\\n{verses_text}",
    "以下是{book}第{chapter}章「{section}」段落的經文：\\n\\n{verses_text}",
    "關於{book}第{chapter}章的「{section}」，其內容如下：\\n\\n{verses_text}",
    "好的，{book}第{chapter}章「{section}」段落的經文內容為：\\n\\n{verses_text}",
    "讓我為您查閱{book}第{chapter}章「{section}」的內容：\\n\\n{verses_text}",
    "{book}第{chapter}章中「{section}」這段記載如下：\\n\\n{verses_text}",
    "「{section}」出現在{book}第{chapter}章，經文內容為：\\n\\n{verses_text}",
    "您詢問的{book}第{chapter}章「{section}」段落包含以下經文：\\n\\n{verses_text}",
    "{book}第{chapter}章「{section}」的段落經文如下所示：\\n\\n{verses_text}",
)"""))
