#!/usr/bin/env python3
"""Rebuild media manifests, download all media/thumbnails, then restore original names.

Phases:
  1) scan job_sets.json → rebuild per-folder media_manifest.json
  2) download outputs + references + thumbnails into Assets/
  3) rename Name__hash folders/files back to original names
  4) write locked id↔path mapping under meta/

Distinguishes:
  - Assets/outputs/     generation results (shot media)
  - Assets/references/  prompt reference materials
  - Assets/thumbnails/  result thumbnails (also next to outputs when tied to a job)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import time
import traceback
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ROOT / "folders"
META = ROOT / "meta"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
)
WORKERS = int(os.environ.get("HG_MEDIA_WORKERS", "32"))
MAX_RETRIES = 5
TIMEOUT = 180

# global blob store for dedup hardlinks
BLOB_DIR = ROOT / "_media_blobs"


def log(msg: str) -> None:
    print(msg, flush=True)


def safe_name(name: str, fallback: str = "unnamed") -> str:
    name = (name or fallback).strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name[:180] or fallback)


def url_ext(url: str, default: str = ".bin") -> str:
    path = urlparse(url).path
    base = Path(path).name
    if "." in base:
        ext = "." + base.rsplit(".", 1)[-1].lower()
        if len(ext) <= 6 and re.match(r"^\.[a-z0-9]+$", ext):
            return ext
    if "thumbnail" in url:
        return ".webp"
    return default


def url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_media_from_job_set(js: dict, folder_id: str) -> list[dict]:
    """Return media records for one job_set: outputs, thumbnails, references."""
    records: list[dict] = []
    jsid = js.get("id") or "unknown"
    params = js.get("params") or {}

    # --- references (prompt-side materials) ---
    def add_ref(url: str, source: str, extra: dict | None = None) -> None:
        if not url or not isinstance(url, str) or not url.startswith("http"):
            return
        rec = {
            "kind": "reference",
            "role": "reference",
            "url": url,
            "job_set_id": jsid,
            "folder_id": folder_id,
            "source": source,
            "ext": url_ext(url, ".png"),
        }
        if extra:
            rec.update(extra)
        records.append(rec)

    for i, relem in enumerate(params.get("reference_elements") or []):
        if not isinstance(relem, dict):
            continue
        for j, m in enumerate(relem.get("medias") or []):
            if isinstance(m, dict):
                add_ref(
                    m.get("url") or "",
                    "params.reference_elements",
                    {
                        "ref_index": i,
                        "media_index": j,
                        "ref_type": relem.get("type") or relem.get("role"),
                        "media_id": m.get("id"),
                    },
                )
            elif isinstance(m, str):
                add_ref(m, "params.reference_elements", {"ref_index": i, "media_index": j})

    for j, m in enumerate(params.get("medias") or []):
        if isinstance(m, dict):
            add_ref(m.get("url") or "", "params.medias", {"media_index": j, "media_id": m.get("id")})
        elif isinstance(m, str):
            add_ref(m, "params.medias", {"media_index": j})

    for key in ("input_image", "start_image", "end_image", "image"):
        v = params.get(key)
        if isinstance(v, str):
            add_ref(v, f"params.{key}")
        elif isinstance(v, dict):
            add_ref(v.get("url") or "", f"params.{key}", {"media_id": v.get("id")})

    # --- outputs ---
    for job in js.get("jobs") or []:
        if not isinstance(job, dict):
            continue
        job_id = job.get("id") or "unknown-job"
        results = job.get("results")
        candidates: list[dict] = []
        if isinstance(results, dict):
            candidates.append(results)
        elif isinstance(results, list):
            candidates.extend([x for x in results if isinstance(x, dict)])
        result = job.get("result")
        if isinstance(result, dict):
            candidates.append(result)

        seen_out_urls: set[str] = set()
        for res in candidates:
            for quality in ("raw", "min", "h264", "hls"):
                part = res.get(quality)
                if not isinstance(part, dict):
                    continue
                url = part.get("url")
                if url and url not in seen_out_urls:
                    seen_out_urls.add(url)
                    records.append(
                        {
                            "kind": "output",
                            "role": "output",
                            "quality": quality,
                            "media_type": part.get("type"),
                            "url": url,
                            "job_set_id": jsid,
                            "job_id": job_id,
                            "folder_id": folder_id,
                            "ext": url_ext(url, ".mp4" if part.get("type") == "video" else ".png"),
                        }
                    )
                thumb = part.get("thumbnail_url")
                if thumb:
                    records.append(
                        {
                            "kind": "thumbnail",
                            "role": "thumbnail",
                            "quality": quality,
                            "url": thumb,
                            "job_set_id": jsid,
                            "job_id": job_id,
                            "folder_id": folder_id,
                            "ext": url_ext(thumb, ".webp"),
                        }
                    )
    return records


def rebuild_manifests() -> dict:
    log("=== Phase 1: rebuild media manifests ===")
    stats = {"folders": 0, "records": 0, "outputs": 0, "thumbnails": 0, "references": 0}
    for folder_json in FOLDERS.rglob("folder.json"):
        folder_dir = folder_json.parent
        job_sets_path = folder_dir / "job_sets.json"
        if not job_sets_path.exists():
            continue
        folder = json.loads(folder_json.read_text(encoding="utf-8"))
        folder_id = folder.get("id") or folder_dir.name
        data = json.loads(job_sets_path.read_text(encoding="utf-8"))
        job_sets = data.get("job_sets") or []
        records: list[dict] = []
        seen: set[tuple] = set()
        for js in job_sets:
            for rec in collect_media_from_job_set(js, folder_id):
                key = (rec["kind"], rec["url"], rec.get("job_id"), rec.get("quality"))
                if key in seen:
                    continue
                seen.add(key)
                records.append(rec)
                stats[rec["kind"] + "s" if rec["kind"] + "s" in stats else "records"]  # noop guard
                if rec["kind"] == "output":
                    stats["outputs"] += 1
                elif rec["kind"] == "thumbnail":
                    stats["thumbnails"] += 1
                elif rec["kind"] == "reference":
                    stats["references"] += 1
        # dedupe by url+kind+job for manifest list
        write_json(folder_dir / "media_manifest.json", records)
        stats["folders"] += 1
        stats["records"] += len(records)
        if stats["folders"] % 20 == 0:
            log(f"  manifests {stats['folders']} folders, {stats['records']} records...")
    write_json(META / "media_manifest_rebuild_stats.json", stats)
    log(f"Phase 1 done: {stats}")
    return stats


def download_one(url: str, dest: Path) -> tuple[str, str, int]:
    """Download url to dest via blob store + hardlink/copy. Returns (status, url, bytes)."""
    if dest.exists() and dest.stat().st_size > 0:
        return ("exists", url, dest.stat().st_size)

    key = url_key(url)
    ext = dest.suffix or url_ext(url)
    blob = BLOB_DIR / key[:2] / f"{key}{ext}"
    blob.parent.mkdir(parents=True, exist_ok=True)
    dest.parent.mkdir(parents=True, exist_ok=True)

    size = 0
    if not (blob.exists() and blob.stat().st_size > 0):
        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": UA,
                        "Accept": "*/*",
                        "Referer": "https://higgsfield.ai/",
                        "Origin": "https://higgsfield.ai",
                    },
                )
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    data = resp.read()
                tmp = blob.with_suffix(blob.suffix + ".part")
                tmp.write_bytes(data)
                tmp.replace(blob)
                size = len(data)
                last_err = None
                break
            except Exception as e:
                last_err = e
                time.sleep(min(2**attempt, 15))
        if last_err is not None:
            return ("error", url, 0)

    size = blob.stat().st_size
    if dest.exists() and dest.stat().st_size > 0:
        return ("exists", url, size)
    try:
        os.link(blob, dest)
    except OSError:
        shutil.copy2(blob, dest)
    return ("ok", url, size)


def local_paths_for_record(folder_dir: Path, rec: dict) -> list[Path]:
    """Where to place a media record under the folder."""
    paths: list[Path] = []
    kind = rec["kind"]
    ext = rec.get("ext") or url_ext(rec["url"])
    jsid = rec.get("job_set_id") or "unknown"
    job_id = rec.get("job_id") or jsid

    if kind == "output":
        quality = rec.get("quality") or "raw"
        # Prefer raw as primary filename; others quality-tagged
        if quality == "raw":
            name = f"output{ext}"
        else:
            name = f"output_{quality}{ext}"
        paths.append(folder_dir / "Assets" / "outputs" / job_id / name)
    elif kind == "thumbnail":
        # single canonical location under outputs; flat index via hardlink after download
        paths.append(folder_dir / "Assets" / "outputs" / job_id / f"thumbnail{ext}")
    elif kind == "reference":
        # stable name from url hash + optional media_id
        mid = rec.get("media_id") or url_key(rec["url"])[:16]
        paths.append(folder_dir / "Assets" / "references" / f"{mid}{ext}")
    return paths


def select_download_records(records: list[dict]) -> list[dict]:
    """Prefer raw output; keep min/h264 only if URL differs. One thumbnail per job."""
    by_job_out: dict[str, list[dict]] = {}
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
            # prefer thumbnail associated with raw quality
            prev = by_job_thumb.get(jid)
            if prev is None or rec.get("quality") == "raw":
                by_job_thumb[jid] = rec

    selected: list[dict] = []
    for jid, outs in by_job_out.items():
        # pick preferred quality order
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
            # also keep alternate qualities only when URL differs (true extra encodes)
            for r in outs:
                if r is preferred:
                    continue
                if r.get("url") and r["url"] != pref_url:
                    selected.append(r)
    selected.extend(by_job_thumb.values())
    # unique refs by url
    seen_ref: set[str] = set()
    for r in refs:
        u = r["url"]
        if u in seen_ref:
            continue
        seen_ref.add(u)
        selected.append(r)
    return selected


def download_all_media() -> dict:
    log("=== Phase 2: download media ===")
    BLOB_DIR.mkdir(parents=True, exist_ok=True)
    tasks: list[tuple[str, Path, dict, Path]] = []  # url, dest, rec, folder_dir

    for manifest in FOLDERS.rglob("media_manifest.json"):
        folder_dir = manifest.parent
        try:
            records = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(records, list):
            continue
        for rec in select_download_records(records):
            url = rec.get("url")
            if not url:
                continue
            for dest in local_paths_for_record(folder_dir, rec):
                tasks.append((url, dest, rec, folder_dir))

    # Dedupe identical (url, dest) pairs, then group by URL (one network fetch, many hardlinks)
    uniq: dict[tuple[str, str], tuple[str, Path, dict, Path]] = {}
    for url, dest, rec, folder_dir in tasks:
        uniq[(url, str(dest))] = (url, dest, rec, folder_dir)
    tasks = list(uniq.values())

    by_url: dict[str, list[Path]] = {}
    for url, dest, rec, folder_dir in tasks:
        by_url.setdefault(url, []).append(dest)
        # flat thumbnail index for thumbnail outputs
        if rec.get("kind") == "thumbnail":
            job_id = rec.get("job_id") or rec.get("job_set_id") or "unknown"
            ext = rec.get("ext") or url_ext(url, ".webp")
            by_url[url].append(folder_dir / "Assets" / "thumbnails" / f"{job_id}{ext}")

    url_list = list(by_url.items())
    log(f"  download tasks: {len(tasks)} path placements, {len(url_list)} unique URLs (workers={WORKERS})")

    stats = {
        "ok": 0,
        "exists": 0,
        "error": 0,
        "bytes": 0,
        "placements": 0,
        "errors": [],
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    progress_path = META / "media_download_progress.json"
    done = 0
    t0 = time.time()

    def fetch_url_to_dests(url: str, dests: list[Path]) -> tuple[str, str, int, int]:
        """Download once, hardlink/copy to all dests. Returns status, url, bytes, placements."""
        # ensure unique dests
        dest_paths = []
        seen_d: set[str] = set()
        for d in dests:
            s = str(d)
            if s in seen_d:
                continue
            seen_d.add(s)
            dest_paths.append(d)

        # if all exist, skip network
        if dest_paths and all(d.exists() and d.stat().st_size > 0 for d in dest_paths):
            return ("exists", url, dest_paths[0].stat().st_size, len(dest_paths))

        # download to first missing via blob
        primary = dest_paths[0]
        status, u, nbytes = download_one(url, primary)
        if status == "error":
            return ("error", url, 0, 0)
        placed = 1
        for d in dest_paths[1:]:
            if d.exists() and d.stat().st_size > 0:
                placed += 1
                continue
            d.parent.mkdir(parents=True, exist_ok=True)
            try:
                if primary.exists():
                    try:
                        os.link(primary, d)
                    except OSError:
                        shutil.copy2(primary, d)
                    placed += 1
            except Exception:
                # fallback re-download path
                st2, _, _ = download_one(url, d)
                if st2 != "error":
                    placed += 1
        return (status, url, nbytes, placed)

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_url_to_dests, url, dests): url for url, dests in url_list}
        for fut in as_completed(futs):
            url = futs[fut]
            done += 1
            try:
                status, u, nbytes, placed = fut.result()
            except Exception as e:
                status, u, nbytes, placed = "error", url, 0, 0
                if len(stats["errors"]) < 500:
                    stats["errors"].append({"url": url, "error": str(e)})
            if status == "ok":
                stats["ok"] += 1
                stats["bytes"] += nbytes
            elif status == "exists":
                stats["exists"] += 1
                stats["bytes"] += nbytes
            else:
                stats["error"] += 1
                if len(stats["errors"]) < 500:
                    stats["errors"].append({"url": url, "error": "download failed"})
            stats["placements"] += placed

            if done % 100 == 0 or done == len(url_list):
                elapsed = max(time.time() - t0, 1)
                rate = done / elapsed
                log(
                    f"  progress {done}/{len(url_list)} urls "
                    f"ok={stats['ok']} exists={stats['exists']} err={stats['error']} "
                    f"bytes={stats['bytes']/1e9:.2f}GB rate={rate:.1f} url/s"
                )
                stats["done"] = done
                stats["total"] = len(url_list)
                stats["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                write_json(progress_path, stats)

    stats["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(META / "media_download_stats.json", stats)
    log(f"Phase 2 done: {stats['ok']}+{stats['exists']} ok/exists, {stats['error']} errors, {stats['bytes']/1e9:.2f}GB")
    return stats


HASH_DIR_RE = re.compile(r"^(?P<name>.+)__(?P<hash>[0-9a-fA-F]{8})$")
# 下载期错误后缀；终态要去掉。prompt 文件用官方 job_set_id 作稳定键（API 标识，非自创场次名）
HASH_FILE_RE = re.compile(r"^(?P<idx>\d{5})_(?P<hash>[0-9a-fA-F]{8})(?P<ext>\.[^.]+)$")


def filesystem_safe_official_name(official_name: str) -> str:
    """仅替换操作系统非法字符，不发明序号/哈希消歧。"""
    # 保留官方 name 的可读性；只处理路径禁止字符
    name = (official_name or "").strip()
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)
    name = name.strip(" .") or "unnamed"
    return name[:200]


def resolve_storage_dirname(
    parent: Path,
    official_name: str,
    folder_id: str,
    used: set[str],
    self_name: str | None = None,
) -> tuple[str, str]:
    """返回 (storage_dirname, storage_kind).

    storage_kind:
      - official_name: 物理名即官方显示名（经非法字符净化）
      - official_folder_id: 同级同名冲突时，物理名用官方 UUID（非自创消歧名）
    """
    desired = filesystem_safe_official_name(official_name)
    conflict = desired in used or (
        (parent / desired).exists()
        and self_name is not None
        and (parent / desired).name != self_name
        and (parent / desired).resolve() != (parent / self_name).resolve()
    )
    # 自身已是 desired 则不冲突
    if self_name == desired:
        conflict = desired in (used - {desired})
    if not conflict:
        used.add(desired)
        return desired, "official_name"
    # 冲突：只用官方 folder_id 作存储键，绝不使用 (2) / __hash8 污染显示名
    if not folder_id:
        raise RuntimeError(f"同名冲突但缺少 folder_id: parent={parent} name={official_name!r}")
    if folder_id in used or ((parent / folder_id).exists() and self_name != folder_id):
        # 极罕见：已有该 id 目录
        used.add(folder_id)
        return folder_id, "official_folder_id"
    used.add(folder_id)
    return folder_id, "official_folder_id"


def rename_tree() -> dict:
    """去掉 Name__hash 错误后缀，恢复官方显示名；同名冲突时物理路径用官方 UUID。"""
    log("=== Phase 3: 恢复官方命名（禁止自创消歧名）===")
    mapping: dict[str, Any] = {
        "version": 2,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "folders": [],
        "files": [],
        "notes": [
            "official_name：API folder.name，与开源项目显示名一致，可重复。",
            "storage_path：本机路径。优先 official_name；仅同级冲突时用官方 folder_id 作目录名。",
            "禁止 Scene 26 (2) / Name__hash 等自创或下载污染名作为终态。",
            "download_path 中的 __hash8 仅为错误下载期痕迹，记入 legacy_hash8 供审计。",
            "prompt 文件可用 job_set_id（官方生成记录 ID）作稳定文件名键，不是场次改名。",
        ],
    }

    folder_dirs = [p.parent for p in FOLDERS.rglob("folder.json")]
    folder_dirs.sort(key=lambda p: len(p.parts), reverse=True)

    for folder_dir in folder_dirs:
        if not folder_dir.exists():
            continue
        folder_meta_path = folder_dir / "folder.json"
        folder = json.loads(folder_meta_path.read_text(encoding="utf-8"))
        folder_id = folder.get("id") or ""
        original_name = folder.get("name") or ""
        legacy_hash8 = None
        m = HASH_DIR_RE.match(folder_dir.name)
        if m:
            legacy_hash8 = m.group("hash")
        elif folder_id:
            legacy_hash8 = folder_id[:8]

        parent = folder_dir.parent
        used: set[str] = set()
        for ch in parent.iterdir() if parent.exists() else []:
            if ch.is_dir() and ch != folder_dir:
                used.add(ch.name)

        # 根目录官方 name 可能是 HELL GRIND / Hell Grind，以 folder.json 为准
        official_name = original_name if original_name else folder_dir.name
        if folder.get("is_root") or folder_id == "3caa2f3a-52b5-4293-9237-0c8f76c7158a":
            # 仍用元数据名；若为空再回退
            official_name = original_name or "HELL GRIND"

        final_name, storage_kind = resolve_storage_dirname(
            parent, official_name, folder_id, used, self_name=folder_dir.name
        )
        old_rel = str(folder_dir.relative_to(ROOT))
        new_dir = parent / final_name
        if folder_dir.resolve() != new_dir.resolve():
            if new_dir.exists() and new_dir.resolve() != folder_dir.resolve():
                # 目标已被占用：改用 UUID 键（若尚未）
                if storage_kind != "official_folder_id" and folder_id:
                    final_name = folder_id
                    storage_kind = "official_folder_id"
                    new_dir = parent / final_name
                if new_dir.exists() and new_dir.resolve() != folder_dir.resolve():
                    raise RuntimeError(f"无法恢复命名：{old_rel} -> {new_dir}")
            folder_dir.rename(new_dir)
            log(f"  目录: {old_rel} -> {new_dir.relative_to(ROOT)} ({storage_kind})")
        else:
            new_dir = folder_dir

        mapping["folders"].append(
            {
                "folder_id": folder_id,
                "official_name": official_name,
                "legacy_hash8": legacy_hash8,
                "legacy_download_path": old_rel,
                "storage_path": str(new_dir.relative_to(ROOT)),
                "storage_dirname": final_name,
                "storage_kind": storage_kind,
            }
        )

        # prompt 文件：序号 + 官方 job_set_id（生成记录 ID），不发明场次名
        prompts_dir = new_dir / "prompts"
        if prompts_dir.is_dir():
            for fp in list(prompts_dir.iterdir()):
                if not fp.is_file():
                    continue
                m = HASH_FILE_RE.match(fp.name)
                if not m:
                    continue
                idx = m.group("idx")
                old_hash = m.group("hash")
                ext = m.group("ext")
                job_set_id = None
                if ext == ".json":
                    try:
                        data = json.loads(fp.read_text(encoding="utf-8"))
                        job_set_id = data.get("job_set_id")
                    except Exception:
                        job_set_id = None
                else:
                    jp = prompts_dir / f"{idx}_{old_hash}.json"
                    if jp.exists():
                        try:
                            data = json.loads(jp.read_text(encoding="utf-8"))
                            job_set_id = data.get("job_set_id")
                        except Exception:
                            job_set_id = None
                if job_set_id:
                    new_name = f"{idx}_{job_set_id}{ext}"
                else:
                    # 无 job_set_id 时保持序号文件，不编造新语义名
                    new_name = f"{idx}{ext}"
                target = prompts_dir / new_name
                if target == fp:
                    continue
                if target.exists():
                    # 真冲突时退回官方 id 全名
                    new_name = f"{idx}_{job_set_id or old_hash}{ext}"
                    target = prompts_dir / new_name
                    if target.exists() and target != fp:
                        continue
                old_frel = str(fp.relative_to(ROOT))
                fp.rename(target)
                mapping["files"].append(
                    {
                        "type": "prompt",
                        "folder_id": folder_id,
                        "job_set_id": job_set_id,
                        "legacy_download_path": old_frel,
                        "storage_path": str(target.relative_to(ROOT)),
                    }
                )

    write_json(META / "id_path_mapping.json", mapping)
    by_id = {f["folder_id"]: f for f in mapping["folders"] if f.get("folder_id")}
    by_official_name: dict[str, list] = {}
    for f in mapping["folders"]:
        by_official_name.setdefault(f.get("official_name") or "", []).append(f)
    write_json(
        META / "id_path_mapping_index.json",
        {
            "by_folder_id": by_id,
            "by_official_name": by_official_name,
            "folder_count": len(mapping["folders"]),
            "file_count": len(mapping["files"]),
            "collision_uuid_storage": [
                f for f in mapping["folders"] if f.get("storage_kind") == "official_folder_id"
            ],
        },
    )
    log(f"Phase 3 完成: {len(mapping['folders'])} 个文件夹, {len(mapping['files'])} 个文件映射")
    return mapping


def write_final_readme(media_stats: dict, mapping: dict) -> None:
    text = f"""# Hell Grind Open-Source Mirror — Final Layout

## Official source
- https://higgsfield.ai/@higgsfield.studio/projects/hell-grind
- API: `https://fnf.higgsfield.ai`
- Snapshot folder: `3caa2f3a-52b5-4293-9237-0c8f76c7158a`

## Totals (metadata phase)
- folders: 162 (108 top-level scenes/groups + nested)
- job_sets: 38,482
- jobs/generations: ~115,449
- prompts with text: 38,422

## 目录约定（终态命名）

- 文件夹**显示语义**以 `folder.json` 的 `name` 为准（与开源项目一致，可重复）。
- 物理路径优先使用官方 `name`；**禁止** `Name (2)` / `Name__hash` 当正式名。
- 同级同名冲突时物理目录用官方 `folder_id`（UUID），不是自创消歧名。

```
folders/
  <官方 name 或冲突时的 folder_id>/
    folder.json                   # 含官方 name + id
    children.json
    job_sets.json
    prompts/                      # 序号 + job_set_id（生成记录 ID）
    Assets/
      outputs/<job_id>/
      thumbnails/
      references/
    media_manifest.json
```

## Media vs references
| Path | Meaning |
|------|---------|
| `Assets/outputs/` | Model generation results for the shot/job |
| `Assets/thumbnails/` | Result thumbnails |
| `Assets/references/` | Input/reference assets attached to prompts (`reference_elements`, `medias`) |
| `brief/images/` | Web project-brief illustration images (not per-shot) |
| `film/` | Feature film HLS reference + thumbnail |

## ID / hash mapping (locked)
- Full structured map: `meta/id_path_mapping.json`
- Lookup index: `meta/id_path_mapping_index.json`
- Each folder entry includes: `folder_id` (UUID), `hash8`, `original_name`, `download_path`, `final_path`

## Media download stats
```json
{json.dumps({k: media_stats.get(k) for k in ('ok','exists','error','bytes','done','total') if media_stats.get(k) is not None}, indent=2)}
```

Blob dedup store: `_media_blobs/` (hardlinked into Assets where possible).
"""
    (ROOT / "STRUCTURE.md").write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    phases = set(argv[1:] or ["manifests", "media", "rename"])
    META.mkdir(parents=True, exist_ok=True)

    if "manifests" in phases:
        rebuild_manifests()
    media_stats: dict = {}
    if "media" in phases:
        media_stats = download_all_media()
    mapping: dict = {}
    if "rename" in phases:
        mapping = rename_tree()
    if media_stats or mapping:
        if not media_stats and (META / "media_download_stats.json").exists():
            media_stats = json.loads((META / "media_download_stats.json").read_text())
        if not mapping and (META / "id_path_mapping.json").exists():
            mapping = json.loads((META / "id_path_mapping.json").read_text())
        write_final_readme(media_stats, mapping)
    log("ALL PHASES COMPLETE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except KeyboardInterrupt:
        log("interrupted")
        raise SystemExit(130)
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
