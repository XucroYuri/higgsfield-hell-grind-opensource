# meta/ — 旁路元数据与报告索引

本目录**不是**官网文件夹镜像，而是本地映射、进度与分析。

## 必读

| 文件 | 说明 |
|------|------|
| [`校验说明.md`](./校验说明.md) | 如何理解校验结果 |
| `id_path_mapping.json` | folder_id ↔ 路径完整映射（大） |
| `id_path_mapping_index.json` | 映射速查索引 |
| `media_download_progress.json` | 媒体下载进度与错误摘要 |
| `totals.json` | 规模计数摘要 |
| `project.json` | 项目级 API 摘要 |

## 校验报告

| 文件 | 说明 |
|------|------|
| `download_validation_report.md` / `.json` | 下载校验 |
| `structure_validation_report.json` | 结构校验 |
| `download-summary.json` | 下载阶段汇总 |
| `folder-inventory.json` | 文件夹清单 |

## 分析与报告

| 文件 | 说明 |
|------|------|
| `Hell-Grind-AIGC成本与采纳分析报告.md` | **成本/采纳中文报告（含人民币）** |
| `aigc_cost_analysis.json` | 成本分析结构化数据 |
| `aigc_cost_analysis.md` | 脚本自动摘要 |

## 其它

| 文件 | 说明 |
|------|------|
| `PIPELINE_STATUS.md` | 流水线状态笔记 |
| `ACCESS-NOTES.md` | 访问/API 备注 |
| `root-*.json` | 根文件夹 API 原始页 |

源媒体与 prompt **不在**本目录；请到 `../folders/`、`../brief/`、`../film/`。
