#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务依赖图 + 执行波次生成：把"任务拆解"变成可校验、可排程的图。
用法: python dep_graph.py tasks.md
输入（Markdown 表格或 CSV）:
  | 任务ID | 任务 | 前置依赖 |
  前置依赖=逗号/空格分隔的任务ID，无依赖留空或 -
功能:
  1. 检测循环依赖（有则报错，退出码 1）
  2. 拓扑排序，按依赖分组为"执行波次"（同波次可并行，对齐 GSD wave 执行）
  3. 标出关键路径上的阻塞任务（被依赖最多的）
"""
import re
import sys
from pathlib import Path


def parse(text):
    tasks = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or set(line) <= set("|-: "):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")] if "|" in line else re.split(r"[\t,]", line)
        if len(cells) < 1 or cells[0] in ("任务ID", "id", "ID", "任务"):
            continue
        tid = cells[0]
        deps = []
        if len(cells) >= 3:
            deps = [d for d in re.split(r"[,\s]+", cells[2]) if d and d != "-"]
        tasks[tid] = {"name": cells[1] if len(cells) > 1 else tid, "deps": deps}
    return tasks


def waves(tasks):
    done, result = set(), []
    remaining = dict(tasks)
    guard = 0
    while remaining:
        ready = [t for t, v in remaining.items() if all(d in done for d in v["deps"])]
        if not ready:  # 有循环或缺失依赖
            return result, list(remaining.keys())
        result.append(sorted(ready))
        for t in ready:
            done.add(t)
            del remaining[t]
        guard += 1
        if guard > 1000:
            break
    return result, []


def main():
    if len(sys.argv) < 2:
        print("用法: python dep_graph.py <tasks.md|csv>"); sys.exit(1)
    tasks = parse(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if not tasks:
        print("未解析到任务（格式: 任务ID | 任务 | 前置依赖）"); sys.exit(1)
    # 依赖引用不存在的检查
    missing = {d for v in tasks.values() for d in v["deps"] if d not in tasks}
    if missing:
        print(f"🟡 警告: 有依赖指向不存在的任务: {', '.join(sorted(missing))}\n")
    wv, leftover = waves(tasks)
    print(f"# 任务依赖图 · 执行波次（共 {len(tasks)} 任务）\n")
    for i, wave in enumerate(wv, 1):
        names = "、".join(f"{t}({tasks[t]['name']})" for t in wave)
        print(f"Wave {i}: {names}")
    # 被依赖次数（关键/阻塞任务）
    dep_count = {}
    for v in tasks.values():
        for d in v["deps"]:
            dep_count[d] = dep_count.get(d, 0) + 1
    if dep_count:
        top = sorted(dep_count.items(), key=lambda x: x[1], reverse=True)[:3]
        print("\n关键路径/阻塞任务（被依赖最多）:")
        for t, c in top:
            print(f"- {t}({tasks[t]['name']}): 被 {c} 个任务依赖")
    if leftover:
        print(f"\n🔴 检测到循环依赖或无法推进的任务: {', '.join(leftover)}")
        print("判定: FAIL —— 先解开循环依赖。")
        sys.exit(1)
    print("\n✅ 依赖图无环，可按波次执行。")


if __name__ == "__main__":
    main()
