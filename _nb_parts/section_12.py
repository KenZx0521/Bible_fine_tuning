# Section 12: Cleanup & Summary
cells.append(md("""---
## Section 12: 清理與總結

### 完成項目

- [x] 解析 66 卷聖經 Markdown 檔案
- [x] 生成 ~19,000 筆訓練樣本（6 種類型）
- [x] QLoRA 微調 Gemma-3-12B-IT 模型
- [x] 合併 LoRA adapter
- [x] 多維度評估
- [x] 互動推論測試

### 產出檔案

| 路徑 | 說明 |
|------|------|
| `outputs/bible_dataset/` | HuggingFace Dataset（train + test） |
| `outputs/bible-assistant/final_adapter/` | LoRA adapter 權重 |
| `outputs/merged_model/` | 合併後的完整模型 |
| `outputs/evaluation_results.json` | 評估結果 |

### 後續步驟

1. **部署**: 將合併模型上傳至 Hugging Face Hub
2. **API 化**: 使用 vLLM / TGI 建立推論 API
3. **持續改進**: 根據評估結果調整訓練資料或超參數"""))

cells.append(code("""# ── 釋放所有 GPU 資源 ──
for var_name in ["eval_model", "eval_tokenizer", "model", "trainer"]:
    if var_name in dir():
        exec(f"del {var_name}")

gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.synchronize()

gpu_mem()
print("\\n所有資源已釋放。Notebook 執行完畢！")"""))
