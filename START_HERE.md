# 从这里开始 · Hell Grind 官方开源镜像

> 给**人类**与 **Agent** 的 3 分钟导览。  
> 本目录 = Higgsfield 公开电影项目 **Hell Grind** 的本地档案馆 + 本地工具旁路。

---

## 30 秒理解

| 问题 | 答案 |
|------|------|
| 这是什么？ | 从 [官方项目页](https://higgsfield.ai/@higgsfield.studio/projects/hell-grind) / API 拉下来的**完整制作档案镜像** |
| 什么不能动？ | `folders/`、`brief/`、`film/` 里的**官方语义**（名称、prompt 原文、job 参数、生成媒体） |
| 媒体在哪？ | 真文件在 `_media_blobs/`；场次下 `Assets/` 多为硬链接指向 blob |
| 提示词在哪？ | **每个场次** `folders/.../prompts/`（不是仓库根的 `prompts/`——根级空目录已删除） |
| 中文在哪？ | 与源文件**并排**的 `*.zh.md`（规范见 `zh/00-治理/并排双语落盘规范.md`）；`zh/` 只做治理不建第二套 Scene 树 |
| 统计/成本？ | `meta/`（含 AIGC 成本报告） |
| 脚本？ | `scripts/`（下载、校验、NAS 同步、成本分析） |

---

## 目录地图（顶层只应有这些）

```text
higgsfield-hell-grind-opensource/
├── START_HERE.md          ← 你在这里
├── README.md              ← 铁律与摘要
├── STRUCTURE.md           ← 场次/媒体布局细则
├── folders/               ★ 源数据：场次树（官方结构）
├── brief/                 ★ 源数据：项目 Brief
├── film/                  ★ 源数据：成片参考 mp4
├── _media_blobs/          ★ 源数据：去重媒体库（大体量）
├── meta/                  ◐ 旁路：映射、进度、校验、分析报告
├── scripts/               ◐ 旁路：工具脚本
├── logs/                  ◐ 旁路：运行日志（可忽略阅读）
├── skills/                ◐ 旁路：技能文件占位（官方 skill 未取得）
└── zh/                    ◐ 旁路：汉化治理/术语/流程（非场次树）
```

**★ = 源站镜像（位置与内容以官方为准）**  
**◐ = 本地旁路（帮助理解与运维，不是官方交付物本身）**

---

## 源数据路径约定（勿错配）

| 内容 | 正确位置 | 错误位置 |
|------|----------|----------|
| 场次 / job_sets / 分 prompt | `folders/<官方名>/…` | 仓库根 `prompts/`（已移除） |
| 镜头生成结果 | `folders/…/Assets/outputs/<job_id>/` | 根目录 `assets/`（已移除） |
| 缩略图 / 参考图 | `…/Assets/thumbnails/`、`…/Assets/references/` | 与 outputs 混用 |
| Brief 配图 | `brief/images/` | 与场次 Assets 混淆 |
| 成片 | `film/hell-grind.mp4`（或同目录说明） | 与单镜头 outputs 混淆 |
| 二进制去重库 | `_media_blobs/<hash前2位>/<hash>.ext` | 直接当浏览入口（请走 Assets 硬链） |
| 汉化对照 | **同目录** `foo.txt` + `foo.zh.md` | 仅 `zh/content/…` 而无源旁文件 |

官方显示名以 `folder.json` 的 `name` 为准；物理路径见 `meta/id_path_mapping.json`。

---

## 推荐阅读顺序

1. **本文** `START_HERE.md`  
2. `README.md` — 命名铁律、允许/禁止  
3. `STRUCTURE.md` — folders 内部长什么样  
4. `meta/校验说明.md` — 如何确认下载完整  
5. `meta/Hell-Grind-AIGC成本与采纳分析报告.md` — 成本与生成量（可选）  
6. `zh/00-治理/并排双语落盘规范.md` — 要做汉化时  

Agent 另读：工作区根 `../AGENTS.md`、`../MEMORY.md`。

---

## 状态快照（镜像阶段）

| 项 | 状态 |
|----|------|
| 元数据 / job_sets / prompts 文本 | 已下载 |
| 媒体全量 | 已完成（约 925GB；少量 URL 失败见 progress） |
| 官方命名恢复 (rename) | 已完成 |
| ID↔路径映射 | `meta/id_path_mapping.json` |
| 技能三件套 CINEDANCE/ACTING/LIRA | **已手动补齐**（`skills/*.md`） |
| Brief 配图 | **14 张**（手动补齐，见 `brief/images/`） |
| 并排 `.zh.md` 全量 | **未做**（规范已就绪） |

---

## 不要做的事

- 不要把 `_media_blobs` 或 `logs` 当成「项目叙事入口」  
- 不要改官方 `name` / 覆盖 `params.prompt` / 替换 `Assets` 冒充官方  
- 不要再建根级空的 `assets/`、`prompts/` 占位目录  
- 不要把 `zh/` 建成第二套 `folders` 树来替代源旁 `.zh.md`  
