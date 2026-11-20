"""A4 分页、HTML 转义与复习打卡区的单元测试。"""

from __future__ import annotations

import unittest
from typing import Tuple

from errorbook.model import ErrorBookError, ErrorItem, parse_csv
from errorbook.render import CARDS_PER_PAGE, paginate, render_html


def make_items(count: int) -> Tuple[ErrorItem, ...]:
    """生成指定数量的合法错题。"""
    return tuple(
        ErrorItem(
            subject="数学" if index % 2 else "语文",
            question="题目 %d" % (index + 1),
            reason="错因 %d" % (index + 1),
            solution="正解 %d" % (index + 1),
            review_date="2026-01-%02d" % (index + 1),
        )
        for index in range(count)
    )


class PaginateTest(unittest.TestCase):
    def test_even_item_count(self) -> None:
        pages = paginate(make_items(4))
        self.assertEqual([len(page) for page in pages], [2, 2])

    def test_odd_item_count(self) -> None:
        pages = paginate(make_items(5))
        self.assertEqual([len(page) for page in pages], [2, 2, 1])

    def test_one_item(self) -> None:
        pages = paginate(make_items(1))
        self.assertEqual(len(pages), 1)
        self.assertEqual(len(pages[0]), 1)

    def test_empty_items(self) -> None:
        self.assertEqual(paginate(()), ())

    def test_custom_page_size(self) -> None:
        pages = paginate(make_items(4), per_page=3)
        self.assertEqual([len(page) for page in pages], [3, 1])

    def test_invalid_page_size(self) -> None:
        for value in (0, -1, True, 1.5):
            with self.subTest(value=value), self.assertRaises(ErrorBookError):
                paginate(make_items(1), per_page=value)  # type: ignore[arg-type]


class RenderHtmlTest(unittest.TestCase):
    def test_basic_document(self) -> None:
        page = render_html(make_items(1))
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertIn('<html lang="zh-CN">', page)
        self.assertIn("A4 portrait", page)
        self.assertIn("错题整理册", page)

    def test_card_contains_all_fields(self) -> None:
        page = render_html(make_items(1))
        for text in ("第 1 题", "语文", "2026-01-01", "题目 1", "错因 1", "正解 1"):
            with self.subTest(text=text):
                self.assertIn(text, page)

    def test_each_page_has_at_most_two_cards(self) -> None:
        page = render_html(make_items(5))
        self.assertEqual(page.count('<section class="page">'), 3)
        self.assertEqual(page.count('<article class="card">'), 5)
        self.assertEqual(CARDS_PER_PAGE, 2)

    def test_even_page_count(self) -> None:
        page = render_html(make_items(4))
        self.assertEqual(page.count('<section class="page">'), 2)
        self.assertIn("第 2 / 2 页", page)

    def test_odd_page_count(self) -> None:
        page = render_html(make_items(3))
        self.assertEqual(page.count('<section class="page">'), 2)
        self.assertIn("第 2 / 2 页", page)

    def test_numbering_continues_across_pages(self) -> None:
        page = render_html(make_items(5))
        for number in range(1, 6):
            self.assertIn("第 %d 题" % number, page)

    def test_page_numbers(self) -> None:
        page = render_html(make_items(5))
        for number in range(1, 4):
            self.assertIn("第 %d / 3 页" % number, page)

    def test_review_checkin_area_for_every_card(self) -> None:
        page = render_html(make_items(3))
        self.assertEqual(page.count("复习打卡"), 3)
        self.assertEqual(page.count("第 1 次 □　第 2 次 □　第 3 次 □"), 3)

    def test_title_is_escaped(self) -> None:
        page = render_html(make_items(1), title="<我的> & \"错题\"")
        self.assertIn("&lt;我的&gt; &amp; &quot;错题&quot;", page)
        self.assertNotIn("<我的>", page)

    def test_all_item_text_is_escaped(self) -> None:
        item = ErrorItem(
            subject="<数学>",
            question="题目 <b>加粗</b> & 内容",
            reason="错因 <i>标记</i>",
            solution='正解 "答案" & <解>',
            review_date="2026-01-01",
        )
        page = render_html((item,))
        for text in (
            "&lt;数学&gt;",
            "题目 &lt;b&gt;加粗&lt;/b&gt; &amp; 内容",
            "错因 &lt;i&gt;标记&lt;/i&gt;",
            "正解 &quot;答案&quot; &amp; &lt;解&gt;",
        ):
            with self.subTest(text=text):
                self.assertIn(text, page)
        self.assertNotIn("<b>加粗</b>", page)

    def test_long_text_wraps_without_overflow(self) -> None:
        item = ErrorItem("数学", "Q" * 120, "粗心", "A" * 120, "2026-01-01")
        page = render_html((item,))
        self.assertIn("overflow-wrap: anywhere", page)
        self.assertIn("white-space: pre-wrap", page)
        self.assertIn("Q" * 120, page)
        self.assertIn("A" * 120, page)

    def test_cards_avoid_page_breaks(self) -> None:
        page = render_html(make_items(2))
        self.assertIn("break-inside: avoid", page)
        self.assertIn("page-break-inside: avoid", page)

    def test_css_is_self_contained(self) -> None:
        page = render_html(make_items(1))
        self.assertIn("<style>", page)
        self.assertNotIn("<link", page)
        self.assertNotIn("<script", page)

    def test_custom_title(self) -> None:
        page = render_html(make_items(1), title=" 我的错题整理册 ")
        self.assertIn("<title>我的错题整理册</title>", page)
        self.assertIn("<h1>我的错题整理册</h1>", page)

    def test_empty_items_are_rejected(self) -> None:
        with self.assertRaises(ErrorBookError):
            render_html(())

    def test_empty_title_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError):
            render_html(make_items(1), title=" ")

    def test_non_text_title_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError):
            render_html(make_items(1), title=1)  # type: ignore[arg-type]

    def test_invalid_items_are_rejected(self) -> None:
        with self.assertRaises(ErrorBookError):
            render_html("not items")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
