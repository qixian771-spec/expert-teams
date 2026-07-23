#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
入口漂移检测：对比"代码里实际存在的路由/入口"与"ENTRY.md 登记的入口"。
用法: python check_entry.py [代码目录] [--entry ENTRY.md]
  默认代码目录=当前目录, ENTRY.md=当前目录下 ENTRY.md
检出两类问题:
  A. 未登记入口   代码里有路由, 但 ENTRY.md 没登记  → 入口漂移(易跑错)
  B. 疑似废弃     ENTRY.md 登记了, 但代码里找不到    → 可能是死入口
支持常见路由写法: express/koa, react-router, vue-router, flask, fastapi, next(pages)。
"""
import os
import re
import sys
from pathlib import Path

EXTS = {".js", ".ts", ".tsx", ".jsx", ".py", ".go", ".java", ".vue"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", ".venv", "venv", "target"}

ROUTE_PATTERNS = [
    re.compile(r"(?:app|router|route)\.(?:get|post|put|delete|patch|use)\(\s*['\"]([^'\"]+)['\"]"),  # express
    re.compile(r"path\s*[:=]\s*['\"]([^'\"]+)['\"]"),  # react/vue router
    re.compile(r"<Route\s+[^>]*path=['\"]([^'\"]+)['\"]"),  # react-router jsx
    re.compile(r"@(?:app|router)\.(?:get|post|put|delete|patch|route)\(\s*['\"]([^'\"]+)['\"]"),  # flask/fastapi
]
ENTRY_PATH_RE = re.compile(r"(/[\w\-/:.{}\[\]]+)")


def collect_code_routes(root):
    routes = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix not in EXTS:
                continue
            p = Path(dirpath) / fn
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in ROUTE_PATTERNS:
                for m in pat.finditer(text):
                    r = m.group(1)
                    if r.startswith("/"):
                        routes.add(r)
    return routes


def collect_entry_paths(entry_file):
    if not entry_file.exists():
        return None
    text = entry_file.read_text(encoding="utf-8", errors="ignore")
    return set(ENTRY_PATH_RE.findall(text))


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    entry_arg = None
    if "--entry" in sys.argv:
        i = sys.argv.index("--entry")
        entry_arg = sys.argv[i + 1]
    entry_file = Path(entry_arg) if entry_arg else root / "ENTRY.md"

    code_routes = collect_code_routes(root)
    entry_paths = collect_entry_paths(entry_file)

    print(f"# 入口漂移检测报告  代码目录: {root}")
    print(f"ENTRY.md: {entry_file}\n")

    if entry_paths is None:
        print("🔴 未找到 ENTRY.md —— 没有入口真相源，必然漂移。请先建立入口登记表。")
        if code_routes:
            print(f"\n代码中检测到 {len(code_routes)} 个路由（均未登记）:")
            for r in sorted(code_routes):
                print(f"- {r}")
        sys.exit(1)

    unregistered = sorted(r for r in code_routes if not any(r.startswith(e) or e.startswith(r) for e in entry_paths))
    stale = sorted(e for e in entry_paths if e not in code_routes and len(e) > 1)

    print(f"代码中路由: {len(code_routes)} 个 | ENTRY.md 登记: {len(entry_paths)} 个\n")
    if unregistered:
        print(f"## 🔴 未登记入口（{len(unregistered)}，会跑错/漂移）")
        for r in unregistered:
            print(f"- {r}")
        print()
    if stale:
        print(f"## 🟡 疑似废弃入口（{len(stale)}，登记了但代码里没有）")
        for e in stale:
            print(f"- {e}")
        print()
    if not unregistered and not stale:
        print("✅ 入口一致：代码路由均已登记，无漂移。")
        sys.exit(0)
    print("判定: 🔴 存在入口漂移/废弃，请先对齐 ENTRY.md 再继续。")
    sys.exit(1 if unregistered else 0)


if __name__ == "__main__":
    main()
