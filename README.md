# pre-commit-hooks

A collection of [pre-commit](https://pre-commit.com/) hooks that automatically fix common
[yamllint](https://yamllint.readthedocs.io/) issues in YAML files.

## Hooks

### `fix-yaml-document-start`

Adds the `---` document-start marker at the very beginning of any YAML file that is
missing it.

**Fixes yamllint rule:** `document-start`

### `fix-yaml-comment-spacing`

Ensures YAML comments comply with yamllint's `comments` rule by:

- Adding a space after `#` when it is missing (e.g. `#comment` → `# comment`).
- Ensuring at least two spaces separate inline content from its comment
  (e.g. `key: value # note` → `key: value  # note`).

**Fixes yamllint rule:** `comments` (`min-spaces-after: 1`, `min-spaces-from-content: 2`)

### `check-csharp-xml-comments`

Checks that every member declared inside a C# `interface` block has an XML
documentation comment (`/// <summary>…</summary>`).  The hook fails (exits
non-zero) for each member that is missing an XML doc comment, printing the
file name, line number, and the offending member signature.

**Example – good (will pass):**

```csharp
public interface IUserService
{
    /// <summary>
    /// Checks whether the supplied user ID is valid.
    /// </summary>
    /// <param name="userId"></param>
    /// <returns></returns>
    bool CheckUserId(int userId);
}
```

**Example – bad (will fail):**

```csharp
public interface IUserService
{
    bool CheckUserId(int userId);  // ← missing XML doc comment
}
```

## Usage

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/halemiles/pre-commit-hooks
    rev: v0.1.0  # use the ref you want to point at
    hooks:
      - id: fix-yaml-document-start
      - id: fix-yaml-comment-spacing
      - id: check-csharp-xml-comments
```

Run the hooks against staged files:

```bash
pre-commit run --all-files
```

## Integration Testing

The `examples/` directory contains two YAML files you can use to see the hooks
in action immediately:

| File | Description |
|------|-------------|
| `examples/bad.yaml` | Missing `---` marker **and** bad comment spacing — the hooks will fix both issues |
| `examples/good.yaml` | Already correctly formatted — the hooks will make no changes |

A `.pre-commit-config.yaml` is included in this repository so you can run the
hooks locally against these example files **without** needing a published
release.

### Why do I see "Skipped"?

The hooks use `types: [yaml]`, so pre-commit only passes `.yaml` / `.yml`
files to them.  If your project contains no YAML files the hooks will always
be reported as **Skipped**.  Use the steps below to verify the hooks are
working correctly.

### Running the hooks locally

```bash
# 1. Install pre-commit (if not already installed)
pip install pre-commit

# 2. Install the hook entry-points from this repo
pip install -e .

# 3. Run all hooks against every file in the repo
pre-commit run --all-files
```

Expected output:

```
Fix YAML Document Start......Failed
- hook id: fix-yaml-document-start
- files were modified by this hook

Fixed document-start marker in: examples/bad.yaml

Fix YAML Comment Spacing......Failed
- hook id: fix-yaml-comment-spacing
- files were modified by this hook

Fixed comment spacing in: examples/bad.yaml
```

> **Note:** "Failed" here means the hooks *modified* a file (which is their
> job).  Run `pre-commit run --all-files` a **second time** and both hooks
> will report **Passed**, confirming the fixes are correct.

## Development

Install in editable mode and run the test suite:

```bash
pip install -e .
pip install pytest
pytest tests/ -v
```