#!/usr/bin/env python3
"""Download Hell Grind open-source archive from public Higgsfield FNF API."""
from __future__ import annotations

import json
import os
import re
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API = "https://fnf.higgsfield.ai"
SNAP = "3caa2f3a-52b5-4293-9237-0c8f76c7158a"
PROJECT_ID = "b9d83e92-2bc2-49de-8ef2-1b8d6ae259fe"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
ROOT = Path(__file__).resolve().parents[1]
PAGE_SIZE = 100
MAX_RETRIES = 6
SLEEP = 0.15

def log(msg: str) -> None:
    print(msg, flush=True)

def safe_name(name: str, fallback: str = "unnamed") -> str:
    name = (name or fallback).strip()
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:120] or fallback

def get_json(url: str, timeout: int = 120) -> Any:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "application/json",
                    "Origin": "https://higgsfield.ai",
                    "Referer": "https://higgsfield.ai/@higgsfield.studio/projects/hell-grind",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except Exception as e:
            last_err = e
            wait = min(2 ** attempt, 20)
            log(f"  retry {attempt}/{MAX_RETRIES} after error on {url}: {e} (sleep {wait}s)")
            time.sleep(wait)
    raise RuntimeError(f"Failed GET {url}: {last_err}")

def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def fetch_children(folder_id: str) -> list[dict]:
    items: list[dict] = []
    cursor = None
    seen = set()
    while True:
        q = {"size": str(PAGE_SIZE)}
        if cursor is not None:
            q["cursor"] = str(cursor)
        url = f"{API}/folders/{folder_id}/children?" + urllib.parse.urlencode(q)
        data = get_json(url)
        batch = data.get("items") or []
        new = 0
        for it in batch:
            iid = it.get("id")
            if iid in seen:
                continue
            seen.add(iid)
            items.append(it)
            new += 1
        next_cursor = data.get("cursor")
        log(f"  children page: +{new} (total {len(items)}) next_cursor={next_cursor}")
        if not batch or next_cursor is None or new == 0:
            break
        if next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(SLEEP)
    return items

def fetch_jobs(folder_id: str) -> list[dict]:
    """Fetch all job sets via /items (cursor pagination works here; /jobs does not)."""
    jobs: list[dict] = []
    cursor = None
    seen = set()
    pages = 0
    while True:
        q = {"size": str(PAGE_SIZE)}
        if cursor is not None:
            q["cursor"] = str(cursor)
        url = f"{API}/folders/{folder_id}/items?" + urllib.parse.urlencode(q)
        data = get_json(url)
        batch_items = data.get("items") or []
        batch = []
        for it in batch_items:
            if isinstance(it, dict) and it.get("type") == "job_set" and it.get("job_set"):
                batch.append(it["job_set"])
            elif isinstance(it, dict) and it.get("job_set"):
                batch.append(it["job_set"])
            elif isinstance(it, dict) and it.get("id") and it.get("params") is not None:
                batch.append(it)
        new = 0
        for js in batch:
            jid = js.get("id")
            if not jid or jid in seen:
                continue
            seen.add(jid)
            jobs.append(js)
            new += 1
        next_cursor = data.get("cursor")
        pages += 1
        log(f"  items page {pages}: +{new} (total {len(jobs)}) next_cursor={next_cursor}")
        if not batch_items or next_cursor is None or new == 0:
            break
        if next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(SLEEP)
        if pages > 5000:
            log("  safety stop at 5000 pages")
            break
    return jobs

def extract_media_urls(job_set: dict) -> list[dict]:
    out = []
    for job in job_set.get("jobs") or []:
        result = job.get("result") or {}
        results = job.get("results")
        candidates = []
        if isinstance(results, list):
            candidates.extend(results)
        if isinstance(result, dict):
            candidates.append(result)
        for res in candidates:
            if not isinstance(res, dict):
                continue
            for key in ("raw", "min", "hls", "h264"):
                part = res.get(key)
                if isinstance(part, dict) and part.get("url"):
                    out.append({
                        "job_id": job.get("id"),
                        "quality": key,
                        "type": part.get("type"),
                        "url": part.get("url"),
                        "thumbnail_url": part.get("thumbnail_url"),
                    })
            # sometimes flat
            if res.get("url"):
                out.append({
                    "job_id": job.get("id"),
                    "quality": "url",
                    "type": res.get("type"),
                    "url": res.get("url"),
                    "thumbnail_url": res.get("thumbnail_url"),
                })
    return out

def save_folder(folder: dict, parent_rel: Path) -> dict:
    """落盘目录名：优先官方 name；同级冲突时用官方 folder_id（禁止 Name__hash / Name (2)）。"""
    fid = folder["id"]
    official = folder.get("name") or fid
    name = safe_name(official, fallback=fid)
    parent_abs = ROOT / parent_rel
    parent_abs.mkdir(parents=True, exist_ok=True)
    candidate = parent_abs / name
    # 若已存在且 folder.json 不是同一 id，则物理键改用官方 UUID
    if candidate.exists():
        existing_meta = candidate / "folder.json"
        same = False
        if existing_meta.exists():
            try:
                same = json.loads(existing_meta.read_text(encoding="utf-8")).get("id") == fid
            except Exception:
                same = False
        if same:
            rel = parent_rel / name
        else:
            rel = parent_rel / fid
    else:
        rel = parent_rel / name
    abs_dir = ROOT / rel
    abs_dir.mkdir(parents=True, exist_ok=True)

    meta_path = abs_dir / "folder.json"
    write_json(meta_path, folder)

    summary = {
        "id": fid,
        "name": folder.get("name"),
        "count": folder.get("count"),
        "subfolders_count": folder.get("subfolders_count") or 0,
        "path": str(rel),
        "jobs": 0,
        "prompts": 0,
        "children": [],
        "errors": [],
    }

    # children first (only when API reports subfolders, or for root)
    try:
        sub_n = folder.get("subfolders_count")
        if sub_n is None or sub_n > 0 or folder.get("is_root"):
            children = fetch_children(fid)
            write_json(abs_dir / "children.json", {"items": children})
            for child in children:
                if child.get("id") == fid:
                    continue
                child_summary = save_folder(child, rel)
                summary["children"].append(child_summary)
        else:
            write_json(abs_dir / "children.json", {"items": []})
    except Exception as e:
        summary["errors"].append(f"children: {e}")
        log(f"ERROR children {name}: {e}")
        traceback.print_exc()

    # jobs / prompts
    try:
        jobs = fetch_jobs(fid)
        write_json(abs_dir / "job_sets.json", {"job_sets": jobs, "count": len(jobs)})
        summary["jobs"] = len(jobs)

        prompts_dir = abs_dir / "prompts"
        prompts_dir.mkdir(exist_ok=True)
        media_manifest = []
        prompt_index = []

        for i, js in enumerate(jobs, 1):
            jid = js.get("id") or f"idx-{i}"
            params = js.get("params") or {}
            prompt = params.get("prompt") or ""
            if not prompt and isinstance(params.get("multi_prompt"), list):
                # multi-prompt forms
                parts = []
                for mp in params.get("multi_prompt") or []:
                    if isinstance(mp, dict) and mp.get("prompt"):
                        parts.append(mp["prompt"])
                    elif isinstance(mp, str):
                        parts.append(mp)
                prompt = "\n\n---\n\n".join(parts)

            record = {
                "job_set_id": jid,
                "type": js.get("type"),
                "created_at": js.get("created_at"),
                "project_id": js.get("project_id"),
                "params": params,
                "client_meta": js.get("client_meta"),
                "jobs": [
                    {
                        "id": j.get("id"),
                        "status": j.get("status"),
                        "created_at": j.get("created_at"),
                        "folder_job_id": j.get("folder_job_id"),
                        "result": j.get("result"),
                        "results": j.get("results"),
                        "representation": j.get("representation"),
                        "meta": j.get("meta"),
                    }
                    for j in (js.get("jobs") or [])
                ],
            }
            write_json(prompts_dir / f"{i:05d}_{jid[:8]}.json", record)

            if prompt:
                summary["prompts"] += 1
                txt = prompts_dir / f"{i:05d}_{jid[:8]}.txt"
                header = [
                    f"job_set_id: {jid}",
                    f"type: {js.get('type')}",
                    f"created_at: {js.get('created_at')}",
                    f"prompt_language: {params.get('prompt_language')}",
                    "",
                ]
                txt.write_text("\n".join(header) + prompt, encoding="utf-8")

            media = extract_media_urls(js)
            for m in media:
                m["job_set_id"] = jid
                m["index"] = i
                media_manifest.append(m)

            prompt_index.append({
                "index": i,
                "job_set_id": jid,
                "type": js.get("type"),
                "created_at": js.get("created_at"),
                "has_prompt": bool(prompt),
                "prompt_chars": len(prompt or ""),
                "media_count": len(media),
            })

        write_json(abs_dir / "prompt_index.json", prompt_index)
        write_json(abs_dir / "media_manifest.json", media_manifest)

        # consolidated prompts file for convenience
        all_prompts = []
        for i, js in enumerate(jobs, 1):
            params = js.get("params") or {}
            prompt = params.get("prompt") or ""
            if prompt:
                all_prompts.append(
                    f"===== [{i}] {js.get('id')} | {js.get('type')} =====\n{prompt}\n"
                )
        if all_prompts:
            (abs_dir / "ALL_PROMPTS.txt").write_text("\n".join(all_prompts), encoding="utf-8")

    except Exception as e:
        summary["errors"].append(f"jobs: {e}")
        log(f"ERROR jobs {name}: {e}")
        traceback.print_exc()

    write_json(abs_dir / "summary.json", summary)
    log(f"DONE folder {name}: jobs={summary['jobs']} prompts={summary['prompts']} children={len(summary['children'])}")
    return summary

def main() -> int:
    (ROOT / "meta").mkdir(parents=True, exist_ok=True)
    (ROOT / "folders").mkdir(parents=True, exist_ok=True)

    log("Fetching root folder...")
    root = get_json(f"{API}/folders/{SNAP}?include_folders_count=true")
    write_json(ROOT / "meta" / "root-folder.json", root)

    project_meta = {
        "source": "https://higgsfield.ai/@higgsfield.studio/projects/hell-grind",
        "api_base": API,
        "project_id": PROJECT_ID,
        "snapshot_folder_id": SNAP,
        "source_folder_id": (root.get("publication") or {}).get("original_folder_id"),
        "title": root.get("name"),
        "count": root.get("count"),
        "subfolders_count": root.get("subfolders_count"),
        "is_snapshot": root.get("is_snapshot"),
        "force_show_prompts": root.get("force_show_prompts"),
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "film": {
            "hls": "https://cdn.higgsfield.ai/hls/video_input/d239c691-6c91-4d46-a498-4adbb4c5f4df/index.m3u8",
            "thumbnail": "https://cdn.higgsfield.ai/hls/video_input/d239c691-6c91-4d46-a498-4adbb4c5f4df/thumbnail.webp",
            "duration_seconds": 5706,
        },
        "github_official": None,
        "notes": [
            "Official open-source delivery is on Higgsfield platform, not a GitHub repo.",
            "Media binary files are listed in per-folder media_manifest.json; full media download is optional due to size.",
        ],
    }
    write_json(ROOT / "meta" / "project.json", project_meta)

    log(f"Root: {root.get('name')} count={root.get('count')} subfolders={root.get('subfolders_count')}")
    summary = save_folder(root, Path("folders"))
    write_json(ROOT / "meta" / "download-summary.json", summary)

    # totals
    def walk(s):
        jobs = s.get("jobs", 0)
        prompts = s.get("prompts", 0)
        errors = list(s.get("errors") or [])
        folders = 1
        for c in s.get("children") or []:
            j, p, f, e = walk(c)
            jobs += j
            prompts += p
            folders += f
            errors.extend(e)
        return jobs, prompts, folders, errors

    jobs, prompts, folders, errors = walk(summary)
    totals = {
        "folders": folders,
        "job_sets": jobs,
        "prompts": prompts,
        "errors": errors,
        "claimed_generations": root.get("count"),
        "claimed_subfolders": root.get("subfolders_count"),
    }
    write_json(ROOT / "meta" / "totals.json", totals)
    log(f"TOTALS: folders={folders} job_sets={jobs} prompts={prompts} errors={len(errors)}")
    return 0 if not errors else 2

if __name__ == "__main__":
    sys.exit(main())
