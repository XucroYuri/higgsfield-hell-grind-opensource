#!/bin/bash
# 清理磁盘后恢复被 disk_guard SIGSTOP 的下载
ROOT="/Volumes/SSD/Code/Share/Hell Grind/higgsfield-hell-grind-opensource"
PIDFILE="$ROOT/logs/media_and_rename.pid"
main=$(cat "$PIDFILE" 2>/dev/null || true)
if [ -z "$main" ] || ! ps -p "$main" >/dev/null 2>&1; then
  echo "原 pipeline 已不在，请重新启动 media 续传："
  echo "  cd \"$ROOT\" && export HG_MEDIA_WORKERS=32"
  echo "  nohup bash -c 'python3 -u scripts/download_media_and_fix_names.py media && python3 -u scripts/download_media_and_fix_names.py rename && echo ALL DONE' >> logs/media_and_rename.log 2>&1 &"
  echo "  echo \$! > logs/media_and_rename.pid"
  exit 1
fi
for p in "$main" $(pgrep -P "$main" 2>/dev/null); do
  kill -CONT "$p" 2>/dev/null && echo "SIGCONT $p"
done
echo "resumed $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$ROOT/logs/disk_guard_state.txt"
df -h /Volumes/SSD | tail -1
ps -p "$main" -o pid,state,etime,command
