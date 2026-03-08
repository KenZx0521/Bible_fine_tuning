# Section 1: Environment Setup
cells.append(md("""---
## Section 1: 環境設定

### 依賴套件

| 套件 | 用途 |
|------|------|
| `torch` | PyTorch 深度學習框架 |
| `transformers` | Hugging Face 模型載入與推論 |
| `trl` | SFT 訓練器 |
| `peft` | LoRA / QLoRA adapter |
| `bitsandbytes` | 4-bit 量化 |
| `datasets` | Hugging Face Dataset 格式 |
| `rouge_score` | ROUGE-L 評估指標 |
| `matplotlib` | 視覺化 |
| `tqdm` | 進度條 |"""))

cells.append(code("""# ── 安裝依賴 ──
!pip install -q trl peft bitsandbytes rouge_score accelerate"""))

cells.append(code("""# ── Hugging Face 登入 ──
from huggingface_hub import login
from kaggle_secrets import UserSecretsClient

HF_TOKEN = UserSecretsClient().get_secret("HF_TOKEN")
login(token=HF_TOKEN)
print("Hugging Face login OK")"""))

cells.append(code("""# ── 匯入所有套件 ──
from __future__ import annotations

import gc
import glob
import json
import os
import random
import re
import warnings
from collections import Counter
from dataclasses import dataclass

import matplotlib.pyplot as plt
import torch
from datasets import ClassLabel, Dataset, DatasetDict
from IPython.display import HTML, display
from tqdm.auto import tqdm

warnings.filterwarnings("ignore", category=FutureWarning)

print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
N_GPUS = torch.cuda.device_count()
print(f"GPU count: {N_GPUS}")
for i in range(N_GPUS):
    props = torch.cuda.get_device_properties(i)
    print(f"  [{i}] {props.name} — {props.total_memory / 1024**3:.1f} GB")"""))
