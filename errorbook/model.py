"""错题数据模型：CSV 解码、逐行校验与科目筛选。"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

HEADER = "科目,题目,错因,正解,复习日期"
HEADER_FIELDS = ("科目", "题目", "错因", "正解", "复习日期")
MIN_ITEMS = 1
MAX_ITEMS = 100
MAX_SUBJECT = 12
MAX_QUESTION = 120
MAX_REASON = 80
MAX_SOLUTION = 120
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ErrorBookError(ValueError):
    """错题数据、筛选条件或渲染参数不合法。"""


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ErrorBookError("%s必须是文本" % field)
    cleaned = value.strip()
    if not cleaned:
        raise ErrorBookError("%s不能为空" % field)
    return cleaned


def _limited_text(value: object, field: str, maximum: int) -> str:
    cleaned = _required_text(value, field)
    if len(cleaned) > maximum:
        raise ErrorBookError("%s最多 %d 个字符，当前 %d 个字符" % (field, maximum, len(cleaned)))
    return cleaned


def _valid_date(value: object) -> str:
    cleaned = _required_text(value, "复习日期")
    if ISO_DATE.fullmatch(cleaned) is None:
        raise ErrorBookError("复习日期格式必须为 YYYY-MM-DD")
    try:
        date.fromisoformat(cleaned)
    except ValueError as exc:
        raise ErrorBookError("复习日期必须是真实日期，格式为 YYYY-MM-DD") from exc
    return cleaned


@dataclass(frozen=True)
class ErrorItem:
    """一道错题及其复习信息。"""

    subject: str
    question: str
    reason: str
    solution: str
    review_date: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject", _limited_text(self.subject, "科目", MAX_SUBJECT))
        object.__setattr__(self, "question", _limited_text(self.question, "题目", MAX_QUESTION))
        object.__setattr__(self, "reason", _limited_text(self.reason, "错因", MAX_REASON))
        object.__setattr__(self, "solution", _limited_text(self.solution, "正解", MAX_SOLUTION))
        object.__setattr__(self, "review_date", _valid_date(self.review_date))


def _decode(data: bytes) -> str:
    """依次尝试 UTF-8（含 BOM）和 GBK。"""
    if not isinstance(data, bytes):
        raise ErrorBookError("文件内容必须是字节")
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ErrorBookError("无法识别文件编码，请另存为 UTF-8、UTF-8 BOM 或 GBK 后重试")


def parse_csv(text: str, source: str = "输入内容") -> Tuple[ErrorItem, ...]:
    """解析固定五列表头的错题 CSV，并为数据错误标注行号。"""
    if not isinstance(text, str):
        raise ErrorBookError("CSV 内容必须是文本")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    rows: List[Tuple[int, List[str]]] = []
    previous_end = 0
    try:
        for row in reader:
            start_line = previous_end + 1
            previous_end = reader.line_num
            cells = [cell.strip() for cell in row]
            if any(cells):
                rows.append((start_line, cells))
    except csv.Error as exc:
        line_no = max(reader.line_num, 1)
        raise ErrorBookError("%s 第 %d 行 CSV 格式错误：%s" % (source, line_no, exc)) from exc

    if not rows:
        raise ErrorBookError("%s 第 1 行：没有内容" % source)

    header_line, header = rows[0]
    if tuple(header) != HEADER_FIELDS:
        raise ErrorBookError("%s 第 %d 行表头错误：必须严格为 %s" % (source, header_line, HEADER))
    if len(rows) == 1:
        raise ErrorBookError(
            "%s 第 %d 行后至少需要 %d 条错题，最多支持 %d 条"
            % (source, header_line, MIN_ITEMS, MAX_ITEMS)
        )

    items: List[ErrorItem] = []
    for line_no, cells in rows[1:]:
        if len(items) >= MAX_ITEMS:
            raise ErrorBookError("%s 第 %d 行：最多支持 %d 条错题" % (source, line_no, MAX_ITEMS))
        if len(cells) != len(HEADER_FIELDS):
            raise ErrorBookError(
                "%s 第 %d 行有 %d 列，应为 5 列（%s）"
                % (source, line_no, len(cells), HEADER)
            )
        try:
            item = ErrorItem(*cells)
        except ErrorBookError as exc:
            raise ErrorBookError("%s 第 %d 行：%s" % (source, line_no, exc)) from exc
        items.append(item)
    return tuple(items)


def load_items(path: Union[str, Path]) -> Tuple[ErrorItem, ...]:
    """从 UTF-8、UTF-8 BOM 或 GBK 文件读取错题；文件错误保留为 OSError。"""
    target = Path(path)
    return parse_csv(_decode(target.read_bytes()), source=str(target))


def filter_by_subject(
    items: Sequence[ErrorItem], subject: Optional[str] = None
) -> Tuple[ErrorItem, ...]:
    """按科目精确筛选；subject 为 None 时保留全部题目。"""
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ErrorBookError("错题集合必须是序列")
    selected = tuple(items)
    if any(not isinstance(item, ErrorItem) for item in selected):
        raise ErrorBookError("错题集合中包含无效数据")
    if subject is None:
        return selected
    cleaned = _required_text(subject, "筛选科目")
    filtered = tuple(item for item in selected if item.subject == cleaned)
    if not filtered:
        raise ErrorBookError("未找到科目「%s」的错题，请检查 --subject 参数" % cleaned)
    return filtered
