"""Merge LoRA adapter weights into base model.

Run: uv run python -m src.training.merge_model
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch
from dotenv import load_dotenv
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.constants import MODEL_ID, OUTPUT_DIR


def merge(
    adapter_path: str | None = None,
    output_path: str | None = None,
) -> None:
    """Merge LoRA adapter into base model and save."""
    load_dotenv()

    adapter_dir = Path(adapter_path or OUTPUT_DIR / "bible-assistant" / "final_adapter")
    merged_dir = Path(output_path or OUTPUT_DIR / "merged_model")

    if not adapter_dir.exists():
        print(f"[錯誤] Adapter 路徑不存在: {adapter_dir}")
        sys.exit(1)

    print("=" * 60)
    print("Merge LoRA Adapter")
    print("=" * 60)

    # Load tokenizer
    print("\n[1/4] 載入 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir))

    # Load base model in bf16
    print("\n[2/4] 載入 base model (bf16)...")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    # Load and merge LoRA
    print("\n[3/4] 合併 LoRA adapter...")
    model = PeftModel.from_pretrained(base_model, str(adapter_dir))
    merged_model = model.merge_and_unload()

    # Save
    print("\n[4/4] 儲存合併模型...")
    merged_dir.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(str(merged_dir))
    tokenizer.save_pretrained(str(merged_dir))
    print(f"  已儲存至: {merged_dir}")

    print("\n" + "=" * 60)
    print("合併完成！")
    print("=" * 60)


if __name__ == "__main__":
    merge()
