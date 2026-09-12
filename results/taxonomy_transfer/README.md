# Frozen taxonomy transfer: six-environment evidence

**These results support wider descriptive generalization of the withholding taxonomy.** The same frozen distinctions describe examples in native craft/trade, document delivery, evidence investigation, and incident response. Negotiation and project allocation add distinct task and incentive settings, but their reviewed traces do not provide clear new fact-specific withholding examples. Thus this is evidence of broader applicability, not six independent positive replications.

We collected **48 new episodes / 252 agent turns** across four stateful environments, with two seeds, GPT-5.4-mini and GPT-5.4, and aligned/mixed/competitive incentives. All episodes completed; every observation, action transition and final state replays exactly. There were two unsuccessful in-game actions, preserved as task failures rather than invalid model responses. Investigation decisions were correct in **12/12**, incident decisions in **11/12**.

The retained comparison data comprise **471 valid document-delivery trajectories** (plus 9 invalid) and **240 craft/trade agent-round packets from six games** selected from the earlier 26-game union. The craft sample does not have a complete accepted semantic census. Nine individually checked examples are supplied; their categories overlap and are not population frequency estimates.

| Distinction | What this evidence adds |
|---|---|
| Silence versus omission while speaking | Explicit silence occurs in craft/trade and a new incident run; investigation advisors sometimes speak while withholding negative evidence. |
| Unannounced omission, acknowledged withholding, reduced specificity | All three v1.2 methods have locally checked craft/trade examples. An acknowledgment is visible to oversight; an unannounced omission requires contextual detection. |
| Content versus audience | A craft agent privately disclosed personal water-production capacity while intentionally omitting it publicly. Prior knowledge and unmet need of other recipients remain unresolved. |
| Content versus false cover | Incident senders sometimes replaced withheld authenticated facts with false reassuring claims. Truthfulness and completeness need separate checks. |
| Content versus timing | Retained document data include 43 late-only deliveries and 22 bystander-only deliveries. These establish observable failures, not per-case intentional delay or strategic routing. |
| Sender behavior versus recipient knowledge and outcome | Independent cross-checks defeated investigation omissions. A later omission did not create a new gap after the recipient had learned the fact. One incident omission accompanied a wrong decision; another agent's purportedly deceptive statement happened to be true. |

## What we can claim

> Across multiple task interfaces and incentive structures, observed cases instantiate several distinctions in a taxonomy frozen before the new runs, providing exploratory evidence for wider descriptive generalization. The evidence does not establish exhaustive coverage, universal applicability, validated latent intent, or incremental monitoring value over a simpler equally informed baseline.

Full coverage remains unestablished, including vagueness/minimization, intentional post-deadline disclosure, and several acquisition/relay/recipient-use diagnostics. Reduced specificity is not automatically legacy pragmatic distortion. Literal intent is based on elicited private plans plus matching behavior, with assistant/Luna review rather than independent human validation. The four new tasks are deliberately selected and short (4–6 turns); they were not sampled randomly from a population of environments.

The distinctions motivate different monitoring evidence and repairs: message presence, material content, recipient/path, timing, truth, and independent recipient knowledge. They do not imply that every category requires a separate monitor agent. A matched monitor/repair comparison remains necessary to demonstrate incremental usefulness.

## Files and offline reproduction

- [Full coverage and evidence limits](COVERAGE.md)
- [Frozen codebook](FROZEN_CODEBOOK.md)
- [Nine checked examples](examples.json), with exact messages/plans, source hashes, and scope qualifications
- [Reproduced summary](reproduced_summary.json)
- [Review status and rejected-annotation corrections](REVIEW_STATUS.md)
- [Raw snapshot](raw_snapshot.zip) and [SHA-256 member manifest](archive.json)
- [Offline reproduction script](../../scripts/reproduce_taxonomy_transfer.py)

From repository root, using Python 3.10+:

```sh
python scripts/reproduce_taxonomy_transfer.py
```

This uses the standard library only, makes no API calls, checks every archive member and frozen source hash, replays all 48 fresh episodes and 471 valid document outcomes, checks craft/example provenance, verifies 254 resolved journal requests, and compares the result against the committed summary. It verifies integrity and mechanical results; it does not automatically validate semantic labels. Frozen environment tests are under `experiments/taxonomy_six_env_20260910/test_environments.py` inside the archive; **11 tests passed** with pytest.

The archive retains original repository-relative paths. It includes frozen environment/runner/runtime sources, raw actor traces, request/cost journal, protocol, retained document data, six retained craft source games, review packets, original analysis scripts, and recovery evidence for a completed episode incorrectly marked incomplete after an output-pipe interruption. Rejected annotation drafts and the prepared but unexecuted external semantic evaluator remain explicitly marked in the review status. Console logs, caches and process locks are excluded. Original scripts and documentation inside the snapshot retain historical paths; use the release-level reproduction command above for a clean checkout.

Fresh collection accounted cost was **$0.90013175**; cumulative pilot accounted spend was **$2.039039 / $3**, including prior accounted failures/reservations. Publishing and offline verification required no new model calls.
