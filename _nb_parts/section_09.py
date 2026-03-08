# Section 9: GPU Cleanup + Model Merge
cells.append(md("""---
## Section 9: GPU 清理與模型合併

### 流程

1. **釋放訓練資源** — 刪除 model、trainer 物件並清空 GPU cache
2. **合併 LoRA adapter** — 將 adapter 權重合併至 base model，產生獨立可部署的完整模型

合併後的模型可以直接用於推論，不需要 PEFT 庫。"""))

cells.append(code("""# ── GPU 清理 ──
print("釋放訓練資源...")
if "trainer" in dir():
    del trainer
if "model" in dir():
    del model
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
gpu_mem()
print("GPU 記憶體已釋放")"""))

cells.append(code("""# ── 合併 LoRA adapter 到 base model ──
from peft import PeftModel

adapter_dir = os.path.join(CONFIG["training"]["output_dir"], "final_adapter")
merged_dir = os.path.join(OUTPUT_DIR, "merged_model")

if not os.path.exists(adapter_dir):
    print(f"[警告] Adapter 路徑不存在: {adapter_dir}")
    print("請先執行 Section 8 的訓練步驟。")
else:
    print("=" * 60)
    print("Merge LoRA Adapter")
    print("=" * 60)

    # 載入 tokenizer
    print("\\n[1/4] 載入 tokenizer...")
    merge_tokenizer = AutoTokenizer.from_pretrained(adapter_dir)

    # 載入 base model (bf16)
    print("\\n[2/4] 載入 base model (bf16)...")
    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        token=HF_TOKEN,
    )
    gpu_mem()

    # 合併 LoRA
    print("\\n[3/4] 合併 LoRA adapter...")
    peft_model = PeftModel.from_pretrained(base_model, adapter_dir)
    merged_model = peft_model.merge_and_unload()

    # 儲存
    print("\\n[4/4] 儲存合併模型...")
    os.makedirs(merged_dir, exist_ok=True)
    merged_model.save_pretrained(merged_dir)
    merge_tokenizer.save_pretrained(merged_dir)
    print(f"  已儲存至: {merged_dir}")

    # 清理
    del base_model, peft_model, merged_model, merge_tokenizer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    print("\\n合併完成！")
    gpu_mem()"""))
