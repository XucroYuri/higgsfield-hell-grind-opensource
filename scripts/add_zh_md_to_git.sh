#!/bin/bash
# add_zh_md_to_git.sh — 将 folders/ 下源旁 .zh.md 汉化对照显式加入 Git 索引。
#
# 背景：opensource 仓 .gitignore 忽略整棵 folders/（媒体/元数据不进 Git），而
# 源旁 .zh.md 汉化必须进 Git。由于父目录被忽略，Git 无法用「! 再入」规则深入到
# folders/ 深层；可靠做法是在提交时按显式路径 `git add -f` 强加（而不是 -A 全树，
# 那会把整棵 folders/ 元数据也拉进来）。
#
# 用法： cd higgsfield-hell-grind-opensource && bash scripts/add_zh_md_to_git.sh
# 安全：只 add 匹配 folders/**/*.zh.md 的文件，绝不触碰其它内容；幂等。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# macOS bash 3.2 无 mapfile，用 while-read 收集
ZHS=()
while IFS= read -r f; do
  ZHS+=("$f")
done < <(find "folders" -type f -name '*.zh.md' 2>/dev/null || true)
if [[ ${#ZHS[@]} -eq 0 ]]; then
  echo "no folders/**/*.zh.md found (nothing to add)"
  exit 0
fi
echo "tracking ${#ZHS[@]} folders/**/*.zh.md files:"
for f in "${ZHS[@]}"; do
  git add -f -- "$f"
  echo "  + $f"
done
# 复核：列入 stage 且未被忽略
STAGED=$(git diff --cached --name-only 2>/dev/null | grep -E '\.zh\.md$' | wc -l | tr -d ' ')
echo "staged zh.md count: ${STAGED}"
echo "done"
