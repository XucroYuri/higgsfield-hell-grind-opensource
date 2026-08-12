# 汉化工作入口（并排双语）

## 核心要求（请先读）

> **源 prompt / 设计文档旁边必须有汉化版，而不是单独一套中文目录。**  
> 源仓 `folders/` 结构仍按原计划执行。

规范全文：[`00-治理/并排双语落盘规范.md`](./00-治理/并排双语落盘规范.md)

### 示例

```text
folders/Hell Grind/Scene 26/prompts/
  00002_15e958ff-….txt      # 源（勿改）
  00002_15e958ff-….json     # 源元数据
  00002_15e958ff-….zh.md    # 汉化对照（并排新增）

brief/
  PROJECT_BRIEF.md
  PROJECT_BRIEF.zh.md
```

## 本目录（`zh/`）是什么

| 是 | 不是 |
|----|------|
| 治理、术语、流程、质检、工具 | 第二套 Scene 文件夹树 |
| 进度与对照索引 | 唯一放译文的地方 |

译文的**主落点**是源树并排的 `.zh.md`。

## 快速链接

| 文档 | 用途 |
|------|------|
| [AGENTS.md](./AGENTS.md) | Agent 约束 |
| [并排双语落盘规范](./00-治理/并排双语落盘规范.md) | **落盘铁律** |
| [翻译原则](./00-治理/翻译原则.md) | 质量与 prompt 策略 |
| [全量汉化启动清单](./02-流程/全量汉化启动清单.md) | 门禁 |
| [受控词表](./01-术语表/受控词表.md) | 术语 |

## 命令

```bash
cd higgsfield-hell-grind-opensource
# 可选：媒体硬链到 zh/content（不能替代并排 .zh.md）
python3 zh/03-工具与脚本/link_media_from_source.py --dry-run
```
