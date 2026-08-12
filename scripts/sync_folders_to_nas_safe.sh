#!/bin/bash
# Safe folders-only sync: SSD → NAS  (ADDITIVE strategy)
#
# Replaces the old first-pass "rename-aside + rebuild" design.
# Why: the old design renamed the NAS folders/ dest aside and background-deleted
# it every run, then re-copied the whole ~78k metadata tree over SMB from scratch.
# That threw away already-synced NAS work, forced a multi-hour re-copy each run,
# and could spawn leaking cleanup processes. This file is additive by default:
# rsync --partial only transfers what changed; nothing is deleted.
#
# Guarantees (unchanged from before):
#   - Runs AFTER rename (official folder names only on SSD); refuses pre-rename.
#   - Excludes any directory named Assets at any depth (hardlinks to _media_blobs;
#     SMB would expand them → 2×). Canonical media stays in _media_blobs/.
#   - Never touches/deletes SSD.
#   - NAS dest is only pruned when NAS_FOLDERS_RESET=1 is set (first-time / bad state).
#
# What is synced under each scene folder:
#   folder.json, job_sets.json, media_manifest.json, other metadata.
# What is excluded:
#   any directory named Assets.
#
set -euo pipefail

SRC_ROOT="${SRC_ROOT:-/Volumes/SSD/Code/Share/Hell Grind}"
DST_ROOT="${DST_ROOT:-/Volumes/ai/项目/Hell Grind}"
OS="$SRC_ROOT/higgsfield-hell-grind-opensource"
OD="$DST_ROOT/higgsfield-hell-grind-opensource"
SRC_FOLDERS="$OS/folders"
DST_FOLDERS="$OD/folders"
LOG_DIR="${LOG_DIR:-$OS/logs}"
STAMP=$(date +%Y%m%d-%H%M%S)
LOG="$LOG_DIR/nas_folders_safe_${STAMP}.log"
PIDFILE="$LOG_DIR/nas_folders_safe.pid"
mkdir -p "$LOG_DIR"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$LOG"; }

echo $$ >"$PIDFILE"
log "=== safe folders sync (additive) start ==="
log "POLICY: never delete SSD; NAS folders additive unless NAS_FOLDERS_RESET=1"
log "SRC=$SRC_FOLDERS"
log "DST=$DST_FOLDERS"

if [[ ! -d /Volumes/ai ]]; then
  log "ERROR: /Volumes/ai not mounted"
  exit 1
fi
if [[ ! -d "$SRC_FOLDERS" ]]; then
  log "ERROR: SRC folders missing"
  exit 1
fi

# --- Preflight: SSD must be post-rename ---
if [[ -d "$SRC_FOLDERS/Hell Grind__3caa2f3a" ]]; then
  log "ERROR: SSD still has Hell Grind__3caa2f3a — rename not finished; refuse sync"
  exit 3
fi
if [[ ! -d "$SRC_FOLDERS/Hell Grind" ]]; then
  log "ERROR: expected post-rename path folders/Hell Grind missing"
  exit 3
fi
# Lightweight preflight (never walk into Assets contents). Avoid `find|head` under pipefail.
HASH_LEFT=$(find "$SRC_FOLDERS" -maxdepth 3 \( -type d -name Assets -prune \) -o -type d -name '*__[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]' -print 2>/dev/null | wc -l | tr -d ' ' || true)
log "preflight: hash-suffix dirs depth<=3 count=${HASH_LEFT:-0} (UUID official_folder_id dirs may remain)"

# --- Optional one-time reset of a partial/unsafe NAS dest (never SSD) ---
# Default additive: leave existing dest in place. Only when the caller opts in
# (first migration from the old rubble, or a known-bad tree) do we prune NAS.
if [[ "${NAS_FOLDERS_RESET:-0}" == "1" ]]; then
  log "NAS_FOLDERS_RESET=1: pruning NAS folders dest ONLY (SSD untouched)"
  if [[ -d "$DST_FOLDERS" ]]; then
    # Move aside then delete in background; avoids rm of huge tree blocking the pass.
    TRASH="${DST_FOLDERS}.reset-${STAMP}"
    mv "$DST_FOLDERS" "$TRASH" 2>>"$LOG" && \
      (sleep 2; rm -rf "$TRASH" >>"$LOG" 2>&1 && log "OK removed NAS reset trash $TRASH" || log "WARN reset trash remains $TRASH") &
  fi
  mkdir -p "$DST_FOLDERS"
else
  log "NAS_FOLDERS_RESET=0: additive rsync into existing dest (no prune)"
  mkdir -p "$DST_FOLDERS"
fi

# --- rsync: additive, correct excludes relative to folders/ root ---
# Patterns without a slash match the final path component → excludes Assets at any depth.
# --partial keeps partial uploads; no --delete unless caller opts into NAS_FOLDERS_DELETE.
# Build rsync flags; safe with bash 3.2 (macOS) — plain array.
RSYNCFLAGS=( -a --partial --timeout=300
  --exclude '.DS_Store'
  --exclude 'Assets'
  --exclude 'Assets/'
  --filter='- Assets/'
  --filter='- Assets' )
if [[ "${NAS_FOLDERS_DELETE:-0}" == "1" ]]; then
  log "NAS_FOLDERS_DELETE=1: will prune NAS folders files gone on SSD (NAS-only)"
  RSYNCFLAGS+=( --delete )
else
  log "NAS_FOLDERS_DELETE=0: additive only (no delete on NAS folders)"
fi

log "rsync folders (exclude Assets at any depth)..."
set +e
rsync "${RSYNCFLAGS[@]}" "$SRC_FOLDERS/" "$DST_FOLDERS/" >>"$LOG" 2>&1
EC=$?
set -e
if [[ "$EC" -ne 0 ]]; then
  log "FAIL rsync exit=$EC — see $LOG"
  exit "$EC"
fi
log "OK rsync folders exit=0"

# --- Verify: no Assets on NAS (protects even in additive mode) ---
log "verify: scanning NAS for leaked Assets..."
LEAK_N=$(find "$DST_FOLDERS" -type d -name Assets 2>/dev/null | wc -l | tr -d ' ')
if [[ "$LEAK_N" != "0" ]]; then
  log "FAIL verify: NAS still has $LEAK_N Assets dirs — exclude broken"
  find "$DST_FOLDERS" -type d -name Assets 2>/dev/null | head -20 | tee -a "$LOG"
  exit 4
fi
log "OK verify: zero Assets directories on NAS folders"

# Large media under folders would mean exclude failed or wrong copy
BIG_N=$(find "$DST_FOLDERS" -type f \( -name '*.mp4' -o -name '*.png' -o -name '*.webp' -o -name '*.jpeg' \) 2>/dev/null | wc -l | tr -d ' ')
if [[ "$BIG_N" != "0" ]]; then
  log "FAIL verify: found $BIG_N media files under NAS folders (Assets leak)"
  find "$DST_FOLDERS" -type f \( -name '*.mp4' -o -name '*.png' -o -name '*.webp' \) 2>/dev/null | head -15 | tee -a "$LOG"
  exit 4
fi
log "OK verify: zero media extensions under NAS folders"

# Spot-check root metadata
if [[ -f "$SRC_FOLDERS/Hell Grind/folder.json" ]]; then
  if [[ -f "$DST_FOLDERS/Hell Grind/folder.json" ]]; then
    log "OK present Hell Grind/folder.json"
  else
    log "FAIL missing on NAS: Hell Grind/folder.json"
    exit 5
  fi
fi

# job_sets.json counts — prune Assets on SSD side for speed
log "verify: counting job_sets.json (SSD prunes Assets)..."
SRC_JS=$(find "$SRC_FOLDERS" \( -type d -name Assets -prune \) -o -name job_sets.json -print 2>/dev/null | wc -l | tr -d ' ')
DST_JS=$(find "$DST_FOLDERS" -name job_sets.json 2>/dev/null | wc -l | tr -d ' ')
log "job_sets.json count SSD=$SRC_JS NAS=$DST_JS"
if [[ "$SRC_JS" -gt 0 && "$DST_JS" -lt "$SRC_JS" ]]; then
  log "FAIL job_sets count NAS < SSD"
  exit 6
fi
if [[ "$SRC_JS" -gt 0 && "$DST_JS" -eq "$SRC_JS" ]]; then
  log "OK job_sets counts match"
fi

df -h /Volumes/ai /Volumes/SSD | tee -a "$LOG"
log "DONE safe folders sync (additive) log=$LOG"
log "SSD source untouched throughout"
echo "$LOG"
