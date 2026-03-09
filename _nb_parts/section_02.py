# Section 2: Config
cells.append(md("""---
## Section 2: 設定

包含模型 ID、系統提示詞、訓練超參數與路徑常數。

- `CONFIG` dict 取代 YAML 設定檔，所有超參數可直接編輯
- `SYSTEM_PROMPT` 為訓練時使用的系統提示詞（含 3 個變體增加多樣性）
- `report_to` 預設為 `"none"`，如需 Trackio 追蹤可改為 `"trackio"`"""))

cells.append(code("""# ── 模型與路徑 ──
MODEL_ID = "google/gemma-3-12b-it"

DATA_DIR = "/kaggle/input/datasets/kenzx0521/bible-data/bible_data"
OUTPUT_DIR = "/kaggle/working/outputs"

# ── 系統提示詞 ──
SYSTEM_PROMPT = (
    "你是一位精通聖經的知識助手，熟悉繁體中文和合本聖經的所有內容。"
    "你能準確引用經文、解釋段落含義、提供上下文背景，並回答各種聖經相關問題。"
    "請根據聖經內容如實回答，若問題超出聖經範圍，請誠實說明。"
)

SYSTEM_PROMPT_VARIANTS = (
    SYSTEM_PROMPT,
    (
        "你是聖經知識助手，精通繁體中文和合本聖經全部66卷書的內容。"
        "你可以引用經文、說明段落意義、提供背景脈絡，並回答聖經相關的各類問題。"
        "回答請以聖經內容為依據，遇到超出範圍的問題請如實告知。"
    ),
    (
        "你是一位熟悉聖經的助手，對繁體中文和合本聖經的經文內容瞭若指掌。"
        "無論是查詢經文、理解段落含義或是探討聖經主題，你都能提供準確的回答。"
        "請依據聖經內容回應，若問題不在聖經範圍內，請誠實說明。"
    ),
    (
        "你是專業的聖經知識顧問，擅長繁體中文和合本聖經的經文查詢與解讀。"
        "你能精確引用經文、分析上下文脈絡，並解答各種與聖經相關的問題。"
        "請基於聖經原文內容作答，若問題超出聖經所涵蓋的範圍，請坦誠說明。"
    ),
)

# ── 訓練設定 ──
CONFIG = {
    "model": {"model_id": MODEL_ID},
    "quantization": {
        "load_in_4bit": True,
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_use_double_quant": True,
        "bnb_4bit_compute_dtype": "bfloat16",
    },
    "lora": {
        "r": 32,
        "lora_alpha": 64,
        "lora_dropout": 0.1,
        "target_modules": "all-linear",
        "bias": "none",
        "task_type": "CAUSAL_LM",
    },
    "training": {
        "output_dir": "outputs/bible-assistant",
        "num_train_epochs": 2,
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 8,
        "learning_rate": 1e-4,
        "weight_decay": 0.01,
        "max_length": 2560,
        "packing": True,
        "gradient_checkpointing": True,
        "optim": "paged_adamw_8bit",
        "lr_scheduler_type": "cosine",
        "warmup_ratio": 0.05,
        "neftune_noise_alpha": 5,
        "logging_steps": 10,
        "save_strategy": "steps",
        "save_steps": 200,
        "save_total_limit": 5,
        "eval_strategy": "steps",
        "eval_steps": 200,
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_loss",
        "bf16": True,
        "report_to": "none",  # 改為 "trackio" 以啟用實驗追蹤
    },
    "dataset": {"test_size": 0.1, "seed": 42},
    # Trackio 設定（report_to="trackio" 時啟用）
    # "trackio": {
    #     "project": "bible-fine-tuning",
    #     "run_name": "qlora-gemma3-12b",
    #     "space_id": "KenZx0521/fine-tuning_bible",
    # },
}

print(f"Model ID: {MODEL_ID}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"OUTPUT_DIR: {OUTPUT_DIR}")"""))

cells.append(code("""# ── SEED 與裝置 ──
SEED = CONFIG["dataset"]["seed"]
random.seed(SEED)
torch.manual_seed(SEED)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {DEVICE}")


def gpu_mem():
    \"\"\"顯示所有 GPU 記憶體使用狀況。\"\"\"
    if not torch.cuda.is_available():
        print("No GPU available")
        return
    for i in range(torch.cuda.device_count()):
        allocated = torch.cuda.memory_allocated(i) / 1024**3
        reserved = torch.cuda.memory_reserved(i) / 1024**3
        total = torch.cuda.get_device_properties(i).total_memory / 1024**3
        print(f"  GPU[{i}]: {allocated:.2f} / {total:.1f} GB (reserved: {reserved:.2f} GB)")


gpu_mem()"""))
