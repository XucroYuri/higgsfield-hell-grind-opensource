#!/bin/bash
# 监视 /Volumes/SSD 剩余空间；临近耗尽时 SIGSTOP 下载进程，腾出空间后可 SIGCONT 续传
ROOT="/Volumes/SSD/Code/Share/Hell Grind/higgsfield-hell-grind-opensource"
MOUNT="/Volumes/SSD"
WARN_GB=30
PAUSE_GB=15
STATE="$ROOT/logs/disk_guard_state.txt"
LOG="$ROOT/logs/disk_guard.log"
PIDFILE="$ROOT/logs/media_and_rename.pid"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

free_gb() {
  # macOS df: Avail column
  df -g "$MOUNT" 2>/dev/null | awk 'NR==2 {print $4}'
}

get_pids() {
  local main
  main=$(cat "$PIDFILE" 2>/dev/null || true)
  if [ -n "$main" ] && ps -p "$main" >/dev/null 2>&1; then
    echo "$main"
    pgrep -P "$main" 2>/dev/null || true
  else
    # fallback: find python media downloader
    pgrep -f "download_media_and_fix_names.py media" 2>/dev/null || true
  fi
}

pause_all() {
  local p
  for p in $(get_pids); do
    if ps -p "$p" >/dev/null 2>&1; then
      kill -STOP "$p" 2>/dev/null && log "SIGSTOP pid=$p" || log "STOP failed pid=$p"
    fi
  done
  echo "paused $(date -u +%Y-%m-%dT%H:%M:%SZ) free_gb=$(free_gb)" > "$STATE"
  log "PAUSED free_gb=$(free_gb) threshold=${PAUSE_GB}G"
}

# 若已暂停且空间恢复，不自动恢复（避免用户清理中途又写满）；仅记录
while true; do
  FREE=$(free_gb)
  FREE=${FREE:-0}
  # integer compare
  if [ "$FREE" -le "$PAUSE_GB" ] 2>/dev/null; then
    # check if already stopped
    ANY_RUN=0
    for p in $(get_pids); do
      st=$(ps -o state= -p "$p" 2>/dev/null | tr -d ' ')
      # T = stopped
      if [ -n "$st" ] && [ "$st" != "T" ]; then ANY_RUN=1; fi
    done
    if [ "$ANY_RUN" = "1" ]; then
      log "LOW_SPACE free_gb=${FREE}G <= ${PAUSE_GB}G — pausing download"
      pause_all
      echo "PAUSED free_gb=${FREE}"
    else
      log "still paused free_gb=${FREE}G"
    fi
  elif [ "$FREE" -le "$WARN_GB" ] 2>/dev/null; then
    log "WARN free_gb=${FREE}G <= ${WARN_GB}G (pause at ${PAUSE_GB}G)"
  else
    log "ok free_gb=${FREE}G"
  fi
  sleep 60
done
