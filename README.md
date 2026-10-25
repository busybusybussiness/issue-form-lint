# Issue Form Lint

A small GitHub Action that fails a pull request when a GitHub issue form
(`.github/ISSUE_TEMPLATE/*.yml`) breaks the documented issue-form schema.

Without a check, a broken form fails silently for the person trying to report
a bug: GitHub only shows the validation error when the form is opened in the UI.

## What it checks

- top-level `name`, `description` and `body` are present and non-empty
- every `body` item has a valid `type` (`markdown`, `textarea`, `input`,
  `dropdown`, `checkboxes`, `upload`)
- every input has an `attributes.label`
- `id` values are unique within a form (checked even on items with an invalid type)
- `dropdown` has a non-empty `options` list; `checkboxes` options each have a `label`
- `markdown` has `attributes.value`
- YAML parse errors are reported as errors, not crashes

## Usage

```yaml
# .github/workflows/lint-issue-forms.yml
name: Lint issue forms
on:
  pull_request:
    paths: ['.github/ISSUE_TEMPLATE/**']
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: <owner>/issue-form-lint@v1   # replace after publishing
        with:
          path: .github/ISSUE_TEMPLATE       # optional, this is the default
```

Exit codes: `0` all forms pass · `1` at least one form has an error · `2` no forms found.

## Limits (not checked)

- Live GitHub UI behaviour is **not** tested. The rules follow the GitHub docs page
  "Syntax for issue forms", which GitHub marks as public preview and subject to change.
- Schema rules GitHub enforces but this tool does not check: the `validations` block,
  label length limits, unknown extra keys.
- Tested only with local fixtures (one known-good, one with 7 planted faults).
  Not yet run against third-party repositories.

## Local run

```
pip install pyyaml==6.0.3
python check_issue_forms.py .github/ISSUE_TEMPLATE
python -m unittest test_check_issue_forms
```

## Licence

MIT. See LICENSE.
