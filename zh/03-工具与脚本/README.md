# 工具与脚本（`zh/` 汉化层）

在 **opensource 仓根**执行（单目录双语）。

| 脚本 | 职责 |
|------|------|
| `link_media_from_source.py` | 仓根 Assets → `zh/content` 硬链接（禁止二次下载） |
| `build_inventory.py` | 扫描仓根，生成 `06-全量作业/inventory.jsonl`（待实现） |
| `check_source_drift.py` | 源文件哈希 vs 对照索引，标记 stale（待实现） |
| `validate_bilingual_prompt.py` | 检查对照 md 是否含原文块+中文块（待实现） |
| `glossary_lint.py` | 译文是否违反受控词表（待实现） |

仓根侧校验：

```bash
cd ../..  # 或 opensource 根
python3 scripts/validate_source_download.py --strict
python3 scripts/validate_source_structure.py
python3 zh/03-工具与脚本/link_media_from_source.py --dry-run
```

实现原则：

- 只读仓根官方语义区  
- 路径与 `meta/id_path_mapping` 一致  
- 日志写到 `zh/logs/`  

