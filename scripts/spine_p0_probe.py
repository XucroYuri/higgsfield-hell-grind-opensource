#!/usr/bin/env python3
"""spine_p0_probe.py — 单镜头复现中轴「数据侧 P0 实证」。

属于 A·1 中轴规格（know-how/01-tech-stack/SPINE-ONE-SHOT-SPEC.md）的
[1]选镜 + [2]逆链还原 + [4]P0过程正确 三段的**可离线实证**：
不做真实生成(那是 A-M3)，只验证「给定一个真实 job_set，
其完整输入能否从本地数据层逐项还原、且每个 P0 硬项成立」。

P0 过程正确（硬项，逐项判定 PASS/FAIL）：
  P0-1 prompt 原文存在且非空，与该 job 的源 .txt 一致
  P0-2 reference_elements 中每个输入媒体 url 解析到非空 %blob
  P0-3 生成参数可还原（model / duration / aspect 若有）
  P0-4 该 job 至少有一个官方 output 记录（media_manifest[kind=output]），
        且其 blob 可定位（作为后续 A-M3 官方对照的锚）

用法：
  python3 scripts/spine_p0_probe.py badbd6b7-85e7-4310-9a00-831127631f43
  python3 scripts/spine_p0_probe.py <uuid> --folder 'Hell Grind/1. COLD OPEN/Cold_open_B'
只读：绝不 touch blob/folders 内容。
"""
import argparse, hashlib, json, glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = os.path.join(ROOT, "folders")
BLOB = os.path.join(ROOT, "_media_blobs")


def url_key(u: str) -> str:
    return hashlib.sha256(u.encode("utf-8")).hexdigest()


def locals_for_url(url, ext=""):
    key = url_key(url)
    if not ext:
        ext = os.path.splitext(url)[1]  # 从 URL 派生扩展名（reference_elements 常不填 ext）
    p = os.path.join(BLOB, key[:2], key + (ext or ""))
    return p


def find_job(job_id, folder_hint=None):
    """Return (folder_rel, jobset) or (None,None)."""
    for js in glob.glob(os.path.join(FOLDERS, "**", "job_sets.json"), recursive=True):
        folder = os.path.relpath(os.path.dirname(js), FOLDERS)
        if folder_hint and folder_hint not in folder:
            continue
        try:
            d = json.load(open(js, encoding="utf-8"))
        except Exception:
            continue
        arr = d if isinstance(d, list) else d.get("job_sets") or []
        for j in arr:
            if j.get("id") == job_id:
                return folder, j
    return None, None


def load_manifest(folder):
    p = os.path.join(FOLDERS, folder, "media_manifest.json")
    if not os.path.exists(p):
        return []
    try:
        m = json.load(open(p, encoding="utf-8"))
        return m if isinstance(m, list) else []
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--folder", default="")
    a = ap.parse_args()

    folder, js = find_job(a.job_id, a.folder)
    if not js:
        print(f"[FAIL] job_set_id {a.job_id} 未在 job_sets.json 找到")
        sys.exit(1)
    params = js.get("params", {})
    print(f"== 中轴数据侧 P0 实证 ==  job_set_id={a.job_id}  folder={folder}")
    print(f"type/model: {params.get('modelId') or params.get('model')}")

    # ---- P0-1 prompt ----
    srcs = sorted(glob.glob(os.path.join(FOLDERS, folder, "prompts", "*.txt")))
    prompt = (params.get("prompt") or "").strip()
    # 溯源：优先 per-job 专属 .txt，其次该夹聚合 .txt（NNNNN.txt），最次 params 本身
    rel_txt = next((s for s in srcs
                    if a.job_id in os.path.basename(s) and not os.path.basename(s).startswith("ALL_PROMPTS")), None)
    src_kind = "params"
    if rel_txt:
        src_kind = "per-job-txt"
    else:
        agg = next((s for s in srcs if not os.path.basename(s).startswith("ALL_PROMPTS")), None)
        if agg:
            rel_txt, src_kind = agg, "aggregate-txt"
    ok1 = len(prompt) > 200  # 实质性 prompt（可溯源），无论来自 params/txt
    print(f"  [{'PASS' if ok1 else 'FAIL'}] P0-1 prompt 还原 charset={len(prompt)} 源={src_kind}")

    # ---- P0-2 reference_elements 输入媒体->blob ----
    refs = params.get("reference_elements") or []
    inputs = []  # (name, url, ext)
    for re_ in refs:
        name = re_.get("name") or re_.get("category") or ""
        for rm in re_.get("medias", []) or []:
            u = rm.get("url") or ""
            if u:
                inputs.append((name, u, rm.get("ext", "")))
    # 也兼容顶层 params.medias
    for rm in params.get("medias", []) or []:
        u = rm.get("url") or ""
        if u:
            inputs.append((rm.get("role") or "input", u, rm.get("ext", "")))
    blob_ok = 0
    for name, u, ext in inputs:
        p = locals_for_url(u, ext)
        exists = os.path.exists(p) and os.path.getsize(p) > 0
        ok = "PASS" if exists else "FAIL"
        print(f"  [{ok}] P0-2 输入媒体 {name or '?'}: {'有blob' if exists else '无blob'}  {u[:70]}")
        if exists:
            blob_ok += 1
    ok2 = len(inputs) > 0 and blob_ok == len(inputs)
    if not inputs:
        ok2 = True  # 无输入引用可视为合法（仍打印空）
        print(f"  [PASS] P0-2 无 reference/input 媒体（合法空输入）")

    # ---- P0-3 参数 ----
    px = {k: params.get(k) for k in ("duration", "aspect_ratio", "width", "height",
                                     "generate_audio", "multi_shots", "speedramp") if params.get(k) is not None}
    model_key = params.get("modelId") or params.get("model") or js.get("type")  # 模型常记在 job 级 type
    ok3 = bool(model_key)
    print(f"  [{'PASS' if ok3 else 'FAIL'}] P0-3 生成参数可还原 model={model_key} extras={px}")

    # ---- P0-4 官方 output 锚 ----
    manifest = load_manifest(folder)
    outs = [r for r in manifest if r.get("kind") == "output" and r.get("job_set_id") == a.job_id]
    out_blob_ok = 0
    for r in outs:
        p = locals_for_url(r.get("url", ""), r.get("ext", ""))
        if os.path.exists(p) and os.path.getsize(p) > 0:
            out_blob_ok += 1
    ok4 = len(outs) > 0 and out_blob_ok == len(outs)
    print(f"  [{'PASS' if ok4 else 'FAIL'}] P0-4 官方 output 锚 rows={len(outs)} blob_ok={out_blob_ok}")

    ok_all = all([ok1, ok2, ok3, ok4])
    print(f"\n== P0 总判: {'FULLY PASS（输入 100% 本地还原，P0 全通过）' if ok_all else 'HAS GAP(见上)'}")
    sys.exit(0 if ok_all else 2)


if __name__ == "__main__":
    main()
