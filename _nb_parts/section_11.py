# Section 11: Interactive Inference
cells.append(md("""---
## Section 11: 互動推論

載入微調後的模型，透過互動介面進行即時問答測試。

### 範例問題

- `創世記第1章第1節的經文是什麼？`
- `請列出聖經中關於「信心」的經文。`
- `「太初有道」這句經文出自哪裏？`
- `馬太福音第5章第3節的上下文是什麼？`
- `保羅書第1章第1節的經文是什麼？`（拒絕測試）"""))

cells.append(code("""# ── 推論函式 ──

def generate(
    model, tokenizer, question: str, *,
    temperature: float = 0.7, top_p: float = 0.9, max_new_tokens: int = 512,
) -> str:
    \"\"\"生成回應（支援取樣參數調整）。\"\"\"
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
            do_sample=temperature > 0,
            temperature=temperature if temperature > 0 else 1.0,
            top_p=top_p,
        )
    response = tokenizer.decode(
        outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )
    return response.strip()

# 載入模型（如果尚未載入）
if "eval_model" not in dir():
    eval_model, eval_tokenizer = _load_eval_model()

# 測試推論
test_q = "創世記第1章第1節的經文是什麼？"
print(f"Q: {test_q}")
print(f"A: {generate(eval_model, eval_tokenizer, test_q)}")"""))

cells.append(code("""# ── 互動推論（在 Notebook 中使用 input loop）──

print("=" * 60)
print("聖經知識助手 — 互動模式")
print("=" * 60)
print("輸入問題開始對話，輸入 'quit' 或 'exit' 退出")
print("-" * 60)

while True:
    try:
        user_input = input("\\n你: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\\n再見！")
        break

    if not user_input:
        continue
    if user_input.lower() in ("quit", "exit"):
        print("再見！")
        break

    response = generate(eval_model, eval_tokenizer, user_input)
    print(f"\\n助手: {response}")"""))
