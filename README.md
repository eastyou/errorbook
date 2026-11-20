# errorbook

[![CI](https://github.com/eastyou/errorbook/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/errorbook/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

给学生用的错题整理册生成器：把固定五列的错题 CSV 转成 A4 纵向打印册，一道题一张卡片，带三次复习打卡区。**零依赖，不联网，Python 3.9+ 标准库即可运行。**

每页两张卡片，自动分页、连续编号并显示页码；可以按科目精确筛选，把数学、语文、英语等错题分别打印复习。

## 特性

- **固定五列**：`科目,题目,错因,正解,复习日期`，逐行校验并用中文指出行号
- **真实日期**：复习日期必须是有效的 `YYYY-MM-DD`，会识别闰年和不存在的日期
- **编码兼容**：自动识别 UTF-8、UTF-8 BOM 与 GBK
- **容量明确**：每份 CSV 支持 1~100 条错题，所有字段必填并限制长度
- **科目筛选**：`--subject 数学` 精确筛选，无匹配时给出中文错误
- **打印排版**：A4 纵向、每页两卡、卡片不跨页，长文本换行不溢出
- **复习打卡**：每题均有「第 1 次 □　第 2 次 □　第 3 次 □」
- **86 个单元测试**：覆盖解析编码、字段边界、日期、筛选、分页、转义与 CLI

## 安装

```bash
pip install errorbook
```

也可以直接下载源码，在项目目录里运行，无需安装第三方依赖：

```bash
python -m errorbook --help
```

## 用法

准备 `错题.csv`：

```csv
科目,题目,错因,正解,复习日期
数学,2x+3=7，求 x,移项时没有变号,2x=7-3=4，所以 x=2,2026-11-22
语文,《春》的作者是谁？,作家与作品对应不牢,《春》的作者是朱自清,2026-11-23
```

生成错题整理册：

```bash
python -m errorbook -i examples/错题.csv --title 我的错题整理册 -o examples/错题整理册.html
```

只生成数学错题：

```bash
python -m errorbook -i examples/错题.csv --subject 数学 -o 数学错题.html
```

安装后也可以使用 `errorbook` 命令，参数完全相同。

### 参数

| 参数 | 说明 | 默认 |
| --- | --- | --- |
| `-i, --input` | 错题 CSV 路径 | 必填 |
| `-o, --output` | 输出 HTML 路径 | `错题整理册.html` |
| `--title` | 整理册标题 | `错题整理册` |
| `--subject` | 按科目精确筛选 | 不筛选 |

成功退出码为 `0`；文件读取或写入失败为 `1`；CSV、标题、筛选条件等数据错误为 `2`。

### CSV 格式

表头必须严格为：

```text
科目,题目,错因,正解,复习日期
```

| 字段 | 规则 |
| --- | --- |
| 科目 | 去首尾空白后 1~12 个字符 |
| 题目 | 1~120 个字符 |
| 错因 | 1~80 个字符 |
| 正解 | 1~120 个字符 |
| 复习日期 | 真实的 ISO 日期，格式为 `YYYY-MM-DD` |

- 所有字段必填，每份文件 1~100 条数据。
- 字段含英文逗号或换行时，按 CSV 规范用双引号包围。
- 编码支持 UTF-8、UTF-8 BOM 与 GBK。
- 空字段、超长、列数不对、非法日期都会报告具体行号。

## 打印

用浏览器打开生成的 HTML，按 `Ctrl/Cmd + P`：

- 纸张：A4 纵向
- 缩放：100%
- 边距：无（页面已预留书写边距）
- 建议勾选「背景图形」，保留科目标签底色

每页两张卡片，奇数题的最后一页只有一张。打印后在各题的打卡区手动勾选三次复习进度。

## 项目结构

```text
errorbook/
├── errorbook/
│   ├── __init__.py   # 公共 API 与版本
│   ├── __main__.py   # python -m errorbook
│   ├── cli.py        # 参数、文件写入与退出码
│   ├── model.py      # dataclass、CSV 校验与科目筛选
│   └── render.py     # 两题一页的 A4 HTML 渲染
├── tests/            # 86 个 unittest 测试
├── examples/         # 示例 CSV 与生成的 HTML
└── .github/workflows/ci.yml
```

## 开发

```bash
python3 -m unittest discover -s tests
python3 -m errorbook -i examples/错题.csv --title 我的错题整理册 -o examples/错题整理册.html
```

## 许可证

[MIT](LICENSE) © 2026 eastyou
