# 对照索引

全量启动后在此维护：

| 文件 | 说明 |
|------|------|
| `source_ref.yaml` | 源仓 commit / mapping 哈希 / 时间 |
| `alignment.jsonl` | 每条：source_path, zh_path, status, glossary_ver |
| `release-notes-zh.md` | 各 zh_release 说明 |

## alignment 行示例

```json
{
  "source_path": "brief/PROJECT_BRIEF.md",
  "zh_path": "content/brief/PROJECT_BRIEF.zh.md",
  "kind": "brief",
  "status": "approved",
  "source_sha256": "…",
  "zh_release": "v0.1.0"
}
```
