#!/bin/bash
# Compatibility wrapper → sync_hell_grind_ssd_to_nas.sh
# Policy: SSD remains permanent dev base; one-way SSD→NAS only; never delete SSD.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
exec bash "$DIR/sync_hell_grind_ssd_to_nas.sh" "$@"
