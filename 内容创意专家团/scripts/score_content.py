#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容创意评分脚本：对文案/脚本变体按多维度打分并排序。
用法: python score_content.py <变体清单.md>
输入文件格式（宽松解析）：用 '### ' 或 '## ' 分隔的每个变体块。
评分维度: 钩子强度/结构完整/利益具体/情绪共鸣/CTA明确/平台匹配（各0-20，总分100）。
说明：本脚本用关键词与结构特征做启发式打分，作为"可执行的初筛";
最终判断仍应结合人工与真实投放数据。
"""
import re
import sys
from pathlib import Path

HOOK_WORDS = ["其实", "别再", "为什么", "居然", "秘密", "真相", "难怪", "原来", "99%", "免费", "仅限", "才知道", "千万别", "震惊", "后悔", "血赚", "踩坑", "避坑"]
CTA_WORDS = ["点击", "关注", "评论", "私信", "领取", "下单", "购买", "链接", "立即", "马上", "现在", "转发", "收藏"]
NUM_RE = re.compile(r"\d")
QUESTION_RE = re.compile(r"[?？]")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")

DIM_MAX = 20
PASS_SCORE = 80


def split_variants(text):
    parts = re.split(r"\n#{1,3}\s+", text)
    variants = [p.strip() for p in parts if p.strip()]
    # 若没有标题分隔，按空行大块切
    if len(variants) <= 1:
        variants = [p.strip() for p in re.split(r"\n\s*\n\s*\n", text) if p.strip()]
    return variants or [text.strip()]


def score_variant(v):
    first = v.splitlines()[0] if v.splitlines() else v
    hook_hits = sum(1 for w in HOOK_WORDS if w in first) + (1 if QUESTION_RE.search(first) else 0)
    hook = min(DIM_MAX, 8 + hook_hits * 4)

    has_structure = all(k in v for k in ["钩子"]) or ("CTA" in v) or ("行动" in v)
    structure = 16 if ("钩子" in v and ("CTA" in v or "行动" in v)) else (12 if has_structure else 8)

    benefit = 8 + (6 if NUM_RE.search(v) else 0) + (6 if any(w in v for w in ["省", "赚", "提升", "翻倍", "免费", "结果"]) else 0)
    benefit = min(DIM_MAX, benefit)

    emotion = 8 + (4 if EMOJI_RE.search(v) else 0) + (4 if any(w in v for w in ["你", "我们", "宝妈", "程序员", "打工人", "学生"]) else 0) + (4 if any(w in v for w in ["焦虑", "惊喜", "心疼", "爽", "扎心"]) else 0)
    emotion = min(DIM_MAX, emotion)

    cta_hits = sum(1 for w in CTA_WORDS if w in v)
    cta = min(DIM_MAX, 6 + cta_hits * 5)

    platform = 14 if any(p in v for p in ["抖音", "小红书", "公众号", "视频号", "B站", "快手"]) else 10

    total = hook + structure + benefit + emotion + cta + platform
    return {
        "钩子强度": hook, "结构完整": structure, "利益具体": benefit,
        "情绪共鸣": emotion, "CTA明确": cta, "平台匹配": platform, "总分": total,
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python score_content.py <变体清单.md>"); sys.exit(1)
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"找不到文件: {path}"); sys.exit(1)
    variants = split_variants(path.read_text(encoding="utf-8"))
    print(f"# 内容评分表（共 {len(variants)} 个变体，达标线 {PASS_SCORE}）\n")
    rows = []
    for i, v in enumerate(variants, 1):
        s = score_variant(v)
        rows.append((i, s, v))
    rows.sort(key=lambda r: r[1]["总分"], reverse=True)
    for rank, (i, s, v) in enumerate(rows, 1):
        verdict = "✅ 达标" if s["总分"] >= PASS_SCORE else "🔁 打回"
        weakest = min((k for k in s if k != "总分"), key=lambda k: s[k])
        title = v.splitlines()[0][:40]
        print(f"## 第{rank}名（变体{i}）总分 {s['总分']} {verdict}")
        print(f"- 摘要: {title}")
        print(f"- 钩子{s['钩子强度']} 结构{s['结构完整']} 利益{s['利益具体']} 情绪{s['情绪共鸣']} CTA{s['CTA明确']} 平台{s['平台匹配']}")
        if s["总分"] < PASS_SCORE:
            print(f"- 建议: 优先强化「{weakest}」维度后重写")
        print()
    passed = sum(1 for _, s, _ in rows if s["总分"] >= PASS_SCORE)
    print(f"---\n达标 {passed}/{len(rows)} 个（达标线 {PASS_SCORE}）")


if __name__ == "__main__":
    main()
