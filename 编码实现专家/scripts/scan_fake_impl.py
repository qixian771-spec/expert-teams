#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
假实现扫描器：检测"看着像做完、其实没做完"的代码。
用法: python scan_fake_impl.py [目标目录]   (默认当前目录)
检测类别:
  1. 待办/占位      TODO/FIXME/XXX/HACK/placeholder/NotImplemented
  2. 硬编码假返回    return null/true/false/{}/[]/"mock"/"test"/"placeholder"
  3. 空实现          py 的 `pass` / js 的空函数体
  4. 假测试          .skip(/xit(/xdescribe(/@skip/assert true
退出码: 发现"硬编码假返回/空实现/假测试"任一 → 1(FAIL)；仅待办类 → 0 但提示。
"""
import os
import re
import sys
from pathlib import Path

EXTS = {".js", ".ts", ".tsx", ".jsx", ".py", ".go", ".java", ".rb", ".php", ".vue", ".mjs", ".cjs"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "__pycache__", ".venv", "venv", "target", "out"}

PATTERNS = {
    "待办/占位": re.compile(r"TODO|FIXME|XXX|HACK|placeholder|NotImplemented|not implemented", re.I),
    "硬编码假返回": re.compile(r"return\s+(null|None|true|false|\{\}|\[\]|\"mock[^\"]*\"|\"test[^\"]*\"|\"placeholder[^\"]*\")\s*;?\s*$", re.I),
    "空实现": re.compile(r"^\s*(pass|\{\s*\})\s*$"),
    "假测试": re.compile(r"\.skip\(|xit\(|xdescribe\(|@skip|@pytest\.mark\.skip|assert\s+true\b|assertTrue\(true\)|expect\(true\)", re.I),
}
CRITICAL = {"硬编码假返回", "空实现", "假测试"}


def scan_file(path):
    findings = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return findings
    for ln, line in enumerate(lines, 1):
        for cat, pat in PATTERNS.items():
            if pat.search(line):
                findings.append((cat, ln, line.strip()[:100]))
    return findings


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.exists():
        print(f"目录不存在: {root}"); sys.exit(2)
    all_findings = []
    files = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix in EXTS:
                files += 1
                p = Path(dirpath) / fn
                for cat, ln, txt in scan_file(p):
                    all_findings.append((str(p.relative_to(root)), cat, ln, txt))

    print(f"# 假实现扫描报告  目录: {root}  扫描文件: {files}\n")
    if not all_findings:
        print("✅ 未发现假实现迹象。")
        sys.exit(0)
    # 按类别汇总
    by_cat = {}
    for f, cat, ln, txt in all_findings:
        by_cat.setdefault(cat, []).append((f, ln, txt))
    for cat, items in by_cat.items():
        flag = "🔴" if cat in CRITICAL else "🟡"
        print(f"## {flag} {cat}（{len(items)} 处）")
        for f, ln, txt in items[:20]:
            print(f"- {f}:{ln}  {txt}")
        if len(items) > 20:
            print(f"  ... 还有 {len(items)-20} 处")
        print()
    critical = sum(len(v) for k, v in by_cat.items() if k in CRITICAL)
    print("---")
    print(f"合计 {len(all_findings)} 处，其中严重(假返回/空实现/假测试) {critical} 处")
    if critical > 0:
        print("判定: 🔴 FAIL —— 存在假实现，打回修复后复扫。")
        sys.exit(1)
    print("判定: 🟡 仅有待办/占位注释，建议清理；无严重假实现。")
    sys.exit(0)


if __name__ == "__main__":
    main()
