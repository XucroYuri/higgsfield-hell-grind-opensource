# scripts/ — 本地工具（旁路，非官网内容）

在仓库根目录执行：`cd higgsfield-hell-grind-opensource`。

## 镜像与校验

| 脚本 | 用途 |
|------|------|
| `download_opensource.py` | 元数据 / 提示词等结构下载 |
| `download_media_and_fix_names.py` | 媒体下载 + 官方命名恢复 |
| `validate_source_download.py` | 下载完整性校验 |
| `validate_source_structure.py` | 目录/映射结构校验 |

## 运维

| 脚本 | 用途 |
|------|------|
| `disk_guard.sh` | SSD 空间不足时 SIGSTOP 下载 |
| `resume_download_after_cleanup.sh` | 清理后 SIGCONT 续传 |

## NAS 同步（SSD 源不删）

| 脚本 | 用途 |
|------|------|
| `sync_folders_to_nas_safe.sh` | folders 元数据安全同步（排除 Assets） |
| `sync_hell_grind_ssd_to_nas.sh` | 全量 SSD→NAS 同步入口 |
| `migrate_hell_grind_to_nas.sh` | 兼容包装 → sync 脚本 |

## 分析

| 脚本 | 用途 |
|------|------|
| `analyze_aigc_cost_and_adoption.py` | 成本与生成/采纳分析 → `meta/` |

## 汉化相关

| 位置 | 用途 |
|------|------|
| `../zh/03-工具与脚本/link_media_from_source.py` | 可选：Assets 硬链到 `zh/content`（**不能替代**源旁 `.zh.md`） |

日志默认写在 `../logs/`。  
**不要**把脚本输出写进 `folders/**/Assets` 覆盖官方文件。
