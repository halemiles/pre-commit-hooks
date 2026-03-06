"""Tests for fix_yaml_document_start hook."""
import os
import textwrap

import pytest

from hooks.fix_yaml_document_start import fix_yaml_document_start, main


def write_file(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding='utf-8')
    return str(path)


class TestFixYamlDocumentStart:
    def test_adds_document_start_when_missing(self, tmp_path):
        filename = write_file(tmp_path, 'test.yaml', 'key: value\n')
        retval = fix_yaml_document_start(filename)
        assert retval == 1
        assert (tmp_path / 'test.yaml').read_text(encoding='utf-8') == '---\nkey: value\n'

    def test_no_change_when_document_start_present(self, tmp_path):
        content = '---\nkey: value\n'
        filename = write_file(tmp_path, 'test.yaml', content)
        retval = fix_yaml_document_start(filename)
        assert retval == 0
        assert (tmp_path / 'test.yaml').read_text(encoding='utf-8') == content

    def test_adds_document_start_to_empty_file(self, tmp_path):
        filename = write_file(tmp_path, 'empty.yaml', '')
        retval = fix_yaml_document_start(filename)
        assert retval == 1
        assert (tmp_path / 'empty.yaml').read_text(encoding='utf-8') == '---\n'

    def test_adds_document_start_to_file_with_comments(self, tmp_path):
        content = '# A comment\nkey: value\n'
        filename = write_file(tmp_path, 'test.yaml', content)
        retval = fix_yaml_document_start(filename)
        assert retval == 1
        assert (tmp_path / 'test.yaml').read_text(encoding='utf-8') == '---\n' + content

    def test_no_change_when_document_start_with_comment(self, tmp_path):
        content = '--- # document start\nkey: value\n'
        filename = write_file(tmp_path, 'test.yaml', content)
        retval = fix_yaml_document_start(filename)
        assert retval == 0

    def test_main_returns_zero_for_already_fixed_file(self, tmp_path):
        filename = write_file(tmp_path, 'test.yaml', '---\nkey: value\n')
        assert main([filename]) == 0

    def test_main_returns_nonzero_for_file_needing_fix(self, tmp_path):
        filename = write_file(tmp_path, 'test.yaml', 'key: value\n')
        assert main([filename]) == 1

    def test_main_multiple_files(self, tmp_path):
        f1 = write_file(tmp_path, 'a.yaml', 'key: value\n')
        f2 = write_file(tmp_path, 'b.yaml', '---\nkey: value\n')
        assert main([f1, f2]) == 1

    def test_main_no_files(self):
        assert main([]) == 0
