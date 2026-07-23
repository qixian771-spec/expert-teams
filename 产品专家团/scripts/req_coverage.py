#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
需求-测试追溯覆盖检查：PRD 里每个 REQ-ID 是否都有测试用例覆盖。
用法: python req_coverage.py <需求文件> <测试用例文件> [--min 覆盖率百分比]
需求文件: 含 REQ-001 / REQ-1 / US-1 等编号
测试文件: 用例里引用对应编号
输出: 未覆盖的需求清单 + 覆盖率；覆盖率低于阈值(默认100)退出码 1。
"""
import re
import sys
from pathlib import Path

ID_RE = re.compile(r"\b(?:REQ|US)-?(\d+)\b", re.I)


def ids(text):
    return {"REQ-" + m for m in ID_RE.findall(text)}


def main():
    if len(sys.argv) < 3:
        print("用法: python req_coverage.py <需求文件> <测试用例文件> [--min N]"); sys.exit(1)
    req_file, test_file = Path(sys.argv[1]), Path(sys.argv[2])
    min_cov = 100.0
    if "--min" in sys.argv:
        min_cov = float(sys.argv[sys.argv.index("--min") + 1])
    reqs = ids(req_file.read_text(encoding="utf-8"))
    tests = ids(test_file.read_text(encoding="utf-8"))
    if not reqs:
        print("需求文件里没找到 REQ-/US- 编号"); sys.exit(2)
    covered = reqs & tests
    uncovered = sorted(reqs - tests)
    cov = len(covered) / len(reqs) * 100
    print(f"# 需求-测试覆盖报告")
    print(f"需求总数: {len(reqs)} | 已覆盖: {len(covered)} | 未覆盖: {len(uncovered)} | 覆盖率: {cov:.0f}% (阈值 {min_cov:.0f}%)\n")
    if uncovered:
        print("## 🔴 未覆盖的需求（无对应测试用例）")
        for u in uncovered:
            print(f"- {u}")
        print()
    if cov >= min_cov:
        print("✅ 覆盖达标：所有需求均有测试用例。")
        sys.exit(0)
    print("判定: 🔴 覆盖不足，先补测试用例再验收。")
    sys.exit(1)


if __name__ == "__main__":
    main()
