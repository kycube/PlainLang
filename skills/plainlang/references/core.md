# PlainLang core

These are the 18 rules that matter most. Use them when drafting, and as the checklist for the judgment calls the script can't make. Rule ids point to the full entries in `rules.md`.

## Structure

1. **Lead with the point.** Put the answer, result, or decision in the first sentence. Background comes after. (ORD-01)
2. **Keep only what the reader needs.** Cut history, background, and nice-to-know detail, or link to it. Three or four main ideas per section at most. (CLR-15)
3. **Say what to do, how, and why** when the text asks for action. (CLR-16)
4. **Put bad news where readers will see it.** Failures, crashes, and caveats go first, not in a trailing clause. (ORD-03)
5. **Say what you checked.** Replace "done", "verified", and "works" with what you did and observed, and name what you didn't check. (ORD-04, CLR-18)

## Sentences

6. **Make the actor the subject and the action the verb.** "I fixed the bug," not "The bug has been fixed." (ACT-01 to ACT-04)
7. **One main point per sentence.** Aim for 25 words or fewer; split sentences with semicolons plus parentheticals. Semicolons are fine used sparingly. (ORD-02)
8. **Start with what the reader knows; end with what's new.** Keep the verb close to its subject. (CLR-02)
9. **Say it positively,** and put conditions before instructions: "If the cache is full, clear it." (CLR-05, CLR-03)

## Words

10. **Use the plain, specific word:** "use" for "utilize", "before" for "prior to", "the GPU" for "the compute substrate". Name the file, the number, or the person. (CLR-07, WORD-02, CLR-06)
11. **Define terms and abbreviations the first time,** and don't coin labels the reader hasn't seen. (CLR-08, WORD-03)
12. **Drop AI-marker words and jargon,** such as "delve", "robust", "seamless", "pivotal", "testament", "leverage", "showcase", "circle back", and "best practices". (WORD-06, WORD-07, WORD-12)
13. **Cut intensifiers, stacked hedges, and filler,** such as "really", "genuinely", "could potentially", "in order to", and "it's worth noting". (WORD-08, FILL-04, FILL-07)

## Templates to avoid

14. **No contrast setups or aphorisms:** "It's not X, it's Y", "That's it.", and lines like "The gap is real but modest." State the claim. (TPL-01, TPL-03)
15. **No inflated significance or trailing -ing commentary:** "a pivotal moment", ", ensuring robust security". Give the concrete effect or cut it. (TPL-05, TPL-06)
16. **No chatbot framing:** no "Certainly!", "Great question!", "I hope this helps!", "Here's the thing:", or restating the request. (FILL-01 to FILL-03, FILL-10)

## Format

17. **Match structure to length.** Write a short answer as a paragraph, without headers or bullets. Bold only what must not be missed. (FMT-05, FMT-02, FMT-03)
18. **Punctuate deliberately.** Use em dashes exceedingly sparingly, at most one per piece. Use the serial comma in every list of three or more. Put a comma before "but" only when it joins two full clauses. Skip emoji. Use at most one exclamation point, and none in error messages. (FMT-01, FMT-14, FMT-13, FMT-06, FMT-12)

## When revising

- Keep the meaning, every fact, every number, all code, and all links.
- Don't invent a number, name, source, or result to make a claim concrete. If a claim needs a specific you don't have, cut the claim or say what's missing.
- Don't add new claims, caveats, or sections.
- Quoted text keeps its original wording.
