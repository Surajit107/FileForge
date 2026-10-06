#!/usr/bin/env python3
"""CLI wrapper around the Markdown conversion pipeline.

Prefer the Django app for interactive use. This script remains for local
one-off conversions without starting the web server.

Usage (from repo root):
    python scripts/md_converter.py samples/example.md -f pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from engines.markdown.pipeline import OutputFormat, convert  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Markdown file to PDF and/or DOCX.",
    )
    parser.add_argument("input", type=Path, help="Path to the Markdown file (.md)")
    parser.add_argument(
        "-f",
        "--format",
        dest="formats",
        choices=("pdf", "docx", "both"),
        default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output file or directory. Extension is adjusted per format.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    formats: list[OutputFormat]
    if args.formats == "both":
        formats = ["pdf", "docx"]
    else:
        formats = [args.formats]

    try:
        outputs = convert(args.input, formats, args.output)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for path in outputs:
        print(f"Wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
