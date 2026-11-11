#!/usr/bin/env python3
"""PlainLang checker: flag unclear writing and AI-writing tells.

Standard library only. Reads rules from ../data/rules.json.

Usage:
  plainlang.py check [FILE ...] [--text TEXT] [--json] [--fail-on error|warn|none]
                     [--only IDS_OR_CATEGORIES] [--skip IDS_OR_CATEGORIES]
                     [--include-fiction] [--include-code]
  plainlang.py rules [--category CAT] [--json]
  plainlang.py explain RULE_ID [--json]

Reads stdin when no FILE or --text is given (or when FILE is "-").
Exit status for "check": 1 if any finding is at or above --fail-on (default: error), else 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
SEVERITY_RANK = {"warn": 1, "error": 2}

# Rules whose hits signal word-level AI tells; used for the rewrite-vs-patch advice.
WORD_CATEGORIES = {"words", "filler", "templates"}

# Substitution entries too common or context-dependent to flag automatically.
SUB_SKIP = {
    "it is", "there is", "there are", "available", "required", "request", "provide", "access",
    "guidelines", "reduce", "detect", "inform", "medication", "maintain", "evaluate", "monitor",
    "outcome", "exposure", "initiative", "integrate", "intervention", "severe", "toxic", "transmit",
    "extract", "implement", "perform", "permit", "previous", "portion", "option", "operate", "observe",
    "remain", "objective", "proceed", "reflect", "require", "validate", "type", "forward", "delete",
    "address", "advise", "accurate", "effect", "benefit", "attempt", "employ", "encounter", "designate",
    "determine", "elect", "allocate", "appropriate", "apparent", "capability", "establishment",
    "the use of", "time period", "the month of", "your office", "establish",
}


# ---------------------------------------------------------------- loading

def load_rules(path: Path | None = None) -> tuple[dict, list[dict]]:
    data = json.loads((path or DATA / "rules.json").read_text(encoding="utf-8"))
    return data["meta"], data["rules"]


@dataclass
class Rule:
    raw: dict
    regexes: list[re.Pattern] = field(default_factory=list)
    sub_regex: re.Pattern | None = None
    sub_map: dict[str, str] = field(default_factory=dict)

    @property
    def id(self) -> str:
        return self.raw["id"]


def compile_rule(r: dict) -> Rule:
    flags = re.MULTILINE | (0 if r.get("case_sensitive") else re.IGNORECASE)
    rule = Rule(raw=r, regexes=[re.compile(p, flags) for p in r.get("patterns", [])])
    subs = r.get("substitutions") or {}
    keys: list[str] = []
    for key, repl in subs.items():
        for k in re.sub(r"\([^)]*\)", "", key).split(","):
            k = k.strip()
            if len(k) > 2 and re.fullmatch(r"[a-z][a-z '-]*", k, re.I) and k.lower() not in SUB_SKIP:
                keys.append(k)
                rule.sub_map[k.lower()] = repl
    if keys:
        keys.sort(key=len, reverse=True)
        alt = "|".join(re.escape(k).replace(r"\ ", r"\s+") for k in keys)
        rule.sub_regex = re.compile(r"\b(?:" + alt + r")\b", re.IGNORECASE)
    return rule


# ---------------------------------------------------------------- masking

def mask(text: str, include_code: bool = False, include_quotes: bool = False) -> str:
    """Blank out code, URLs, blockquotes, and quoted strings, keeping offsets and newlines.

    Quoted strings are treated as mentions, not use: quoting a bad phrase to discuss it
    should not trigger the rule. Pass include_quotes=True to scan them anyway.
    """
    def blank(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))

    out = text
    if not include_code:
        out = re.sub(r"^```.*?^```[^\n]*$", blank, out, flags=re.M | re.S)
        out = re.sub(r"^~~~.*?^~~~[^\n]*$", blank, out, flags=re.M | re.S)
        out = re.sub(r"`[^`\n]+`", blank, out)
    out = re.sub(r"https?://\S+", blank, out)
    out = re.sub(r"^\s*>.*$", blank, out, flags=re.M)
    if not include_quotes:
        out = re.sub(r"\"[^\"\n]{1,300}\"", blank, out)
        out = re.sub(r"\u201c[^\u201d\n]{1,300}\u201d", blank, out)
    return out


def paragraphs(text: str) -> list[tuple[int, str]]:
    """(offset, paragraph) pairs, split on blank lines."""
    result, pos = [], 0
    for part in re.split(r"(\n\s*\n)", text):
        if part and not re.fullmatch(r"\n\s*\n", part):
            result.append((pos, part))
        pos += len(part)
    return result


def line_col(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    col = offset - (text.rfind("\n", 0, offset) + 1) + 1
    return line, col


# ---------------------------------------------------------------- metrics

SENT_RX = re.compile(r"[^.!?\n]+(?:[.!?]+|$)", re.M)


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and n > 1 and not w.endswith(("le", "ee", "ye")):
        n -= 1
    return max(1, n)


def metrics(prose: str) -> dict:
    sentences = [s.strip() for s in SENT_RX.findall(prose) if len(re.findall(r"[A-Za-z0-9']+", s)) >= 3]
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", prose)
    lengths = [len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", s)) for s in sentences]
    syl = sum(syllables(w) for w in words)
    fre = None
    if sentences and words:
        fre = round(206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syl / len(words)), 1)
    long_sentences = [s for s, n in zip(sentences, lengths) if n > 25]
    paras = [p for _, p in paragraphs(prose) if p.strip()]
    long_paras = [p for p in paras if len([s for s in SENT_RX.findall(p) if s.strip()]) > 5]
    return {
        "words": len(words),
        "sentences": len(sentences),
        "avg_sentence_words": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        "max_sentence_words": max(lengths) if lengths else 0,
        "sentences_over_25_words": len(long_sentences),
        "paragraphs": len(paras),
        "paragraphs_over_5_sentences": len(long_paras),
        "em_dashes": prose.count("—"),
        "flesch_reading_ease": fre,
        "note": "Metrics are prompts to look, not verdicts. Readability scores don't measure comprehension.",
    }


# ---------------------------------------------------------------- checking

def select_rules(rules: list[dict], only: list[str], skip: list[str], include_fiction: bool) -> list[dict]:
    def hit(r: dict, keys: list[str]) -> bool:
        return any(k.upper() == r["id"].upper() or k.lower() == r["category"] or r["id"].upper().startswith(k.upper() + "-") for k in keys)

    selected = []
    for r in rules:
        if only and not hit(r, only):
            continue
        if skip and hit(r, skip):
            continue
        if r["category"] == "fiction" and not include_fiction and not (only and hit(r, only)):
            continue
        selected.append(r)
    return selected


LISTY = re.compile(r"^\s*(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|\|)")


def is_structured(par: str) -> bool:
    """True for paragraphs that are mostly list items, headings, or table rows."""
    lines = [ln for ln in par.splitlines() if ln.strip()]
    return bool(lines) and sum(1 for ln in lines if LISTY.match(ln)) * 2 >= len(lines)


def check_text(text: str, rules: list[dict], include_code: bool = False, include_quotes: bool = False) -> dict:
    prose = mask(text, include_code, include_quotes)
    findings = []
    for raw in rules:
        rule = compile_rule(raw)
        source = text if raw.get("scan") == "raw" else prose
        scope = raw.get("scope", "sentence")
        minimum = max(1, int(raw.get("min_matches", 1)))
        units = [(b, u) for b, u in paragraphs(source) if not is_structured(u)] if scope == "paragraph" else [(0, source)]
        for base, unit in units:
            matches = []
            if rule.sub_regex:
                matches += [(m, rule.sub_map.get(re.sub(r"\s+", " ", m.group(0).lower()))) for m in rule.sub_regex.finditer(unit)]
            for rx in rule.regexes:
                matches += [(m, None) for m in rx.finditer(unit) if m.group(0).strip()]
            if len(matches) < minimum:
                continue
            seen = set()
            covered_to = -1
            for m, sub in sorted(matches, key=lambda t: (t[0].start(), -t[0].end())):
                if m.start() < covered_to:
                    continue
                covered_to = m.end()
                txt = m.group(0)
                lead = len(txt) - len(txt.lstrip(" \t\n.!?;:,"))
                start = base + m.start() + lead
                if start in seen:
                    continue
                seen.add(start)
                line, col = line_col(text, start)
                f = {
                    "rule": raw["id"],
                    "name": raw["name"],
                    "category": raw["category"],
                    "severity": raw.get("severity", "warn"),
                    "line": line,
                    "column": col,
                    "match": re.sub(r"\s+", " ", txt[lead:].strip())[:160],
                    "fix": raw.get("do", ""),
                }
                if sub:
                    f["suggestion"] = sub
                if minimum > 1:
                    f["threshold"] = f"{len(matches)} matches; flags at {minimum} per {scope}"
                findings.append(f)
    findings.sort(key=lambda f: (f["line"], f["column"], -SEVERITY_RANK.get(f["severity"], 0)))
    word_hits = sum(1 for f in findings if f["category"] in WORD_CATEGORIES)
    categories = {f["category"] for f in findings}
    m = metrics(prose)
    summary = {
        "errors": sum(1 for f in findings if f["severity"] == "error"),
        "warnings": sum(1 for f in findings if f["severity"] == "warn"),
        "rules_hit": sorted({f["rule"] for f in findings}),
        "advice": (
            "Rewrite from the main point instead of patching: 5+ word-level hits across 3+ categories."
            if word_hits >= 5 and len(categories) >= 3
            else "Patch the flagged spots."
            if findings
            else "No pattern hits. Still review the judgment-only rules."
        ),
        "judgment_only_rules": [r["id"] for r in rules if not r.get("patterns") and not r.get("substitutions")],
    }
    return {"summary": summary, "metrics": m, "findings": findings}


# ---------------------------------------------------------------- output

def print_report(report: dict, label: str) -> None:
    s, m = report["summary"], report["metrics"]
    print(f"== {label}: {s['errors']} error(s), {s['warnings']} warning(s)")
    for f in report["findings"]:
        extra = f" -> {f['suggestion']}" if f.get("suggestion") else ""
        thr = f" [{f['threshold']}]" if f.get("threshold") else ""
        print(f"{f['line']}:{f['column']} {f['severity'].upper():5} {f['rule']} {f['name']}: \"{f['match']}\"{extra}{thr}")
    print(
        f"-- {m['words']} words, {m['sentences']} sentence(s), avg {m['avg_sentence_words']} words/sentence, "
        f"max {m['max_sentence_words']}, {m['sentences_over_25_words']} over 25, "
        f"{m['paragraphs_over_5_sentences']} long paragraph(s), {m['em_dashes']} em dash(es), "
        f"Flesch {m['flesch_reading_ease']}"
    )
    print(f"-- {s['advice']}")
    print(f"-- Judgment-only rules to review by hand: {', '.join(s['judgment_only_rules'])}")


def read_inputs(files: list[str], text: str | None) -> list[tuple[str, str]]:
    if text is not None:
        return [("text", text)]
    if not files or files == ["-"]:
        return [("stdin", sys.stdin.read())]
    return [(f, sys.stdin.read() if f == "-" else Path(f).read_text(encoding="utf-8")) for f in files]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="plainlang", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="check text against the rules")
    c.add_argument("files", nargs="*")
    c.add_argument("--text")
    c.add_argument("--json", action="store_true")
    c.add_argument("--fail-on", choices=["error", "warn", "none"], default="error")
    c.add_argument("--only", default="", help="comma-separated rule ids, prefixes (CLR), or categories")
    c.add_argument("--skip", default="", help="comma-separated rule ids, prefixes, or categories")
    c.add_argument("--include-fiction", action="store_true")
    c.add_argument("--include-code", action="store_true", help="also scan code blocks and inline code")
    c.add_argument("--include-quotes", action="store_true", help="also scan text inside double quotes")
    c.add_argument("--rules-file", type=Path)

    l = sub.add_parser("rules", help="list rules")
    l.add_argument("--category")
    l.add_argument("--json", action="store_true")
    l.add_argument("--rules-file", type=Path)

    e = sub.add_parser("explain", help="show one rule in full")
    e.add_argument("rule_id")
    e.add_argument("--json", action="store_true")
    e.add_argument("--rules-file", type=Path)

    a = ap.parse_args(argv)
    _, rules = load_rules(a.rules_file)

    if a.cmd == "rules":
        sel = [r for r in rules if not a.category or r["category"] == a.category]
        if a.json:
            print(json.dumps([{k: r[k] for k in ("id", "category", "severity", "name")} for r in sel], indent=1))
        else:
            for r in sel:
                kind = "pattern" if (r.get("patterns") or r.get("substitutions")) else "judgment"
                print(f"{r['id']:8} {r['severity']:5} {kind:8} {r['name']}")
        return 0

    if a.cmd == "explain":
        r = next((r for r in rules if r["id"].upper() == a.rule_id.upper()), None)
        if not r:
            print(f"Unknown rule: {a.rule_id}", file=sys.stderr)
            return 2
        if a.json:
            print(json.dumps(r, indent=1, ensure_ascii=False))
        else:
            print(f"{r['id']} {r['name']} ({r['category']}, {r['severity']})\n")
            print(f"Don't: {r['dont']}\nDo: {r['do']}\nWhy: {r['rationale']}")
            if r.get("exceptions"):
                print(f"Exceptions: {r['exceptions']}")
            for ex in r.get("examples", [])[:4]:
                print(f"\n  - {ex['bad']}\n  + {ex['better']}")
        return 0

    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    sel = select_rules(rules, split(a.only), split(a.skip), a.include_fiction)
    reports = []
    worst = 0
    for label, text in read_inputs(a.files, a.text):
        rep = check_text(text, sel, a.include_code, a.include_quotes)
        rep["source"] = label
        reports.append(rep)
        for f in rep["findings"]:
            worst = max(worst, SEVERITY_RANK.get(f["severity"], 0))
    if a.json:
        print(json.dumps(reports[0] if len(reports) == 1 else reports, indent=1, ensure_ascii=False))
    else:
        for rep in reports:
            print_report(rep, rep["source"])
    threshold = {"error": 2, "warn": 1, "none": 99}[a.fail_on]
    return 1 if worst >= threshold else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
