# Contributing

The JSON files in `skills/plainlang/data/` are the source of truth. The Markdown files in `skills/plainlang/references/` (except `core.md`) are generated from them.

## Change or add a rule

1. Edit `skills/plainlang/data/rules.json`. Each rule needs:
   - `id` with its group's prefix (for example `CLR-22`), plus `category`, `name`, and `severity` (`error` or `warn`).
   - `dont` and `do`: what not to write and what to write instead.
   - `rationale`, `exceptions`, `detect` (signals for a human or agent reviewer), and `source`.
   - `patterns`: Python regular expressions. Leave the list empty for a judgment-only rule.
   - `examples`: at least two `bad` and `better` pairs. Mark examples taken from a named source with a note that starts "Human-identified:".
   - Optional: `min_matches` and `scope` (`sentence`, `paragraph`, or `text`) for rules that only fire when a pattern repeats; `case_sensitive`; `scan: "raw"` to match before code and quotes are masked.
2. Regenerate the references:
   ```bash
   python3 tools/build_docs.py
   ```
3. Run the tests:
   ```bash
   python3 -m unittest discover -s tests
   ```
   The tests check that every "bad" example triggers its rule, that no "better" example does, and that no "better" example triggers any error-level rule. If a pattern can't catch an example, add it to `KNOWN_MISSES` in `tests/test_rules.py` and say why in the commit message.
4. Check your own prose:
   ```bash
   python3 skills/plainlang/scripts/plainlang.py check README.md CONTRIBUTING.md
   ```

## Writing patterns

- Prefer a precise pattern that misses some cases over a broad one that fires on good writing. A false alarm costs the agent a revision.
- Test the pattern against the "better" examples of every rule, not only its own. The test suite does this for error-level rules.
- Use `min_matches` when a single hit is normal but a cluster is a tell (for example, AI-favored words or lists of three).

## House style

US English, the serial comma in every list, em dashes exceedingly sparingly, semicolons sparingly, and a comma before "but" only when it joins two full clauses.
