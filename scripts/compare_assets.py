#!/usr/bin/env python3
"""Compare root assets against template assets with flexible output."""
from __future__ import annotations

import argparse
import json
import hashlib
import sys
from pathlib import Path
from typing import List

COLOR_RESET = "\033[0m"
COLORS = {
    "identical": "\033[33m",    # yellow
    "missing": "\033[31m",      # red
    "different": "\033[32m",    # green
    "additional": "\033[36m",   # cyan
}


def hash_file(path: Path) -> str:
    """Return the SHA256 hash of a file."""
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def gather_files(base: Path) -> List[Path]:
    """Return all files under *base* recursively."""
    return sorted(p for p in base.rglob("*") if p.is_file())


def compare_assets(root_assets: Path, template_assets: Path) -> dict:
    root_files = gather_files(root_assets)
    template_files = gather_files(template_assets)

    root_map = {p.relative_to(root_assets): p for p in root_files}
    template_map = {p.relative_to(template_assets): p for p in template_files}

    results: List[dict] = []
    counts = {"identical": 0, "missing": 0, "different": 0, "additional": 0}

    all_paths = sorted(set(root_map) | set(template_map))

    for rel_path in all_paths:
        root_file = root_map.get(rel_path)
        template_file = template_map.get(rel_path)

        if root_file and template_file:
            if hash_file(root_file) == hash_file(template_file):
                status = "identical"
            else:
                status = "different"
        elif template_file and not root_file:
            status = "missing"
        else:
            status = "additional"

        counts[status] += 1
        results.append({"status": status, "path": str(rel_path)})

    total = sum(counts.values())
    identical_ratio = (counts["identical"] / total * 100) if total else 100.0

    return {
        "total": total,
        "counts": counts,
        "identical_ratio": identical_ratio,
        "results": results,
    }


SUMMARY_ORDER = ("identical", "different", "missing", "additional")


def build_text_report(report: dict, use_color: bool) -> str:
    total = report["total"]
    counts = report["counts"]
    lines: List[str] = [
        f"Compared {total} root files; {counts['identical']} identical ({report['identical_ratio']:.2f}%)."
    ]

    for entry in report["results"]:
        status = entry["status"]
        label = status.upper().ljust(9)
        color = COLORS[status] if use_color else ""
        reset = COLOR_RESET if use_color else ""
        lines.append(f"{color}[{label}] {entry['path']}{reset}")

    lines.append("")
    lines.append("Summary:")
    for key in SUMMARY_ORDER:
        count = counts[key]
        percent = (count / total * 100) if total else 0.0
        color = COLORS[key] if use_color else ""
        reset = COLOR_RESET if use_color else ""
        title = key.title().ljust(9)
        lines.append(f"{color}{title}{reset}: {count} files ({percent:.2f}%)")

    return "\n".join(lines)


def build_json_report(report: dict) -> str:
    payload = {
        "total": report["total"],
        "identical_ratio": report["identical_ratio"],
        "counts": report["counts"],
        "files": report["results"],
    }
    return json.dumps(payload, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the current pack's assets with the template pack.")
    parser.add_argument(
        "root",
        nargs="?",
        default=Path.cwd() / "assets",
        type=Path,
        help="Path to the root pack's assets directory (default: ./assets)",
    )
    parser.add_argument(
        "template",
        nargs="?",
        default=Path(".packs/template-1.21.11/assets"),
        type=Path,
        help="Path to the template pack's assets directory",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=("text", "json"),
        default="text",
        help="Choose the output format (default: text)",
    )
    parser.add_argument(
        "-in",
        "--input",
        dest="input_path",
        type=Path,
        default=None,
        help="Full path to the source assets to compare (overrides the positional root)",
    )
    parser.add_argument(
        "-to",
        "--template",
        dest="template_path",
        type=Path,
        default=None,
        help="Full path to the template assets to compare (overrides the positional template)",
    )
    parser.add_argument(
        "-r",
        "--report",
        "--report-file",
        "--output-file",
        dest="report_file",
        type=Path,
        help="Write the report to this file instead of stdout",
    )
    args = parser.parse_args()

    root_assets = (args.input_path or args.root).resolve()
    template_assets = (args.template_path or args.template).resolve()

    if not root_assets.exists():
        raise SystemExit(f"Root assets folder not found: {root_assets}")
    if not template_assets.exists():
        raise SystemExit(f"Template assets folder not found: {template_assets}")

    report = compare_assets(root_assets, template_assets)

    if args.format == "json":
        output_text = build_json_report(report)
    else:
        color_enabled = args.report_file is None and sys.stdout.isatty()
        output_text = build_text_report(report, use_color=color_enabled)

    if args.report_file:
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(output_text + "\n", encoding="utf-8")
    else:
        print(output_text)


if __name__ == "__main__":
    main()
