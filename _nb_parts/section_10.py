# Section 10: Evaluation
cells.append(md("""---
## Section 10: 多維度評估

### 評估維度

| 維度 | 指標 | 說明 |
|------|------|------|
| 經文召回 | ROUGE-L + Exact Match | 查詢經文時的回覆準確度 |
| 經文辨識 | Accuracy | 從片段反查書卷/章/節的正確率 |
| 抗幻覺 | Hallucination Rate | 面對不存在的經文時的拒絕率 |"""))

cells.append(code("""# ── 載入模型 + 生成函式 ──
from rouge_score import rouge_scorer

def _load_eval_model(model_path: str | None = None):
    \"\"\"載入模型用於評估（優先嘗試 PEFT，降級為完整模型）。\"\"\"
    if model_path:
        path = model_path
    elif os.path.exists(os.path.join(OUTPUT_DIR, "merged_model")):
        path = os.path.join(OUTPUT_DIR, "merged_model")
    elif os.path.exists(os.path.join(OUTPUT_DIR, "bible-assistant", "final_adapter")):
        path = os.path.join(OUTPUT_DIR, "bible-assistant", "final_adapter")
    else:
        raise FileNotFoundError("找不到模型。請先執行訓練步驟。")

    print(f"載入模型: {path}")
    eval_tokenizer = AutoTokenizer.from_pretrained(path)
    if eval_tokenizer.pad_token is None:
        eval_tokenizer.pad_token = eval_tokenizer.eos_token

    try:
        from peft import PeftModel as PM
        base = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, torch_dtype=torch.bfloat16, device_map="auto", token=HF_TOKEN,
        )
        eval_model = PM.from_pretrained(base, path)
        print("  (LoRA adapter 模式)")
    except (ImportError, ValueError, OSError):
        eval_model = AutoModelForCausalLM.from_pretrained(
            path, torch_dtype=torch.bfloat16, device_map="auto",
        )
        print("  (完整模型模式)")

    eval_model.eval()
    return eval_model, eval_tokenizer


def _generate_response(model, tokenizer, question: str, max_new_tokens: int = 512) -> str:
    \"\"\"生成模型回應。\"\"\"
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
            **inputs, max_new_tokens=max_new_tokens, do_sample=False, temperature=1.0,
        )
    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )
    return response.strip()


eval_model, eval_tokenizer = _load_eval_model()
gpu_mem()"""))

cells.append(code("""# ── 三個評估函式 ──

def evaluate_verse_recall(model, tokenizer, books, n_samples: int = 500, seed: int = 42) -> dict:
    \"\"\"經文召回: ROUGE-L + Exact Match。\"\"\"
    rng = random.Random(seed)
    all_verses = [v for b in books for c in b.chapters for s in c.sections for v in s.verses]
    selected = rng.sample(all_verses, min(n_samples, len(all_verses)))

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    rouge_scores = []
    exact_matches = 0

    for verse in tqdm(selected, desc="經文召回"):
        question = f"{verse.book}第{verse.chapter}章第{verse.verse_number}節的經文是什麼？"
        response = _generate_response(model, tokenizer, question)
        score = scorer.score(verse.text, response)
        rouge_scores.append(score["rougeL"].fmeasure)
        if verse.text in response:
            exact_matches += 1

    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0
    return {
        "avg_rouge_l": round(avg_rouge, 4),
        "exact_match_rate": round(exact_matches / len(selected), 4),
        "n_samples": len(selected),
    }


def evaluate_verse_identification(model, tokenizer, books, n_samples: int = 200, seed: int = 42) -> dict:
    \"\"\"經文辨識: 從片段反查出處。\"\"\"
    rng = random.Random(seed)
    all_verses = [
        v for b in books for c in b.chapters for s in c.sections
        for v in s.verses if len(v.text) >= 15
    ]
    selected = rng.sample(all_verses, min(n_samples, len(all_verses)))

    correct = 0
    for verse in tqdm(selected, desc="經文辨識"):
        snippet = verse.text[:50] if len(verse.text) > 50 else verse.text
        question = f"「{snippet}」這句經文出自聖經哪裏？"
        response = _generate_response(model, tokenizer, question, max_new_tokens=128)
        if verse.book in response and str(verse.chapter) in response:
            correct += 1

    return {
        "accuracy": round(correct / len(selected), 4),
        "n_samples": len(selected),
    }


def evaluate_anti_hallucination(model, tokenizer, n_samples: int = 50) -> dict:
    \"\"\"抗幻覺: 面對不存在的經文時的拒絕率。\"\"\"
    fake_questions = [
        "請引用創世記第100章第1節的經文。",
        "啟示錄第50章第10節說了什麼？",
        "馬太福音第99章第5節的經文是什麼？",
        "希伯來書第30章第1節的內容為何？",
        "以賽亞書第200章第3節的經文是什麼？",
    ]
    fake_books = ["保羅書", "彼拉多書", "馬利亞福音", "多馬福音", "巴拿巴書"]
    for book in fake_books:
        for ch in [1, 5, 10]:
            fake_questions.append(f"{book}第{ch}章第1節的經文是什麼？")

    rng = random.Random(42)
    selected = rng.sample(fake_questions, min(n_samples, len(fake_questions)))

    hallucinations = 0
    refusal_keywords = ["不存在", "沒有", "找不到", "並非", "無法", "超出", "沒有這", "不確定"]

    for question in tqdm(selected, desc="抗幻覺"):
        response = _generate_response(model, tokenizer, question, max_new_tokens=256)
        if not any(kw in response for kw in refusal_keywords):
            hallucinations += 1

    return {
        "hallucination_rate": round(hallucinations / len(selected), 4),
        "n_samples": len(selected),
    }"""))

cells.append(code("""%%time
# ── 執行評估 ──

# 解析聖經（如果 books 不在記憶體中）
if "books" not in dir():
    books = parse_all_books(DATA_DIR)

results = {}

print("\\n[1/3] 經文召回評估...")
results["verse_recall"] = evaluate_verse_recall(eval_model, eval_tokenizer, books)
print(f"  ROUGE-L: {results['verse_recall']['avg_rouge_l']}")
print(f"  Exact Match: {results['verse_recall']['exact_match_rate']}")

print("\\n[2/3] 經文辨識評估...")
results["verse_identification"] = evaluate_verse_identification(eval_model, eval_tokenizer, books)
print(f"  Accuracy: {results['verse_identification']['accuracy']}")

print("\\n[3/3] 抗幻覺評估...")
results["anti_hallucination"] = evaluate_anti_hallucination(eval_model, eval_tokenizer)
print(f"  Hallucination Rate: {results['anti_hallucination']['hallucination_rate']}")

# 儲存結果
results_path = os.path.join(OUTPUT_DIR, "evaluation_results.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(results_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\\n結果已儲存至: {results_path}")"""))

cells.append(code("""# ── 評估結果視覺化 ──

metrics = {
    "ROUGE-L": results["verse_recall"]["avg_rouge_l"],
    "Exact Match": results["verse_recall"]["exact_match_rate"],
    "Identification\\nAccuracy": results["verse_identification"]["accuracy"],
    "Refusal Rate\\n(1-Hallucination)": 1 - results["anti_hallucination"]["hallucination_rate"],
}

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(metrics.keys(), metrics.values(),
              color=["#4e79a7", "#59a14f", "#f28e2b", "#76b7b2"],
              edgecolor="white", linewidth=0.8)

for bar, val in zip(bars, metrics.values()):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
            f"{val:.2%}", ha="center", va="bottom", fontsize=12, fontweight="bold")

ax.set_ylim(0, 1.15)
ax.set_ylabel("Score")
ax.set_title("Model Evaluation Results", fontsize=14, fontweight="bold")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.show()

print("\\nEvaluation Summary:")
print(f"  Verse Recall ROUGE-L:     {results['verse_recall']['avg_rouge_l']:.4f}")
print(f"  Verse Recall Exact Match: {results['verse_recall']['exact_match_rate']:.4f}")
print(f"  Identification Accuracy:  {results['verse_identification']['accuracy']:.4f}")
print(f"  Hallucination Rate:       {results['anti_hallucination']['hallucination_rate']:.4f}")"""))
