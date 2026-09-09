# Writing readiness review of PR #4

Reviewed the merged snapshot at commit `73fc7cc7dbf090d91cd2f0d529a7ea256f3eb557`.
The root README is restored byte-for-byte to its pre-PR version. Keep experiment
and writing details in this folder rather than inserting them above the project introduction.

## Decision

The additions help a writing sprint now: they provide a reproducible native
resource extension, exact traces, descriptive comparisons and inspectable
examples. They do not complete the revised paper's measurement validation or
recipient-consequence claims. Write methods, provisional results and limitations
now; make stronger claims conditional on the specific checks below.

This review concerns the committed 26-game snapshot. Later local collection and
Luna audits are separate artifacts, not automatically part of the published
cohort or independent human validation.

## What each contribution can use

| Contribution | Usable now | What remains missing | Smallest useful fix |
| --- | --- | --- | --- |
| C1: omissions that message counts miss | Exact messages/plans and examples of speaking while stating a withholding intention; 512 candidate speaking rounds | Candidate intent does not verify a material information omission; reviewing only positive candidates cannot estimate missed omissions | Sample both candidate-positive and candidate-negative rounds by game; label actual disclosure independently of plans, with fact, recipient, prior knowledge and evidence spans |
| C2: distinguish failure types | Exporter preserves source evidence and separate content/audience/timing review fields; trade examples distinguish execution success from planning success | Blank semantic labels are not a validated taxonomy; craft/trade does not supply the separate document policy experiment or cooperative-handoff comparison | Freeze a development codebook, then independently annotate held-out games; bring in separately versioned handoff and document-policy evidence without treating them as new craft/trade results |
| C3: goal-sensitive disclosure and recipient consequences | Descriptive differences across goal compositions in a fixed, plan-elicited GPT-5.4 configuration | No matched disclosure intervention; intent, survival and completed trades do not establish consequences caused by withholding | Branch from a fixed checkpoint with recipient knowledge controlled; compare factual disclosure versus silence, hold other state/policies fixed, and measure feasible action and payoff differences |

Craft/trade is a resource/survival extension, not an additional non-resource
family. It can strengthen the resource section, but should not silently replace
the handoff or document-delivery setups. The cohort changes goal composition,
not merely a focal sender's goal, so label comparisons accordingly.

## Results text that can be drafted now

> We extended the native resource/survival game with locally observed recipes
> and reciprocal, colocated trades. In a frozen development snapshot, 26 games
> completed across aligned, mixed and competitive goal compositions. Of 1,040
> agent-rounds in completed games, 1,029 had evaluable communication and judge
> records. The operational conjunction of judge-coded withholding intent and
> no messages occurred in 0/395 aligned, 16/276 mixed and 69/358 competitive
> agent-rounds. These are descriptive, plan-elicited observations from one model
> configuration; rounds and agents within a game are dependent. The conjunction
> measures an intent-and-communication pattern, not verified concealment from a
> recipient or its causal effect on task outcomes.

| Composition | Complete games | Operational conjunction / evaluable rounds | Descriptive rate |
| --- | ---: | ---: | ---: |
| Aligned | 10 | 0 / 395 | 0.00% |
| Mixed | 7 | 16 / 276 | 5.80% |
| Competitive | 9 | 69 / 358 | 19.27% |

> The judge also identified 512 speaking rounds with withholding intent. These
> are candidates for semantic review rather than verified selective disclosures.
> All 23 craft attempts succeeded mechanically; 15 trade action choices produced
> three completed exchanges. Some successful exchanges failed to achieve the
> agents' stated crafting objectives, illustrating why successful action execution
> and successful coordination must be evaluated separately.

Use these paragraphs as a provisional results subsection. Do not insert raw
legacy fabrication rates into the abstract or describe 512 validated omissions.
The existing case examples in README.md can support a clearly labeled qualitative
figure, with exact plan and message spans and an explicit unknown recipient gap.

## Fixes in priority order

1. **Separate endpoints before drafting claims.** Report the reproducible
   conjunction and original judge PREMEDITATED labels in separate columns.
   Their counts are 0/16/69 versus 0/12/55 by composition. Inspect individual
   disagreements before interpreting the difference; do not silently overwrite
   either original field. Use raw plans when checking legacy parser truncation.
2. **Repair message scope before reporting deception rates.** Distinguish claims
   about local stocks, own inventory, recipes and secondhand reports. Retain
   unknown/unsupported categories and score accuracy separately from completeness.
   Freeze a new classifier version and validate on independent annotations before
   re-scoring the cohort. Preserve the original labels as historical output.
3. **Use games and matched seeds for comparisons.** Only seven seeds have all
   three completed conditions: 609080, 609081, 609082, 609083, 609085, 609087 and
   609088. Show per-game rates and a matched-seed sensitivity table alongside all
   completed games. Exclude the 144 partial-game evaluated rounds from the primary
   table and document stopping/missingness. Matching does not remove all selection
   bias or make this interim sample confirmatory. Do not run an agent-round
   independence test on 1,029 rows.
4. **Resolve the goal/score contract for future cohorts.** Competitive instructions
   maximize total carried food + water + gold, while the reported surviving-agent
   ranking uses gold. The current archive preserves this tension. Specify the
   endpoint in writing and use an explicit consistent contract in a separately
   versioned future run; never rewrite the historical goals.
5. **Prioritize annotation and controlled replay over more blind collection.**
   More games will not fix recipe-classifier errors or establish recipient
   knowledge. Freeze development examples, reserve unseen games for evaluation,
   label disclosure without plan exposure, then review motive separately. Report
   agreement before and after any corrections, including disagreements and
   unknowns. Model-reviewer consensus alone is not human ground truth.
6. **Keep prompt and consequence claims narrow.** This actor prompt asks what to
   share or keep private. Unprompted emergence needs a matched prompt comparison.
   Recipient harm/benefit needs the controlled checkpoint test described above.
   Craft success and survival totals cannot substitute for that intervention.

## Suggested sprint order

- First: write environment, protocol, cohort flow and the descriptive table above.
- Next: write the measurement limitations and one exact-evidence qualitative
  example each for literal silence, selective speech and coordination failure.
- Then: build the per-game/matched-seed table and complete an independent semantic
  development audit. Keep unreviewed cells unknown rather than inventing counts.
- Finally: integrate the separate handoff and document-policy results only after
  checking their own run manifests, labels and completion status. If those gates
  remain open, describe the taxonomy and consequence study as a method/protocol,
  not a completed empirical contribution.

## Verification performed

All 28 PR-specific tests pass, including replay of observations and post-action
states for every archived complete game and the unchanged original judge prompt.
The archive/input hashes verify; the reproduced summary equals the committed
summary. The raw manifest confirms seven complete condition triplets. These are
mechanics and reproducibility checks, not semantic-label validation. No API
experiments were launched during this review.
