# Section 8: QLoRA Training
cells.append(md("""---
## Section 8: QLoRA 微調訓練

### QLoRA 原理

QLoRA（Quantized LoRA）結合 4-bit 量化與 LoRA adapter：
1. **4-bit NF4 量化** — 將 base model 權重壓縮至 4-bit，大幅降低 VRAM 需求
2. **LoRA adapter** — 僅訓練低秩分解矩陣（r=32），參數量極少
3. **Double quantization** — 進一步壓縮量化常數

### 超參數

| 參數 | 值 | 說明 |
|------|-----|------|
| LoRA r | 32 | 低秩矩陣的秩 |
| LoRA alpha | 64 | 縮放係數 (alpha/r = 2) |
| Batch size | 2 | 每 GPU batch size |
| Grad accum | 8 | 等效 batch = 16 |
| Learning rate | 1e-4 | cosine scheduler |
| Epochs | 2 | 訓練輪數 |
| Max length | 2560 | 最大 token 長度 |
| Packing | True | 多樣本打包加速訓練 |

### VRAM 估算

- 12B 模型 4-bit: ~7GB
- LoRA adapter + optimizer: ~3GB
- Activations (grad checkpoint): ~3-5GB
- **總計: ~13-15GB** (建議 16GB+)"""))

cells.append(code("""# ── 載入模型 + Tokenizer + 量化設定 ──
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

# 載入 dataset（如果從 checkpoint 重新開始）
from datasets import load_from_disk
dataset_path = os.path.join(OUTPUT_DIR, "bible_dataset")
if "ds_dict" not in dir() or ds_dict is None:
    print("從 checkpoint 載入 Dataset...")
    ds_dict = load_from_disk(dataset_path)

# 量化設定
quant_cfg = CONFIG["quantization"]
compute_dtype = getattr(torch, quant_cfg["bnb_4bit_compute_dtype"])
bnb_config = BitsAndBytesConfig(
    load_in_4bit=quant_cfg["load_in_4bit"],
    bnb_4bit_quant_type=quant_cfg["bnb_4bit_quant_type"],
    bnb_4bit_use_double_quant=quant_cfg["bnb_4bit_use_double_quant"],
    bnb_4bit_compute_dtype=compute_dtype,
)

# Tokenizer
print("載入 tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, token=HF_TOKEN)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Model
print("載入模型（4-bit 量化）...")
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    quantization_config=bnb_config,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    token=HF_TOKEN,
)

gpu_mem()
print(f"Total parameters: {model.num_parameters():,}")
if hasattr(model, "hf_device_map"):
    print(f"Device map: {dict(Counter(model.hf_device_map.values()))}")"""))

cells.append(code("""# ── LoRA + SFT 設定 ──
lora_cfg = CONFIG["lora"]
lora_config = LoraConfig(
    r=lora_cfg["r"],
    lora_alpha=lora_cfg["lora_alpha"],
    lora_dropout=lora_cfg["lora_dropout"],
    target_modules=lora_cfg["target_modules"],
    bias=lora_cfg["bias"],
    task_type=lora_cfg["task_type"],
)

train_cfg = CONFIG["training"]
sft_kwargs = {
    "output_dir": train_cfg["output_dir"],
    "num_train_epochs": train_cfg["num_train_epochs"],
    "per_device_train_batch_size": train_cfg["per_device_train_batch_size"],
    "gradient_accumulation_steps": train_cfg["gradient_accumulation_steps"],
    "learning_rate": train_cfg["learning_rate"],
    "weight_decay": train_cfg["weight_decay"],
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
# Multi-GPU: disable unused param detection for model-parallel QLoRA
if torch.cuda.device_count() > 1:
    sft_kwargs["ddp_find_unused_parameters"] = False

if train_cfg.get("neftune_noise_alpha") is not None:
    sft_kwargs["neftune_noise_alpha"] = train_cfg["neftune_noise_alpha"]
if train_cfg.get("load_best_model_at_end"):
    sft_kwargs["load_best_model_at_end"] = True
    sft_kwargs["metric_for_best_model"] = train_cfg.get("metric_for_best_model", "eval_loss")

sft_config = SFTConfig(**sft_kwargs)

# 如需 Trackio 追蹤，取消以下註解：
# import trackio
# trackio.init(
#     project="bible-fine-tuning",
#     name="qlora-gemma3-12b",
#     space_id="KenZx0521/fine-tuning_bible",
#     config={...},
# )

trainer = SFTTrainer(
    model=model,
    args=sft_config,
    train_dataset=ds_dict["train"],
    eval_dataset=ds_dict["test"],
    peft_config=lora_config,
    processing_class=tokenizer,
)

print(f"Trainable parameters: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
print(f"Total parameters: {model.num_parameters():,}")
gpu_mem()"""))

cells.append(code("""%%time
# ── 執行訓練 ──
print("開始訓練...")
trainer.train()

# 儲存 adapter
adapter_path = os.path.join(train_cfg["output_dir"], "final_adapter")
trainer.save_model(adapter_path)
tokenizer.save_pretrained(adapter_path)
print(f"\\nLoRA adapter 已儲存至: {adapter_path}")

# trackio.finish()  # 如有啟用 Trackio，取消此行註解

gpu_mem()"""))

cells.append(code("""# ── 訓練曲線視覺化 ──

log_history = trainer.state.log_history

# 擷取 loss 與 eval_loss
train_steps, train_losses = [], []
eval_steps_list, eval_losses = [], []

for entry in log_history:
    if "loss" in entry and "eval_loss" not in entry:
        train_steps.append(entry.get("step", 0))
        train_losses.append(entry["loss"])
    if "eval_loss" in entry:
        eval_steps_list.append(entry.get("step", 0))
        eval_losses.append(entry["eval_loss"])

fig, ax = plt.subplots(figsize=(10, 5))
if train_steps:
    ax.plot(train_steps, train_losses, label="Train Loss", alpha=0.7, linewidth=1)
if eval_steps_list:
    ax.plot(eval_steps_list, eval_losses, label="Eval Loss", marker="o", markersize=4, linewidth=2)

ax.set_xlabel("Step")
ax.set_ylabel("Loss")
ax.set_title("Training & Validation Loss", fontsize=14, fontweight="bold")
ax.legend()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.show()

if eval_losses:
    print(f"Best Eval Loss: {min(eval_losses):.4f} (step {eval_steps_list[eval_losses.index(min(eval_losses))]})")"""))
