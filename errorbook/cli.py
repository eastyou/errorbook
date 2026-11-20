"""命令行入口：错题 CSV 一键生成可打印、可打卡的错题整理册。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .model import ErrorBookError, filter_by_subject, load_items
from .render import CARDS_PER_PAGE, render_html


def build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="errorbook",
        description="错题整理册：固定五列 CSV 一键生成 A4 纵向复习打卡册",
    )
    parser.add_argument("--version", action="version", version="errorbook 0.1.0")
    parser.add_argument("-i", "--input", required=True, help="错题 CSV（固定五列表头）")
    parser.add_argument("-o", "--output", default="错题整理册.html", help="输出 HTML 路径")
    parser.add_argument("--title", default="错题整理册", help="整理册标题")
    parser.add_argument("--subject", default=None, help="按科目精确筛选，例如：数学")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """运行命令行；成功返回 0，文件错误返回 1，数据错误返回 2。"""
    args = build_parser().parse_args(argv)
    try:
        items = load_items(args.input)
        selected = filter_by_subject(items, args.subject)
        page = render_html(selected, title=args.title)
    except ErrorBookError as exc:
        print("错误: %s" % exc, file=sys.stderr)
        return 2
    except OSError as exc:
        print("错误: 读取 CSV 文件失败: %s" % exc, file=sys.stderr)
        return 1

    try:
        Path(args.output).write_text(page, encoding="utf-8")
    except OSError as exc:
        print("错误: 写入 HTML 文件失败: %s" % exc, file=sys.stderr)
        return 1

    page_count = (len(selected) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE
    print("已生成 %s：%d 道错题，%d 页" % (args.output, len(selected), page_count))
    print("用浏览器打开后按 Ctrl/Cmd + P，纸张选 A4 纵向即可打印")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
