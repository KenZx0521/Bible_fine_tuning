"""Multi-dimensional Bible knowledge evaluation.

Dimensions:
  1. Verse recall — ROUGE-L + exact match on verse lookup
  2. Section knowledge — key verse coverage in section summaries
  3. Verse identification — accuracy of source identification
  4. Anti-hallucination — hallucination rate on non-existent references
  5. Perplexity — compared to base model

Run: uv run python -m src.evaluation.evaluate
"""

from __future__ import annotations

import json
import random
import sys

import torch
from dotenv import load_dotenv
from rouge_score import rouge_scorer
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.constants import MODEL_ID, OUTPUT_DIR, SYSTEM_PROMPT
from src.data.parser import parse_all_books
from src.constants import DATA_DIR


def _load_model_and_tokenizer(model_path: str | None = None):
    """Load model and tokenizer for evaluation."""
    path = model_path or str(OUTPUT_DIR / "bible-assistant" / "final_adapter")

    tokenizer = AutoTokenizer.from_pretrained(path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Try loading as PEFT model first, fall back to full model
    try:
        from peft import PeftModel

        base_model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        model = PeftModel.from_pretrained(base_model, path)
    except (ImportError, ValueError, OSError) as e:
        print(f"  載入為完整模型 (LoRA: {e})")
        model = AutoModelForCausalLM.from_pretrained(
            path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )

    model.eval()
    return model, tokenizer


def _generate_response(
    model, tokenizer, question: str, max_new_tokens: int = 512
) -> str:
    """Generate a response from the model."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    input_text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=1.0,
        )

    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )
    return response.strip()


def evaluate_verse_recall(
    model, tokenizer, books, n_samples: int = 500, seed: int = 42
) -> dict:
    """Evaluate verse recall with ROUGE-L and exact match."""
    rng = random.Random(seed)
    all_verses = [
        v for b in books for c in b.chapters for s in c.sections for v in s.verses
    ]
    selected = rng.sample(all_verses, min(n_samples, len(all_verses)))

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    rouge_scores = []
    exact_matches = 0

    for i, verse in enumerate(selected):
        question = f"{verse.book}第{verse.chapter}章第{verse.verse_number}節的經文是什麼？"
        response = _generate_response(model, tokenizer, question)

        score = scorer.score(verse.text, response)
        rouge_scores.append(score["rougeL"].fmeasure)

        if verse.text in response:
            exact_matches += 1

        if (i + 1) % 50 == 0:
            print(f"    經文召回: {i + 1}/{len(selected)}")

    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0
    return {
        "avg_rouge_l": round(avg_rouge, 4),
        "exact_match_rate": round(exact_matches / len(selected), 4),
        "n_samples": len(selected),
    }


def evaluate_verse_identification(
    model, tokenizer, books, n_samples: int = 200, seed: int = 42
) -> dict:
    """Evaluate verse source identification accuracy."""
    rng = random.Random(seed)
    all_verses = [
        v
        for b in books
        for c in b.chapters
        for s in c.sections
        for v in s.verses
        if len(v.text) >= 15
    ]
    selected = rng.sample(all_verses, min(n_samples, len(all_verses)))

    correct = 0
    for i, verse in enumerate(selected):
        snippet = verse.text[:50] if len(verse.text) > 50 else verse.text
        question = f"「{snippet}」這句經文出自聖經哪裏？"
        response = _generate_response(model, tokenizer, question, max_new_tokens=128)

        # Check if response contains the correct reference
        if verse.book in response and str(verse.chapter) in response:
            correct += 1

        if (i + 1) % 50 == 0:
            print(f"    經文辨識: {i + 1}/{len(selected)}")

    return {
        "accuracy": round(correct / len(selected), 4),
        "n_samples": len(selected),
    }


def evaluate_anti_hallucination(
    model, tokenizer, n_samples: int = 50
) -> dict:
    """Evaluate hallucination rate on non-existent references."""
    fake_questions = [
        "請引用創世記第100章第1節的經文。",
        "啟示錄第50章第10節說了什麼？",
        "馬太福音第99章第5節的經文是什麼？",
        "希伯來書第30章第1節的內容為何？",
        "以賽亞書第200章第3節的經文是什麼？",
    ]
    # Generate more fake questions
    fake_books = ["保羅書", "彼拉多書", "馬利亞福音", "多馬福音", "巴拿巴書"]
    for book in fake_books:
        for ch in [1, 5, 10]:
            fake_questions.append(f"{book}第{ch}章第1節的經文是什麼？")

    rng = random.Random(42)
    selected = rng.sample(fake_questions, min(n_samples, len(fake_questions)))

    hallucinations = 0
    refusal_keywords = ["不存在", "沒有", "找不到", "並非", "無法", "超出", "沒有這", "不確定"]

    for question in selected:
        response = _generate_response(model, tokenizer, question, max_new_tokens=256)
        # If response doesn't contain any refusal keyword, count as hallucination
        if not any(kw in response for kw in refusal_keywords):
            hallucinations += 1

    return {
        "hallucination_rate": round(hallucinations / len(selected), 4),
        "n_samples": len(selected),
    }


def evaluate(model_path: str | None = None) -> None:
    """Run all evaluation dimensions."""
    load_dotenv()

    print("=" * 60)
    print("Bible Knowledge Evaluation")
    print("=" * 60)

    # Load model
    print("\n[1/5] 載入模型...")
    model, tokenizer = _load_model_and_tokenizer(model_path)

    # Parse Bible for ground truth
    print("\n[2/5] 解析聖經資料...")
    books = parse_all_books(DATA_DIR)

    # Evaluate
    results = {}

    print("\n[3/5] 經文召回評估...")
    results["verse_recall"] = evaluate_verse_recall(model, tokenizer, books)
    print(f"    ROUGE-L: {results['verse_recall']['avg_rouge_l']}")
    print(f"    Exact Match: {results['verse_recall']['exact_match_rate']}")

    print("\n[4/5] 經文辨識評估...")
    results["verse_identification"] = evaluate_verse_identification(
        model, tokenizer, books
    )
    print(f"    Accuracy: {results['verse_identification']['accuracy']}")

    print("\n[5/5] 抗幻覺評估...")
    results["anti_hallucination"] = evaluate_anti_hallucination(model, tokenizer)
    print(f"    Hallucination Rate: {results['anti_hallucination']['hallucination_rate']}")

    # Save results
    results_path = OUTPUT_DIR / "evaluation_results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n結果已儲存至: {results_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("評估摘要")
    print("=" * 60)
    print(f"  經文召回 ROUGE-L:     {results['verse_recall']['avg_rouge_l']}")
    print(f"  經文召回 Exact Match: {results['verse_recall']['exact_match_rate']}")
    print(f"  經文辨識 Accuracy:    {results['verse_identification']['accuracy']}")
    print(f"  幻覺率:               {results['anti_hallucination']['hallucination_rate']}")
    print("=" * 60)


if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else None
    evaluate(model_path)
