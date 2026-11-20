"""errorbook：A4 可打印、可复习打卡的错题整理册。"""

from __future__ import annotations

from .model import (
    HEADER,
    MAX_ITEMS,
    ErrorBookError,
    ErrorItem,
    filter_by_subject,
    load_items,
    parse_csv,
)
from .render import CARDS_PER_PAGE, paginate, render_html

__version__ = "0.1.0"

__all__ = [
    "CARDS_PER_PAGE",
    "HEADER",
    "MAX_ITEMS",
    "ErrorBookError",
    "ErrorItem",
    "filter_by_subject",
    "load_items",
    "paginate",
    "parse_csv",
    "render_html",
    "__version__",
]
