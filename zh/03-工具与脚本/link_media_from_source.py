#!/usr/bin/env python3
"""将仓根（原文镜像）Assets 映射到 zh/content 对应路径（硬链接优先，禁止重新下载）。

单目录双语布局后：
  SOURCE = higgsfield-hell-grind-opensource/   （本脚本的上两级）
  DEST   = zh/content/                        （与原文相对路径镜像）

用法（在 opensource 仓根或任意 cwd）：
  python3 zh/03-工具与脚本/link_media_from_source.py
  python3 zh/03-工具与脚本/link_media_from_source.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # .../zh
SOURCE = HERE.parent  # .../higgsfield-hell-grind-opensource
DEST_ROOT = HERE / "content"
MANIFEST_OUT = HERE / "07-对照索引" / "media_link_manifest.jsonl"
ASSET_PARTS = ("Assets",)


def link_or_copy(src: Path, dst: Path, dry: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return "exists"
    if dry:
        return "dry-run"
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        try:
            os.symlink(src.resolve(), dst)
            return "symlink"
        except OSError:
            shutil.copy2(src, dst)
            return "copy"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--source", type=Path, default=SOURCE)
    args = ap.parse_args()
    src_root: Path = args.source
    if not src_root.is_dir():
        print(f"源仓不存在: {src_root}", file=sys.stderr)
        return 2

    assets_dirs = list((src_root / "folders").rglob("Assets")) if (src_root / "folders").is_dir() else []
    if not assets_dirs:
        print("未找到源仓 folders/**/Assets，可能尚未下载完或路径未就绪")
        return 1

    MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    stats = {"hardlink": 0, "symlink": 0, "copy": 0, "exists": 0, "dry-run": 0, "missing": 0}
    t0 = time.time()
    with MANIFEST_OUT.open("w", encoding="utf-8") as mf:
        for assets in assets_dirs:
            for f in assets.rglob("*"):
                if not f.is_file():
                    continue
                rel = f.relative_to(src_root)
                dst = DEST_ROOT / rel
                if not f.exists() or f.stat().st_size <= 0:
                    stats["missing"] += 1
                    mf.write(
                        json.dumps(
                            {
                                "source_path": str(rel),
                                "zh_path": str(dst.relative_to(HERE)),
                                "link_type": "missing_source",
                                "status": "missing_source",
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    continue
                kind = link_or_copy(f, dst, args.dry_run)
                stats[kind] = stats.get(kind, 0) + 1
                n += 1
                mf.write(
                    json.dumps(
                        {
                            "source_path": str(rel),
                            "zh_path": str(Path("content") / rel),
                            "link_type": kind,
                            "status": "ok" if kind not in ("missing_source",) else kind,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                if n % 2000 == 0:
                    print(f"  linked {n} … {stats}", flush=True)

    print(f"done files={n} stats={stats} elapsed={time.time()-t0:.1f}s")
    print(f"manifest: {MANIFEST_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
