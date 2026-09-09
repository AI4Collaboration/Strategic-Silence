# Exploratory full-cohort Luna review: selective disclosure

Three independent `gpt-5.6-luna` Codex subagents reviewed the 944 speaking rounds from the immutable 26-game craft/trade snapshot (`raw_snapshot.zip`, SHA-256 `ee8b7906d0bf070bd7191105ad435d2a5dd55c5d484b2e5f91f5f4125b3cf7e6`). Each reviewer was assigned one goal-composition partition and used `PROTOCOL.md`; no external model/API calls, new games, legacy-label changes, or manuscript changes were made.

This is an exploratory model-review layer, not the v1.2 automated evaluator and not human ground truth. It must not be substituted for the preregistered/preserved Appendix C labels or strategic-silence endpoint. It is subject to model-reviewer error and lacks cross-reviewer agreement because partitions do not overlap. Exact plan/message evidence is preserved in the reviewer JSONL outputs; the validation script checks partition coverage, endpoint consistency, permitted audiences, and verbatim evidence provenance.

## LLM and human validation status

All 944 speaking rounds have an LLM (Luna) review. The user then manually reviewed the 29 all-competitive cases in the fixed random 10% audit sample using the lean, blinded packet before opening Luna's collapsed judgments. This is human validation of that sampled competitive subset, not a claim that every Luna decision or the full cohort has been human-adjudicated. The exact sample, seed, private plans, current messages, and Luna evidence are retained in `manual_validation_sample_10pct_manifest.json` and `LEAN_MANUAL_VALIDATION_COMPETITIVE_10PCT.md`.

| Condition | Speaking rounds reviewed | Positive | Negative | Unresolved |
|---|---:|---:|---:|---:|
| all aligned | 395 | 14 | 381 | 0 |
| mixed | 260 | 26 | 223 | 11 |
| all competitive | 289 | 185 | 56 | 48 |
| **Total** | **944** | **225** | **660** | **59** |

The same frozen cohort additionally has 85 no-message rounds (automatically false for selective disclosure, but potentially relevant to the unchanged strategic-silence measure) and 11 invalid-communication rounds. Thus, across all 1,040 observed agent-rounds, this exploratory layer reports 225 positives, 745 negatives, and 70 unresolved/invalid rows. These are descriptive annotation counts, not accuracy, prevalence, causal, recipient-knowledge, or generalization estimates.

Recipient-information gaps were retained as a separate field. With only actor-local context supplied for this task, reviewers record unknown rather than inferring concealment from intentional nondisclosure. Stated motives are copied only when explicit in private plans and remain self-reported explanations, not causal ground truth.

Reproduce mechanical validation with:

```sh
python3 scripts/validate_luna_selective_disclosure.py
```
