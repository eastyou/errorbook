"""CSV 解析、数据模型与科目筛选的单元测试。"""

from __future__ import annotations

import dataclasses
import tempfile
import unittest
from pathlib import Path
from typing import List

from errorbook.model import (
    HEADER,
    MAX_ITEMS,
    ErrorBookError,
    ErrorItem,
    filter_by_subject,
    load_items,
    parse_csv,
)

SAMPLE = """科目,题目,错因,正解,复习日期
数学,2x+3=7，求 x,移项时符号写错,2x=4，所以 x=2,2026-01-05
语文,《春》的作者是谁？,作家作品对应不牢,作者是朱自清,2026-01-06
英语,go 的过去式,不规则变化记错,go 的过去式是 went,2026-01-07
"""


def make_row(
    subject: str = "数学",
    question: str = "1+1=?",
    reason: str = "粗心",
    solution: str = "2",
    review_date: str = "2026-01-01",
) -> str:
    """构造一条不需要额外 CSV 引号的测试数据。"""
    return ",".join((subject, question, reason, solution, review_date))


class ParseCsvTest(unittest.TestCase):
    def test_parse_sample(self) -> None:
        items = parse_csv(SAMPLE)
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].subject, "数学")
        self.assertEqual(items[0].question, "2x+3=7，求 x")
        self.assertEqual(items[0].review_date, "2026-01-05")

    def test_return_type_is_tuple(self) -> None:
        self.assertIsInstance(parse_csv(SAMPLE), tuple)

    def test_subject_is_trimmed(self) -> None:
        items = parse_csv(HEADER + "\n" + make_row(subject="  数学  "))
        self.assertEqual(items[0].subject, "数学")

    def test_other_fields_are_trimmed(self) -> None:
        row = make_row(question=" 题目 ", reason=" 错因 ", solution=" 正解 ", review_date=" 2026-01-01 ")
        item = parse_csv(HEADER + "\n" + row)[0]
        self.assertEqual(
            (item.question, item.reason, item.solution, item.review_date),
            ("题目", "错因", "正解", "2026-01-01"),
        )

    def test_quoted_comma(self) -> None:
        text = HEADER + '\n数学,"1,2,3 的平均数",粗心,答案是 2,2026-01-01\n'
        self.assertEqual(parse_csv(text)[0].question, "1,2,3 的平均数")

    def test_multiline_question(self) -> None:
        text = HEADER + '\n数学,"第一行\n第二行",粗心,正解,2026-01-01\n'
        self.assertEqual(parse_csv(text)[0].question, "第一行\n第二行")

    def test_blank_lines_are_ignored(self) -> None:
        text = "\n" + HEADER + "\n\n" + make_row() + "\n\n"
        self.assertEqual(len(parse_csv(text)), 1)

    def test_bom_is_accepted(self) -> None:
        self.assertEqual(len(parse_csv("\ufeff" + SAMPLE)), 3)

    def test_empty_content_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv("\n\n")
        self.assertIn("没有内容", str(ctx.exception))

    def test_only_header_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n")
        self.assertIn("第 1 行", str(ctx.exception))
        self.assertIn("至少", str(ctx.exception))

    def test_wrong_header_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv("学科,题目,错因,正解,复习日期\n" + make_row())
        self.assertIn("第 1 行", str(ctx.exception))
        self.assertIn(HEADER, str(ctx.exception))

    def test_header_order_is_fixed(self) -> None:
        with self.assertRaises(ErrorBookError):
            parse_csv("题目,科目,错因,正解,复习日期\n" + make_row())

    def test_extra_header_column_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError):
            parse_csv(HEADER + ",备注\n" + make_row() + ",备注")

    def test_wrong_column_count_has_line_number(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n数学,题目,错因,正解\n")
        self.assertIn("第 2 行", str(ctx.exception))
        self.assertIn("5 列", str(ctx.exception))

    def test_empty_subject_has_line_number(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(subject="  "))
        self.assertIn("第 2 行", str(ctx.exception))
        self.assertIn("科目", str(ctx.exception))

    def test_empty_question_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(question=""))
        self.assertIn("第 2 行", str(ctx.exception))
        self.assertIn("题目", str(ctx.exception))

    def test_empty_reason_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(reason=" "))
        self.assertIn("错因", str(ctx.exception))

    def test_empty_solution_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(solution=""))
        self.assertIn("正解", str(ctx.exception))

    def test_empty_review_date_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(review_date=""))
        self.assertIn("复习日期", str(ctx.exception))

    def test_subject_too_long(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(subject="科" * 13))
        self.assertIn("12", str(ctx.exception))

    def test_question_too_long(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(question="题" * 121))
        self.assertIn("120", str(ctx.exception))

    def test_reason_too_long(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(reason="因" * 81))
        self.assertIn("80", str(ctx.exception))

    def test_solution_too_long(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(solution="解" * 121))
        self.assertIn("120", str(ctx.exception))

    def test_max_length_fields_are_accepted(self) -> None:
        row = make_row(
            subject="科" * 12,
            question="题" * 120,
            reason="因" * 80,
            solution="解" * 120,
        )
        self.assertEqual(len(parse_csv(HEADER + "\n" + row)), 1)

    def test_invalid_date_format(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(review_date="2026/01/01"))
        self.assertIn("YYYY-MM-DD", str(ctx.exception))

    def test_impossible_date_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + make_row(review_date="2026-02-30"))
        self.assertIn("第 2 行", str(ctx.exception))
        self.assertIn("真实", str(ctx.exception))

    def test_leap_day_is_accepted(self) -> None:
        row = make_row(review_date="2028-02-29")
        self.assertEqual(parse_csv(HEADER + "\n" + row)[0].review_date, "2028-02-29")

    def test_non_leap_day_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError):
            parse_csv(HEADER + "\n" + make_row(review_date="2027-02-29"))

    def test_date_must_be_zero_padded(self) -> None:
        with self.assertRaises(ErrorBookError):
            parse_csv(HEADER + "\n" + make_row(review_date="2026-1-01"))

    def test_one_hundred_items_are_accepted(self) -> None:
        rows: List[str] = [make_row(question="题目 %d" % index) for index in range(MAX_ITEMS)]
        self.assertEqual(len(parse_csv(HEADER + "\n" + "\n".join(rows))), MAX_ITEMS)

    def test_more_than_one_hundred_items_is_rejected(self) -> None:
        rows = [make_row(question="题目 %d" % index) for index in range(MAX_ITEMS + 1)]
        with self.assertRaises(ErrorBookError) as ctx:
            parse_csv(HEADER + "\n" + "\n".join(rows))
        self.assertIn("第 102 行", str(ctx.exception))
        self.assertIn("100", str(ctx.exception))

    def test_non_text_content_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError):
            parse_csv(b"not text")  # type: ignore[arg-type]


class LoadItemsTest(unittest.TestCase):
    def test_load_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "utf8.csv"
            path.write_text(SAMPLE, encoding="utf-8")
            self.assertEqual(len(load_items(path)), 3)

    def test_load_utf8_bom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bom.csv"
            path.write_bytes(SAMPLE.encode("utf-8-sig"))
            self.assertEqual(load_items(path)[1].subject, "语文")

    def test_load_gbk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gbk.csv"
            path.write_bytes(SAMPLE.encode("gbk"))
            self.assertEqual(load_items(path)[2].subject, "英语")

    def test_unknown_encoding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unknown.csv"
            path.write_bytes(b"\xff\xff\xff\xff")
            with self.assertRaises(ErrorBookError) as ctx:
                load_items(path)
            self.assertIn("编码", str(ctx.exception))

    def test_missing_file_raises_os_error(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_items("/tmp/definitely-missing-errorbook.csv")


class ErrorItemTest(unittest.TestCase):
    def test_direct_model_trims_subject(self) -> None:
        item = ErrorItem(" 数学 ", "题目", "错因", "正解", "2026-01-01")
        self.assertEqual(item.subject, "数学")

    def test_model_is_frozen(self) -> None:
        item = ErrorItem("数学", "题目", "错因", "正解", "2026-01-01")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.subject = "英语"  # type: ignore[misc]

    def test_direct_model_rejects_non_text(self) -> None:
        with self.assertRaises(ErrorBookError):
            ErrorItem(1, "题目", "错因", "正解", "2026-01-01")  # type: ignore[arg-type]

    def test_direct_model_rejects_bad_date(self) -> None:
        with self.assertRaises(ErrorBookError):
            ErrorItem("数学", "题目", "错因", "正解", "2026-13-01")


class FilterBySubjectTest(unittest.TestCase):
    def setUp(self) -> None:
        self.items = parse_csv(SAMPLE)

    def test_exact_filter(self) -> None:
        selected = filter_by_subject(self.items, "数学")
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].subject, "数学")

    def test_none_returns_all_items(self) -> None:
        self.assertEqual(filter_by_subject(self.items, None), self.items)

    def test_substring_does_not_match(self) -> None:
        with self.assertRaises(ErrorBookError):
            filter_by_subject(self.items, "数")

    def test_no_match_has_chinese_error(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            filter_by_subject(self.items, "物理")
        self.assertIn("未找到", str(ctx.exception))
        self.assertIn("物理", str(ctx.exception))

    def test_empty_subject_is_rejected(self) -> None:
        with self.assertRaises(ErrorBookError) as ctx:
            filter_by_subject(self.items, " ")
        self.assertIn("科目", str(ctx.exception))

    def test_filter_result_is_tuple(self) -> None:
        self.assertIsInstance(filter_by_subject(self.items, "语文"), tuple)


if __name__ == "__main__":
    unittest.main()
