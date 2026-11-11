"""Behavior tests for scripts/plainlang.py."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "plainlang" / "scripts" / "plainlang.py"


def run(*args, stdin=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True)


class CLI(unittest.TestCase):
    def test_json_report_shape(self):
        res = run("check", "--json", "--fail-on", "none", "--text", "Certainly! Let's delve into it.")
        self.assertEqual(res.returncode, 0)
        rep = json.loads(res.stdout)
        self.assertEqual(set(rep), {"summary", "metrics", "findings", "source"})
        rules = {f["rule"] for f in rep["findings"]}
        self.assertIn("FILL-02", rules)
        self.assertIn("WORD-06", rules)

    def test_exit_code_on_error(self):
        self.assertEqual(run("check", "--text", "Let's delve into it.").returncode, 1)
        self.assertEqual(run("check", "--text", "Run the tests before you merge.").returncode, 0)

    def test_stdin(self):
        res = run("check", "--json", "--fail-on", "none", stdin="This robust fix works.")
        self.assertIn("WORD-06", {f["rule"] for f in json.loads(res.stdout)["findings"]})

    def test_code_and_quotes_are_masked(self):
        text = 'Use `robust_mode` here.\n\n```\nleverage = delve()\n```\n\nAvoid "Great question!" openers.'
        rep = json.loads(run("check", "--json", "--fail-on", "none", "--text", text).stdout)
        self.assertEqual([f for f in rep["findings"] if f["severity"] == "error"], [])
        rep = json.loads(run("check", "--json", "--fail-on", "none", "--include-code", "--include-quotes", "--text", text).stdout)
        self.assertTrue({"WORD-06", "FILL-03"} <= {f["rule"] for f in rep["findings"]})

    def test_substitution_suggestion(self):
        rep = json.loads(run("check", "--json", "--fail-on", "none", "--text", "Please utilize the form prior to Monday.").stdout)
        subs = {f["match"].lower(): f.get("suggestion") for f in rep["findings"] if f["rule"] == "CLR-07"}
        self.assertEqual(subs.get("prior to"), "before")

    def test_only_and_skip(self):
        rep = json.loads(run("check", "--json", "--fail-on", "none", "--only", "WORD-06", "--text", "Certainly! A robust plan.").stdout)
        self.assertEqual({f["rule"] for f in rep["findings"]}, {"WORD-06"})
        rep = json.loads(run("check", "--json", "--fail-on", "none", "--skip", "words", "--text", "A robust plan.").stdout)
        self.assertNotIn("WORD-06", {f["rule"] for f in rep["findings"]})

    def test_fiction_is_opt_in(self):
        text = "She took a deep breath."
        self.assertNotIn("FIC-01", run("check", "--fail-on", "none", "--text", text).stdout)
        self.assertIn("FIC-01", run("check", "--fail-on", "none", "--include-fiction", "--text", text).stdout)

    def test_threshold_rules(self):
        one = json.loads(run("check", "--json", "--fail-on", "none", "--text", "It works—mostly.").stdout)
        two = json.loads(run("check", "--json", "--fail-on", "none", "--text", "It works—mostly—today.").stdout)
        self.assertNotIn("FMT-01", {f["rule"] for f in one["findings"]})
        self.assertIn("FMT-01", {f["rule"] for f in two["findings"]})

    def test_explain_and_rules(self):
        self.assertIn("serial", run("explain", "FMT-14").stdout.lower())
        self.assertEqual(run("explain", "NOPE-1").returncode, 2)
        self.assertGreater(len(json.loads(run("rules", "--json").stdout)), 80)


if __name__ == "__main__":
    unittest.main()
