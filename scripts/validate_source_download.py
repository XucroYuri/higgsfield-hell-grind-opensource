#!/usr/bin/env python3
"""校验源仓媒体下载完整性：漏下、空文件、路径偏移、manifest 与落盘不一致。

用法：
  python3 scripts/validate_source_download.py
  python3 scripts/validate_source_download.py --strict
  python3 scripts/validate_source_download.py --sample 50

输出：
  meta/download_validation_report.json
  meta/download_validation_report.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ROOT / "folders"
META = ROOT / "meta"
BLOB = ROOT / "_media_blobs"

# 与 download_media_and_fix_names.select_download_records 对齐的精简版期望路径
def url_ext(url: str, default: str = ".bin") -> str:
    path = urlparse(url).path
    base = Path(path).name
    if "." in base:
        ext = "." + base.rsplit(".", 1)[-1].lower()
        if 1 < len(ext) <= 6:
            return ext
    return default


def select_expected(records: list[dict]) -> list[dict]:
    """与下载脚本一致：每 job 优先 raw；缩略图每 job 一张；references 按 url 去重。"""
    by_job_out: dict[str, list] = {}
    by_job_thumb: dict[str, dict] = {}
    refs: list[dict] = []
    for rec in records:
        kind = rec.get("kind")
        url = rec.get("url")
        if not url:
            continue
        if kind == "reference":
            refs.append(rec)
        elif kind == "output":
            jid = rec.get("job_id") or rec.get("job_set_id") or "unknown"
            by_job_out.setdefault(jid, []).append(rec)
        elif kind == "thumbnail":
            jid = rec.get("job_id") or rec.get("job_set_id") or "unknown"
            prev = by_job_thumb.get(jid)
            if prev is None or rec.get("quality") == "raw":
                by_job_thumb[jid] = rec
    selected: list[dict] = []
    for jid, outs in by_job_out.items():
        preferred = None
        for q in ("raw", "min", "h264"):
            for r in outs:
                if r.get("quality") == q:
                    preferred = r
                    break
            if preferred:
                break
        if preferred is None and outs:
            preferred = outs[0]
        if preferred:
            selected.append(preferred)
            pref_url = preferred["url"]
            for r in outs:
                if r is not preferred and r.get("url") and r["url"] != pref_url:
                    selected.append(r)
    selected.extend(by_job_thumb.values())
    seen = set()
    for r in refs:
        u = r["url"]
        if u in seen:
            continue
        seen.add(u)
        selected.append(r)
    return selected


def expected_paths(folder_dir: Path, rec: dict) -> list[Path]:
    kind = rec.get("kind")
    ext = rec.get("ext") or url_ext(rec.get("url") or "", ".bin")
    job_id = rec.get("job_id") or rec.get("job_set_id") or "unknown"
    paths: list[Path] = []
    if kind == "output":
        quality = rec.get("quality") or "raw"
        name = f"output{ext}" if quality == "raw" else f"output_{quality}{ext}"
        paths.append(folder_dir / "Assets" / "outputs" / job_id / name)
    elif kind == "thumbnail":
        paths.append(folder_dir / "Assets" / "outputs" / job_id / f"thumbnail{ext}")
        paths.append(folder_dir / "Assets" / "thumbnails" / f"{job_id}{ext}")
    elif kind == "reference":
        mid = rec.get("media_id")
        if not mid:
            import hashlib
            mid = hashlib.sha256((rec.get("url") or "").encode()).hexdigest()[:16]
        paths.append(folder_dir / "Assets" / "references" / f"{mid}{ext}")
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="任一 missing/empty 则 exit 1")
    ap.add_argument("--sample", type=int, default=0, help="仅抽查 N 个 folder（0=全量）")
    args = ap.parse_args()

    manifests = sorted(FOLDERS.rglob("media_manifest.json"))
    if args.sample > 0:
        manifests = manifests[: args.sample]

    stats = Counter()
    missing: list[dict] = []
    empty: list[dict] = []
    orphan_hint = Counter()
    folders_ok = 0
    folders_bad = 0
    by_folder: dict[str, dict] = {}

    t0 = time.time()
    for mi, man in enumerate(manifests, 1):
        folder_dir = man.parent
        rel = str(folder_dir.relative_to(ROOT))
        try:
            records = json.loads(man.read_text(encoding="utf-8"))
        except Exception as e:
            stats["manifest_read_error"] += 1
            missing.append({"folder": rel, "error": f"manifest: {e}"})
            folders_bad += 1
            continue
        if not isinstance(records, list):
            stats["manifest_not_list"] += 1
            folders_bad += 1
            continue

        selected = select_expected(records)
        exp_files = 0
        miss = 0
        emp = 0
        ok = 0
        for rec in selected:
            paths = expected_paths(folder_dir, rec)
            # thumbnail 有双路径：至少一个有效即可算到；但 outputs 下 thumbnail 为规范
            if rec.get("kind") == "thumbnail":
                primary = paths[0] if paths else None
                if primary is None:
                    continue
                exp_files += 1
                if primary.exists() and primary.stat().st_size > 0:
                    ok += 1
                elif primary.exists():
                    emp += 1
                    empty.append({"path": str(primary.relative_to(ROOT)), "url": rec.get("url"), "kind": "thumbnail"})
                else:
                    # 扁平索引是否存在
                    alt = paths[1] if len(paths) > 1 else None
                    if alt and alt.exists() and alt.stat().st_size > 0:
                        ok += 1
                        stats["thumbnail_only_flat"] += 1
                    else:
                        miss += 1
                        missing.append(
                            {
                                "path": str(primary.relative_to(ROOT)),
                                "url": rec.get("url"),
                                "kind": "thumbnail",
                                "job_id": rec.get("job_id"),
                            }
                        )
                continue

            for p in paths:
                exp_files += 1
                if p.exists() and p.stat().st_size > 0:
                    ok += 1
                elif p.exists():
                    emp += 1
                    empty.append({"path": str(p.relative_to(ROOT)), "url": rec.get("url"), "kind": rec.get("kind")})
                else:
                    miss += 1
                    missing.append(
                        {
                            "path": str(p.relative_to(ROOT)),
                            "url": rec.get("url"),
                            "kind": rec.get("kind"),
                            "job_id": rec.get("job_id"),
                            "job_set_id": rec.get("job_set_id"),
                        }
                    )

        # 粗检：Assets 是否存在但无任何 expected 文件（路径偏移线索）
        assets = folder_dir / "Assets"
        if assets.is_dir() and exp_files == 0 and any(assets.rglob("*")):
            orphan_hint["assets_without_selected_expectations"] += 1

        folder_stat = {
            "expected": exp_files,
            "ok": ok,
            "missing": miss,
            "empty": emp,
            "records_in_manifest": len(records),
            "selected": len(selected),
        }
        by_folder[rel] = folder_stat
        stats["expected_files"] += exp_files
        stats["ok_files"] += ok
        stats["missing_files"] += miss
        stats["empty_files"] += emp
        if miss or emp:
            folders_bad += 1
        else:
            folders_ok += 1

        if mi % 20 == 0:
            print(f"  scanned {mi}/{len(manifests)} folders…", flush=True)

    # 进度文件对照
    progress = {}
    prog_path = META / "media_download_progress.json"
    if prog_path.exists():
        try:
            progress = json.loads(prog_path.read_text(encoding="utf-8"))
        except Exception:
            progress = {}

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_sec": round(time.time() - t0, 2),
        "manifests_scanned": len(manifests),
        "folders_ok": folders_ok,
        "folders_with_issues": folders_bad,
        "stats": dict(stats),
        "download_progress_snapshot": {
            "done": progress.get("done"),
            "total": progress.get("total"),
            "ok": progress.get("ok"),
            "error": progress.get("error"),
            "bytes": progress.get("bytes"),
        },
        "blob_dir_exists": BLOB.is_dir(),
        "missing_count": len(missing),
        "empty_count": len(empty),
        "missing_sample": missing[:200],
        "empty_sample": empty[:100],
        "orphan_hints": dict(orphan_hint),
        "by_folder_sample": dict(list(by_folder.items())[:30]),
        "notes": [
            "期望路径与 download_media_and_fix_names.select_download_records 对齐。",
            "下载进行中 missing 属正常；完成后应 missing≈0。",
            "rename 前后路径会变；全量校验应在命名后处理完成后重跑。",
        ],
    }

    META.mkdir(parents=True, exist_ok=True)
    out_json = META / "download_validation_report.json"
    out_md = META / "download_validation_report.md"
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    pct = 0.0
    if stats["expected_files"]:
        pct = 100.0 * stats["ok_files"] / stats["expected_files"]
    md = f"""# 源仓下载校验报告

- 生成时间：{report['generated_at']}
- 扫描 manifest：{len(manifests)}
- 文件夹完好 / 有问题：{folders_ok} / {folders_bad}
- 期望文件：{stats['expected_files']}
- 已存在非空：{stats['ok_files']}（{pct:.2f}%）
- 缺失：{stats['missing_files']}
- 空文件：{stats['empty_files']}
- 下载进度快照：done={progress.get('done')} / total={progress.get('total')} err={progress.get('error')}

## 说明

期望落盘规则与 `scripts/download_media_and_fix_names.py` 一致。  
**全量通过标准（下载+命名后处理完成后）：** missing=0、empty=0、folders_with_issues=0。

## 缺失样本（最多 50）

"""
    for m in missing[:50]:
        md += f"- `{m.get('path')}` kind={m.get('kind')}\n"
    if not missing:
        md += "- （无）\n"
    md += "\n## 空文件样本\n\n"
    for m in empty[:30]:
        md += f"- `{m.get('path')}`\n"
    if not empty:
        md += "- （无）\n"
    out_md.write_text(md, encoding="utf-8")

    print(md)
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")

    if args.strict and (missing or empty):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
