"""Fix YAML comment spacing to satisfy yamllint's 'comments' rule.

Two classes of issues are corrected:

1. **Missing space after '#'** – ``#comment`` → ``# comment``
   (yamllint: *comments* rule, ``min-spaces-after: 1``)

2. **Insufficient space before an inline comment** – ``value #comment`` or
   ``value # comment`` → ``value  # comment``
   (yamllint: *comments* rule, ``min-spaces-from-content: 2``)

Lines where '#' appears inside a single- or double-quoted string are left
unchanged.  Shebang lines (``#!``) and YAML directives (``%``) are also
preserved.
"""
from __future__ import annotations

import argparse
import re
import sys
from typing import Sequence

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Matches a '#' that starts a comment on an otherwise blank line (possibly
# with leading whitespace).
_PURE_COMMENT_RE = re.compile(r'^(\s*)(#)((?!\s|#|!).*)?$')

# Matches content followed by a '#' that introduces an inline comment.
# Group 1 = everything before the comment (non-empty, ends with non-space
# after stripping trailing space used as separator).
# Group 2 = spaces between content and '#' (may be 0-1, indicating too few)
# Group 3 = the '#' and everything after it
_INLINE_COMMENT_RE = re.compile(r'^(.+\S)(\s{0,1})(#.*)$')


def _fix_comment_body(comment: str) -> str:
    """Ensure *comment* (starting with '#') has a space after the '#'.

    Preserves ``##``, ``#!``, and already-correct comments.
    """
    if len(comment) < 2:
        # bare '#' – nothing to do
        return comment
    if comment[1] in (' ', '#', '!'):
        # already has a space, is a ## marker, or is a shebang-style token
        return comment
    return '# ' + comment[1:]


def _line_has_unquoted_hash(line: str) -> bool:
    """Return True if *line* contains a '#' outside of any quoted string."""
    in_single = False
    in_double = False
    for ch in line:
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == '#' and not in_single and not in_double:
            return True
    return False


def fix_line(line: str) -> str:
    """Return *line* with comment spacing corrected (trailing newline preserved)."""
    # Preserve the original line ending
    eol = '\n' if line.endswith('\n') else ''
    stripped = line.rstrip('\n')

    # Skip shebang, YAML directives, and lines without any '#'
    if stripped.startswith('#!') or stripped.startswith('%') or '#' not in stripped:
        return line

    # ------------------------------------------------------------------ #
    # Pure comment lines  (optional whitespace, then '#', then text)      #
    # ------------------------------------------------------------------ #
    pure_match = _PURE_COMMENT_RE.match(stripped)
    if pure_match:
        indent = pure_match.group(1)
        body = pure_match.group(2) + (pure_match.group(3) or '')
        fixed_body = _fix_comment_body(body)
        return f'{indent}{fixed_body}{eol}'

    # ------------------------------------------------------------------ #
    # Inline comment                                                       #
    # ------------------------------------------------------------------ #
    # Only attempt to fix if the '#' is outside any quoted string
    if not _line_has_unquoted_hash(stripped):
        return line

    inline_match = _INLINE_COMMENT_RE.match(stripped)
    if inline_match:
        content = inline_match.group(1)
        spaces = inline_match.group(2)
        comment = inline_match.group(3)

        fixed_comment = _fix_comment_body(comment)
        # Ensure at least two spaces separate content from the comment
        separator = spaces if len(spaces) >= 2 else '  '
        return f'{content}{separator}{fixed_comment}{eol}'

    return line


def fix_yaml_comment_spacing(filename: str) -> int:
    """Fix comment spacing in *filename*.

    Returns 1 if the file was changed, 0 otherwise.
    """
    with open(filename, encoding='utf-8') as fh:
        original_lines = fh.readlines()

    fixed_lines = [fix_line(line) for line in original_lines]

    if fixed_lines == original_lines:
        return 0

    with open(filename, 'w', encoding='utf-8') as fh:
        fh.writelines(fixed_lines)

    print(f'Fixed comment spacing in: {filename}')
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Fix YAML comment spacing to satisfy yamllint.',
    )
    parser.add_argument('filenames', nargs='*', help='YAML files to fix')
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        retval |= fix_yaml_comment_spacing(filename)
    return retval


if __name__ == '__main__':
    sys.exit(main())
