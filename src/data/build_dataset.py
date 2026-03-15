"""Build HuggingFace Dataset from Bible markdown files.

Orchestrates: parse → generate → validate → save.
Run: uv run python -m src.data.build_dataset
"""

from __future__ import annotations

import sys
from collections import Counter

from datasets import ClassLabel, Dataset, DatasetDict

from src.constants import DATA_DIR, OUTPUT_DIR
from src.data.dataset_generator import Sample, generate_all_samples
from src.data.parser import count_stats, parse_all_books


def _validate_parsing(stats: dict[str, int]) -> None:
    """Validate parsing results meet expectations."""
    print("\n=== 解析驗證 ===")
    print(f"  書卷: {stats['books']}")
    print(f"  章數: {stats['chapters']}")
    print(f"  段落: {stats['sections']}")
    print(f"  經文: {stats['verses']}")

    if stats["books"] != 66:
        print(f"  [警告] 預期 66 卷，實際 {stats['books']} 卷")
    if stats["verses"] < 25000:
        print(f"  [警告] 經文數量偏低: {stats['verses']}（預期 ~31000）")


def _validate_samples(samples: list[Sample]) -> None:
    """Validate generated samples."""
    print("\n=== 樣本驗證 ===")

    # Count by type
    type_counts = Counter(s.sample_type for s in samples)
    for sample_type in sorted(type_counts):
        print(f"  Type {sample_type}: {type_counts[sample_type]} 筆")
    print(f"  總計: {len(samples)} 筆")

    # Validate message format
    errors = 0
    for i, sample in enumerate(samples):
        msgs = sample.messages
        if len(msgs) != 3:
            print(f"  [錯誤] 樣本 {i}: 預期 3 層 messages，實際 {len(msgs)}")
            errors += 1
            continue
        if msgs[0]["role"] != "system":
            print(f"  [錯誤] 樣本 {i}: 第一層應為 system")
            errors += 1
        if msgs[1]["role"] != "user":
            print(f"  [錯誤] 樣本 {i}: 第二層應為 user")
            errors += 1
        if msgs[2]["role"] != "assistant":
            print(f"  [錯誤] 樣本 {i}: 第三層應為 assistant")
            errors += 1
        # Check for empty content
        for msg in msgs:
            if not msg.get("content", "").strip():
                print(f"  [錯誤] 樣本 {i}: 空白內容 (role={msg['role']})")
                errors += 1

    if errors:
        print(f"  共 {errors} 個格式錯誤")
    else:
        print("  格式驗證通過 ✓")


def _print_sample_preview(samples: list[Sample], n: int = 2) -> None:
    """Print sample previews for manual inspection."""
    print("\n=== 樣本預覽 ===")
    type_groups: dict[str, list[Sample]] = {}
    for s in samples:
        type_groups.setdefault(s.sample_type, []).append(s)

    for sample_type in sorted(type_groups):
        print(f"\n--- Type {sample_type} ---")
        for sample in type_groups[sample_type][:n]:
            user_msg = sample.messages[1]["content"]
            asst_msg = sample.messages[2]["content"]
            # Truncate long answers
            if len(asst_msg) > 200:
                asst_msg = asst_msg[:200] + "..."
            print(f"  Q: {user_msg}")
            print(f"  A: {asst_msg}")
            print()


_MAX_TOTAL_CHARS = 2600  # ~2048 max_length with buffer for chat template tokens + CoT


def _estimate_too_long(sample: Sample, max_chars: int = _MAX_TOTAL_CHARS) -> bool:
    """Check if a sample's total message content exceeds the character limit."""
    total = sum(len(m["content"]) for m in sample.messages)
    return total > max_chars


def _samples_to_dataset_dict(
    samples: list[Sample], test_size: float = 0.1, seed: int = 42
) -> DatasetDict:
    """Convert samples to HuggingFace DatasetDict with train/test split.

    v7: Deduplicate by question text before splitting to prevent
    train/test leakage and remove exact duplicate questions.
    v8: Filter out samples exceeding _MAX_TOTAL_CHARS.
    """
    seen_questions: set[str] = set()
    deduped: list[Sample] = []
    for s in samples:
        question = s.messages[1]["content"]
        if question not in seen_questions:
            seen_questions.add(question)
            deduped.append(s)

    # v8: Filter overly long samples
    filtered: list[Sample] = []
    for s in deduped:
        if _estimate_too_long(s):
            total = sum(len(m["content"]) for m in s.messages)
            print(
                f"  [警告] 過濾超長樣本 (Type {s.sample_type}, {total} chars): "
                f"{s.messages[1]['content'][:50]}..."
            )
        else:
            filtered.append(s)

    records = [
        {
            "sample_type": s.sample_type,
            "messages": [dict(m) for m in s.messages],
        }
        for s in filtered
    ]

    dataset = Dataset.from_list(records)

    # Cast sample_type to ClassLabel for stratified splitting
    type_names = sorted(set(r["sample_type"] for r in records))
    class_label = ClassLabel(names=type_names)
    dataset = dataset.cast_column("sample_type", class_label)

    split = dataset.train_test_split(
        test_size=test_size, seed=seed, stratify_by_column="sample_type",
    )

    # Remove the ClassLabel column and add back as plain string
    result = {}
    for split_name in split:
        ds = split[split_name]
        labels = ds["sample_type"]
        decoded = [class_label.int2str(label) for label in labels]
        ds = ds.remove_columns("sample_type")
        ds = ds.add_column("sample_type", decoded)
        result[split_name] = ds

    return DatasetDict(result)


def build() -> None:
    """Execute the full data pipeline."""
    print("=" * 60)
    print("Bible Fine-Tuning Dataset Builder")
    print("=" * 60)

    # Step 1: Parse
    print("\n[1/4] 解析聖經 markdown 檔案...")
    books = parse_all_books(DATA_DIR)
    stats = count_stats(books)
    _validate_parsing(stats)

    # Step 2: Generate samples
    print("\n[2/4] 生成訓練樣本...")
    samples = generate_all_samples(books, seed=42)

    # Step 3: Validate
    _validate_samples(samples)
    _print_sample_preview(samples)

    # Step 4: Build and save dataset
    print("\n[3/4] 建立 HuggingFace Dataset...")
    ds_dict = _samples_to_dataset_dict(samples)
    print(f"  Train: {len(ds_dict['train'])} 筆")
    print(f"  Test:  {len(ds_dict['test'])} 筆")

    print("\n[4/4] 儲存到磁碟...")
    output_path = OUTPUT_DIR / "bible_dataset"
    output_path.mkdir(parents=True, exist_ok=True)
    ds_dict.save_to_disk(str(output_path))
    print(f"  已儲存至: {output_path}")

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


def main() -> None:
    """Entry point."""
    try:
        build()
    except Exception as e:
        print(f"\n[錯誤] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
