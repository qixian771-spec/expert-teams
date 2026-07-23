#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RICE 优先级评分：把"拍脑袋排优先级"变成可复算的排序。
用法:
  python rice_score.py features.md
输入（Markdown 表格或 CSV，含表头）:
  | 功能 | Reach | Impact | Confidence% | Effort |
  功能=名称, Reach=触达人数/周期, Impact=影响(3巨大/2高/1中/0.5低),
  Confidence=信心(0-100), Effort=投入(人月或人日, 统一即可)
RICE = Reach × Impact × (Confidence/100) / Effort
输出: 按 RICE 降序 + 分层(P0/P1/P2)。
"""
import csv
import re
import sys
from pathlib import Path

IMPACT_MAP = {"巨大": 3.0, "高": 2.0, "中": 1.0, "低": 0.5, "massive": 3.0, "high": 2.0, "medium": 1.0, "low": 0.5}


def parse_impact(v):
    v = str(v).strip()
    try:
        return float(v)
    except ValueError:
        return IMPACT_MAP.get(v.lower(), IMPACT_MAP.get(v, 1.0))


def parse_rows(text):
    rows = []
    if "|" in text:  # markdown table
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.strip("|").split("|")]
                rows.append(cells)
    else:  # csv
        rows = [r for r in csv.reader(text.splitlines()) if r]
    # 去表头与分隔行
    rows = [r for r in rows if r and not re.match(r"^[-:\s|]+$", "".join(r)) and r[0] not in ("功能", "feature", "Feature", "名称")]
    return rows


def main():
    if len(sys.argv) < 2:
        print("用法: python rice_score.py <features.md|csv>"); sys.exit(1)
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    rows = parse_rows(text)
    if not rows:
        print("未解析到功能行，检查格式（功能|Reach|Impact|Confidence|Effort）"); sys.exit(1)
    results = []
    for r in rows:
        if len(r) < 5:
            continue
        name, reach, impact, conf, effort = r[0], r[1], r[2], r[3], r[4]
        try:
            reach = float(re.sub(r"[^\d.]", "", str(reach)) or 0)
            conf = float(re.sub(r"[^\d.]", "", str(conf)) or 100)
            effort = float(re.sub(r"[^\d.]", "", str(effort)) or 1)
        except ValueError:
            continue
        impact = parse_impact(impact)
        if effort <= 0:
            effort = 1
        rice = reach * impact * (conf / 100.0) / effort
        results.append((name, reach, impact, conf, effort, rice))
    if not results:
        print("没有有效数据行"); sys.exit(1)
    results.sort(key=lambda x: x[5], reverse=True)
    max_rice = results[0][5] or 1
    print(f"# RICE 优先级评分（共 {len(results)} 项，按分数降序）\n")
    print("| 排名 | 功能 | Reach | Impact | Conf% | Effort | RICE | 分层 |")
    print("|---|---|---|---|---|---|---|---|")
    for i, (name, reach, impact, conf, effort, rice) in enumerate(results, 1):
        ratio = rice / max_rice
        tier = "P0" if ratio >= 0.66 else ("P1" if ratio >= 0.33 else "P2")
        print(f"| {i} | {name} | {reach:g} | {impact:g} | {conf:g} | {effort:g} | {rice:.1f} | {tier} |")
    print("\n说明: P0=优先做, P1=其次, P2=可缓。RICE=Reach×Impact×Confidence/Effort。")


if __name__ == "__main__":
    main()
