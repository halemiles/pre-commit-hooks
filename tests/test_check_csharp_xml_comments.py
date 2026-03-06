"""Tests for check_csharp_xml_comments hook."""
import pytest

from hooks.check_csharp_xml_comments import check_csharp_xml_comments, main


def write_file(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding='utf-8')
    return str(path)


class TestCheckCsharpXmlComments:
    # ------------------------------------------------------------------
    # Fully documented interfaces – should pass (return 0)
    # ------------------------------------------------------------------

    def test_single_method_with_summary_ok(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>Does something.</summary>\n'
            '    void DoSomething();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_multi_line_xml_comment_ok(self, tmp_path):
        """Reproduces the exact example from the problem statement."""
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>\n'
            '    /// This is a comment for my method\n'
            '    /// </summary>\n'
            '    /// <param name="userId"></param>\n'
            '    /// <returns></returns>\n'
            '    bool CheckUserId(int userId);\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_property_with_xml_comment_ok(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>Gets the name.</summary>\n'
            '    string Name { get; set; }\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_multiple_members_all_documented_ok(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>Method one.</summary>\n'
            '    void MethodOne();\n'
            '\n'
            '    /// <summary>Gets the value.</summary>\n'
            '    int Value { get; }\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_multiple_interfaces_all_documented_ok(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>A method.</summary>\n'
            '    void Method();\n'
            '}\n'
            '\n'
            'public interface IBar\n'
            '{\n'
            '    /// <summary>Another method.</summary>\n'
            '    void OtherMethod();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'Interfaces.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_empty_interface_ok(self, tmp_path):
        content = (
            'public interface IEmpty\n'
            '{\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IEmpty.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_no_interface_in_file_ok(self, tmp_path):
        content = (
            'public class Foo\n'
            '{\n'
            '    public void Bar() { }\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'Foo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_attribute_between_xml_doc_and_member_ok(self, tmp_path):
        """Attributes between the XML doc block and the member are allowed."""
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>A method.</summary>\n'
            '    [Obsolete]\n'
            '    void Method();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_interface_keyword_in_comment_ignored(self, tmp_path):
        """A comment mentioning 'interface' must not trigger a false check."""
        content = (
            '// This class implements the interface IFoo\n'
            'public class Foo\n'
            '{\n'
            '    public void Bar() { }\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'Foo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_interface_keyword_in_block_comment_ignored(self, tmp_path):
        """An 'interface' keyword inside a /* ... */ block comment is ignored."""
        content = (
            '/*\n'
            ' * This module implements the interface IFoo contract.\n'
            ' */\n'
            'public class Foo\n'
            '{\n'
            '    public void Bar() { }\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'Foo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    def test_string_with_braces_does_not_affect_depth(self, tmp_path):
        """Braces inside a string literal must not disturb brace-depth counting."""
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>Get a template string.</summary>\n'
            '    string GetTemplate();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 0

    # ------------------------------------------------------------------
    # Missing documentation – should fail (return 1)
    # ------------------------------------------------------------------

    def test_method_without_xml_doc_fails(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    void DoSomething();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 1

    def test_property_without_xml_doc_fails(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    string Name { get; set; }\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 1

    def test_second_member_missing_doc_fails(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>Method one.</summary>\n'
            '    void MethodOne();\n'
            '    void MethodTwo();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 1

    def test_multiple_interfaces_one_undocumented_fails(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>A method.</summary>\n'
            '    void Method();\n'
            '}\n'
            '\n'
            'public interface IBar\n'
            '{\n'
            '    void OtherMethod();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'Interfaces.cs', content)
        assert check_csharp_xml_comments(filename) == 1

    def test_regular_comment_does_not_satisfy_xml_doc_requirement(self, tmp_path):
        """A plain ``//`` comment is NOT an XML doc comment."""
        content = (
            'public interface IFoo\n'
            '{\n'
            '    // This is just a regular comment, not XML docs\n'
            '    void Method();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert check_csharp_xml_comments(filename) == 1

    # ------------------------------------------------------------------
    # main() entry-point tests
    # ------------------------------------------------------------------

    def test_main_returns_zero_for_clean_file(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    /// <summary>A method.</summary>\n'
            '    void Method();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert main([filename]) == 0

    def test_main_returns_nonzero_for_missing_docs(self, tmp_path):
        content = (
            'public interface IFoo\n'
            '{\n'
            '    void Method();\n'
            '}\n'
        )
        filename = write_file(tmp_path, 'IFoo.cs', content)
        assert main([filename]) == 1

    def test_main_no_files(self):
        assert main([]) == 0

    def test_main_multiple_files_one_bad(self, tmp_path):
        good = write_file(
            tmp_path,
            'IGood.cs',
            (
                'public interface IGood\n'
                '{\n'
                '    /// <summary>OK.</summary>\n'
                '    void Method();\n'
                '}\n'
            ),
        )
        bad = write_file(
            tmp_path,
            'IBad.cs',
            (
                'public interface IBad\n'
                '{\n'
                '    void Method();\n'
                '}\n'
            ),
        )
        assert main([good, bad]) == 1
