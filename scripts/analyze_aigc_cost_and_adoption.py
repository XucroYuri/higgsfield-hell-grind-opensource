#!/usr/bin/env python3
"""Hell Grind AIGC cost mining + generation/adoption analysis.

Reads all folders/**/job_sets.json (prunes Assets), emits:
  - meta/aigc_cost_analysis.json  (machine-readable)
  - meta/aigc_cost_analysis.md   (human report)

Cost model (documented assumptions — platform `cost` is ~99.9% null):
  1) When job_set.cost is present: treat as internal_units; observed law for
     seedance 1080p: cost ≈ 900 * duration_s * n_jobs  → credits ≈ cost/1000
  2) Public rate card (Higgsfield blog Jun 2026, cite in report):
     Seedance 2.0 Standard 720p 8s ≈ 36 credits ≈ $1.55
     → USD/credit ≈ 1.55/36 ≈ 0.04306
     Fast 720p 8s ≈ 28 credits ≈ $1.20
  3) Scale Seedance by duration/8 and resolution multipliers.
  4) Image models: Nano Banana class ≈ 2 cr/gen; Soul cinematic ≈ 3;
     GPT Image / Seedream ≈ 4; unknown image ≈ 2; unknown video ≈ 20.

Adoption proxies (no explicit "used in final cut" field in export):
  A) Variant efficiency: within job_set, n_jobs variants; if final cut picks ~1
     → adoption ≈ 1/n_jobs (batch utilization)
  B) Folder intensity: jobs / job_sets per scene folder
  C) Completion rate: status==completed / all jobs (here nearly 100%)
  D) Platform signals: is_favourite, published_at (mostly empty in this dump)

Never modifies source media.
"""
from __future__ import annotations

import json
import os
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ROOT / "folders"
META = ROOT / "meta"
OUT_JSON = META / "aigc_cost_analysis.json"
OUT_MD = META / "aigc_cost_analysis.md"

# --- Public rate card (Higgsfield, mid-2026; approximate) ---
USD_PER_CREDIT = 1.55 / 36.0  # from Seedance 720p 8s standard quote
SEEDANCE_STD_720P_8S_CREDITS = 36.0
SEEDANCE_FAST_720P_8S_CREDITS = 28.0

# Resolution multipliers vs 720p baseline (engineering estimate)
RES_MULT = {
    "480p": 0.7,
    "720p": 1.0,
    "1080p": 1.5,
    "4k": 2.5,
    "4K": 2.5,
}

# Flat credit estimates per completed job when not Seedance-duration-based
FLAT_CREDITS_BY_TYPE = {
    "nano_banana_2": 2.0,
    "nano_banana_flash": 1.0,
    "nano_banana_pro": 2.0,
    "soul_cinematic": 3.0,
    "text2image_soul_v2": 2.0,
    "soul_cinema_studio": 3.0,
    "cinematic_studio_image": 3.0,
    "cinematic_studio_soul_cast": 3.0,
    "imagegen_2_0": 3.0,
    "image_auto": 2.0,
    "gpt_image_2": 4.0,
    "seedream_v4_5": 4.0,
    "seedream_v5_lite": 3.0,
    "cinematic_studio_video_3_5": 40.0,  # video-ish fallback
    "cinematic_studio_3_0": 40.0,
    "qwen_camera_control": 2.0,
}


def res_mult(resolution: str | None) -> float:
    if not resolution:
        return 1.0
    return RES_MULT.get(str(resolution), 1.2)


def estimate_seedance_credits(params: dict, n_jobs: int, mode: str | None = None) -> float:
    """Credits for whole job_set (all jobs)."""
    duration = float(params.get("duration") or 8)
    resolution = str(params.get("resolution") or "720p")
    mode = str(mode or params.get("mode") or "std").lower()
    base_8s = SEEDANCE_FAST_720P_8S_CREDITS if mode in ("fast", "mini") else SEEDANCE_STD_720P_8S_CREDITS
    per_job = base_8s * (duration / 8.0) * res_mult(resolution)
    return per_job * max(n_jobs, 1)


def estimate_job_set_credits(js_type: str, params: dict, n_jobs: int) -> tuple[float, str]:
    t = js_type or "unknown"
    p = params or {}
    if t.startswith("seedance") or str(p.get("model", "")).startswith("seedance"):
        return estimate_seedance_credits(p, n_jobs, p.get("mode")), "ratecard_seedance"
    flat = FLAT_CREDITS_BY_TYPE.get(t)
    if flat is not None:
        return flat * max(n_jobs, 1), "ratecard_flat"
    # heuristic
    if "video" in t or "cinematic_studio_video" in t:
        return 30.0 * max(n_jobs, 1), "heuristic_video"
    return 2.0 * max(n_jobs, 1), "heuristic_image"


def platform_cost_to_credits(cost) -> float | None:
    """Map sparse platform cost field → credits. Empirical: cost/1000 ≈ credits for job_set."""
    if cost is None:
        return None
    try:
        return float(cost) / 1000.0
    except (TypeError, ValueError):
        return None


def walk_job_sets():
    for dirpath, dirnames, filenames in os.walk(FOLDERS):
        dirnames[:] = [d for d in dirnames if d != "Assets"]
        if "job_sets.json" not in filenames:
            continue
        path = Path(dirpath) / "job_sets.json"
        try:
            rel = str(Path(dirpath).relative_to(FOLDERS / "Hell Grind"))
        except ValueError:
            try:
                rel = str(Path(dirpath).relative_to(FOLDERS))
            except ValueError:
                rel = dirpath
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        jss = data.get("job_sets") if isinstance(data, dict) else data
        if not isinstance(jss, list):
            continue
        yield rel, path, jss


def main() -> None:
    t0 = time.time()
    types = Counter()
    statuses = Counter()
    jobs_per_js = Counter()
    duration_hist = Counter()
    resolution_by_type = defaultdict(Counter)
    mode_by_type = defaultdict(Counter)

    by_type = defaultdict(lambda: {
        "job_sets": 0,
        "jobs": 0,
        "est_credits": 0.0,
        "est_usd": 0.0,
        "platform_credits_sum": 0.0,
        "platform_cost_samples": 0,
        "total_duration_s": 0.0,  # sum duration * n_jobs for video
    })

    folder_stats = defaultdict(lambda: {
        "job_sets": 0,
        "jobs": 0,
        "est_credits": 0.0,
        "est_usd": 0.0,
        "types": Counter(),
        "jobs_per_js": [],
    })

    js_total = 0
    job_total = 0
    fav = 0
    published = 0
    platform_cost_null = 0
    platform_cost_present = 0

    # For adoption: distribution of n_jobs
    adoption_if_pick_one = []  # 1/n_jobs per job_set

    for rel, path, jss in walk_job_sets():
        for js in jss:
            if not isinstance(js, dict):
                continue
            js_total += 1
            t = js.get("type") or "unknown"
            types[t] += 1
            params = js.get("params") if isinstance(js.get("params"), dict) else {}
            jobs = [j for j in (js.get("jobs") or []) if isinstance(j, dict)]
            n_jobs = len(jobs)
            job_total += n_jobs
            jobs_per_js[n_jobs] += 1
            if n_jobs > 0:
                adoption_if_pick_one.append(1.0 / n_jobs)

            pc = platform_cost_to_credits(js.get("cost"))
            if pc is None:
                platform_cost_null += 1
            else:
                platform_cost_present += 1

            est_cr, method = estimate_job_set_credits(t, params, n_jobs)
            # Prefer platform cost when present for that job_set
            if pc is not None:
                use_cr = pc
                method = "platform_cost_field"
                by_type[t]["platform_credits_sum"] += pc
                by_type[t]["platform_cost_samples"] += 1
            else:
                use_cr = est_cr

            use_usd = use_cr * USD_PER_CREDIT

            by_type[t]["job_sets"] += 1
            by_type[t]["jobs"] += n_jobs
            by_type[t]["est_credits"] += use_cr
            by_type[t]["est_usd"] += use_usd

            dur = params.get("duration")
            if dur is not None:
                try:
                    d = float(dur)
                    duration_hist[int(d)] += 1
                    by_type[t]["total_duration_s"] += d * max(n_jobs, 1)
                except (TypeError, ValueError):
                    pass
            if params.get("resolution"):
                resolution_by_type[t][str(params.get("resolution"))] += 1
            if params.get("mode"):
                mode_by_type[t][str(params.get("mode"))] += 1

            fs = folder_stats[rel]
            fs["job_sets"] += 1
            fs["jobs"] += n_jobs
            fs["est_credits"] += use_cr
            fs["est_usd"] += use_usd
            fs["types"][t] += 1
            fs["jobs_per_js"].append(n_jobs)

            for job in jobs:
                st = (job.get("status") or "unknown").lower()
                statuses[st] += 1
                if job.get("is_favourite"):
                    fav += 1
                if job.get("published_at"):
                    published += 1

    # Folder adoption metrics
    folder_rows = []
    for rel, fs in folder_stats.items():
        jp = fs["jobs_per_js"]
        mean_jp = statistics.mean(jp) if jp else 0
        # if pick 1 variant per job_set
        adopt = statistics.mean(1 / n for n in jp if n) if jp else 0
        folder_rows.append({
            "folder": rel,
            "job_sets": fs["job_sets"],
            "jobs": fs["jobs"],
            "mean_jobs_per_job_set": round(mean_jp, 3),
            "variant_adoption_if_pick_one": round(adopt, 4),
            "est_credits": round(fs["est_credits"], 1),
            "est_usd": round(fs["est_usd"], 2),
            "top_types": fs["types"].most_common(5),
        })
    folder_rows.sort(key=lambda r: -r["jobs"])

    total_credits = sum(v["est_credits"] for v in by_type.values())
    total_usd = sum(v["est_usd"] for v in by_type.values())

    mean_jobs_per_js = (job_total / js_total) if js_total else 0
    mean_adopt = statistics.mean(adoption_if_pick_one) if adoption_if_pick_one else 0
    median_adopt = statistics.median(adoption_if_pick_one) if adoption_if_pick_one else 0

    # Scene-level folders (exclude pure UUID regenerations depth heuristics)
    scene_folders = [r for r in folder_rows if r["folder"].startswith("Scene") or r["folder"] == "."]
    if not scene_folders:
        scene_folders = folder_rows

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 2),
        "scope": {
            "folders_scanned_with_job_sets": len(folder_stats),
            "job_sets": js_total,
            "jobs": job_total,
            "claimed_generations_meta": 115451,
        },
        "cost_assumptions": {
            "usd_per_credit": USD_PER_CREDIT,
            "seedance_std_720p_8s_credits": SEEDANCE_STD_720P_8S_CREDITS,
            "seedance_fast_720p_8s_credits": SEEDANCE_FAST_720P_8S_CREDITS,
            "resolution_multipliers": RES_MULT,
            "flat_credits_by_type": FLAT_CREDITS_BY_TYPE,
            "platform_cost_field": "When present, cost/1000 treated as credits (empirical fit: 900*duration*n_jobs for 1080p seedance).",
            "sources": [
                "https://higgsfield.ai/blog/seedance-2-0-pricing-2026",
                "https://higgsfield.ai/pricing",
                "local job_sets.json cost/type/params/jobs",
            ],
            "caveats": [
                "99%+ of job_set.cost fields are null — totals are ESTIMATES",
                "No official 'accepted into final film' flag; adoption uses proxies",
                "Enterprise / unlimited plan pricing may differ substantially",
                "Audio/reference extras not fully priced",
            ],
        },
        "platform_cost_field_coverage": {
            "present": platform_cost_present,
            "null": platform_cost_null,
            "coverage_pct": round(100 * platform_cost_present / js_total, 3) if js_total else 0,
        },
        "totals": {
            "est_credits": round(total_credits, 1),
            "est_usd": round(total_usd, 2),
            "est_usd_low_minus_30pct": round(total_usd * 0.7, 2),
            "est_usd_high_plus_50pct": round(total_usd * 1.5, 2),
            "mean_jobs_per_job_set": round(mean_jobs_per_js, 3),
            "variant_adoption_if_pick_one_mean": round(mean_adopt, 4),
            "variant_adoption_if_pick_one_median": round(median_adopt, 4),
            "implied_selected_if_one_per_job_set": js_total,
            "implied_discarded_variants": job_total - js_total,
            "favourite_jobs": fav,
            "published_jobs": published,
        },
        "statuses": dict(statuses.most_common()),
        "jobs_per_job_set_distribution": {str(k): v for k, v in sorted(jobs_per_js.items())},
        "by_type": {
            t: {
                "job_sets": v["job_sets"],
                "jobs": v["jobs"],
                "share_jobs_pct": round(100 * v["jobs"] / job_total, 2) if job_total else 0,
                "est_credits": round(v["est_credits"], 1),
                "est_usd": round(v["est_usd"], 2),
                "share_usd_pct": round(100 * v["est_usd"] / total_usd, 2) if total_usd else 0,
                "total_duration_job_seconds": round(v["total_duration_s"], 1),
                "platform_cost_samples": v["platform_cost_samples"],
            }
            for t, v in sorted(by_type.items(), key=lambda x: -x[1]["est_usd"])
        },
        "seedance_params": {
            "resolution": dict(resolution_by_type.get("seedance_2_0", Counter()).most_common()),
            "mode": dict(mode_by_type.get("seedance_2_0", Counter()).most_common()),
            "duration_hist": {str(k): duration_hist[k] for k in sorted(duration_hist)},
        },
        "top_folders_by_jobs": folder_rows[:40],
        "folder_adoption_summary": {
            "mean_jobs_per_job_set_across_folders": round(
                statistics.mean(r["mean_jobs_per_job_set"] for r in folder_rows), 3
            ) if folder_rows else 0,
            "median_jobs_per_job_set_across_folders": round(
                statistics.median(r["mean_jobs_per_job_set"] for r in folder_rows), 3
            ) if folder_rows else 0,
            "mean_variant_adoption_if_pick_one": round(
                statistics.mean(r["variant_adoption_if_pick_one"] for r in folder_rows), 4
            ) if folder_rows else 0,
        },
    }

    META.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Markdown report
    lines = []
    a = lines.append
    a("# Hell Grind AIGC 成本与采纳分析\n")
    a(f"> 生成时间（UTC）：`{report['generated_at']}`  \n")
    a(f"> 数据源：`folders/**/job_sets.json`（跳过 Assets）  \n")
    a(f"> 明细 JSON：`meta/aigc_cost_analysis.json`\n")

    a("## 1. 结论摘要\n")
    a("| 指标 | 数值 |")
    a("|------|------|")
    a(f"| job_set 数（调用/批次） | **{js_total:,}** |")
    a(f"| job 数（生成条数） | **{job_total:,}** |")
    a(f"| 平均每 job_set 生成条数 | **{mean_jobs_per_js:.2f}** |")
    a(f"| 若每批次只采纳 1 条 → 平均采纳率 | **{mean_adopt*100:.1f}%**（中位 {median_adopt*100:.1f}%） |")
    a(f"| 隐含「选用」条数（= job_sets） | **{js_total:,}** |")
    a(f"| 隐含「落选变体」 | **{job_total - js_total:,}** |")
    a(f"| 估算总 credits | **{total_credits:,.0f}** |")
    a(f"| 估算总 USD（中位假设） | **${total_usd:,.0f}** |")
    a(f"| 估算区间（−30% / +50%） | **${total_usd*0.7:,.0f} – ${total_usd*1.5:,.0f}** |")
    a(f"| 平台 cost 字段覆盖率 | **{report['platform_cost_field_coverage']['coverage_pct']}%**（几乎全空，以价目估算为主） |")
    a("")

    a("## 2. 模型 / 类型分布与成本\n")
    a("| type | job_sets | jobs | jobs占比 | 估 credits | 估 USD | USD占比 |")
    a("|------|----------|------|----------|------------|--------|---------|")
    for t, v in report["by_type"].items():
        a(
            f"| `{t}` | {v['job_sets']:,} | {v['jobs']:,} | {v['share_jobs_pct']}% | "
            f"{v['est_credits']:,.0f} | ${v['est_usd']:,.0f} | {v['share_usd_pct']}% |"
        )
    a("")

    a("### Seedance 2.0 参数画像\n")
    a(f"- resolution: `{report['seedance_params']['resolution']}`\n")
    a(f"- mode: `{report['seedance_params']['mode']}`\n")
    a(f"- duration 直方图（秒 → job_set 数）: `{report['seedance_params']['duration_hist']}`\n")
    a("")

    a("## 3. 生成 / 采纳（镜头级代理指标）\n")
    a("导出数据**没有**「最终成片选用」标记（`is_favourite` / `published_at` 基本为空）。\n")
    a("采用可计算代理：\n")
    a("1. **变体采纳率** = 1 / (该 job_set 的 jobs 数) — 假设每批次最终只用 1 条  \n")
    a("2. **场景迭代强度** = 该文件夹 jobs / job_sets  \n")
    a("3. **完成率** = completed / all（本库 jobs 状态几乎全是 completed）  \n")
    a("")
    a(f"- 全局平均变体采纳率：**{mean_adopt*100:.1f}%** → 平均约 **{mean_jobs_per_js:.2f} 次生成换 1 次采纳**  \n")
    a(f"- jobs/job_set 分布：`{dict(sorted(jobs_per_js.items()))}`  \n")
    a(f"- 最常见：4 变体批次（{jobs_per_js.get(4,0):,} 个 job_set）→ 采纳率 25%  \n")
    a(f"- 单变体批次：{jobs_per_js.get(1,0):,} 个 job_set → 采纳率 100%（无同批落选）  \n")
    a("")
    a("### 按文件夹（场景）Top 20 — 按生成量\n")
    a("| 文件夹 | jobs | job_sets | 均 jobs/批 | 变体采纳率* | 估 USD |")
    a("|--------|------|----------|------------|-------------|--------|")
    for r in folder_rows[:20]:
        a(
            f"| {r['folder'][:60]} | {r['jobs']:,} | {r['job_sets']:,} | "
            f"{r['mean_jobs_per_job_set']:.2f} | {r['variant_adoption_if_pick_one']*100:.1f}% | "
            f"${r['est_usd']:,.0f} |"
        )
    a("\n\\* 变体采纳率 = 若每 job_set 只保留 1 条  \n")

    a("## 4. 成本假设与方法\n")
    a("详见 JSON `cost_assumptions`。要点：\n")
    a(f"- 1 credit ≈ **${USD_PER_CREDIT:.4f}**（由 Seedance 720p/8s/$1.55/36cr 反推）  \n")
    a("- Seedance：按 duration/resolution/mode 相对 8s@720p 线性缩放 × 批内 job 数  \n")
    a("- 图像模型：固定 credits/job 表  \n")
    a("- 稀疏 `job_set.cost`：经验式 `credits ≈ cost/1000`，与 1080p 下 `900*dur*n_jobs` 一致  \n")
    a("")
    a("## 5. 风险与后续可挖\n")
    a("1. 成片时间线（final edit）对齐 → 真·采纳率  \n")
    a("2. 企业价/无限套餐会显著低于本报告  \n")
    a("3. 参考图张数、音频、多镜头 `multi_shots` 可能加价（未全计入）  \n")
    a("4. 与 `media_download_progress` 交叉：下载成功/失败 URL vs job 结果  \n")
    a("")
    a("---\n*脚本：`scripts/analyze_aigc_cost_and_adoption.py`*\n")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"job_sets={js_total} jobs={job_total} est_usd=${total_usd:,.0f} adopt={mean_adopt*100:.1f}%")


if __name__ == "__main__":
    main()
