#!/usr/bin/env python3
"""结构校验：folder.json 与目录、job_sets 与 prompts 粗对齐、映射表一致性（若存在）。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ROOT / "folders"
META = ROOT / "meta"


def main() -> int:
    issues = []
    folder_jsons = list(FOLDERS.rglob("folder.json"))
    for fj in folder_jsons:
        d = fj.parent
        try:
            meta = json.loads(fj.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(f"folder.json 不可读: {fj.relative_to(ROOT)}: {e}")
            continue
        fid = meta.get("id")
        name = meta.get("name")
        if not fid:
            issues.append(f"缺少 id: {fj.relative_to(ROOT)}")
        # job_sets 与 prompts 目录
        js = d / "job_sets.json"
        if js.exists():
            try:
                data = json.loads(js.read_text(encoding="utf-8"))
                n = len(data.get("job_sets") or [])
            except Exception as e:
                issues.append(f"job_sets 损坏: {js.relative_to(ROOT)}: {e}")
                n = -1
            prompts = d / "prompts"
            if n > 0 and not prompts.is_dir():
                issues.append(f"有 job_sets 但无 prompts/: {d.relative_to(ROOT)}")
        # 非法自创消歧名检测（启发式）
        if " (" in d.name and d.name.endswith(")"):
            issues.append(f"疑似自创消歧目录名: {d.relative_to(ROOT)}")

    mapping_path = META / "id_path_mapping.json"
    mapping_note = "mapping 尚未生成（rename 后应有）"
    if mapping_path.exists():
        mapping_note = "mapping 存在"
        try:
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            for ent in mapping.get("folders") or []:
                sp = ent.get("storage_path")
                if sp and not (ROOT / sp).exists():
                    issues.append(f"mapping 指向不存在路径: {sp}")
                on = ent.get("official_name")
                sk = ent.get("storage_kind")
                if sk == "official_name" and on and sp:
                    # storage 末级应等于净化后的 official 或 id
                    pass
        except Exception as e:
            issues.append(f"mapping 不可读: {e}")

    report = {
        "folder_json_count": len(folder_jsons),
        "issue_count": len(issues),
        "mapping_note": mapping_note,
        "issues_sample": issues[:100],
    }
    out = META / "structure_validation_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2)[:3000])
    print(f"wrote {out}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
