#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台物料规格查询：给定平台与物料类型，输出推荐尺寸/比例/时长/格式。
用法:
  python platform_spec.py                # 列出全部
  python platform_spec.py 抖音 视频      # 查某平台某物料
  python platform_spec.py 小红书 图文
"""
import sys

SPECS = {
    "抖音": {"视频": "1080×1920, 9:16, 15-60s, MP4(H.264)", "封面": "1080×1920, 9:16", "图文": "1080×1440, 3:4"},
    "视频号": {"视频": "1080×1920, 9:16, MP4", "封面": "1080×1920, 9:16"},
    "快手": {"视频": "1080×1920, 9:16, MP4", "封面": "1080×1920, 9:16"},
    "B站": {"视频": "1920×1080, 16:9, MP4", "封面": "1920×1080, 16:9"},
    "小红书": {"图文": "1080×1440, 3:4", "方图": "1080×1080, 1:1", "视频": "1080×1920, 9:16, ≤5min, MP4", "封面": "1080×1440, 3:4"},
    "公众号": {"头条封面": "900×383, 2.35:1", "次条封面": "200×200, 1:1"},
    "朋友圈": {"海报": "1080×1920, 9:16"},
}
ALIASES = {"douyin": "抖音", "xhs": "小红书", "red": "小红书", "bilibili": "B站", "wechat": "公众号"}


def norm(p):
    return ALIASES.get(p.lower(), p)


def main():
    args = sys.argv[1:]
    if not args:
        print("# 平台规格库\n")
        for plat, mats in SPECS.items():
            print(f"## {plat}")
            for m, s in mats.items():
                print(f"- {m}: {s}")
            print()
        return
    plat = norm(args[0])
    if plat not in SPECS:
        print(f"未知平台: {args[0]}。可选: {', '.join(SPECS.keys())}"); sys.exit(1)
    mats = SPECS[plat]
    if len(args) == 1:
        print(f"# {plat} 全部物料规格")
        for m, s in mats.items():
            print(f"- {m}: {s}")
        return
    mat = args[1]
    hit = {k: v for k, v in mats.items() if mat in k or k in mat}
    if not hit:
        print(f"{plat} 下未找到物料「{mat}」。可选: {', '.join(mats.keys())}"); sys.exit(1)
    print(f"# {plat} · {mat}")
    for k, v in hit.items():
        print(f"- {k}: {v}")


if __name__ == "__main__":
    main()
