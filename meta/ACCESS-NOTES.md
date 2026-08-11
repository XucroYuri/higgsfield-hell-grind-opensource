# Access & Coverage Notes

## Official delivery channel

Higgsfield open-sourced Hell Grind **on the Higgsfield platform**, not as a GitHub repository.

- Project: https://higgsfield.ai/@higgsfield.studio/projects/hell-grind
- Public API: `https://fnf.higgsfield.ai`
- No login required for folder metadata + items/prompts

## What we mirrored

| Layer | Method | Status |
|-------|--------|--------|
| Project metadata | SSR + `/folders/{snapshotId}` | Done |
| Folder tree (~108) | `/folders/{id}/children` | Done |
| Job sets + prompts | `/folders/{id}/items` (cursor pagination) | In progress via `scripts/download_opensource.py` |
| Media URL manifests | derived from job results | In progress (URLs only) |
| Full media binaries | CloudFront/CDN raw URLs | **Not bulk-downloaded** (very large) |
| Feature film | HLS URL recorded; optional ffmpeg | Manifest only + thumbnail |
| Project brief | page extract | Done (text + sample images) |
| Skills (CINEDANCE/ACTING/LIRA) | UI chips only | **Not obtained** — see `skills/README.md` |
| GitHub official repo | search | **Not found** |

## Known API quirks

1. `/folders/{id}/jobs` returns `has_more`/`next_cursor` but **cursor does not advance** (always first page). Use `/items` instead.
2. `size=100` is accepted for children/items.
3. Folder `count` is generation-oriented; job_set count is typically lower (multiple results per set possible).
4. `force_show_prompts: false` on folder meta, but prompts still appear in `params.prompt` on public items.

## Third-party references (not official archive)

- https://best.xiaohu.ai/article/higgsfield-hell-grind-opensource/ (method analysis)
- Community skill repos that *document* Hell Grind methods (not the raw archive)
