"""把错题渲染为每页两张卡片的 A4 纵向打印册。"""

from __future__ import annotations

import html
from typing import List, Sequence, Tuple

from .model import ErrorBookError, ErrorItem

CARDS_PER_PAGE = 2

STYLE = """
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    padding: 8mm 0;
    background: #e2e8f0;
    color: #172033;
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
  }
  .page {
    width: 210mm;
    height: 297mm;
    margin: 0 auto 8mm;
    padding: 10mm 12mm 8mm;
    background: #fff;
    box-shadow: 0 5px 20px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    page-break-after: always;
    break-after: page;
  }
  .page:last-child { page-break-after: auto; break-after: auto; }
  .page-head {
    margin-bottom: 4mm;
    padding-bottom: 2.5mm;
    border-bottom: 0.35mm solid #334155;
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 6mm;
  }
  .page-head h1 { margin: 0; font-size: 19pt; font-weight: 650; letter-spacing: 2pt; }
  .page-head span { flex: none; color: #64748b; font-size: 9pt; }
  .cards {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-rows: repeat(2, minmax(0, 1fr));
    gap: 5mm;
  }
  .card {
    min-height: 0;
    padding: 4mm 5mm 3.5mm;
    border: 0.3mm solid #94a3b8;
    border-radius: 2mm;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    break-inside: avoid;
    page-break-inside: avoid;
  }
  .card-head {
    display: flex;
    align-items: center;
    gap: 3mm;
    margin-bottom: 2.5mm;
    font-size: 9pt;
    color: #475569;
  }
  .number { color: #0f172a; font-size: 12pt; font-weight: 700; }
  .subject { padding: 0.8mm 2.5mm; background: #eef2ff; color: #3730a3; border-radius: 5mm; }
  .date { margin-left: auto; }
  .field { margin: 0 0 2.2mm; }
  .field h2 { margin: 0 0 0.8mm; color: #475569; font-size: 9pt; font-weight: 650; }
  .field p {
    margin: 0;
    font-size: 10.5pt;
    line-height: 1.45;
    overflow-wrap: anywhere;
    word-break: break-word;
    white-space: pre-wrap;
  }
  .question p { color: #0f172a; font-weight: 600; }
  .reason p { color: #9f1239; }
  .solution p { color: #14532d; }
  .checkin {
    margin-top: auto;
    padding-top: 2mm;
    border-top: 0.25mm dashed #cbd5e1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4mm;
    color: #334155;
    font-size: 10pt;
  }
  .checkin strong { font-size: 9pt; }
  .page-foot {
    margin-top: 4mm;
    padding-top: 2mm;
    border-top: 0.2mm solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    color: #64748b;
    font-size: 8pt;
  }
  @page { size: A4 portrait; margin: 0; }
  @media print {
    body { padding: 0; background: #fff; }
    .page { margin: 0; box-shadow: none; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""


def paginate(
    items: Sequence[ErrorItem], per_page: int = CARDS_PER_PAGE
) -> Tuple[Tuple[ErrorItem, ...], ...]:
    """把错题按固定页容量分组，保留原始顺序。"""
    if isinstance(per_page, bool) or not isinstance(per_page, int) or per_page < 1:
        raise ErrorBookError("每页卡片数必须是正整数")
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ErrorBookError("错题集合必须是序列")
    selected = tuple(items)
    if any(not isinstance(item, ErrorItem) for item in selected):
        raise ErrorBookError("错题集合中包含无效数据")
    return tuple(
        selected[start : start + per_page]
        for start in range(0, len(selected), per_page)
    )


def _render_card(item: ErrorItem, number: int) -> str:
    return (
        '<article class="card">\n'
        '<header class="card-head"><span class="number">第 %d 题</span>'
        '<span class="subject">%s</span>'
        '<span class="date">复习日期：%s</span></header>\n'
        '<section class="field question"><h2>题目</h2><p>%s</p></section>\n'
        '<section class="field reason"><h2>错因</h2><p>%s</p></section>\n'
        '<section class="field solution"><h2>正解</h2><p>%s</p></section>\n'
        '<footer class="checkin"><strong>复习打卡</strong>'
        '<span>第 1 次 □　第 2 次 □　第 3 次 □</span></footer>\n'
        "</article>"
        % (
            number,
            html.escape(item.subject),
            html.escape(item.review_date),
            html.escape(item.question),
            html.escape(item.reason),
            html.escape(item.solution),
        )
    )


def render_html(items: Sequence[ErrorItem], title: str = "错题整理册") -> str:
    """生成完整、自包含且所有外部文本均转义的打印 HTML。"""
    if not isinstance(title, str) or not title.strip():
        raise ErrorBookError("标题不能为空")
    clean_title = title.strip()
    pages = paginate(items, per_page=CARDS_PER_PAGE)
    if not pages:
        raise ErrorBookError("没有可渲染的错题")

    rendered_pages: List[str] = []
    card_number = 1
    for page_number, page_items in enumerate(pages, start=1):
        cards: List[str] = []
        for item in page_items:
            cards.append(_render_card(item, card_number))
            card_number += 1
        rendered_pages.append(
            '<section class="page">\n'
            '<header class="page-head"><h1>%s</h1><span>共 %d 题</span></header>\n'
            '<div class="cards">\n%s\n</div>\n'
            '<footer class="page-foot"><span>errorbook · A4 纵向</span>'
            "<span>第 %d / %d 页</span></footer>\n"
            "</section>"
            % (
                html.escape(clean_title),
                len(items),
                "\n".join(cards),
                page_number,
                len(pages),
            )
        )

    return (
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n<style>%s</style>\n</head>\n<body>\n%s\n</body>\n</html>\n"
        % (html.escape(clean_title), STYLE, "\n".join(rendered_pages))
    )
