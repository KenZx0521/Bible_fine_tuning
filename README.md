# Fine-Tuning Bible

使用 [TAIDE Gemma-3-12B](https://huggingface.co/taide/Gemma-3-TAIDE-12b-Chat-2602) 模型進行 QLoRA SFT fine-tuning，建立繁體中文聖經知識問答助手。

## 功能特色

- 從 66 卷繁體中文和合本聖經 markdown 原始檔案自動解析、生成訓練資料
- 6 種多元樣本類型，涵蓋經文查詢、段落摘要、主題搜尋、上下文理解、經文辨識、拒絕回應
- QLoRA 4-bit 量化訓練，降低 GPU 記憶體需求
- 內建多維度評估（ROUGE-L、經文辨識準確率、抗幻覺率）
- 使用 [Trackio](https://github.com/gradio-app/trackio) 進行訓練實驗追蹤，支援本機儀表板或同步至 Hugging Face Space

## 專案結構

```
fine_tuning_bible/
├── bible_data/                  # 66 卷聖經 markdown 檔案
├── configs/
│   └── training_config.yaml     # 訓練超參數設定
├── src/
│   ├── constants.py             # 共用常數（模型 ID、路徑、System Prompt）
│   ├── data/
│   │   ├── parser.py            # Markdown 解析器（Book/Chapter/Section/Verse）
│   │   ├── templates.py         # 問答模板、主題關鍵字、拒絕範本
│   │   ├── dataset_generator.py # 6 類樣本生成器（A-F）
│   │   └── build_dataset.py     # 資料集建構與驗證
│   ├── training/
│   │   ├── train.py             # QLoRA SFT 訓練
│   │   └── merge_model.py       # 合併 LoRA adapter 至 base model
│   └── evaluation/
│       ├── evaluate.py          # 多維度自動評估
│       └── inference.py         # 互動式推論 REPL
├── tests/                       # 測試（parser、generator、templates、build）
├── pyproject.toml
└── .env.example
```

## 訓練樣本類型

| 類型 | 說明 | 數量 | 佔比 |
|------|------|------|------|
| A | 經文查詢 — 查詢特定章節經文 | ~10,137 | 40.0% |
| B | 段落摘要 — 摘要段落標題下的經文 | ~2,596 | 10.3% |
| C | 主題經文 — 按主題關鍵字搜尋相關經文（32 個主題） | ~312 | 1.2% |
| D | 上下文理解 — 提供經文的前後文脈絡 | ~7,308 | 28.9% |
| E | 經文辨識 — 從引文反查出處 | ~4,482 | 17.7% |
| F | 拒絕回應 — 拒絕不存在書卷 / 超範圍 / 非聖經問題 | ~480 | 1.9% |

總計約 **25,315** 筆樣本，90/10 train/eval split。

## 環境需求

- Python >= 3.11
- CUDA 相容 GPU（建議 VRAM >= 16GB）
- [uv](https://docs.astral.sh/uv/) 套件管理工具

## 快速開始

### 1. 安裝依賴

```bash
uv sync
```

### 2. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env` 填入你的 Hugging Face Token：

```
HF_TOKEN=hf_your_token_here
```

### 3. 建構訓練資料集

```bash
uv run python -m src.data.build_dataset
```

解析 66 卷聖經 markdown、生成約 25,000 筆訓練樣本，輸出至 `outputs/bible_dataset/`。

### 4. 訓練模型

```bash
uv run python -m src.training.train
```

使用 QLoRA 進行 SFT 訓練，adapter 儲存至 `outputs/bible-assistant/final_adapter/`。

### 5. 合併模型（可選）

```bash
uv run python -m src.training.merge_model
```

將 LoRA adapter 合併至 base model，輸出完整模型至 `outputs/merged_model/`。

### 6. 互動推論

```bash
uv run python -m src.evaluation.inference
```

啟動互動式 REPL，可即時向聖經助手提問。支援參數調整：

```
/set temperature=0.5
/set top_p=0.85
/set max_new_tokens=1024
```

### 7. 自動評估

```bash
uv run python -m src.evaluation.evaluate
```

執行三維度評估，結果儲存至 `outputs/evaluation_results.json`：

| 維度 | 指標 | 說明 |
|------|------|------|
| 經文召回 | ROUGE-L / Exact Match | 模型能否準確引用經文 |
| 經文辨識 | Accuracy | 模型能否正確辨識經文出處 |
| 抗幻覺 | Hallucination Rate | 對不存在經文的拒答率 |

## 訓練設定

| 參數 | 值 |
|------|-----|
| 基礎模型 | `taide/Gemma-3-TAIDE-12b-Chat-2602` |
| 量化 | 4-bit NF4, double quant, bfloat16 |
| LoRA rank | 16 |
| LoRA alpha | 32 |
| Target modules | all-linear |
| Batch size | 2 |
| Gradient accumulation | 8 (effective batch = 16) |
| Learning rate | 2e-4 (cosine schedule, 10% warmup) |
| Epochs | 3 |
| Max sequence length | 2048 |
| Packing | enabled |
| Optimizer | paged AdamW 8-bit |
| Gradient checkpointing | enabled |

完整設定參見 [`configs/training_config.yaml`](configs/training_config.yaml)。

## 實驗追蹤（Trackio）

訓練過程使用 [Trackio](https://github.com/gradio-app/trackio) 記錄 loss 等指標。

### 本機模式（預設）

```bash
# 訓練完成後查看儀表板
uv run trackio show --project bible-fine-tuning
```

### 遠端 Hugging Face Space 模式

在 `configs/training_config.yaml` 中設定 `space_id`：

```yaml
trackio:
  space_id: "your-username/bible-fine-tuning"
  dataset_id: ""  # 留空則自動命名
```

訓練指標會同步至 HF Space 儀表板，並每 5 分鐘備份為 HF Dataset。需要在 `.env` 中設定有效的 `HF_TOKEN`。

## 測試

```bash
uv run pytest
```

## 授權

本專案僅供學術研究與個人學習使用。聖經文本版權歸原出版方所有。
