"""Check that C# interface members have XML documentation comments.

Every member declared inside an ``interface`` block should be preceded by at
least one ``///`` XML doc comment line (typically ``/// <summary>``).  Any
member that is missing such a comment is reported and the hook exits with a
non-zero status so that pre-commit blocks the commit.
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import Sequence

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches the ``interface`` keyword followed by an identifier.
_INTERFACE_RE = re.compile(r'\binterface\s+\w')

# Matches a line that is (or starts with) a ``///`` XML doc comment.
_XML_DOC_RE = re.compile(r'^\s*///')

# Matches string literal contents (single- or double-quoted, with escape
# handling) so they can be stripped before counting braces/parentheses.
_STRING_CONTENT_RE = re.compile(r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_strings(line: str) -> str:
    """Replace string literal contents in *line* with empty strings.

    This is a best-effort helper to prevent braces and parentheses inside
    string literals from distorting the depth-counting heuristics.
    Verbatim (``@"..."``) and multi-line interpolated strings are not fully
    handled, but the approach covers the vast majority of real-world cases.
    """
    return _STRING_CONTENT_RE.sub('""', line)


def _strip_line_comment(line: str) -> str:
    """Return *line* with any trailing ``//`` single-line comment removed.

    Only removes comments whose ``//`` token is outside quoted strings.
    """
    in_single = False
    in_double = False
    for idx, ch in enumerate(line):
        if ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '/' and not in_single and not in_double:
            if idx + 1 < len(line) and line[idx + 1] == '/':
                return line[:idx]
    return line


def _count_block_comment_delta(line: str) -> tuple[int, int]:
    """Return ``(opens, closes)`` – the number of ``/*`` and ``*/`` tokens
    in *line* that are outside single-line and double-quoted strings."""
    clean = _strip_strings(line)
    opens = clean.count('/*')
    closes = clean.count('*/')
    return opens, closes


def _is_member_line(stripped: str) -> bool:
    """Return True if *stripped* looks like an interface member declaration.

    Lines that are blank, braces, comments, attributes, preprocessor
    directives, or generic constraints are excluded.
    """
    if not stripped:
        return False
    # XML doc comment – handled separately
    if stripped.startswith('///'):
        return False
    # Regular comments (single-line and block comment lines)
    if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
        return False
    # Lone braces (opening/closing blocks)
    if stripped in ('{', '}'):
        return False
    # Attributes  e.g. [Obsolete], [HttpGet]
    if stripped.startswith('['):
        return False
    # Preprocessor directives  e.g. #region, #pragma
    if stripped.startswith('#'):
        return False
    # Generic type constraints  e.g. ``where T : class``
    if stripped.lower().startswith('where '):
        return False
    return True


# ---------------------------------------------------------------------------
# Core checker
# ---------------------------------------------------------------------------

def check_csharp_xml_comments(filename: str) -> int:
    """Check *filename* for interface members missing XML doc comments.

    Returns 1 if any member lacks an XML doc comment, 0 otherwise.
    """
    with open(filename, encoding='utf-8') as fh:
        lines = fh.readlines()

    errors: list[tuple[int, str]] = []
    i = 0
    in_block_comment = False  # tracks ``/* ... */`` block comment state

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Update block-comment state for this line.
        bc_opens, bc_closes = _count_block_comment_delta(line)
        if in_block_comment:
            if bc_closes > 0:
                in_block_comment = False
            i += 1
            continue

        if bc_opens > bc_closes:
            in_block_comment = True
            i += 1
            continue

        # Locate an interface declaration; ignore the keyword inside
        # single-line comments.
        if _INTERFACE_RE.search(line) and not stripped.startswith('//'):
            # Scan forward from the declaration line to find the opening '{'.
            # Strip strings and single-line comments before counting braces
            # to avoid false triggers from literals or comments.
            depth = 0
            body_start = -1
            scan_block_comment = False
            for k in range(i, len(lines)):
                scan_line = lines[k]
                s_opens, s_closes = _count_block_comment_delta(scan_line)

                if scan_block_comment:
                    if s_closes > 0:
                        scan_block_comment = False
                    continue

                if s_opens > s_closes:
                    scan_block_comment = True
                    continue

                clean = _strip_strings(_strip_line_comment(scan_line))
                depth += clean.count('{') - clean.count('}')
                if depth > 0:
                    body_start = k + 1
                    break

            if body_start == -1:
                # No opening brace found (e.g. partial / abstract declaration
                # split across files) – skip gracefully.
                i += 1
                continue

            # Walk through the interface body tracking brace depth and
            # parenthesis depth (to skip multi-line parameter lists).
            depth = 1
            paren_depth = 0
            had_xml_doc = False
            body_block_comment = False
            k = body_start

            while k < len(lines) and depth > 0:
                curr = lines[k]
                curr_stripped = curr.strip()

                b_opens, b_closes = _count_block_comment_delta(curr)
                if body_block_comment:
                    if b_closes > 0:
                        body_block_comment = False
                    k += 1
                    continue

                if b_opens > b_closes:
                    body_block_comment = True
                    k += 1
                    continue

                if depth == 1 and paren_depth == 0:
                    if _XML_DOC_RE.match(curr):
                        # Accumulate XML doc comment lines.
                        had_xml_doc = True
                    elif _is_member_line(curr_stripped):
                        # This is a member declaration (or the first line of
                        # a multi-line one).  Check for preceding XML doc.
                        if not had_xml_doc:
                            errors.append((k + 1, curr_stripped))
                        had_xml_doc = False

                clean = _strip_strings(_strip_line_comment(curr))
                depth += clean.count('{') - clean.count('}')
                paren_depth += clean.count('(') - clean.count(')')

                if depth <= 0:
                    break

                k += 1

            # Resume scanning after the end of this interface body.
            i = k + 1
        else:
            i += 1

    for lineno, member in errors:
        print(
            f'{filename}:{lineno}: '
            f'Missing XML documentation comment for interface member: {member}',
        )

    return 1 if errors else 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Check that every member of a C# interface has an XML '
            'documentation comment (/// <summary>…</summary>).'
        ),
    )
    parser.add_argument('filenames', nargs='*', help='C# files to check')
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        retval |= check_csharp_xml_comments(filename)
    return retval


if __name__ == '__main__':
    sys.exit(main())
