"""QLoRA SFT training with Trackio experiment tracking.

Run: uv run python -m src.training.train
"""

from __future__ import annotations

import sys
from pathlib import Path

import torch
import trackio
import yaml
from datasets import DatasetDict, load_from_disk
from dotenv import load_dotenv
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

from src.constants import CONFIG_PATH, MODEL_ID, OUTPUT_DIR


def _load_config() -> dict:
    """Load training configuration from YAML."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_bnb_config(quant_cfg: dict) -> BitsAndBytesConfig:
    """Build BitsAndBytes quantization config."""
    compute_dtype = getattr(torch, quant_cfg["bnb_4bit_compute_dtype"])
    return BitsAndBytesConfig(
        load_in_4bit=quant_cfg["load_in_4bit"],
        bnb_4bit_quant_type=quant_cfg["bnb_4bit_quant_type"],
        bnb_4bit_use_double_quant=quant_cfg["bnb_4bit_use_double_quant"],
        bnb_4bit_compute_dtype=compute_dtype,
    )


def _build_lora_config(lora_cfg: dict) -> LoraConfig:
    """Build LoRA configuration."""
    kwargs: dict = {
        "r": lora_cfg["r"],
        "lora_alpha": lora_cfg["lora_alpha"],
        "lora_dropout": lora_cfg["lora_dropout"],
        "target_modules": lora_cfg["target_modules"],
        "bias": lora_cfg["bias"],
        "task_type": lora_cfg["task_type"],
    }
    if lora_cfg.get("modules_to_save"):
        kwargs["modules_to_save"] = lora_cfg["modules_to_save"]
    return LoraConfig(**kwargs)


def train() -> None:
    """Execute the full training pipeline."""
    # Load environment
    load_dotenv()

    config = _load_config()
    model_id = config["model"]["model_id"]
    train_cfg = config["training"]
    trackio_cfg = config["trackio"]

    print("=" * 60)
    print("Bible QLoRA SFT Training")
    print("=" * 60)
    print(f"  Model: {model_id}")

    # Initialize Trackio
    trackio_kwargs: dict = {
        "project": trackio_cfg["project"],
        "name": trackio_cfg["run_name"],
        "config": {
            "model": model_id,
            "learning_rate": train_cfg["learning_rate"],
            "weight_decay": train_cfg.get("weight_decay", 0.0),
            "epochs": train_cfg["num_train_epochs"],
            "lora_r": config["lora"]["r"],
            "lora_alpha": config["lora"]["lora_alpha"],
            "lora_dropout": config["lora"]["lora_dropout"],
            "batch_size": train_cfg["per_device_train_batch_size"],
            "grad_accum": train_cfg["gradient_accumulation_steps"],
            "max_length": train_cfg["max_length"],
            "neftune_noise_alpha": train_cfg.get("neftune_noise_alpha"),
        },
    }
    space_id = trackio_cfg.get("space_id", "")
    if space_id:
        trackio_kwargs["space_id"] = space_id
        dataset_id = trackio_cfg.get("dataset_id", "")
        if dataset_id:
            trackio_kwargs["dataset_id"] = dataset_id
        print(f"  Trackio remote: {space_id}")
    else:
        print("  Trackio: local mode")
    trackio.init(**trackio_kwargs)

    # Load dataset
    print("\n[1/5] 載入資料集...")
    dataset_path = OUTPUT_DIR / "bible_dataset"
    if not dataset_path.exists():
        print("  [錯誤] 資料集不存在，請先執行: uv run python -m src.data.build_dataset")
        sys.exit(1)

    ds_dict = load_from_disk(str(dataset_path))
    print(f"  Train: {len(ds_dict['train'])} 筆")
    print(f"  Test:  {len(ds_dict['test'])} 筆")

    # Build quantization config
    print("\n[2/5] 設定量化參數...")
    bnb_config = _build_bnb_config(config["quantization"])

    # Load tokenizer and model
    print("\n[3/5] 載入模型和 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )

    # Build LoRA config
    print("\n[4/5] 設定 LoRA...")
    lora_config = _build_lora_config(config["lora"])

    # Build SFT config
    output_dir = str(Path(train_cfg["output_dir"]))
    sft_kwargs: dict = {
        "output_dir": output_dir,
        "num_train_epochs": train_cfg["num_train_epochs"],
        "per_device_train_batch_size": train_cfg["per_device_train_batch_size"],
        "gradient_accumulation_steps": train_cfg["gradient_accumulation_steps"],
        "learning_rate": train_cfg["learning_rate"],
        "weight_decay": train_cfg.get("weight_decay", 0.0),
        "max_length": train_cfg["max_length"],
        "packing": train_cfg["packing"],
        "gradient_checkpointing": train_cfg["gradient_checkpointing"],
        "optim": train_cfg["optim"],
        "lr_scheduler_type": train_cfg["lr_scheduler_type"],
        "warmup_ratio": train_cfg["warmup_ratio"],
        "logging_steps": train_cfg["logging_steps"],
        "save_strategy": train_cfg["save_strategy"],
        "save_steps": train_cfg["save_steps"],
        "save_total_limit": train_cfg["save_total_limit"],
        "eval_strategy": train_cfg["eval_strategy"],
        "eval_steps": train_cfg["eval_steps"],
        "bf16": train_cfg["bf16"],
        "report_to": train_cfg["report_to"],
    }
    if train_cfg.get("neftune_noise_alpha") is not None:
        sft_kwargs["neftune_noise_alpha"] = train_cfg["neftune_noise_alpha"]
    if train_cfg.get("max_grad_norm") is not None:
        sft_kwargs["max_grad_norm"] = train_cfg["max_grad_norm"]
    if train_cfg.get("load_best_model_at_end"):
        sft_kwargs["load_best_model_at_end"] = True
        sft_kwargs["metric_for_best_model"] = train_cfg.get(
            "metric_for_best_model", "eval_loss"
        )
    sft_config = SFTConfig(**sft_kwargs)

    # Initialize trainer
    print("\n[5/5] 開始訓練...")
    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=ds_dict["train"],
        eval_dataset=ds_dict["test"],
        peft_config=lora_config,
        processing_class=tokenizer,
    )

    trainer.train()

    # Save LoRA adapter
    print("\n儲存 LoRA adapter...")
    adapter_path = Path(output_dir) / "final_adapter"
    trainer.save_model(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    print(f"  已儲存至: {adapter_path}")

    trackio.finish()

    print("\n" + "=" * 60)
    print("訓練完成！")
    print(f"  Adapter: {adapter_path}")
    if trackio_cfg.get("space_id"):
        print(f"  Dashboard: https://huggingface.co/spaces/{trackio_cfg['space_id']}")
    else:
        print(f"  Dashboard: uv run trackio show --project {trackio_cfg['project']}")
    print("=" * 60)


if __name__ == "__main__":
    train()
