"""Interactive inference REPL for the fine-tuned Bible assistant.

Run: uv run python -m src.evaluation.inference
"""

from __future__ import annotations

import sys

import torch
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.constants import MODEL_ID, OUTPUT_DIR, SYSTEM_PROMPT


def _load_model(model_path: str | None = None):
    """Load the fine-tuned model for inference."""
    # Try adapter path first, then merged model
    if model_path:
        path = model_path
    elif (OUTPUT_DIR / "merged_model").exists():
        path = str(OUTPUT_DIR / "merged_model")
    elif (OUTPUT_DIR / "bible-assistant" / "final_adapter").exists():
        path = str(OUTPUT_DIR / "bible-assistant" / "final_adapter")
    else:
        print("[錯誤] 找不到模型。請先訓練或指定模型路徑。")
        sys.exit(1)

    print(f"載入模型: {path}")
    tokenizer = AutoTokenizer.from_pretrained(path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Try as PEFT model
    try:
        from peft import PeftModel

        base_model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        model = PeftModel.from_pretrained(base_model, path)
        print("  (載入為 LoRA adapter)")
    except (ImportError, ValueError, OSError):
        model = AutoModelForCausalLM.from_pretrained(
            path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        print("  (載入為完整模型)")

    model.eval()
    return model, tokenizer


def generate(
    model,
    tokenizer,
    question: str,
    *,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_new_tokens: int = 512,
) -> str:
    """Generate a response to a question."""
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


def repl(model_path: str | None = None) -> None:
    """Interactive REPL for Bible QA."""
    load_dotenv()

    print("=" * 60)
    print("聖經知識助手 — 互動模式")
    print("=" * 60)
    print("輸入問題開始對話，輸入 'quit' 退出")
    print("可調參數: temperature=0.7, top_p=0.9, max_new_tokens=512")
    print("-" * 60)

    model, tokenizer = _load_model(model_path)

    temperature = 0.7
    top_p = 0.9
    max_new_tokens = 512

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再見！")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("再見！")
            break

        # Handle parameter adjustment
        if user_input.startswith("/set "):
            parts = user_input[5:].split("=")
            if len(parts) == 2:
                param, value = parts[0].strip(), parts[1].strip()
                if param == "temperature":
                    temperature = float(value)
                    print(f"  temperature = {temperature}")
                elif param == "top_p":
                    top_p = float(value)
                    print(f"  top_p = {top_p}")
                elif param == "max_new_tokens":
                    max_new_tokens = int(value)
                    print(f"  max_new_tokens = {max_new_tokens}")
                else:
                    print(f"  未知參數: {param}")
            continue

        response = generate(
            model,
            tokenizer,
            user_input,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens,
        )
        print(f"\n助手: {response}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    repl(path)
