import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_issue_forms.py")
sys.path.insert(0, HERE)
import check_issue_forms as cif  # noqa: E402


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)


class FormRules(unittest.TestCase):
    def errors(self, text):
        return cif.check_form("f.yml", text)

    def test_good_form_passes(self):
        good = os.path.join(HERE, "fixtures", "good", "bug-report.yml")
        with open(good, encoding="utf-8") as h:
            self.assertEqual(self.errors(h.read()), [])

    def test_missing_top_level_keys(self):
        errs = self.errors("body:\n  - type: markdown\n    attributes:\n      value: hi\n")
        self.assertTrue(any("'name'" in e for e in errs))
        self.assertTrue(any("'description'" in e for e in errs))

    def test_bad_type_caught(self):
        errs = self.errors("name: a\ndescription: b\nbody:\n  - type: select\n    attributes:\n      label: x\n")
        self.assertTrue(any("type 'select'" in e for e in errs))

    def test_missing_label_caught(self):
        errs = self.errors("name: a\ndescription: b\nbody:\n  - type: input\n    attributes:\n      placeholder: p\n")
        self.assertTrue(any("attributes.label" in e for e in errs))

    def test_empty_dropdown_caught(self):
        errs = self.errors("name: a\ndescription: b\nbody:\n  - type: dropdown\n    attributes:\n      label: c\n      options: []\n")
        self.assertTrue(any("dropdown" in e and "options" in e for e in errs))

    def test_checkbox_option_needs_label(self):
        errs = self.errors("name: a\ndescription: b\nbody:\n  - type: checkboxes\n    attributes:\n      label: c\n      options:\n        - required: true\n")
        self.assertTrue(any("options[0] needs a label" in e for e in errs))

    def test_duplicate_id_caught(self):
        text = ("name: a\ndescription: b\nbody:\n"
                "  - type: input\n    id: x\n    attributes:\n      label: one\n"
                "  - type: input\n    id: x\n    attributes:\n      label: two\n")
        self.assertTrue(any("duplicate id 'x'" in e for e in self.errors(text)))

    def test_duplicate_id_caught_on_invalid_type_item(self):
        text = ("name: a\ndescription: b\nbody:\n"
                "  - type: input\n    id: x\n    attributes:\n      label: one\n"
                "  - type: select\n    id: x\n    attributes:\n      label: two\n")
        errs = self.errors(text)
        self.assertTrue(any("duplicate id 'x'" in e for e in errs))

    def test_yaml_parse_error_reported_not_raised(self):
        errs = self.errors("name: a\nbody\n  - x")
        self.assertTrue(errs and "YAML parse error" in errs[0])


class CLI(unittest.TestCase):
    def test_good_fixture_exit_0(self):
        r = run(os.path.join(HERE, "fixtures", "good"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_bad_fixtures_exit_1(self):
        r = run(os.path.join(HERE, "fixtures", "bad"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_empty_dir_exit_2(self):
        empty = os.path.join(HERE, "fixtures", "empty")
        os.makedirs(empty, exist_ok=True)
        r = run(empty)
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
