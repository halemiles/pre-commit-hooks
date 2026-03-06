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

## Usage

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/halemiles/pre-commit-hooks
    rev: v0.1.0  # use the ref you want to point at
    hooks:
      - id: fix-yaml-document-start
      - id: fix-yaml-comment-spacing
```

Run the hooks against staged files:

```bash
pre-commit run --all-files
```

## Development

Install in editable mode and run the test suite:

```bash
pip install -e .
pip install pytest
pytest tests/ -v
```