#!/usr/bin/env python3
"""
Utility to scan and remove emoji characters from a codebase.

- --check: scans and lists files containing emojis
- --write: removes emojis in-place from text files

It skips common dependency and build directories and attempts to avoid binary files.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Iterable, List, Set, Tuple


EXCLUDED_DIR_NAMES: Set[str] = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".cache",
    "target",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "vendor",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".DS_Store",
}


def compile_emoji_pattern() -> re.Pattern[str]:
    # Comprehensive set of ranges and code points that cover modern emoji.
    # This approach removes emoji code points, ZWJ, variation selectors, and tag/combining marks used in emoji sequences.
    ranges = (
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        "\U0001F680-\U0001F6FF"  # Transport and Map
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols, Symbols for Legacy Computing, etc.
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U0001FB00-\U0001FBFF"  # Symbols for Legacy Computing Supplement (future use)
        "\U0001F1E6-\U0001F1FF"  # Regional Indicator Symbols (flags)
        "\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement (includes some emoji-like)
        "\u2600-\u26FF"          # Miscellaneous Symbols
        "\u2700-\u27BF"          # Dingbats
        "\u2300-\u23FF"          # Misc Technical (wrenches, etc.)
        "\uFE00-\uFE0F"          # Variation Selectors (VS15..VS16)
        "\u200D"                  # Zero Width Joiner
        "\u20E3"                  # Combining Enclosing Keycap
        "\U000E0020-\U000E007F"  # Tags (used in flag sequences)
    )

    # Put all ranges and singletons into a character class.
    pattern = re.compile(f"[{ranges}]", flags=re.UNICODE)
    return pattern


EMOJI_RE: re.Pattern[str] = compile_emoji_pattern()


def is_probably_binary(path: str, sample_size: int = 4096) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(sample_size)
        if b"\x00" in chunk:
            return True
        # Heuristic: if many bytes are outside typical text ranges and not UTF-8 decodable, treat as binary
        try:
            chunk.decode("utf-8")
            return False
        except UnicodeDecodeError:
            return True
    except Exception:
        return True


def iter_text_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories in-place
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIR_NAMES]
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            # Skip obvious binary extensions quickly
            lower = filename.lower()
            if lower.endswith((
                ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
                ".pdf", ".zip", ".gz", ".tgz", ".bz2", ".xz", ".7z",
                ".mp3", ".mp4", ".mov", ".avi", ".ogg", ".wav",
                ".woff", ".woff2", ".ttf", ".eot", ".otf",
                ".class", ".jar", ".war", ".ear",
                ".so", ".dll", ".dylib", ".bin",
                ".pyc", ".pyo",
            )):
                continue
            if is_probably_binary(path):
                continue
            yield path


def file_contains_emoji(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if EMOJI_RE.search(line):
                    return True
        return False
    except Exception:
        return False


def remove_emojis_from_text(text: str) -> str:
    return EMOJI_RE.sub("", text)


def process_file(path: str) -> Tuple[bool, int]:
    """Returns (changed, removed_count)."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            original = f.read()
        new_text = remove_emojis_from_text(original)
        if new_text != original:
            removed_count = len(original) - len(new_text)
            with open(path, "w", encoding="utf-8", errors="ignore", newline="") as f:
                f.write(new_text)
            return True, removed_count
        return False, 0
    except Exception:
        return False, 0


def scan(root: str) -> List[str]:
    affected: List[str] = []
    for path in iter_text_files(root):
        if file_contains_emoji(path):
            affected.append(path)
    return affected


def write_changes(root: str) -> Tuple[int, int]:
    changed_files = 0
    removed_total = 0
    for path in iter_text_files(root):
        changed, removed = process_file(path)
        if changed:
            changed_files += 1
            removed_total += removed
            print(f"cleaned: {path} (-{removed} chars)")
    return changed_files, removed_total


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Scan and remove emoji characters from a codebase")
    parser.add_argument("--root", default=os.getcwd(), help="Root directory to scan (default: cwd)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Only scan and list files containing emojis")
    group.add_argument("--write", action="store_true", help="Remove emojis from files in-place")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2

    if args.check:
        affected = scan(root)
        if affected:
            print("Files containing emojis:")
            for p in affected:
                print(p)
            print(f"Total files with emojis: {len(affected)}")
            return 1
        else:
            print("No emojis found.")
            return 0

    if args.write:
        changed_files, removed_total = write_changes(root)
        print(f"Removed emojis from {changed_files} files, total characters removed: {removed_total}")
        # Return non-zero only if nothing changed? Keep 0 for success.
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

