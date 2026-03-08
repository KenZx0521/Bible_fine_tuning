# Section 4 continued: Cell 4.3 (Type C templates + topics + book categories)
cells.append(code("""# ── Type C: 主題經文模板 ──

_THEMATIC_TEMPLATES = (
    "聖經中有哪些關於「{topic}」的經文？",
    "請列出聖經中提到「{topic}」的經文。",
    "聖經裏關於「{topic}」的教導有哪些？",
    "「{topic}」這個主題在聖經中有哪些相關經文？",
    "我想了解聖經中關於「{topic}」的經文。",
    "可以幫我找聖經裏跟「{topic}」有關的經文嗎？",
    "聖經對於「{topic}」有什麼樣的教導？",
    "請問聖經哪些地方有提到「{topic}」？",
)

_THEMATIC_CATEGORY_TEMPLATES = (
    "{category}中有哪些關於「{topic}」的經文？",
    "請列出{category}中提到「{topic}」的經文。",
    "{category}裏關於「{topic}」的教導有哪些？",
    "「{topic}」這個主題在{category}中有哪些相關經文？",
    "我想看看{category}中跟「{topic}」相關的經文。",
    "可以幫我查{category}裏面關於「{topic}」的經文嗎？",
    "{category}對「{topic}」有哪些教導或記載？",
    "請問{category}中哪些經文跟「{topic}」有關？",
)

_THEMATIC_ANSWER_TEMPLATES = (
    "以下是一些關於「{topic}」的經文：\\n\\n{verse_lines}",
    "聖經中關於「{topic}」的經文如下：\\n\\n{verse_lines}",
    "關於「{topic}」，以下是相關的聖經經文：\\n\\n{verse_lines}",
    "讓我為您列出聖經中提到「{topic}」的經文：\\n\\n{verse_lines}",
    "以下經文與「{topic}」這個主題相關：\\n\\n{verse_lines}",
    "聖經裏提到「{topic}」的經文有：\\n\\n{verse_lines}",
    "好的，以下是與「{topic}」相關的聖經經文：\\n\\n{verse_lines}",
    "為您整理聖經中關於「{topic}」的經文如下：\\n\\n{verse_lines}",
)

_THEMATIC_CATEGORY_ANSWER_TEMPLATES = (
    "以下是{category}中關於「{topic}」的經文：\\n\\n{verse_lines}",
    "{category}中提到「{topic}」的經文如下：\\n\\n{verse_lines}",
    "關於「{topic}」，{category}中有以下記載：\\n\\n{verse_lines}",
    "在{category}裏，與「{topic}」相關的經文有：\\n\\n{verse_lines}",
    "好的，{category}中與「{topic}」相關的經文如下：\\n\\n{verse_lines}",
    "{category}裏提到「{topic}」的經文有這些：\\n\\n{verse_lines}",
    "讓我為您列出{category}中關於「{topic}」的經文：\\n\\n{verse_lines}",
    "為您查閱{category}中與「{topic}」相關的記載：\\n\\n{verse_lines}",
)

_TESTAMENT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "舊約": ("律法書", "歷史書", "詩歌智慧書", "大先知書", "小先知書"),
    "新約": ("福音書", "教會歷史", "保羅書信", "一般書信", "啟示文學"),
}

_THEMATIC_TESTAMENT_TEMPLATES = (
    "{testament}中有哪些關於「{topic}」的經文？",
    "請列出{testament}中提到「{topic}」的經文。",
    "{testament}裏關於「{topic}」的教導有哪些？",
    "「{topic}」這個主題在{testament}中有哪些相關經文？",
    "我想了解{testament}中關於「{topic}」的經文。",
    "可以幫我找{testament}裏跟「{topic}」有關的經文嗎？",
    "{testament}對於「{topic}」有什麼樣的教導？",
    "請問{testament}哪些地方有提到「{topic}」？",
)

_THEMATIC_TESTAMENT_ANSWER_TEMPLATES = (
    "以下是{testament}中關於「{topic}」的經文：\\n\\n{verse_lines}",
    "{testament}中提到「{topic}」的經文如下：\\n\\n{verse_lines}",
    "關於「{topic}」，{testament}中有以下記載：\\n\\n{verse_lines}",
    "在{testament}裏，與「{topic}」相關的經文有：\\n\\n{verse_lines}",
)

# ── 主題關鍵字（58 個主題，含 include/exclude 規則）──

TOPIC_KEYWORDS: dict[str, dict] = {
    "創造": {"include": ["創造", "造物", "起初"], "exclude": ["建造", "打造", "製造", "造訪"]},
    "救贖": {"include": ["救贖", "拯救", "救恩", "得救"], "exclude": []},
    "信心": {"include": ["信心", "相信", "信靠"], "exclude": ["書信", "信差", "送信"]},
    "愛": {"include": ["慈愛", "仁愛", "愛人", "愛心", "相愛"], "exclude": []},
    "立約": {"include": ["立約", "盟約", "新約", "守約"], "exclude": []},
    "先知預言": {"include": ["預言", "先知"], "exclude": []},
    "禱告": {"include": ["禱告", "祈禱", "祈求", "呼求"], "exclude": []},
    "智慧": {"include": ["智慧", "聰明"], "exclude": []},
    "公義": {"include": ["公義", "正義", "公正"], "exclude": []},
    "盼望": {"include": ["盼望", "指望", "仰望"], "exclude": []},
    "恩典": {"include": ["恩典", "恩惠"], "exclude": []},
    "平安": {"include": ["平安"], "exclude": []},
    "審判": {"include": ["審判", "刑罰", "懲罰"], "exclude": []},
    "罪與赦免": {"include": ["罪孽", "過犯", "犯罪", "赦免"], "exclude": []},
    "悔改": {"include": ["悔改", "回轉", "歸向"], "exclude": []},
    "聖靈": {"include": ["聖靈"], "exclude": []},
    "永生": {"include": ["永生", "永遠的生命"], "exclude": []},
    "敬拜讚美": {"include": ["敬拜", "頌讚", "讚美", "稱頌"], "exclude": []},
    "順服": {"include": ["順服", "順從", "遵行", "遵守"], "exclude": []},
    "苦難": {"include": ["苦難", "患難", "受苦"], "exclude": []},
    "復活": {"include": ["復活", "從死裏"], "exclude": []},
    "天國": {"include": ["天國", "天上的國", "上帝的國", "神的國"], "exclude": []},
    "十字架": {"include": ["十字架", "釘十字架"], "exclude": []},
    "洗禮": {"include": ["洗禮", "受洗", "施洗"], "exclude": []},
    "聖殿": {"include": ["聖殿", "殿裏", "殿中"], "exclude": []},
    "天使": {"include": ["天使"], "exclude": ["高天使"]},
    "喜樂": {"include": ["喜樂", "歡喜", "喜悅"], "exclude": []},
    "饒恕": {"include": ["饒恕", "寬恕", "原諒"], "exclude": []},
    "謙卑": {"include": ["謙卑", "謙虛", "謙遜"], "exclude": []},
    "試探": {"include": ["試探", "誘惑", "引誘"], "exclude": []},
    "光明": {"include": ["光明", "光照", "發光"], "exclude": ["刀劍", "槍矛", "銅"]},
    "安息": {"include": ["安息", "歇息"], "exclude": ["安息日"]},
    "應許": {"include": ["應許", "應驗"], "exclude": []},
    "聖潔": {"include": ["聖潔", "潔淨"], "exclude": []},
    "忍耐": {"include": ["忍耐", "忍受"], "exclude": []},
    "感恩": {"include": ["感恩", "感謝", "稱謝"], "exclude": []},
    "僕人": {"include": ["僕人", "奴僕", "服事"], "exclude": []},
    "牧者": {"include": ["牧者", "牧人", "牧羊"], "exclude": []},
    "葡萄園": {"include": ["葡萄園", "葡萄樹"], "exclude": []},
    "生命": {"include": ["生命", "活水", "生命樹"], "exclude": []},
    "死亡": {"include": ["死亡", "死人", "陰間"], "exclude": ["安息"]},
    "耶路撒冷": {"include": ["耶路撒冷", "錫安"], "exclude": []},
    "出埃及": {"include": ["出埃及", "法老"], "exclude": []},
    "獻祭": {"include": ["獻祭", "祭物", "燔祭"], "exclude": []},
    "律法": {"include": ["律法", "誡命", "典章"], "exclude": []},
    "醫治": {"include": ["醫治", "醫好", "痊癒"], "exclude": []},
    "神蹟": {"include": ["神蹟", "奇事", "異能"], "exclude": []},
    "合一": {"include": ["合一", "同心", "合而為一"], "exclude": []},
    "祝福": {"include": ["祝福", "賜福", "蒙福"], "exclude": []},
    "揀選": {"include": ["揀選", "選召", "選民"], "exclude": []},
    "榮耀": {"include": ["榮耀", "榮光"], "exclude": []},
    "安慰": {"include": ["安慰", "慰藉"], "exclude": []},
    "爭戰": {"include": ["爭戰", "打仗", "戰爭"], "exclude": []},
    "曠野": {"include": ["曠野", "沙漠", "荒野"], "exclude": []},
    "安息日": {"include": ["安息日"], "exclude": []},
    "逾越節": {"include": ["逾越節", "逾越"], "exclude": []},
    "比喻": {"include": ["比喻", "比方"], "exclude": []},
    "見證": {"include": ["見證", "作證"], "exclude": []},
    "異象": {"include": ["異象", "異夢"], "exclude": []},
    "仇敵": {"include": ["仇敵", "敵人", "對敵"], "exclude": []},
    "豐收": {"include": ["豐收", "收割", "莊稼"], "exclude": []},
    "使命": {"include": ["使命", "差遣", "差派"], "exclude": []},
    "天父": {"include": ["天父", "父神"], "exclude": []},
    "羔羊": {"include": ["羔羊", "羊羔"], "exclude": []},
    "誠實": {"include": ["誠實", "真誠", "誠信"], "exclude": []},
    "勇氣": {"include": ["勇敢", "壯膽", "剛強"], "exclude": []},
    "貧窮": {"include": ["貧窮", "窮人", "貧乏"], "exclude": []},
    "寶血": {"include": ["寶血", "血約", "流血"], "exclude": []},
    "教會": {"include": ["教會", "會眾"], "exclude": []},
    "福音": {"include": ["福音", "好消息"], "exclude": []},
    "呼召": {"include": ["呼召", "蒙召"], "exclude": []},
    "權柄": {"include": ["權柄", "權能", "權勢"], "exclude": []},
    "憐憫": {"include": ["憐憫", "憐恤", "施恩"], "exclude": []},
    "產業": {"include": ["產業", "基業", "地業"], "exclude": []},
    "約櫃": {"include": ["約櫃", "法櫃"], "exclude": []},
    "恩賜": {"include": ["恩賜", "屬靈的恩賜"], "exclude": []},
    "末世": {"include": ["末世", "末後", "末日"], "exclude": []},
    "受膏": {"include": ["受膏", "膏抹", "彌賽亞"], "exclude": []},
}

# ── 書卷分類 ──

_BOOK_CATEGORIES: dict[str, tuple[str, ...]] = {
    "律法書": ("創世記", "出埃及記", "利未記", "民數記", "申命記"),
    "歷史書": (
        "約書亞記", "士師記", "路得記", "撒母耳記上", "撒母耳記下",
        "列王紀上", "列王紀下", "歷代志上", "歷代志下", "以斯拉記",
        "尼希米記", "以斯帖記",
    ),
    "詩歌智慧書": ("約伯記", "詩篇", "箴言", "傳道書", "雅歌"),
    "大先知書": ("以賽亞書", "耶利米書", "耶利米哀歌", "以西結書", "但以理書"),
    "小先知書": (
        "何西阿書", "約珥書", "阿摩司書", "俄巴底亞書", "約拿書",
        "彌迦書", "那鴻書", "哈巴谷書", "西番雅書", "哈該書",
        "撒迦利亞書", "瑪拉基書",
    ),
    "福音書": ("馬太福音", "馬可福音", "路加福音", "約翰福音"),
    "教會歷史": ("使徒行傳",),
    "保羅書信": (
        "羅馬書", "哥林多前書", "哥林多後書", "加拉太書", "以弗所書",
        "腓立比書", "歌羅西書", "帖撒羅尼迦前書", "帖撒羅尼迦後書",
        "提摩太前書", "提摩太後書", "提多書", "腓利門書",
    ),
    "一般書信": (
        "希伯來書", "雅各書", "彼得前書", "彼得後書",
        "約翰一書", "約翰二書", "約翰三書", "猶大書",
    ),
    "啟示文學": ("啟示錄",),
}

_BOOK_TO_CATEGORY: dict[str, str] = {}
for _cat, _book_names in _BOOK_CATEGORIES.items():
    for _bn in _book_names:
        _BOOK_TO_CATEGORY[_bn] = _cat"""))
