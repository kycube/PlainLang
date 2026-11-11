"""Data and pattern tests for PlainLang. Run: python3 -m unittest discover -s tests"""
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "plainlang"
sys.path.insert(0, str(SKILL / "scripts"))
import plainlang as pl  # noqa: E402

META, RULES = pl.load_rules()
BY_ID = {r["id"]: r for r in RULES}
PRINCIPLES = json.loads((SKILL / "data" / "principles.json").read_text(encoding="utf-8"))
EXEMPLARS = json.loads((SKILL / "data" / "exemplars.json").read_text(encoding="utf-8"))

# "Don't write" examples the patterns are known not to catch. Most are described (not quoted)
# examples, judgment calls, or rules that only fire above a threshold (TPL-02, FMT-01).
# If you fix one, delete it here; if a change makes a new one, the test fails.
KNOWN_MISSES = {
    "CLR-05#3", "CLR-06#1", "CLR-08#1", "CLR-08#2", "CLR-08#3", "CLR-17#1", "CLR-17#2", "CLR-17#3",
    "CLR-21#2", "WORD-01#4", "WORD-02#4", "WORD-11#3", "WORD-11#4", "TPL-02#0", "TPL-02#1", "TPL-02#2",
    "FILL-07#5", "ORD-01#3", "ORD-02#2", "ORD-02#3", "ORD-02#4", "FMT-01#2", "FMT-04#3", "FMT-04#4",
    "FMT-05#1", "FMT-07#1",
}

REQUIRED = {"id", "category", "name", "severity", "dont", "do", "rationale", "patterns", "examples", "source"}


def fires(rule, text):
    return bool(pl.check_text(text, [rule], include_quotes=True)["findings"])


class DataShape(unittest.TestCase):
    def test_required_fields_and_values(self):
        cats = {c["id"] for c in META["categories"]}
        for r in RULES:
            with self.subTest(rule=r.get("id")):
                self.assertTrue(REQUIRED <= r.keys(), REQUIRED - r.keys())
                self.assertIn(r["category"], cats)
                self.assertIn(r["severity"], {"error", "warn"})
                self.assertIn(r.get("scope", "sentence"), {"sentence", "paragraph", "text"})
                self.assertGreaterEqual(len(r["examples"]), 2)
                prefix = next(c["prefix"] for c in META["categories"] if c["id"] == r["category"])
                self.assertTrue(r["id"].startswith(prefix + "-"))

    def test_unique_ids(self):
        ids = [r["id"] for r in RULES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_patterns_compile(self):
        for r in RULES:
            flags = re.M | (0 if r.get("case_sensitive") else re.I)
            for p in r["patterns"]:
                with self.subTest(rule=r["id"], pattern=p):
                    re.compile(p, flags)

    def test_cross_references(self):
        for p in PRINCIPLES:
            for rid in p.get("rule_ids", []):
                self.assertIn(rid, BY_ID, f"{p['id']} -> {rid}")
        for x in EXEMPLARS:
            for rid in x.get("rule_ids", []):
                self.assertIn(rid, BY_ID, f"{x['id']} -> {rid}")


class Examples(unittest.TestCase):
    def test_bad_examples_fire_their_rule(self):
        for r in RULES:
            if not (r["patterns"] or r.get("substitutions")):
                continue
            for i, e in enumerate(r["examples"]):
                key = f"{r['id']}#{i}"
                with self.subTest(example=key):
                    if key in KNOWN_MISSES:
                        continue
                    self.assertTrue(fires(r, e["bad"]), f"{key} not caught: {e['bad']!r}")

    def test_known_misses_are_still_misses(self):
        for key in KNOWN_MISSES:
            rid, i = key.split("#")
            with self.subTest(example=key):
                self.assertFalse(fires(BY_ID[rid], BY_ID[rid]["examples"][int(i)]["bad"]), f"{key} is caught now; remove it from KNOWN_MISSES")

    def test_better_examples_pass_their_rule(self):
        for r in RULES:
            for i, e in enumerate(r["examples"]):
                with self.subTest(example=f"{r['id']}#{i}"):
                    self.assertFalse(fires(r, e["better"]), e["better"])

    def test_better_examples_trigger_no_errors(self):
        for r in RULES:
            for i, e in enumerate(r["examples"]):
                errs = [f for f in pl.check_text(e["better"], RULES, include_quotes=True)["findings"] if f["severity"] == "error"]
                with self.subTest(example=f"{r['id']}#{i}"):
                    self.assertEqual(errs, [], e["better"])


class GeneratedDocs(unittest.TestCase):
    def test_references_up_to_date(self):
        res = subprocess.run([sys.executable, str(ROOT / "tools" / "build_docs.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
