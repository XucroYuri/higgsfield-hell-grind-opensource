#!/usr/bin/env python3
"""audit_generation_chain.py — 全链条生成追溯审计（按全量 162 文件夹）。

目的：验证「每一个被分享出来的生成产物，能否回溯到它的完整输入链」。
链式映射（与 scripts/download_media_and_fix_names.py 的下载器一致）：
    output(media_manifest .url/.job_id)
      -> _media_blobs/<sha256(url)[:2]>/<sha256(url)>.ext     (内容寻址, 磁盘)
      -> .job_set_id                                           (manifest)
      -> job_sets.json 中该 id 的 params.prompt/.reference_elements/.medias (输入链)

本脚本是【只读审计】：绝不 touch blobs / folders 内容 / 元数据原文，
只读 manifest/job_sets/prompt_index，并把结果写进 logs/ 与可复用 reverse-map 规范。
输出：
  - logs/audit_chain_<stamp>.json      机器可读汇总 + 断链账本
  - logs/audit_chain_<stamp>.summary   人类可读摘要
设计：断链每一种都附 reason，不臆造链接；只有「真可映射」或「如实记账」两种结局。
"""
import hashlib, json, sys, glob, os, time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # opensource repo root
FOLDERS = os.path.join(ROOT, "folders")
BLOB_DIR = os.path.join(ROOT, "_media_blobs")
LOG_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT_JSON = os.path.join(LOG_DIR, f"audit_chain_{STAMP}.json")
OUT_SUM = os.path.join(LOG_DIR, f"audit_chain_{STAMP}.summary")


def url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def load_jobset_map():
    """folder -> dict[jsid] = jobset. 同时维护 global id->(folder, idx) for cross-folder."""
    per_folder = {}
    global_id = {}
    for jp in glob.glob(os.path.join(FOLDERS, "**", "job_sets.json"), recursive=True):
        folder = os.path.relpath(os.path.dirname(jp), FOLDERS)
        try:
            data = json.load(open(jp, encoding="utf-8"))
        except Exception as e:
            per_folder[folder] = {"__error__": str(e), "id": {}}
            continue
        arr = data if isinstance(data, list) else data.get("job_sets") or data.get("jobSets") or []
        m = {}
        for js in arr:
            jsid = js.get("id")
            if jsid:
                m[jsid] = js
                global_id.setdefault(jsid, (folder, js))
        per_folder[folder] = m
    return per_folder, global_id


def load_manifest(folder):
    p = os.path.join(FOLDERS, folder, "media_manifest.json")
    if not os.path.exists(p):
        return None
    try:
        data = json.load(open(p, encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def blob_path_for(url, ext):
    key = url_key(url)
    fname = key + (ext or "")
    return os.path.exists(os.path.join(BLOB_DIR, key[:2], fname)), f"{key[:2]}/{key}{ext or ''}"


def discover_folders():
    """Colle all dirs that actually contain per-scene metadata (job_sets.json present).
    Scene dirs live two levels below opensource/folders (e.g. folders/Hell Grind/Scene 26/)."""
    out = []
    for root, dirs, files in os.walk(FOLDERS):
        # prune heavy Assets inside walk for speed
        dirs[:] = [d for d in dirs if d != "Assets"]
        if "job_sets.json" in files:
            out.append(os.path.relpath(root, FOLDERS))
    return sorted(out)


def main():
    folders = discover_folders()
    if not folders:
        print("ERROR: no per-scene folders (with job_sets.json) under %s" % FOLDERS, file=sys.stderr)
        sys.exit(1)
    per_folder, global_id = load_jobset_map()

    summary = {
        "folders": len(folders),
        "blob_buckets": len([d for d in os.listdir(BLOB_DIR) if os.path.isdir(os.path.join(BLOB_DIR, d))]) if os.path.isdir(BLOB_DIR) else 0,
        "per_folder": {},
        "totals": {},
        "broken": [],          # ledger
    }
    agg = Counter()
    kind_counter = Counter()
    folder_rows = {}

    for folder in folders:
        manifest = load_manifest(folder)
        jsm = per_folder.get(folder, {})
        n_out = n_out_ok_js = n_out_ok_blob = n_thumb = 0
        reason = Counter()
        unresolved_examples = []

        for rec in manifest or []:
            k = rec.get("kind")
            kind_counter[k] += 1
            if k != "output":
                if k == "thumbnail":
                    n_thumb += 1
                continue
            n_out += 1
            url = rec.get("url", "")
            jsid = rec.get("job_set_id")
            has_blob, blob_rel = blob_path_for(url, rec.get("ext", ""))
            # job_set resolution: local folder, then global fallback
            js_resolved = jsid in jsm
            if not js_resolved and jsid and jsid in global_id:
                js_resolved = True  # cross-folder (shouldn't happen; log if it does)
            if js_resolved:
                n_out_ok_js += 1
            else:
                reason["job_set_id_unresolved"] += 1
            if has_blob:
                n_out_ok_blob += 1
            else:
                reason["blob_missing"] += 1
            if not js_resolved or not has_blob:
                if len(unresolved_examples) < 5:
                    unresolved_examples.append(
                        {"job_id": rec.get("job_id"), "job_set_id": jsid,
                         "blob": blob_rel, "why": "job_set" if not js_resolved else "blob",
                         "url": url[:90] if not has_blob else None})
        sf = {
            "manifest_rows": len(manifest or []),
            "output_rows": n_out,
            "output_js_resolved": n_out_ok_js,
            "output_blob_present": n_out_ok_blob,
            "thumb_rows": n_thumb,
            "jobset_count_local": len([k for k in jsm if not k.startswith("__")]),
            "reasons": dict(reason),
            "unresolved_samples": unresolved_examples,
        }
        folder_rows[folder] = sf
        summary["per_folder"][folder] = sf
        agg["output_rows"] += n_out
        agg["output_js_resolved"] += n_out_ok_js
        agg["output_blob_present"] += n_out_ok_blob
        agg["jobset_total"] += len([k for k in jsm if not k.startswith("__")])
        for rk, rv in reason.items():
            agg["reason_" + rk] += rv

    # prompt->output reverse coverage: for a sample of job_sets across folders, does at least one output exist?
    # (lightweight: count job_sets that appear in any manifest output job_set_id set)
    mc = Counter()
    for folder in folders:
        for rec in (load_manifest(folder) or []):
            if rec.get("kind") == "output" and rec.get("job_set_id"):
                mc[rec["job_set_id"]] += 1
    js_with_output = len(mc)
    js_total = sum(v for k, v in agg.items() if k == "jobset_total") or 0
    # true distinct jobset ids
    distinct_js = set()
    for folder, m in per_folder.items():
        distinct_js.update(k for k in m if not k.startswith("__"))
    summary["totals"] = dict(agg)
    summary["kinds"] = dict(kind_counter)
    summary["distinct_jobset_ids"] = len(distinct_js)
    summary["jobset_ids_with_output"] = js_with_output
    summary["jobset_with_output_frac"] = round(js_with_output / max(1, len(distinct_js)), 4)

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    # Human summary
    rows = []
    rows.append(f"=== 全链条追溯审计 ===  stamp={STAMP}")
    rows.append(f"folders={summary['folders']}  blob_buckets={summary['blob_buckets']}")
    rows.append(f"kinds: {dict(kind_counter)}")
    t = summary["totals"]
    rows.append(f"output_rows={t.get('output_rows')}  js_resolved={t.get('output_js_resolved')}  "
                f"blob_present={t.get('output_blob_present')}")
    rows.append(f"distinct_jobset_ids={summary['distinct_jobset_ids']}  "
                f"ids_with_output={summary['jobset_ids_with_output']}  "
                f"frac={summary['jobset_with_output_frac']}")
    br = {k.replace('reason_',''): v for k, v in t.items() if k.startswith('reason_')}
    rows.append(f"broken_reasons= {br if br else '(none)'}")
    rows.append("")
    rows.append("PER-FOLDER（仅列有断链或 output>0 且未全闭）:")
    for folder, sf in sorted(folder_rows.items()):
        if sf["output_rows"] == 0:
            continue
        if sf["reasons"]:
            rows.append(f"  {folder}: out={sf['output_rows']} js={sf['output_js_resolved']} "
                        f"blob={sf['output_blob_present']} reasons={sf['reasons']}")
        # else fully closed; count them
    closed = sum(1 for sf in folder_rows.values() if sf["output_rows"] > 0 and not sf["reasons"])
    rows.append(f">> 完全闭环(无断链)的文件夹数: {closed}")
    rows.append(f"机器可读账本: {OUT_JSON}")
    with open(OUT_SUM, "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
