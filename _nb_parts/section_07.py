# Section 7: Data Exploration & Visualization
cells.append(md("""---
## Section 7: 資料探索與視覺化

對生成的訓練資料進行視覺化分析，包括：
- 樣本類型分佈長條圖
- 各類型樣本預覽
- 文字長度分析箱型圖"""))

cells.append(code("""# ── 樣本類型分佈長條圖 ──

type_labels = {"A": "Verse Query", "B": "Summary", "C": "Topic Verse",
               "D": "Context", "E": "Identification", "F": "Refusal"}

# 統計 train + test
all_types = list(ds_dict["train"]["sample_type"]) + list(ds_dict["test"]["sample_type"])
type_counter = Counter(all_types)

types_sorted = sorted(type_counter.keys())
counts = [type_counter[t] for t in types_sorted]
labels = [f"Type {t}\\n{type_labels.get(t, t)}" for t in types_sorted]
colors = ["#4e79a7", "#59a14f", "#f28e2b", "#e15759", "#76b7b2", "#edc948"]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(labels, counts, color=colors[:len(types_sorted)], edgecolor="white", linewidth=0.8)

for bar, count in zip(bars, counts):
    pct = count / sum(counts) * 100
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
            f"{count:,}\\n({pct:.1f}%)", ha="center", va="bottom", fontsize=10)

ax.set_title("Training Sample Type Distribution", fontsize=14, fontweight="bold")
ax.set_ylabel("Count")
ax.set_ylim(0, max(counts) * 1.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.show()

print(f"\\n總樣本數: {sum(counts):,}")
print(f"Train: {len(ds_dict['train']):,} | Test: {len(ds_dict['test']):,}")"""))

cells.append(code("""# ── 各類型樣本預覽 ──

def preview_samples(dataset, n_per_type: int = 1):
    \"\"\"以 HTML 表格預覽各類型樣本。\"\"\"
    type_groups: dict[str, list] = {}
    for i, row in enumerate(dataset):
        st = row["sample_type"]
        type_groups.setdefault(st, []).append(row)

    html = "<style>td{vertical-align:top;padding:8px;border:1px solid #ddd;max-width:500px;word-wrap:break-word}</style>"
    html += "<table><tr><th>Type</th><th>問題 (User)</th><th>回答 (Assistant)</th></tr>"

    for st in sorted(type_groups):
        for row in type_groups[st][:n_per_type]:
            msgs = row["messages"]
            q = msgs[1]["content"]
            a = msgs[2]["content"]
            if len(a) > 300:
                a = a[:300] + "..."
            html += f"<tr><td><b>{st}</b><br>{type_labels.get(st, '')}</td>"
            html += f"<td>{q}</td><td>{a}</td></tr>"

    html += "</table>"
    display(HTML(html))

preview_samples(ds_dict["train"], n_per_type=2)"""))

cells.append(code("""# ── 文字長度分析箱型圖 ──

def compute_lengths(dataset) -> dict[str, list[int]]:
    \"\"\"計算各類型樣本的總字元數。\"\"\"
    lengths: dict[str, list[int]] = {}
    for row in dataset:
        st = row["sample_type"]
        total = sum(len(m["content"]) for m in row["messages"])
        lengths.setdefault(st, []).append(total)
    return lengths

lengths = compute_lengths(ds_dict["train"])
types_sorted = sorted(lengths.keys())
data = [lengths[t] for t in types_sorted]
labels = [f"Type {t}" for t in types_sorted]

fig, ax = plt.subplots(figsize=(10, 5))
bp = ax.boxplot(data, labels=labels, patch_artist=True, showfliers=True,
                flierprops={"marker": ".", "markersize": 3, "alpha": 0.5})
for patch, color in zip(bp["boxes"], colors[:len(types_sorted)]):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax.axhline(y=_MAX_TOTAL_CHARS, color="red", linestyle="--", alpha=0.7, label=f"Max {_MAX_TOTAL_CHARS} chars")
ax.set_title("Token Length Distribution by Sample Type (system + user + assistant)", fontsize=13, fontweight="bold")
ax.set_ylabel("Total Characters")
ax.legend()
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.show()

for t in types_sorted:
    vals = lengths[t]
    print(f"  Type {t}: mean={sum(vals)/len(vals):.0f}, median={sorted(vals)[len(vals)//2]}, max={max(vals)}")"""))
