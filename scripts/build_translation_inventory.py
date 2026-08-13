#!/usr/bin/env python3
"""build_translation_inventory.py — 全量汉化 inventory：列出所有待译 prompt 源。

对应 zh/06-全量作业/progress.md「inventory: 未开始」→ 生成可执行清单。
对每一条 params.prompt 记录：job_set_id、场景文件夹、job_type、源 txt 路径(若有)、
prompt 字符数、是否已有 .zh.md(并排)、按批次(P01…P35)可分批。

只读；产出 meta/translation_inventory.json + 摘要。不改任何源文件。
"""
import json, glob, os, time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = os.path.join(ROOT, "folders")
META = os.path.join(ROOT, "meta")
os.makedirs(META, exist_ok=True)

rows = []
for jp in glob.glob(os.path.join(FOLDERS, "**", "job_sets.json"), recursive=True):
    folder = os.path.relpath(os.path.dirname(jp), FOLDERS)
    try:
        d = json.load(open(jp, encoding="utf-8"))
    except Exception:
        continue
    arr = d if isinstance(d, list) else d.get("job_sets") or d.get("jobSets") or []
    for js in arr:
        jsid = js.get("id")
        p = js.get("params", {}) or {}
        prompt = p.get("prompt") or ""
        if not prompt:
            continue
        t = js.get("type") or p.get("modelId") or p.get("model") or ""
        rows.append({
            "job_set_id": jsid, "folder": folder, "type": t,
            "prompt_chars": len(prompt), "have_zh": False,
        })

# 标记已有并排 .zh.md
zh_paths = set()
for z in glob.glob(os.path.join(FOLDERS, "**", "prompts", "*.zh.md"), recursive=True):
    base = os.path.basename(z).replace(".zh.md", "")
    zh_paths.add(base)

n_total = len(rows)
n_zh = 0
for r in rows:
    # 并排.zH 判断：job_set_id 出现在 zh.md 文件名
    if r["job_set_id"] and any(r["job_set_id"] in zp for zp in zh_paths):
        r["have_zh"] = True
        n_zh += 1

by_type = Counter(r["type"] or "unknown" for r in rows)
by_folder = Counter(r["folder"] for r in rows)

out = {
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "total_prompts": n_total,
    "with_zh": n_zh,
    "pending": n_total - n_zh,
    "by_type": dict(by_type.most_common()),
    "by_folder": dict(by_folder.most_common()),
    "rows": rows,
}
p = os.path.join(META, "translation_inventory.json")
with open(p, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"全量待译 prompt: {n_total}")
print(f"已有并排 zh.md: {n_zh}  待译: {n_total-n_zh}")
print("type 分布:", dict(by_type.most_common(8)))
print("场景夹数:", len(by_folder))
print(f"写出: {p}")
