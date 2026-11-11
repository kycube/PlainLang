---
name: plainlang
description: Check and revise prose for clarity and AI-writing tells (ClaudeSpeak, slop) using the PlainLang rules and checker script. Use when asked to check, edit, tighten, de-slop, or plain-language a draft, reply, doc, PR description, or message, or to review text before it is sent.
---

# PlainLang

PlainLang checks text against 85 rules drawn from plain-language guidance (federal plain-language guidelines, SEC, GOV.UK, CDC, NIH, Williams, Pinker, Orwell, and Gopen & Swan) and from catalogs of AI-writing tells (Wikipedia's Signs of AI writing, Humanizer, stop-slop, avoid-ai-writing, Antislop). It can report problems or revise the text.

## Files

- `scripts/plainlang.py`: the checker. Python 3.9+, standard library only.
- `references/core.md`: the 18 rules that matter most, plus revision ground rules. Read this every time.
- `references/rules.md`: every rule with examples. Read the entries for rules the checker flags, and for the judgment-only rules.
- `references/principles.md`, `references/examples.md`: the evidence and human-identified examples behind the rules. Read only when asked why a rule exists.
- `data/*.json`: machine-readable rules, principles, and examples.

## Workflow

1. **Get the text into a file** (or pipe it on stdin).
2. **Run the checker:**
   ```bash
   python3 scripts/plainlang.py check draft.md --json
   ```
   Useful options:
   - `--only CLR,ORD-01` or `--skip format` narrows the rules.
   - `--include-fiction` adds the fiction rules.
   - `--include-code` and `--include-quotes` scan code and quoted text, which the checker skips by default.
   - `--fail-on warn` makes warnings fail the exit code.
   - `python3 scripts/plainlang.py explain WORD-06` prints one rule in full.
3. **Read the report.**
   - `error`: fix it unless an exception in `rules.md` applies.
   - `warn`: look, then decide. Patterns are heuristics, and some warnings will be false alarms.
   - `suggestion`: a plain-word replacement from the substitution list. Check that it fits the context.
   - `summary.advice`: when it says to rewrite from the main point, don't patch word by word; restate the core message in one sentence and rebuild around it.
   - `metrics`: sentence length, paragraph length, em-dash count, and Flesch score. Treat them as prompts, not targets.
4. **Review the judgment-only rules** listed in `summary.judgment_only_rules` against the text yourself, using `references/core.md`. The script can't check these (for example: give an example for every abstract claim, keep only what the reader needs).
5. **Revise** only when asked to revise or edit, not just check. Follow the ground rules at the end of `core.md`. Keep every fact, number, link, and code block. Don't invent specifics or add claims.
6. **Re-run the checker** on the revision. Repeat until there are no errors and every remaining warning is a deliberate choice.

## Reporting back

When asked only to check, list the problems by rule, most severe first, with the exact text and a one-line fix, and leave the text unchanged.

When asked to revise, return the revised text, then a short list of what changed and any warnings you kept on purpose. If a claim needed a fact you didn't have, say so instead of inventing one.

## Scope

- English prose: replies, docs, READMEs, pull request descriptions, commit messages, emails, and web copy. Fiction rules (FIC) run only with `--include-fiction`.
- Out of scope: inclusive and bias-free language, grammar and spelling correctness beyond the rules here, and fact-checking.
- The rules follow US English and these house choices: the serial comma in every list, em dashes exceedingly sparingly, semicolons sparingly, and a comma before "but" only between two full clauses.
