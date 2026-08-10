#!/usr/bin/env python3
"""OCR a scanned Chinese PDF and organize the result as hierarchical JSON.

The OCR backend is the built-in Windows.Media.Ocr engine. Poppler's
``pdfinfo`` and ``pdftoppm`` executables are used to inspect and render PDFs.
No cloud service is involved.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


CHAPTER_RE = re.compile(r"^第\s*([一二三四五六七八九十百零〇0-9]+)\s*章?(?:\s+(.+))?$")
CN_SECTION_RE = re.compile(r"^([一二三四五六七八九十百]+)\s*[、．.]\s*(.+)$")
DECIMAL_RE = re.compile(r"^(\d+(?:\s*[.．]\s*\d+){1,3})\s+(.+)$")
CASE_RE = re.compile(r"^(?:(\d{1,3})|[.。·])\s*[、.．]?\s*(.{5,})$")
PAGE_NUMBER_RE = re.compile(r"^[—–-]?\s*\d{1,3}\s*[—–-]?$")


@dataclass
class Node:
    type: str
    title: str
    level: int
    number: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    content: list[str] = field(default_factory=list)
    children: list["Node"] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "page_start": self.page_start,
            "page_end": self.page_end,
        }
        if self.number is not None:
            result["number"] = self.number
        if self.content:
            result["content"] = self.content
        if self.children:
            result["children"] = [child.as_dict() for child in self.children]
        return result


def run(command: list[str]) -> None:
    printable = subprocess.list2cmdline(command)
    print(f"[run] {printable}", file=sys.stderr)
    subprocess.run(command, check=True)


def get_page_count(pdf: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(pdf)], check=True, capture_output=True, text=True, errors="replace"
    )
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        raise RuntimeError("Cannot determine PDF page count from pdfinfo output")
    return int(match.group(1))


def render_pdf(pdf: Path, image_dir: Path, dpi: int, first_page: int, last_page: int) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    prefix = image_dir / "page"
    run(
        [
            "pdftoppm",
            "-f",
            str(first_page),
            "-l",
            str(last_page),
            "-r",
            str(dpi),
            "-gray",
            "-png",
            str(pdf),
            str(prefix),
        ]
    )


def run_windows_ocr(image_dir: Path, raw_output: Path, language: str) -> None:
    helper = Path(__file__).with_name("windows_ocr.ps1")
    run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(helper),
            "-ImageDirectory",
            str(image_dir.resolve()),
            "-OutputFile",
            str(raw_output.resolve()),
            "-Language",
            language,
        ]
    )


def read_ndjson(path: Path) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                try:
                    pages.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid OCR JSON at line {line_number}: {exc}") from exc
    return pages


def normalize(text: str) -> str:
    text = text.replace("．", ".")
    text = re.sub(r"[ \t\u3000]+", " ", text)
    text = re.sub(r"(?<=\d)\s*[，,]\s*(?=\d)", ".", text)
    # Windows OCR often emits every Chinese glyph as an individual word.
    text = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", text)
    text = re.sub(r"\s+([，。；：！？、）】])", r"\1", text)
    text = re.sub(r"([（【])\s+", r"\1", text)
    return text.strip()


def iter_clean_lines(page: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    height = float(page.get("height") or 1)
    source_lines = list(page.get("lines", []))
    consumed: set[int] = set()
    for index, line in enumerate(source_lines):
        if index in consumed:
            continue
        text = normalize(str(line.get("text", "")))
        if not text:
            continue
        # On many case headers Windows OCR treats the dark circular badge and
        # the title as separate lines. Merge the isolated badge with a title
        # immediately to its right on the same visual row.
        if re.fullmatch(r"[0OoQ@.]", text) and float(line.get("height") or 0) >= height * 0.02:
            center_y = float(line.get("y") or 0) + float(line.get("height") or 0) / 2
            for other_index in range(index + 1, min(index + 4, len(source_lines))):
                other = source_lines[other_index]
                other_text = normalize(str(other.get("text", "")))
                other_center = float(other.get("y") or 0) + float(other.get("height") or 0) / 2
                if (
                    "故障" in other_text
                    and float(other.get("x") or 0) > float(line.get("x") or 0)
                    and abs(other_center - center_y) <= height * 0.025
                ):
                    text = f"0 {other_text}"
                    right = max(
                        float(line.get("x") or 0) + float(line.get("width") or 0),
                        float(other.get("x") or 0) + float(other.get("width") or 0),
                    )
                    line = dict(line)
                    line["width"] = right - float(line.get("x") or 0)
                    line["height"] = max(float(line.get("height") or 0), float(other.get("height") or 0))
                    consumed.add(other_index)
                    break
        if PAGE_NUMBER_RE.fullmatch(text):
            continue
        # Repeated running headers and footers carry little semantic content.
        y = float(line.get("y") or 0)
        if (y < height * 0.035 or y > height * 0.965) and len(text) < 25:
            continue
        yield text, line


def classify_heading(text: str, line: dict[str, Any], page: dict[str, Any]) -> tuple[int, str, str | None, str] | None:
    compact = normalize(text)
    line_height = float(line.get("height") or 0)
    page_height = float(page.get("height") or 1)
    line_x = float(line.get("x") or 0)
    page_width = float(page.get("width") or 1)
    match = CHAPTER_RE.fullmatch(compact)
    if match:
        line_height = float(line.get("height") or 0)
        page_height = float(page.get("height") or 1)
        if "章" not in compact and line_height < page_height * 0.02:
            return None
        suffix = normalize(match.group(2) or "")
        title = f"第{match.group(1)}章" + (f" {suffix}" if suffix else "")
        return 1, "chapter", match.group(1), title

    match = CN_SECTION_RE.fullmatch(compact)
    if match and "故障" in match.group(2):
        return 2, "section", match.group(1), compact

    match = re.fullmatch(r"^[、.．]\s*(.+?)\s*([一二三四五六七八九十百])$", compact)
    if match and "故障" in match.group(1):
        return 2, "section", match.group(2), f"{match.group(2)}、{match.group(1)}"

    match = DECIMAL_RE.fullmatch(compact)
    if match:
        number = re.sub(r"\s+", "", match.group(1)).replace("．", ".")
        depth = number.count(".")
        return min(4 + depth, 6), "subsection", number, f"{number} {normalize(match.group(2))}"

    match = CASE_RE.fullmatch(compact)
    if match:
        # Case titles are visually prominent. Requiring a larger-than-body line
        # prevents ordinary numbered list items from becoming case nodes.
        if line_height >= page_height * 0.024 and line_x <= page_width * 0.4:
            number = match.group(1) or "0"
            return 3, "case", number, f"{number} {normalize(match.group(2))}"

    # The circular badge is the least reliable glyph on a case-title line;
    # depending on the page it may become 0, punctuation, a letter, or vanish.
    # Typography and the “故障” keyword are much more stable signals.
    if (
        "故障" in compact
        and len(compact) >= 8
        and line_height >= page_height * 0.026
        and line_x <= page_width * 0.4
    ):
        title = re.sub(r"^[^0-9A-Za-z\u3400-\u9fff]+", "", compact)
        title = re.sub(r"^[0OoQ]\s+", "", title)
        return 3, "case", "0", f"0 {title}"
    return None


def organize(pages: list[dict[str, Any]]) -> list[Node]:
    roots: list[Node] = []
    stack: list[Node] = []
    preface: Node | None = None
    last_case_major = 0

    def chapter_count() -> int:
        return sum(item.type == "chapter" for item in roots)

    def chinese_number(value: int) -> str:
        digits = "零一二三四五六七八九"
        if value < 10:
            return digits[value]
        if value == 10:
            return "十"
        if value < 20:
            return "十" + digits[value - 10]
        return str(value)

    for page in pages:
        page_number = int(page["page"])
        for text, line in iter_clean_lines(page):
            heading = classify_heading(text, line, page)
            is_chapter_title = (
                "故障汇编" in text
                and float(line.get("height") or 0) >= float(page.get("height") or 1) * 0.03
                and len(text) <= 30
            )

            # Some divider pages lose “第X章” entirely during OCR. Their large
            # “……故障汇编” line is stable enough to synthesize the chapter.
            if is_chapter_title and (not stack or stack[-1].type != "chapter" or stack[-1].page_start != page_number):
                index = chapter_count() + 1
                number = chinese_number(index)
                node = Node("chapter", f"第{number}章 {text}", 1, number, page_number, page_number)
                roots.append(node)
                stack = [node]
                continue

            # Everything before the first divider page is cover/metadata/TOC,
            # even if it resembles a real section heading.
            if chapter_count() == 0 and (not heading or heading[1] != "chapter"):
                if preface is None:
                    preface = Node("front_matter", "前置内容", 0, page_start=page_number, page_end=page_number)
                    roots.append(preface)
                preface.content.append(text)
                preface.page_end = page_number
                continue

            if heading:
                level, node_type, number, title = heading
                if node_type == "chapter":
                    index = chapter_count() + 1
                    number = chinese_number(index)
                    title = re.sub(r"^第\s*[一二三四五六七八九十百零〇0-9]+\s*章?", f"第{number}章", title)
                if node_type == "case" and number == "0":
                    # Circled “1” is commonly recognized as zero in this book.
                    siblings = stack[-1].children if stack and stack[-1].level < level else roots
                    number = str(1 + sum(item.type == "case" for item in siblings))
                    title = re.sub(r"^0\b", number, title)

                # A top-level subsection such as “37.1 故障情况说明” is also
                # a reliable case boundary when OCR has lost the title badge.
                if node_type == "subsection" and number and number.count(".") == 1:
                    major = number.split(".")[0]
                    major_value = int(major) if major.isdigit() else 0
                    if 1 <= major_value <= 85 and last_case_major < major_value <= last_case_major + 3:
                        active_case = next((item for item in reversed(stack) if item.type == "case"), None)
                        active_major = active_case.number if active_case else None
                        if active_case is not None and not active_case.children and active_major in {"0", "1"}:
                            active_case.number = major
                        elif active_major != major:
                            candidate = ""
                            for owner in reversed(stack):
                                for value in reversed(owner.content[-3:]):
                                    if "故障" in value and len(value) <= 80:
                                        candidate = value
                                        owner.content.remove(value)
                                        break
                                if candidate:
                                    break
                            while stack and stack[-1].level >= 3:
                                stack.pop()
                            case_title = f"{major} {candidate}" if candidate else f"{major} 案例（标题OCR缺失）"
                            case_node = Node("case", case_title, 3, major, page_number, page_number)
                            if stack:
                                stack[-1].children.append(case_node)
                            else:
                                roots.append(case_node)
                            stack.append(case_node)
                        last_case_major = major_value
                node = Node(node_type, title, level, number, page_number, page_number)
                while stack and stack[-1].level >= level:
                    stack.pop()
                if stack:
                    stack[-1].children.append(node)
                else:
                    roots.append(node)
                stack.append(node)
                continue

            # Chapter divider pages frequently split “第X章” and the chapter
            # name into two distant, oversized OCR lines.
            if (
                stack
                and stack[-1].type == "chapter"
                and not stack[-1].children
                and float(line.get("height") or 0) >= float(page.get("height") or 1) * 0.03
                and len(text) <= 30
            ):
                index = sum(item.type == "chapter" for item in roots[:-1]) + 1
                number = chinese_number(index)
                stack[-1].number = number
                stack[-1].title = f"第{number}章 {text}"
                stack[-1].content.clear()
                stack[-1].page_end = page_number
                continue

            if not stack:
                if preface is None:
                    preface = Node("front_matter", "前置内容", 0, page_start=page_number, page_end=page_number)
                    roots.append(preface)
                target = preface
            else:
                target = stack[-1]
            target.content.append(text)
            target.page_end = page_number
            for ancestor in stack[:-1]:
                ancestor.page_end = page_number

    # The printed book numbers cases continuously. Circled numbers are usually
    # recognized as 0 or punctuation, so restore reliable sequential IDs after
    # the hierarchy has been built.
    case_index = 0

    def renumber_cases(nodes: list[Node]) -> None:
        nonlocal case_index
        for node in nodes:
            if node.type == "case":
                case_index += 1
                node.number = str(case_index)
                node.title = re.sub(r"^\d+\s+", f"{case_index} ", node.title)
            renumber_cases(node.children)

    renumber_cases(roots)
    return roots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Input scanned PDF")
    parser.add_argument("output", type=Path, help="Structured JSON output")
    parser.add_argument("--raw-output", type=Path, help="OCR NDJSON output (defaults beside JSON)")
    parser.add_argument("--dpi", type=int, default=200, help="Render resolution; 200 keeps A4 pages below Windows OCR's limit")
    parser.add_argument("--language", default="zh-Hans-CN", help="Installed Windows OCR language tag")
    parser.add_argument("--first-page", type=int, default=1)
    parser.add_argument("--last-page", type=int)
    parser.add_argument("--keep-images", type=Path, help="Keep rendered page images in this directory")
    parser.add_argument("--reuse-raw", action="store_true", help="Skip rendering/OCR and organize an existing raw output")
    args = parser.parse_args()

    pdf = args.pdf.resolve()
    if not pdf.is_file():
        parser.error(f"PDF does not exist: {pdf}")
    for executable in ("pdfinfo", "pdftoppm", "powershell"):
        if shutil.which(executable) is None:
            parser.error(f"Required executable is not available: {executable}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw_output = args.raw_output or args.output.with_suffix(".ocr.ndjson")
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    page_count = get_page_count(pdf)
    last_page = min(args.last_page or page_count, page_count)
    if args.first_page < 1 or args.first_page > last_page:
        parser.error("Invalid page range")

    if not args.reuse_raw:
        if args.keep_images:
            image_dir = args.keep_images.resolve()
            image_dir.mkdir(parents=True, exist_ok=True)
            render_pdf(pdf, image_dir, args.dpi, args.first_page, last_page)
            run_windows_ocr(image_dir, raw_output, args.language)
        else:
            with tempfile.TemporaryDirectory(prefix="pdf_ocr_") as temp_dir:
                image_dir = Path(temp_dir)
                render_pdf(pdf, image_dir, args.dpi, args.first_page, last_page)
                run_windows_ocr(image_dir, raw_output, args.language)
    elif not raw_output.is_file():
        parser.error(f"--reuse-raw requires an existing file: {raw_output}")

    pages = read_ndjson(raw_output)
    document = {
        "schema_version": "1.0",
        "source": {
            "file": pdf.name,
            "path": str(pdf),
            "page_count": page_count,
            "processed_pages": [args.first_page, last_page],
            "ocr_engine": "Windows.Media.Ocr",
            "ocr_language": args.language,
            "render_dpi": args.dpi,
            "raw_ocr": str(raw_output.resolve()),
        },
        "document": [node.as_dict() for node in organize(pages)],
    }
    with args.output.open("w", encoding="utf-8") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Wrote {args.output} ({len(pages)} OCR pages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
