# 样本试点 —— 初译草稿（未过评审闸门）

> 源仓就绪后，在此目录放**少量**试点译文。本文件记录**已产出、仍为 draft** 的试点样本。
> **通过标准尚未满足**：需双角色校对（译/校分离）+ 零 S0/S1 + 术语表无新增冲突 + 对照索引可打开，才会写 `PILOT_PASS.md`。
> 状态：`draft`（2026-08-12，与 NAS rsync 并行推进时产出）。

---

## 试点集（3 类，已产出草稿）

| # | 类别 | 源文件 | 对照文件 | job_type / 主题 |
|---|------|--------|----------|-----------------|
| 1 | 视频 prompt（最长） | `folders/Hell Grind/1. COLD OPEN/Cold_open_B/prompts/00023_badbd6b7-85e7-4310-9a00-831127631f43.txt` | `…/00023_badbd6b7-….zh.md` | `seedance_2_0`，冷开场东角色顶点变身 + 坠落 + 熄灭 |
| 2 | 图像 prompt | `folders/Hell Grind/Regenerations/Extra Regen 3/prompts/00012_5a618805-9b8a-4c52-8050-c8b31f8e4f0a.txt` | `…/00012_5a618805-….zh.md` | `gpt_image_2`，35mm 胶片静帧 + 掩体内景点改 |
| 3 | Brief 节选 | `brief/PROJECT_BRIEF.md`（L48–130, L298–340） | `brief/PROJECT_BRIEF.zh.md` | 资产原则 + 技术底座（Style Prefix / GEO） |

> 按 `05-样本试点/README.md` 建议试点集，补齐了 3 类：资产原则+技术底座、最短 seedance、图像 prompt。

---

## 评审闸门（待做）

- [ ] 双角色校对（译 / 校分离，分离角色）
- [ ] 零 S0/S1 缺陷
- [ ] 术语表无新增冲突（新增待入库词见各文件「备注」）
- [ ] 对照索引可打开（`zh/07-对照索引/` + `media_link_manifest.jsonl`）
- [ ] 通过后写 `PILOT_PASS.md`（含日期与 source_ref）

## 新增待入库术语（各 draft 文件「备注」中列出的候选）

- `descriptor → 描述符`
- `character sheet → 角色表 / 角色三视图资产`
- `headless (front full-body) → 无头（正面全身）`
- `point change → 点改 / 局部修改`
- `catch-light → 眼神光 / catch-light`
- `stress test → 压力测试`
- `Style Prefix → Style 前缀（技术底座）`
- `contre-jour → 逆光背光`
- `anamorphic lens → 变形宽银幕镜头`
- `halation → 光晕 / 辉散`
- `negative instructions → 反面指令`
- `24fps / 8K / NON-IP / SFX only / NO CGI` → 技术标签保留原文，仅释义

> 以上候选**批准后方入** `zh/01-术语表/受控词表.md`；批准前正文已随用。

---

## 对照索引

- 与 `zh/07-对照索引/media_link_manifest.jsonl`：`brief/PROJECT_BRIEF.zh.md` 与两支 prompt 的 `.zh.md` 应登记（尚未登记，随试点评审一并做）。

---

## 变更记录

| 日期 | 记要 |
|------|------|
| 2026-08-12 | 产出 3 类试点初译草稿（draft），待双角色校对与评审闸门 |
