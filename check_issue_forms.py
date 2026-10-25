#!/usr/bin/env python3
"""gh-issue-form-lint: validate GitHub issue-form YAML files.

Checks the rules stated on GitHub's "syntax for issue forms" docs page
(fetched 2026-10-24; page is marked public preview and may change):
  - top-level keys name, description, body are present and non-empty
  - body is a non-empty list of mappings
  - each body item has a type in {markdown, textarea, input, dropdown, checkboxes, upload}
  - markdown items have attributes.value
  - every other type has attributes.label
  - dropdown has a non-empty options list of strings
  - checkboxes has a non-empty options list of mappings, each with a label
  - optional item id values are unique within a form
Anything not listed above is NOT checked (UNKNOWN until verified against the live UI).

Usage: python check_issue_forms.py [DIR_OR_FILE ...]   (default: .github/ISSUE_TEMPLATE)
Exit 0 = all forms pass, 1 = at least one error, 2 = no form files found or bad usage.
"""
import os
import sys
import glob

import yaml

ALLOWED_TYPES = {"markdown", "textarea", "input", "dropdown", "checkboxes", "upload"}


def check_form(path, text):
    """Return a list of error strings for one form file (empty = pass)."""
    errors = []

    def err(msg):
        errors.append(f"{path}: {msg}")

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return [f"{path}: YAML parse error: {str(exc).splitlines()[0]}"]

    if not isinstance(data, dict):
        return [f"{path}: top level must be a mapping"]

    for key in ("name", "description"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            err(f"'{key}' is required and must be a non-empty string")

    body = data.get("body")
    if not isinstance(body, list) or not body:
        err("'body' is required and must be a non-empty list")
        return errors

    seen_ids = set()
    for index, item in enumerate(body):
        where = f"body[{index}]"
        if not isinstance(item, dict):
            err(f"{where} must be a mapping")
            continue
        item_id = item.get("id")
        if item_id is not None:
            if item_id in seen_ids:
                err(f"{where} duplicate id {item_id!r}")
            seen_ids.add(item_id)
        item_type = item.get("type")
        if item_type not in ALLOWED_TYPES:
            err(f"{where} has type {item_type!r}; allowed: {sorted(ALLOWED_TYPES)}")
            continue
        attributes = item.get("attributes")
        if not isinstance(attributes, dict):
            err(f"{where} ({item_type}) needs an 'attributes' mapping")
            continue

        if item_type == "markdown":
            if not attributes.get("value"):
                err(f"{where} (markdown) needs attributes.value")
        else:
            label = attributes.get("label")
            if not isinstance(label, str) or not label.strip():
                err(f"{where} ({item_type}) needs a non-empty attributes.label")

        if item_type == "dropdown":
            options = attributes.get("options")
            if not isinstance(options, list) or not options:
                err(f"{where} (dropdown) needs a non-empty attributes.options list")
            elif not all(isinstance(o, str) for o in options):
                err(f"{where} (dropdown) options must all be strings")

        if item_type == "checkboxes":
            options = attributes.get("options")
            if not isinstance(options, list) or not options:
                err(f"{where} (checkboxes) needs a non-empty attributes.options list")
            else:
                for j, opt in enumerate(options):
                    if not isinstance(opt, dict) or not str(opt.get("label", "")).strip():
                        err(f"{where} (checkboxes) options[{j}] needs a label")

    return errors


def find_forms(targets):
    files = []
    for target in targets:
        if os.path.isdir(target):
            for pattern in ("*.yml", "*.yaml"):
                files.extend(glob.glob(os.path.join(target, pattern)))
        elif os.path.isfile(target):
            files.append(target)
    return sorted(files)


def main(argv):
    targets = argv[1:] or [os.path.join(".github", "ISSUE_TEMPLATE")]
    files = find_forms(targets)
    if not files:
        print(f"no issue-form files found in {targets}")
        return 2
    all_errors = []
    for path in files:
        with open(path, encoding="utf-8") as handle:
            errors = check_form(path, handle.read())
        status = "FAIL" if errors else "PASS"
        print(f"{status} {path}")
        for line in errors:
            print(f"  - {line}")
        all_errors.extend(errors)
    print(f"checked {len(files)} form(s); {len(all_errors)} error(s)")
    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
