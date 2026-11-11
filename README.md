# PlainLang

PlainLang is a skill that agents call to check and revise prose. It flags unclear writing and the habits that make text read as machine-written, then gives the agent rules and examples for fixing them.

It has three parts:

- `skills/plainlang/scripts/plainlang.py` runs 85 rules against text and reports each hit with its line, rule, and fix. It uses only the Python standard library.
- `skills/plainlang/data/rules.json` holds the rules. Each has a "don't write" and "write instead" pair, examples, exceptions, and sources.
- `skills/plainlang/SKILL.md` tells the agent when to check, how to read the report, and how to revise without changing the meaning.

## Quick start

```bash
python3 skills/plainlang/scripts/plainlang.py check draft.md
```

Sample output for a two-line draft:

```
== draft.md: 2 error(s), 1 warning(s)
1:1 ERROR FILL-02 No chatbot openers or sign-offs: "Certainly!"
1:25 ERROR WORD-06 Replace AI-marker words: "robust"
2:8 WARN  CLR-07 Use the short, familiar word: "prior to" -> before
```

Add `--json` for machine-readable output. Run `plainlang.py --help` for the rest.

## Install as a skill

**Claude Code plugin:** run `/plugin marketplace add kycube/PlainLang`, then `/plugin install plainlang@plainlang`.

**Any agent that reads skill folders:** copy `skills/plainlang/` into the agent's skills directory (for Claude Code, `~/.claude/skills/plainlang/`).

**Without a skills system:** give the agent `skills/plainlang/references/core.md` as a style guide, and let it run the checker as a tool.

## What the rules cover

The rules come from two kinds of sources.

Plain-language guidance tells writers what to do. PlainLang draws on the federal plain-language guidelines, the SEC Plain English Handbook, GOV.UK, CDC's Clear Communication Index and Simply Put, NIH's Clear & Simple, HHS Health Literacy Online, the Microsoft, Google, and Mailchimp style guides, and the work of Williams, Pinker, Orwell, Zinsser, Flesch, and Gopen & Swan.

Catalogs of AI-writing tells say what to avoid. These include Wikipedia's Signs of AI writing, Humanizer, Declaude, stop-slop, no-ai-slop, avoid-ai-writing, and the Antislop research, along with Zhizhuo Zhou's study of unclear Claude Code replies.

Rules fall into eight groups:

| Group | Prefix | Covers |
|---|---|---|
| Clarity principles | CLR | Reader focus, plain words, numbers, actions, links |
| Actors and actions | ACT | Who does what; hidden verbs; passive voice |
| Word choice | WORD | Jargon, AI-marker words, noun stacks, slogans |
| Rhetorical templates | TPL | Contrast setups, aphorisms, inflated significance |
| Filler and chat habits | FILL | Throat-clearing, sign-offs, hedges, flattery |
| Order, emphasis, and claims | ORD | Main point first, sentence length, evidence |
| Formatting and output | FMT | Structure, emphasis, punctuation, placeholders |
| Fiction | FIC | Stock phrases and names (opt-in) |

`skills/plainlang/references/principles.md` explains why each group exists, with the research behind it. `skills/plainlang/references/examples.md` collects 50 examples that editors, award juries, and researchers singled out as good or bad.

## Limits

- The patterns are heuristics. Errors are usually worth fixing; warnings need judgment. Seven rules have no pattern and rely on the agent's review.
- The checker skips code, URLs, block quotes, and text in double quotes, so quoting a bad phrase to discuss it doesn't trigger a rule.
- Readability scores in the report are prompts, not targets. They don't measure whether readers understand the text.
- Inclusive and bias-free language is out of scope.

## Repository layout

```
skills/plainlang/
  SKILL.md              agent instructions
  scripts/plainlang.py  checker
  data/                 rules.json, principles.json, exemplars.json (source of truth)
  references/           core.md (hand-written) and generated rules, principles, and examples
tools/build_docs.py     regenerates references/*.md from data/
tests/                  data, pattern, and CLI tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) to add or change a rule.

## License

The code and the rule text written for this project are MIT-licensed. Short quotations and examples from other sources keep their original terms; see [NOTICE.md](NOTICE.md).
