# Pipeline Status

## Completed
1. **Metadata + prompts** — 162 folders, 38,482 job_sets, 38,422 prompts, ~115,449 jobs
2. **media_manifest.json rebuild** — outputs / thumbnails / references separated
3. **Media download pipeline started** (background)
4. **Feature film ffmpeg download started** (background)

## In progress
- Download unique media URLs (~226,078) into:
  - `Assets/outputs/<job_id>/` — shot generation media
  - `Assets/thumbnails/` — result thumbnails  
  - `Assets/references/` — prompt reference materials
- Dedup blob store: `_media_blobs/`
- After media: strip erroneous `Name__hash` download suffixes; restore official `name`
- Same-name siblings: physical path uses official `folder_id` only (never invent `Name (2)`)
- Mapping: `meta/id_path_mapping.json` (`official_name` vs `storage_path`)

## Logs
- `logs/media_and_rename.log`
- `logs/film_download.log`
- `meta/media_download_progress.json`

## Resume
```bash
export HG_MEDIA_WORKERS=32
python3 scripts/download_media_and_fix_names.py media
python3 scripts/download_media_and_fix_names.py rename
```
