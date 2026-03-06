"""Tests for fix_yaml_comment_spacing hook."""
import pytest

from hooks.fix_yaml_comment_spacing import fix_line, fix_yaml_comment_spacing, main


def write_file(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding='utf-8')
    return str(path)


class TestFixLine:
    # ------------------------------------------------------------------
    # Pure comment lines – missing space after '#'
    # ------------------------------------------------------------------
    def test_adds_space_after_hash_on_comment_line(self):
        assert fix_line('#comment\n') == '# comment\n'

    def test_adds_space_after_hash_with_leading_indent(self):
        assert fix_line('  #comment\n') == '  # comment\n'

    def test_no_change_when_space_already_present(self):
        assert fix_line('# comment\n') == '# comment\n'

    def test_no_change_for_double_hash(self):
        assert fix_line('## heading\n') == '## heading\n'

    def test_no_change_for_shebang(self):
        assert fix_line('#!shebang\n') == '#!shebang\n'

    def test_no_change_for_bare_hash(self):
        assert fix_line('#\n') == '#\n'

    def test_preserves_lines_without_hash(self):
        assert fix_line('key: value\n') == 'key: value\n'

    def test_preserves_yaml_directive(self):
        assert fix_line('%YAML 1.2\n') == '%YAML 1.2\n'

    # ------------------------------------------------------------------
    # Inline comments – spacing between content and '#'
    # ------------------------------------------------------------------
    def test_adds_two_spaces_before_inline_comment(self):
        assert fix_line('key: value # comment\n') == 'key: value  # comment\n'

    def test_no_change_when_two_spaces_already_present(self):
        assert fix_line('key: value  # comment\n') == 'key: value  # comment\n'

    def test_no_change_when_more_than_two_spaces_before_comment(self):
        assert fix_line('key: value   # comment\n') == 'key: value   # comment\n'

    def test_inline_with_no_space_before_hash(self):
        assert fix_line('key: value#comment\n') == 'key: value  # comment\n'

    def test_inline_also_fixes_body_spacing(self):
        # Only 1 space before '#' AND missing space after '#'
        assert fix_line('key: value #comment\n') == 'key: value  # comment\n'

    # ------------------------------------------------------------------
    # Lines with '#' inside quoted strings (must not be changed)
    # ------------------------------------------------------------------
    def test_no_change_for_hash_in_double_quoted_string(self):
        line = 'key: "value # not a comment"\n'
        assert fix_line(line) == line

    def test_no_change_for_hash_in_single_quoted_string(self):
        line = "key: 'value # not a comment'\n"
        assert fix_line(line) == line

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------
    def test_no_trailing_newline_preserved(self):
        # Last line without newline
        assert fix_line('#comment') == '# comment'

    def test_empty_line(self):
        assert fix_line('\n') == '\n'

    def test_whitespace_only_line(self):
        assert fix_line('   \n') == '   \n'


class TestFixYamlCommentSpacing:
    def test_file_with_no_issues_unchanged(self, tmp_path):
        content = '---\n# good comment\nkey: value  # also good\n'
        filename = write_file(tmp_path, 'test.yaml', content)
        retval = fix_yaml_comment_spacing(filename)
        assert retval == 0
        assert (tmp_path / 'test.yaml').read_text(encoding='utf-8') == content

    def test_file_with_missing_hash_space_fixed(self, tmp_path):
        filename = write_file(tmp_path, 'test.yaml', '---\n#bad comment\n')
        retval = fix_yaml_comment_spacing(filename)
        assert retval == 1
        assert (tmp_path / 'test.yaml').read_text(encoding='utf-8') == '---\n# bad comment\n'

    def test_file_with_inline_spacing_fixed(self, tmp_path):
        filename = write_file(tmp_path, 'test.yaml', '---\nkey: value # comment\n')
        retval = fix_yaml_comment_spacing(filename)
        assert retval == 1
        assert (tmp_path / 'test.yaml').read_text(encoding='utf-8') == '---\nkey: value  # comment\n'

    def test_main_returns_zero_for_clean_file(self, tmp_path):
        filename = write_file(tmp_path, 'test.yaml', '---\n# clean\n')
        assert main([filename]) == 0

    def test_main_returns_nonzero_for_dirty_file(self, tmp_path):
        filename = write_file(tmp_path, 'test.yaml', '#dirty\n')
        assert main([filename]) == 1

    def test_main_no_files(self):
        assert main([]) == 0
