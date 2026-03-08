# Section 6: Data Pipeline
cells.append(md("""---
## Section 6: 資料管線

將樣本轉換為 Hugging Face DatasetDict，包含：

1. **問題去重** — 移除重複的 user 問題
2. **長度過濾** — 過濾超過 1400 字元的樣本
3. **分層切分** — 按 sample_type 分層的 train/test split（90%/10%）
4. **儲存 checkpoint** — 可從此處重新載入"""))

cells.append(code("""# ── 驗證與轉換函式 ──

_MAX_TOTAL_CHARS = 1400


def _estimate_too_long(sample: Sample, max_chars: int = _MAX_TOTAL_CHARS) -> bool:
    \"\"\"檢查樣本總字元數是否超過上限。\"\"\"
    total = sum(len(m["content"]) for m in sample.messages)
    return total > max_chars


def _samples_to_dataset_dict(
    samples: list[Sample], test_size: float = 0.1, seed: int = 42
) -> DatasetDict:
    \"\"\"轉換為 HuggingFace DatasetDict（去重 + 長度過濾 + 分層切分）。\"\"\"
    # 問題去重
    seen_questions: set[str] = set()
    deduped: list[Sample] = []
    for s in samples:
        question = s.messages[1]["content"]
        if question not in seen_questions:
            seen_questions.add(question)
            deduped.append(s)

    # 長度過濾
    filtered: list[Sample] = []
    for s in deduped:
        if _estimate_too_long(s):
            total = sum(len(m["content"]) for m in s.messages)
            print(f"  [過濾] 超長樣本 (Type {s.sample_type}, {total} chars): {s.messages[1]['content'][:50]}...")
        else:
            filtered.append(s)

    records = [
        {"sample_type": s.sample_type, "messages": [dict(m) for m in s.messages]}
        for s in filtered
    ]

    dataset = Dataset.from_list(records)

    # ClassLabel cast → 分層切分 → 還原為 string
    type_names = sorted(set(r["sample_type"] for r in records))
    class_label = ClassLabel(names=type_names)
    dataset = dataset.cast_column("sample_type", class_label)

    split = dataset.train_test_split(
        test_size=test_size, seed=seed, stratify_by_column="sample_type",
    )

    result = {}
    for split_name in split:
        ds = split[split_name]
        labels = ds["sample_type"]
        decoded = [class_label.int2str(label) for label in labels]
        ds = ds.remove_columns("sample_type")
        ds = ds.add_column("sample_type", decoded)
        result[split_name] = ds

    return DatasetDict(result)"""))

cells.append(code("""%%time
# ── 執行完整資料管線 ──

print("=" * 60)
print("Bible Fine-Tuning Dataset Builder")
print("=" * 60)

# Step 1: 解析
print("\\n[1/4] 解析聖經 markdown 檔案...")
books = parse_all_books(DATA_DIR)
stats = count_stats(books)
print(f"  書卷: {stats['books']}, 章數: {stats['chapters']}, 段落: {stats['sections']}, 經文: {stats['verses']}")

if stats["books"] != 66:
    print(f"  [警告] 預期 66 卷，實際 {stats['books']} 卷")

# Step 2: 生成樣本
print("\\n[2/4] 生成訓練樣本...")
all_samples = generate_all_samples(books, seed=SEED)
type_counts = Counter(s.sample_type for s in all_samples)
for st in sorted(type_counts):
    print(f"  Type {st}: {type_counts[st]} 筆")
print(f"  總計: {len(all_samples)} 筆")

# Step 3: 建立 Dataset
print("\\n[3/4] 建立 HuggingFace Dataset...")
ds_dict = _samples_to_dataset_dict(all_samples, test_size=CONFIG["dataset"]["test_size"], seed=SEED)
print(f"  Train: {len(ds_dict['train'])} 筆")
print(f"  Test:  {len(ds_dict['test'])} 筆")

print("\\n" + "=" * 60)
print("資料管線完成！")
print("=" * 60)"""))

cells.append(code("""# ── 儲存 Dataset checkpoint ──
dataset_path = os.path.join(OUTPUT_DIR, "bible_dataset")
os.makedirs(dataset_path, exist_ok=True)
ds_dict.save_to_disk(dataset_path)
print(f"Dataset 已儲存至: {dataset_path}")"""))
