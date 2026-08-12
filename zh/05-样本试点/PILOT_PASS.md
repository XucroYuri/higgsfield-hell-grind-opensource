# PILOT_PASS — 样本试点通过

> **日期：2026-08-12**
> 评审结果：**通过**（3 类试点初译经双角色校对，零 S0/S1，术语已入 v0.1，对照索引可打开）。
> 依据：`05-样本试点/README.md`「通过标准」逐条核对。

---

## 评审结论

| 通过标准 | 结果 |
|----------|------|
| 双角色校对（译/校分离） | ✅ 覆盖：翻译起草 + 校对复核（对源 `.txt`/`.md` 逐块比对） |
| 零 S0 / S1 | ✅ 无致命/严重缺陷（S0 硬禁令完整；S1 术语/因果/标签均合规） |
| 术语表无新增冲突 | ✅ 新增候选经评审入 v0.1（8 词），其余沿用既有 approved 词 |
| 对照索引可打开 | ✅ `zh/07-对照索引/alignment.jsonl` 三条登记，源 path/zen path/sha256 均可解析 |

---

## 试点集（3 类，均 `reviewed`）

| # | 类别 | source | zh | type / 主题 |
|---|------|--------|-----|-------------|
| 1 | 视频 prompt | `folders/Hell Grind/1. COLD OPEN/Cold_open_B/prompts/00023_badbd6b7-….txt` | `…/00023_badbd6b7-….zh.md` | `seedance_2_0`，冷开场变身/坠落/熄灭 |
| 2 | 图像 prompt | `folders/Hell Grind/Regenerations/Extra Regen 3/prompts/00012_5a618805-….txt` | `…/00012_5a618805-….zh.md` | `gpt_image_2`，35mm 点改 |
| 3 | Brief 节选 | `brief/PROJECT_BRIEF.md`（L48–130, L298–340） | `brief/PROJECT_BRIEF.zh.md` | 资产原则 + 技术底座 |

---

## source_ref（原文钉扎）

- opensource commit：`191e69783d55ecccc46d86c38833c40515ea75dc`
- `id_path_mapping.json` sha256：`ee8d81e4eb526171c7d7c346c9ee4c4c3b74eb4cba4e2b626ab4bc376400d686`
- 状态：`pilot_draft` → **`PILOT_PASS`**（见 `source_ref.yaml`）

---

## 术语冻结 v0.1（试点新增 8 词已在 `zh/01-术语表/受控词表.md`）

`descriptor` `character sheet` `headless full-body` `point change` `catch-light`（沿用既有 approved）+ 新增：`stress test` `Style Prefix` `contre-jour` `anamorphic lens` `halation` `negative instructions` `baseline state` `ultimate / maximum transformation form`

---

## 变更记录

| 日期 | 记要 |
|------|------|
| 2026-08-12 | 3 类试点产出初译 → 校对评审零 S0/S1 → 术语冻 v0.1 → 对照索引登记 → **通过，写入本 PASS** |

## 后续全量汉化启动前提

- 待「镜像媒体 + NAS rsync」完成后，用 `02-流程/全量汉化启动清单.md` 起全量 draft；
- 本条 PASS 作为试点结论，供全量对照复用的词表（v0.1）索引。
