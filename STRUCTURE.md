# 源数据结构说明（folders / 媒体）

配合 [`START_HERE.md`](./START_HERE.md)。本文只描述**官网镜像应有的形状**，避免路径错配。

---

## 官方标识

| 项 | 值 |
|----|-----|
| 项目页 | https://higgsfield.ai/@higgsfield.studio/projects/hell-grind |
| API | `https://fnf.higgsfield.ai` |
| Snapshot folder | `3caa2f3a-52b5-4293-9237-0c8f76c7158a` |
| 规模（元数据） | ≈162 文件夹节点；38,482 job_sets；≈115,449 jobs |

---

## 场次树（`folders/`）

```text
folders/
  Hell Grind/                          # 项目根（官方 name）
    folder.json                        # id + name（权威）
    children.json / job_sets.json …
    Scene 26/                          # 场次（官方 name，可重复语义）
      folder.json
      children.json
      job_sets.json                    # 该场全部生成批次
      media_manifest.json
      summary.json / prompt_index.json …
      prompts/
        00001_<job_set_id>.txt         # 源 prompt 正文
        00001_<job_set_id>.json        # 旁路元数据导出
        00001_<job_set_id>.zh.md       # 汉化对照（并排，可选阶段）
        …
      Assets/
        outputs/<job_id>/              # 该 job 生成结果
          output.mp4 | *.png …
          thumbnail.webp               # 有时与 outputs 同级策略并存
        thumbnails/                    # 缩略图汇总
        references/                    # 提示词参考素材
```

### 路径语义

| 路径 | 含义 | 勿与…混淆 |
|------|------|-----------|
| `Assets/outputs/<job_id>/` | **该次生成**的成片/成图 | Brief 配图、成片 film |
| `Assets/thumbnails/` | 结果缩略图 | references |
| `Assets/references/` | 提示词参考图/素材 | outputs |
| `brief/images/` | 项目页 Brief 插图 | 单镜头 outputs |
| `film/` | 整片参考 | 单镜头 outputs |
| `_media_blobs/` | 去重存储后端 | 浏览入口（请走 Assets） |

---

## 命名规则

1. **显示名** = `folder.json.name`（与官网一致）。  
2. **禁止** `Name (2)`、`Name__hash` 作为正式展示名。  
3. 同级物理重名时：目录名 = 官方 `folder_id`（UUID），`name` 仍写在 JSON。  
4. 完整对照：`meta/id_path_mapping.json` + `meta/id_path_mapping_index.json`。

---

## 媒体落盘与硬链

- 下载脚本写入 `_media_blobs/<sha256前2位>/<sha256><ext>`。  
- `Assets/` 内文件优先 **hardlink** 到 blob（省空间、内容同一 inode）。  
- 校验：`scripts/validate_source_download.py`、`scripts/validate_source_structure.py`。

### 媒体进度（摘要）

见 `meta/media_download_progress.json`（完成后 done≈total；error 为失败 URL 数）。

---

## 旁路目录（非官网结构）

| 路径 | 用途 |
|------|------|
| `meta/` | 映射、进度、校验报告、成本分析 |
| `scripts/` | 本地工具（见 `scripts/README.md`） |
| `logs/` | 运行日志 |
| `zh/` | 汉化治理；**译文主落点是源旁 `.zh.md`** |
| `skills/` | 官方 skill 文件占位 |

这些目录**可以**存在且应被说明；它们**不是** FNF 网站上的文件夹镜像。

---

## 已清理的误导项

| 项 | 处理 |
|----|------|
| 根目录空 `assets/`、`prompts/` | 已删除（真数据在 `folders/**`） |
| `zh/content` 下大量空目录脚手架 | 已清空（并排 `.zh.md` 才是主策略） |
| `scripts/__pycache__` | 已删除 |

---

## 并排双语（提醒）

```text
…/prompts/00002_<job_set_id>.txt
…/prompts/00002_<job_set_id>.zh.md    ← 同目录，不另建中文树
```

规范：`zh/00-治理/并排双语落盘规范.md`。
