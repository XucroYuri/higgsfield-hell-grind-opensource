#!/bin/bash
# Hell Grind continuous sync: SSD (dev base) → NAS (archive / remote copy)
#
# Policy (do not change without user confirmation):
#   - SRC on SSD is the development base for later stages — NEVER delete/move SRC.
#   - Only rsync SRC → NAS. No rm/rmtree on /Volumes/SSD/Code/Share/Hell Grind.
#   - Default: no --delete on NAS (additive/update). Set NAS_MIRROR_DELETE=1 to
#     prune dest files removed on SSD (still never touches SSD).
#   - folders/**/Assets hardlinks are excluded (SMB would expand → 2× size).
#     Canonical media lives in _media_blobs/; rebuild Assets on SSD when needed.
#   - Safe to re-run anytime (catch-up / resume).
#
# Paths:
#   SRC: /Volumes/SSD/Code/Share/Hell Grind
#   DST: /Volumes/ai/项目/Hell Grind   (smb://192.168.2.12/ai/项目/Hell Grind)
#
set -euo pipefail

SRC_ROOT="${SRC_ROOT:-/Volumes/SSD/Code/Share/Hell Grind}"
DST_ROOT="${DST_ROOT:-/Volumes/ai/项目/Hell Grind}"
LOG_DIR="${LOG_DIR:-$SRC_ROOT/higgsfield-hell-grind-opensource/logs}"
STAMP=$(date +%Y%m%d-%H%M%S)
LOG="$LOG_DIR/nas_sync_${STAMP}.log"
PIDFILE="$LOG_DIR/nas_sync.pid"
mkdir -p "$LOG_DIR" "$DST_ROOT"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

# Refuse any accidental destructive flags on source
if [[ "${1:-}" == "--delete-source" ]] || [[ "${ALLOW_DELETE_SSD:-}" == "1" ]]; then
  log "REFUSED: deleting SSD source is forbidden by policy"
  exit 99
fi

if [[ ! -d /Volumes/ai ]]; then
  log "ERROR: /Volumes/ai not mounted (need smb://192.168.2.12/ai)"
  exit 1
fi
if [[ ! -d "$SRC_ROOT" ]]; then
  log "ERROR: SRC missing $SRC_ROOT"
  exit 1
fi

echo $$ >"$PIDFILE"
log "POLICY: SSD is permanent dev base; sync is one-way SSD→NAS; never delete SRC"
log "SRC=$SRC_ROOT"
log "DST=$DST_ROOT"
df -h /Volumes/ai /Volumes/SSD | tee -a "$LOG"
AVAIL_GI=$(df -g /Volumes/ai | awk 'NR==2{print $4}')
log "NAS avail_Gi=$AVAIL_GI"
if [[ "${AVAIL_GI:-0}" -lt 100 ]]; then
  log "ERROR: NAS free < 100Gi — abort this pass"
  exit 2
fi

# Optional dest-only mirror prune (never affects SSD)
# Build rsync base; avoid empty-array + set -u on macOS bash 3.2 / bash 5
if [[ "${NAS_MIRROR_DELETE:-0}" == "1" ]]; then
  log "NAS_MIRROR_DELETE=1: will prune files on NAS that are gone on SSD"
  RSYNC=(rsync -a --partial --timeout=300 --delete
    --exclude '.DS_Store'
    --exclude '*.part'
    --exclude '__pycache__/')
else
  log "NAS_MIRROR_DELETE=0: additive rsync (no --delete on NAS)"
  RSYNC=(rsync -a --partial --timeout=300
    --exclude '.DS_Store'
    --exclude '*.part'
    --exclude '__pycache__/')
fi

rsync_dir() {
  local label="$1"
  local src="$2"
  local dst="$3"
  shift 3 || true
  if [[ ! -e "$src" ]]; then
    log "SKIP missing $label"
    return 0
  fi
  log "START $label"
  if [[ -d "$src" ]]; then
    mkdir -p "$dst"
    if "${RSYNC[@]}" "$@" "$src/" "$dst/" >>"$LOG" 2>&1; then
      log "OK $label"
      return 0
    fi
    local ec=$?
    log "FAIL $label rsync_exit=$ec (re-run to resume)"
    return "$ec"
  else
    # file: ensure parent exists, never mkdir the file path itself
    mkdir -p "$(dirname "$dst")"
    if cp -X -p "$src" "$dst" 2>>"$LOG" || cp -p "$src" "$dst" 2>>"$LOG"; then
      log "OK $label"
      return 0
    fi
    log "FAIL $label copy"
    return 1
  fi
}

log "=== phase: workspace small trees ==="
rsync_dir "docs" "$SRC_ROOT/docs" "$DST_ROOT/docs" || true
for f in AGENTS.md MEMORY.md README.md .gitignore.workspace; do
  rsync_dir "root/$f" "$SRC_ROOT/$f" "$DST_ROOT/$f" || true
done
rsync_dir "know-how" \
  "$SRC_ROOT/higgsfield-hell-grind-know-how" \
  "$DST_ROOT/higgsfield-hell-grind-know-how" || true
# 汉化层已并入 opensource/zh/，随 opensource 树同步；不再单独同步旧 Chinese 目录

OS="$SRC_ROOT/higgsfield-hell-grind-opensource"
OD="$DST_ROOT/higgsfield-hell-grind-opensource"
mkdir -p "$OD"

log "=== phase: opensource non-blob ==="
for sub in scripts meta brief film logs skills assets prompts README.md .git .gitignore .gitkeep-note.md; do
  rsync_dir "opensource/$sub" "$OS/$sub" "$OD/$sub" || true
done

log "=== phase: opensource/folders via sync_folders_to_nas_safe.sh ==="
# Dedicated safe path: post-rename check, correct Assets exclude, rebuild NAS folders only
FSAFE="$(cd "$(dirname "$0")" && pwd)/sync_folders_to_nas_safe.sh"
if [[ -x "$FSAFE" ]] || [[ -f "$FSAFE" ]]; then
  if bash "$FSAFE" >>"$LOG" 2>&1; then
    log "OK opensource/folders (safe)"
  else
    log "FAIL opensource/folders safe sync — abort before blobs"
    exit 7
  fi
else
  log "ERROR missing $FSAFE"
  exit 7
fi

log "=== phase: opensource/_media_blobs (bulk) ==="
rsync_dir "opensource/_media_blobs" "$OS/_media_blobs" "$OD/_media_blobs" \
  || log "WARN blobs incomplete — re-run later"

log "=== summary ==="
df -h /Volumes/ai /Volumes/SSD | tee -a "$LOG"
log "DONE sync pass stamp=$STAMP log=$LOG"
log "SSD source untouched. Re-run: bash $0"
echo "$LOG"
