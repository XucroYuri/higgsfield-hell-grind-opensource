#!/usr/bin/env python3
"""download_series_missing.py — 补齐审计发现的缺失媒体 blob（Series/ 及任一带缺口）。

背景：全链条审计（audit_generation_chain.py）发现 123,158 条 output 里 948 条
blob 缺，98% 集中在 Series/ 子目录，且抽查 URL 返回 HTTP 200（可再下载）——
是下载覆盖缺口，不是结构断链。

本脚本：
  1) 遍历全部 media_manifest.json，收集 kind=output|thumbnail|reference 的缺失 blob
     （用与 download_media_and_fix_names.py 一致的 url_key=sha256(url)，落在 _media_blobs）。
  2) 增量下载缺失项（并发带限），跳过已存在/非零的 blob。
  3) 输出缺失/成功/失败账本到 logs/；绝不 touch folders 内容，绝不动已存在 blob。

用法：
  python3 scripts/download_series_missing.py            # 真实下载
  python3 scripts/download_series_missing.py --dry-run  # 只看会下什么

安全/纪律：
  - 只写 _media_blobs（内容寻址目录）；不新建/改 folders/**/Assets。
  - 增量：存在且非空的 blob 一律跳过。
  - 与 862G NAS 同步抢带宽 → 建议同步完成后再跑。
"""
import argparse, concurrent.futures, hashlib, json, glob, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = os.path.join(ROOT, "folders")
BLOB = os.path.join(ROOT, "_media_blobs")
LOG_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

TIMEOUT = 120
WORKERS = 8


def url_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def collect_missing():
    """Return list of (url, ext, kind, job_set_id, folder) for references lacking a non-empty blob."""
    missing = []
    seen_path = set()
    for mp in glob.glob(os.path.join(FOLDERS, "**", "media_manifest.json"), recursive=True):
        folder = os.path.relpath(os.path.dirname(mp), FOLDERS)
        try:
            m = json.load(open(mp, encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(m, list):
            continue
        for r in m:
            k = r.get("kind")
            u = r.get("url") or ""
            if not u:
                continue
            ext = r.get("ext") or ""
            key = url_key(u)
            p = os.path.join(BLOB, key[:2], key + ext)
            if os.path.exists(p) and os.path.getsize(p) > 0:
                continue
            if p in seen_path:
                continue
            seen_path.add(p)
            missing.append({"url": u, "ext": ext, "kind": k,
                            "job_set_id": r.get("job_set_id"),
                            "folder": folder, "path": p})
    return missing


def fetch(rec):
    u, p = rec["url"], rec["path"]
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".part-" + str(os.getpid())
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(tmp, "wb") as f:
            sh = hashlib.sha256()
            while True:
                c = r.read(65536)
                if not c:
                    break
                sh.update(c)
                f.write(c)
        # verify content-address matches url_key (defensive; url_key is sha256(url) not bytes;
        # we keep filename as sha256(url) to stay consistent with the downloader)
        os.replace(tmp, p)
        return {"ok": True, "url": u, "size": os.path.getsize(p)}
    except Exception as e:
        if os.path.exists(tmp):
            try: os.remove(tmp)
            except OSError: pass
        return {"ok": False, "url": u, "why": f"{type(e).__name__}: {e}"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="仅处理前 N 条（调试）")
    ap.add_argument("--workers", type=int, default=WORKERS)
    a = ap.parse_args()

    missing = collect_missing()
    if a.limit:
        missing = missing[: a.limit]
    print(f"[scan] missing blobs to fetch: {len(missing)}")
    from collections import Counter
    print("[scan] by kind:", dict(Counter(x["kind"] for x in missing)))
    print("[scan] by folder(top6):", dict(Counter(x["folder"] for x in missing).most_common(6)))

    if a.dry_run or not missing:
        if not missing:
            print("[done] 已无缺失 blob（覆盖完整）")
        return

    ok = fail = 0
    ledger = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        for res in ex.map(fetch, missing):
            if res["ok"]:
                ok += 1
            else:
                fail += 1
                ledger.append(res)
            if (ok + fail) % 50 == 0:
                print(f"  ...progress ok={ok} fail={fail}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    report = os.path.join(LOG_DIR, f"series_missing_fetch_{stamp}.json")
    with open(report, "w", encoding="utf-8") as f:
        json.dump({"requested": len(missing), "ok": ok, "fail": fail,
                   "failures": ledger}, f, ensure_ascii=False, indent=1)
    print(f"[done] ok={ok} fail={fail}")
    print(f"[report] {report}")
    if fail:
        print("  失败项见 report；可重跑续传（增量跳过已成功者）")


if __name__ == "__main__":
    main()
