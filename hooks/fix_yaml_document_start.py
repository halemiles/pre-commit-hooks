"""Fix missing YAML document-start marker ('---').

Adds a '---' line at the very beginning of any YAML file that does not
already start with one.  Returns a non-zero exit code for every file that
was modified so that pre-commit can report the change.
"""
from __future__ import annotations

import argparse
import sys
from typing import Sequence


def fix_yaml_document_start(filename: str) -> int:
    """Add '---' to the top of *filename* if it is missing.

    Returns 1 if the file was changed, 0 otherwise.
    """
    with open(filename, encoding='utf-8') as fh:
        contents = fh.read()

    if contents.startswith('---'):
        return 0

    new_contents = '---\n' + contents
    with open(filename, 'w', encoding='utf-8') as fh:
        fh.write(new_contents)

    print(f'Fixed document-start marker in: {filename}')
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Add missing YAML document-start (---) markers.',
    )
    parser.add_argument('filenames', nargs='*', help='YAML files to fix')
    args = parser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        retval |= fix_yaml_document_start(filename)
    return retval


if __name__ == '__main__':
    sys.exit(main())
