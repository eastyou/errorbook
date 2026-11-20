"""命令行参数、输出文件与退出码的单元测试。"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import List, Tuple

from errorbook.cli import main

SAMPLE = """科目,题目,错因,正解,复习日期
数学,2x+3=7，求 x,移项时符号写错,x=2,2026-01-05
语文,《春》的作者是谁？,作家作品对应不牢,朱自清,2026-01-06
数学,三角形内角和是多少？,公式记忆不牢,180 度,2026-01-07
"""


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "错题.csv"
        self.source.write_text(SAMPLE, encoding="utf-8")
        self.target = self.root / "错题整理册.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, argv: List[str]) -> Tuple[int, str, str]:
        """运行 CLI 并捕获标准输出和错误输出。"""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_generate_html(self) -> None:
        code, out, err = self.run_cli(["-i", str(self.source), "-o", str(self.target)])
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        self.assertIn("已生成", out)
        self.assertIn("3 道错题", out)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("2x+3=7", page)
        self.assertEqual(page.count('<article class="card">'), 3)

    def test_custom_title(self) -> None:
        code, _, _ = self.run_cli(
            ["-i", str(self.source), "--title", "我的错题整理册", "-o", str(self.target)]
        )
        self.assertEqual(code, 0)
        self.assertIn("<title>我的错题整理册</title>", self.target.read_text(encoding="utf-8"))

    def test_subject_filter(self) -> None:
        code, out, _ = self.run_cli(
            ["-i", str(self.source), "--subject", "数学", "-o", str(self.target)]
        )
        self.assertEqual(code, 0)
        self.assertIn("2 道错题", out)
        page = self.target.read_text(encoding="utf-8")
        self.assertIn("2x+3=7", page)
        self.assertIn("三角形内角和", page)
        self.assertNotIn("《春》", page)

    def test_subject_must_be_exact(self) -> None:
        code, _, err = self.run_cli(
            ["-i", str(self.source), "--subject", "数", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("未找到", err)
        self.assertFalse(self.target.exists())

    def test_unknown_subject_has_chinese_error(self) -> None:
        code, _, err = self.run_cli(
            ["-i", str(self.source), "--subject", "物理", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误", err)
        self.assertIn("物理", err)

    def test_invalid_csv_returns_two(self) -> None:
        bad = self.root / "bad.csv"
        bad.write_text("科目,题目,错因,正解,复习日期\n数学,题目,错因,正解,2026-02-30\n", encoding="utf-8")
        code, _, err = self.run_cli(["-i", str(bad), "-o", str(self.target)])
        self.assertEqual(code, 2)
        self.assertIn("第 2 行", err)
        self.assertFalse(self.target.exists())

    def test_missing_input_file_returns_one(self) -> None:
        code, _, err = self.run_cli(
            ["-i", str(self.root / "missing.csv"), "-o", str(self.target)]
        )
        self.assertEqual(code, 1)
        self.assertIn("读取", err)

    def test_output_error_returns_one(self) -> None:
        code, _, err = self.run_cli(["-i", str(self.source), "-o", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("写入", err)

    def test_default_output_name(self) -> None:
        previous = Path.cwd()
        try:
            os.chdir(str(self.root))
            code, _, _ = self.run_cli(["-i", str(self.source)])
        finally:
            os.chdir(str(previous))
        self.assertEqual(code, 0)
        self.assertTrue((self.root / "错题整理册.html").exists())

    def test_default_title(self) -> None:
        code, _, _ = self.run_cli(["-i", str(self.source), "-o", str(self.target)])
        self.assertEqual(code, 0)
        self.assertIn("<title>错题整理册</title>", self.target.read_text(encoding="utf-8"))

    def test_missing_input_argument_exits_two(self) -> None:
        with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stderr(io.StringIO()):
            main(["-o", str(self.target)])
        self.assertEqual(ctx.exception.code, 2)

    def test_help_exits_zero(self) -> None:
        with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stdout(io.StringIO()):
            main(["--help"])
        self.assertEqual(ctx.exception.code, 0)

    def test_version_exits_zero(self) -> None:
        with self.assertRaises(SystemExit) as ctx, contextlib.redirect_stdout(io.StringIO()):
            main(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_python_dash_m_entry_point(self) -> None:
        project = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "errorbook",
                "-i",
                str(self.source),
                "-o",
                str(self.target),
            ],
            cwd=str(project),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.target.exists())

    def test_empty_title_returns_two(self) -> None:
        code, _, err = self.run_cli(
            ["-i", str(self.source), "--title", " ", "-o", str(self.target)]
        )
        self.assertEqual(code, 2)
        self.assertIn("标题", err)


if __name__ == "__main__":
    unittest.main()
