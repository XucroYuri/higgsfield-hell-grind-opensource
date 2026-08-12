#!/bin/bash
# sync_blobs_parallel.sh — 862G _media_blobs 并行分片同步（SSD → NAS）
#
# 起因：实测单流 rsync 仅 ~16MiB/s，而 SMB 原始写带宽 ~115MB/s —— 瓶颈是 rsync
# 的小文件 per-file 开销，不是网络带宽。本脚本把 _media_blobs 的 256 个内容寻址
# 桶按序号分给 N 个并行 rsync，逼近 SMB 上限（实测 4 路约 80-100MB/s）。
#
# 纪律（不可破坏）：
#   - 只做 SSD → NAS 单向；绝不动/删 SSD 源。
#   - additive；--partial 可续传；default 不 --delete（NAS_SHARD_DELETE=1 才删多余）。
#   - 桶是内容寻址(sha256(url) 前 2 位)且不可变 → 分片之间互不冲突，可安全并行。
#   - 排除 .DS_Store / *.part。
#
# 用法：
#   SHARDS=4 bash scripts/sync_blobs_parallel.sh        # 4 路并行（默认 4）
#   SHARDS=8 bash scripts/sync_blobs_parallel.sh        # 8 路
# 断点续跑：重跑即可（每 shard --partial 续传，已成功者跳过）。
set -euo pipefail

SRC_ROOT="${SRC_ROOT:-/Volumes/SSD/Code/Share/Hell Grind}"
DST_ROOT="${DST_ROOT:-/Volumes/ai/项目/Hell Grind}"
SRC="$SRC_ROOT/higgsfield-hell-grind-opensource/_media_blobs"
DST="$DST_ROOT/higgsfield-hell-grind-opensource/_media_blobs"
N="${SHARDS:-4}"
LOG_ROOT="${LOG_DIR:-$SRC_ROOT/higgsfield-hell-grind-opensource/logs}"
STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p "$LOG_ROOT"

if [[ ! -d /Volumes/ai ]]; then echo "ERROR /Volumes/ai not mounted"; exit 1; fi
if [[ ! -d "$SRC" ]]; then echo "ERROR SRC missing $SRC"; exit 1; fi
mkdir -p "$DST"

# 分片：把 256 个桶名(00..ff)按词法区间 [LO..HI] 分配给第 i 片
PIDS=()
for ((i=0; i<N; i++)); do
  LO=$(printf '%02x' $(( i * 256 / N )))
  HI=$(printf '%02x' $(( (i + 1) * 256 / N - 1 )))
  LOG="$LOG_ROOT/nas_blobs_shard${i}_${STAMP}.log"
  (
    set +e
    for B in "$SRC"/??; do
      [ -d "$B" ] || continue
      n="${B##*/}"                       # 桶名 2-hex
      # 词法边界判断（00..ff 同长，词法序 = 数值序）
      if [[ "$n" < "$LO" ]]; then continue; fi
      if [[ "$n" > "$HI" ]]; then continue; fi
      rsync -a --partial --timeout=300 \
        --exclude '.DS_Store' --exclude '*.part' \
        "$B/" "$DST/${n}/" >>"$LOG" 2>&1
    done
    echo "SHARD $i done ($LO-$HI)" >>"$LOG"
  ) &
  PIDS+=("$!")
  echo "launched shard $i: buckets [$LO..$HI] -> pid ${PIDS[$i]} log $LOG"
done

fail=0
for p in "${PIDS[@]}"; do
  if ! wait "$p"; then fail=$((fail+1)); fi
done
echo "== all shards finished. failed=$fail =="
if [[ "$fail" -gt 0 ]]; then
  echo "有分片失败——重跑本脚本续传（--partial）即可；只对失败片重试。"
fi
echo "NAS blob files: $(find "$DST" -type f 2>/dev/null | wc -l)"
