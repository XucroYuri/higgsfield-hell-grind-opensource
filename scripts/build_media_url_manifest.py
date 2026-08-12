#!/usr/bin/env python3
"""build_media_url_manifest.py — 生成发布用媒体 URL 清单（不落本地媒体文件）。

原则（第1点 · opensource GitHub 发布边界）：
  > GitHub 发布内容里，视频/媒体只引用「官方公开网页 / 官方 CDN」的 URL，
  > 绝不提交本地 blob 文件（862G `_media_blobs/`、`film/*.mp4` 等均已 gitignore）。

本脚本把 162 个 `media_manifest.json` 里的全部媒体记录（output/thumbnail/reference）
汇聚去重，输出一份**只含官方 URL 的清单**，供 GitHub 发布物可追溯引用：
  meta/media_url_manifest.jsonl   —— 机器可读：url, kind, job_set_id, job_id, folder, ext
  meta/media_url_manifest.md      —— 人类可读：按 kind 计数 + 官方 CDN 域名统计

安全：只读 manifest，绝 touch blob/folders。
"""
import json, glob, os, time
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = os.path.join(ROOT, "folders")
META = os.path.join(ROOT, "meta")
DOMAINS = ("higgsfield.ai", "cloudfront.net")


def main():
    os.makedirs(META, exist_ok=True)
    seen = set()
    rows = []
    for mp in glob.glob(os.path.join(FOLDERS, "**", "media_manifest.json"), recursive=True):
        folder = os.path.relpath(os.path.dirname(mp), FOLDERS)
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(m, list):
            continue
        for r in m:
            u = r.get("url") or ""
            if not u:
                continue
            if u in seen:
                continue
            seen.add(u)
            rows.append({
                "url": u, "kind": r.get("kind"), "role": r.get("role"),
                "job_set_id": r.get("job_set_id"), "job_id": r.get("job_id"),
                "folder": folder, "ext": r.get("ext"),
            })

    # 排序：folder, kind, url
    rows.sort(key=lambda x: (x["folder"], str(x["kind"]), x["url"]))

    knife = {k: n for k, n in Counter(r["kind"] for r in rows).items() if k}
    domain_counter = Counter()
    for r in rows:
        for dom in DOMAINS:
            if dom in r["url"]:
                domain_counter[dom] += 1
                break

    jsonl = os.path.join(META, "media_url_manifest.jsonl")
    with open(jsonl, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    md = os.path.join(META, "media_url_manifest.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# 媒体 URL 发布清单（不落本地媒体文件）\n\n")
        f.write("> 原则：GitHub 发布只引用官方公开 URL，绝不含本地 blob/媒体文件。\n")
        f.write(f"> 生成：{time.strftime('%Y-%m-%d %H:%M:%S')}  |  去重后媒体行 {len(rows)}\n\n")
        f.write("## 按 kind 计数\n\n| kind | 数量 |\n|------|-----:|\n")
        for k, n in sorted(knife.items(), key=lambda x: -x[1]):
            f.write(f"| {k} | {n} |\n")
        f.write("\n## 官方 CDN 域名计数\n\n| 域名 | 引用数 |\n|------|------:|\n")
        for dom, n in domain_counter.most_common():
            f.write(f"| {dom} | {n} |\n")
        f.write("\n## 样例（每 kind 3 条）\n\n")
        for k in knife:
            f.write(f"### {k}\n\n")
            for r in [x for x in rows if x.get("kind") == k][:3]:
                f.write(f"- {r['url']}  `{r['folder']}` jobset={r.get('job_set_id')}\n")
        f.write("\n---\n机器可读：`meta/media_url_manifest.jsonl`\n")

    print(f"去重媒体 URL 行数: {len(rows)}")
    print(f"kind 分布: {dict(knife)}")
    print(f"域名分布: {dict(domain_counter)}")
    print(f"写出:\n  {jsonl}\n  {md}")


if __name__ == "__main__":
    main()
