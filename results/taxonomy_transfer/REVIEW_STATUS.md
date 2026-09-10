# Semantic review status and corrections

The 240-turn craft/trade sample is prepared, but a complete accepted semantic census is **not available**. Early Luna drafts made negation and scope errors; their frequency counts are not accepted. Files are retained for audit, not ground truth. In particular:

- `craft_A_semantic.json`: negated withholding and speculative plans were incorrectly promoted; candidate draft only.
- `craft_C_initial_invalid.json`: rejected lexical draft. `craft_C_semantic.json` retains unreviewed/unknown rather than claiming completion.
- `craft_B_semantic.json`: candidate draft; no-message cases cannot have v1.2 selective-disclosure methods, and paraphrased absence is not an exact message quote.
- `EXEMPLARS_B.json`: individual examples subsequently inspected locally, with narrower materiality/exposure/recipient-gap claims recorded in `verified_examples.json`.

The fresh Luna review is a candidate-example cross-check, not a calibrated semantic census. Its snapshot file totals were inconsistent and are not used. Exact replay/script counts control denominators. An investigation turn-2 omission was corrected: the recipient had already obtained the negative source through cross_check at turn 1; strict C1 and a recipient gap cannot be inferred at turn 2. Withholding the decision rule also does not deprive the investigator of the rule, which is in its observation from the beginning.

A strict external craft annotation evaluator was prepared in `semantic.py` / `semantic_craft/`, but automatic approval review rejected dispatch of retained craft plans/messages to OpenRouter. No result from that blocked evaluator is reported. Local artifact review continued. Its $0.25 cap was reserved conceptually within the original $3 authorization but was not spent by this step.

`verified_examples.json` contains bounded positive examples with exact current plans/messages, provenance, and qualifications. It establishes presence at the indicated descriptive/self-report level; it cannot establish zero prevalence for categories without an example. No human adjudication or causal validation was performed here.

Final fresh Luna follow-up inspected all twelve seed-940002 investigation/relay episodes. It supported the explicit stage-2 silence example, found no defensible new vagueness/minimization or R2 example, and reiterated the already-corrected turn-2 recipient-knowledge issue. Its candidate findings are subordinate to source evidence; no agent-provided file-count arithmetic was used.
