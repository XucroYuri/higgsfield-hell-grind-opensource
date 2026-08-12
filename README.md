# Hell Grind 官方开源镜像

**先读 → [`START_HERE.md`](./START_HERE.md)**（目录地图与路径约定）。

本目录是 Higgsfield 公开制作档案的**本地镜像**（独立 Git 仓库）。  
铁律：**忠实源头**；禁止以「整理/纠正」改写官方语义内容。

- 官方项目：https://higgsfield.ai/@higgsfield.studio/projects/hell-grind  
- API：`https://fnf.higgsfield.ai`  
- 工作区总则：`../AGENTS.md`

---

## 顶层一览

| 路径 | 角色 | 说明 |
|------|------|------|
| **`folders/`** | ★ 源 | 场次树：job_sets、prompts、Assets |
| **`brief/`** | ★ 源 | 项目 Brief 与页面配图 |
| **`film/`** | ★ 源 | 成片参考 |
| **`_media_blobs/`** | ★ 源 | 媒体去重库（大体量；经 Assets 硬链使用） |
| **`meta/`** | ◐ 旁路 | 映射、下载进度、校验与分析报告 |
| **`scripts/`** | ◐ 旁路 | 下载/校验/同步/分析脚本 |
| **`logs/`** | ◐ 旁路 | 运行日志 |
| **`skills/`** | ◐ 旁路 | 官方 skill 占位（文件尚未取得） |
| **`zh/`** | ◐ 旁路 | 汉化**治理**（术语/流程）；译文主落点见下 |

★ = 官网镜像数据 · ◐ = 本地工具与说明（不是官方网站上的「另一套内容」）

---

## 命名铁律（源数据）

- 官方文件夹 **显示名**（`folder.json` → `name`）必须与开源项目一致。  
- 同名场次是源头迭代痕迹，**禁止** `Scene 26 (2)` 等自创消歧。  
- **禁止**终态保留 `Name__hash` 作正式名。  
- 仅当文件系统同级不能重名时：物理目录用官方 **UUID**，显示名仍在元数据里。  

细则：`STRUCTURE.md`、`meta/id_path_mapping.json`。

---

## 并排双语（汉化）

- **源结构不变**；在源文件旁增加 `*.zh.md`。  
- 例：`folders/.../prompts/00002_<id>.txt` + `00002_<id>.zh.md`。  
- 规范：`zh/00-治理/并排双语落盘规范.md`。  
- `zh/` **不是**第二套场次目录树。

---

## 允许 vs 禁止

| 允许 | 禁止 |
|------|------|
| 旁路 `meta/`、`scripts/`、`logs/`、并排 `.zh.md` | 改写官方 prompt / 参数冒充原文 |
| 非法字符最小替换；冲突时用官方 UUID 物理键 | 自创消歧名 / 哈希污染原名 |
| `_media_blobs` 去重 + Assets 硬链 | 删除 generation「打扫」或覆盖 Assets 冒充官方 |
| 校验与成本分析报告 | 把下载失败文件伪装成成功交付 |

---

## 常用入口

| 需求 | 打开 |
|------|------|
| 快速理解项目 | [`START_HERE.md`](./START_HERE.md) |
| 场次/媒体布局 | [`STRUCTURE.md`](./STRUCTURE.md) |
| 下载是否完整 | `meta/校验说明.md`、`meta/media_download_progress.json` |
| 成本与生成量 | `meta/Hell-Grind-AIGC成本与采纳分析报告.md` |
| 脚本说明 | [`scripts/README.md`](./scripts/README.md) |
| meta 文件索引 | [`meta/README.md`](./meta/README.md) |
