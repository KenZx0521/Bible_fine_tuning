# Section 4 continued: Cell 4.4 (Type D + E templates)
cells.append(code("""# ── Type D: 上下文理解模板 ──

_CONTEXT_TEMPLATES = (
    "{book}第{chapter}章第{verse}節的上下文是什麼？",
    "請提供{book}第{chapter}章第{verse}節的前後文背景。",
    "{book}第{chapter}章第{verse}節出現在什麼樣的段落背景中？",
    "請解釋{book}第{chapter}章第{verse}節的上下文脈絡。",
    "幫我看看{book}第{chapter}章第{verse}節的前後文。",
    "{book}{chapter}章{verse}節出現在什麼語境之中？",
    "請問{book}第{chapter}章第{verse}節前後在說些什麼？",
    "{book}第{chapter}章第{verse}節附近的經文是什麼？",
    "我想了解{book}第{chapter}章第{verse}節的上下文。",
    "請幫我查一下{book}第{chapter}章第{verse}節的段落背景。",
    "請描述{book}第{chapter}章第{verse}節的段落背景與上下文。",
    "請問{book}第{chapter}章第{verse}節這段經文的來龍去脈。",
    "{book}第{chapter}章第{verse}節附近有哪些相關的經文？",
    "可以幫我看看{book}第{chapter}章第{verse}節所在段落的完整內容嗎？",
    "想知道{book}第{chapter}章第{verse}節前後的經文在講什麼。",
    "{book}第{chapter}章第{verse}節這節經文周圍的內容是什麼？",
    "請問{book}第{chapter}章第{verse}節前後各有什麼經文？",
    "幫我理解{book}第{chapter}章第{verse}節的上下文脈絡。",
    "{book}{chapter}章{verse}節的段落主題和前後文是什麼？",
    "請告訴我{book}第{chapter}章第{verse}節前一節和後一節的內容。",
    "{book}第{chapter}章第{verse}節的上下文環境是怎樣的？",
    "我想看{book}第{chapter}章第{verse}節周邊的經文。",
    "請問{book}第{chapter}章第{verse}節是在討論什麼主題時提到的？",
    "關於{book}第{chapter}章第{verse}節，它的上文和下文分別是什麼？",
    "{book}第{chapter}章第{verse}節在整段經文中的位置和前後文是什麼？",
)

_CONTEXT_ANSWER_TEMPLATES = (
    "{book}第{chapter}章第{verse}節的上下文如下：\\n\\n{context_text}{section_info}",
    "以下是{book}第{chapter}章第{verse}節的前後文：\\n\\n{context_text}{section_info}",
    "讓我為您查閱{book}第{chapter}章第{verse}節的上下文脈絡：\\n\\n{context_text}{section_info}",
    "{book}{chapter}章{verse}節出現在以下段落之中：\\n\\n{context_text}{section_info}",
    "關於{book}第{chapter}章第{verse}節的段落背景：\\n\\n{context_text}{section_info}",
    "好的，以下是{book}第{chapter}章第{verse}節附近的經文內容：\\n\\n{context_text}{section_info}",
)

# ── Type E: 經文辨識模板 ──

_IDENTIFICATION_TEMPLATES = (
    "「{text}」這句經文出自聖經哪裏？",
    "「{text}」這段話是聖經哪一卷哪一章哪一節？",
    "請問「{text}」出自聖經的什麼地方？",
    "「{text}」是哪卷書的經文？",
    "「{text}」這句話在聖經哪裏？",
    "請幫我找一下「{text}」這段經文的出處。",
    "「{text}」是聖經裏面哪個地方的？",
    "有一段經文說「{text}」，這是出自哪裏的？",
    "請查閱「{text}」這段經文出自聖經何處。",
    "「{text}」這段話的聖經出處為何？",
    "請問「{text}」記載在聖經的哪一卷書？",
    "「{text}」這句經文的出處與章節為何？",
    "我記得聖經裏有一段「{text}」，請問出自哪裏？",
    "「{text}」好像是聖經的經文，可以告訴我出處嗎？",
    "想確認一下「{text}」是不是聖經的內容，出自哪裏？",
    "聽過一句「{text}」，請問這是聖經哪一段？",
    "幫我查經文「{text}」的出處。",
    "可以幫我確認「{text}」是出自聖經哪裏嗎？",
    "想請教「{text}」這段經文是來自哪卷書？",
    "麻煩查一下「{text}」出自聖經第幾卷第幾章。",
)

_IDENTIFICATION_ANSWER_TEMPLATES = (
    "這句經文出自{book}第{chapter}章第{verse}節。",
    "這段話記載在{book}第{chapter}章第{verse}節。",
    "您引用的經文出自{book}第{chapter}章第{verse}節。",
    "這是{book}第{chapter}章第{verse}節的經文。",
    "經查閱，這句話出自{book}第{chapter}章第{verse}節。",
    "這段經文的出處是{book}第{chapter}章第{verse}節。",
)

_IDENTIFICATION_ANSWER_WITH_SECTION_TEMPLATES = (
    "這句經文出自{book}第{chapter}章第{verse}節，位於「{section_title}」段落中。",
    "這段話記載在{book}第{chapter}章第{verse}節，屬於「{section_title}」段落。",
    "您引用的經文出自{book}第{chapter}章第{verse}節，出現在「{section_title}」這一段中。",
    "經查閱，這句話出自{book}第{chapter}章第{verse}節，段落主題為「{section_title}」。",
    "這段經文來自{book}第{chapter}章第{verse}節，位於「{section_title}」的段落之中。",
    "這是{book}第{chapter}章第{verse}節的經文，收錄在「{section_title}」段落裏。",
)

_IDENTIFICATION_ANSWER_ENRICHED_NO_SECTION = (
    "您引用的「{text}」這段經文出自{book}第{chapter}章第{verse}節。",
    "「{text}」記載在{book}第{chapter}章第{verse}節中。",
    "這段話「{text}」的出處是{book}第{chapter}章第{verse}節。",
    "經查閱，「{text}」出自{book}第{chapter}章第{verse}節。",
)

_IDENTIFICATION_ANSWER_ENRICHED_WITH_SECTION = (
    "「{text}」記載在{book}第{chapter}章第{verse}節中。這節經文位於「{section_title}」段落。",
    "經查閱，「{text}」出自{book}第{chapter}章第{verse}節，屬於「{section_title}」段落的內容。",
    "您所引用的「{text}」來自{book}第{chapter}章第{verse}節，收錄在「{section_title}」段落之中。",
    "沒錯，「{text}」的確出自{book}第{chapter}章第{verse}節，位於「{section_title}」段落。",
)"""))
