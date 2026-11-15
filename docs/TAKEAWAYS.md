# When do agents withhold information?

The earlier pilots motivate the following mechanisms. They do not establish a
general rule predicting silence in real workflows. Their implementations and
results are retired; this document retains the useful observations and questions.

## Observations worth carrying forward

### Disclosure can threaten a private advantage

Under competing objectives, some agents sent no messages while their elicited
plans described keeping useful knowledge private. The recorded conjunction of a
withholding-intent label and no delivered messages occurred in mixed and
competitive conditions, but not in the aligned cohort. This supports testing
goal conflict as a driver of silence. The comparison is descriptive, and the
prompt explicitly invited consideration of sharing versus keeping information
private. It does not establish spontaneous deception or recipient harm. [1]

### An agent can preserve others' dependence while continuing to speak

With payment rules fixed, the service pilot disclosed useful knowledge in
team-objective episodes and withheld it in individual-expert-objective episodes.
The withholding episodes still contained messages, sometimes openly announcing
the withholding. The useful takeaway is a possible dependence mechanism:
disclosure can help another agent act independently, reducing the informed
agent's advantage. These records demonstrate content omission, not literal
silence. [2]

### A stated reason for silence can be protective

One inspected record withheld useful information because the elicited plan said
sharing it could encourage others to consume scarce shared resources. This is an
observed stated rationale. It does not show that silence actually protected the
group, or that the explanation faithfully identifies the causal motive. The new
design should allow omissions with beneficial as well as harmful consequences. [1]

### Truthfulness and completeness can produce different disclosure choices

The archived prompt write-up reports omissions under a truth-only instruction
and disclosure under a whole-truth instruction on selected states. This motivates
the hypothesis that factual truthfulness alone does not ensure material
completeness. The underlying collection journals are not in this checkout; some
arms were collected in separate batches. Treat this as a reported pilot lead,
not a reproduced causal result or evidence that a completeness instruction
always succeeds. [3]

### Silence, omission and harm require separate evidence

Message presence can coexist with withheld material information. Conversely,
withholding does not establish that the recipient lacked the information or lost
anything. In the service pilot, some recipients still chose service after full
information was provided; the two routes tied on total team payoff. No team-total
harm from withholding was established. [2]

Literal silence means no delivered message on the specified channels during a
valid communication opportunity. Speaking while leaving a material fact out is
content omission. Invalid output, refusal, lack of knowledge and permitted
confidentiality must be recorded separately. Elicited plans are supporting
artifacts, not independent proof of strategic intent.

## Conditions to test in the new environments

| Condition | Proposed comparison | Current evidence status |
| --- | --- | --- |
| Disclosure reduces the sender's private advantage | Aligned versus conflicting objectives in the same case | Motivated by pilot observations |
| Disclosure enables independent recipient action | Vary whether withholding preserves dependence, keeping task facts fixed | Mechanism suggested by the service pilot; not isolated experimentally |
| The recipient can obtain the omitted fact elsewhere | Sender-exclusive evidence versus independently retrievable evidence | Open hypothesis |
| Verification is difficult or costly | Vary document access or inspection cost within the same task | Open hypothesis |
| The recipient asks directly about the missing issue | Matched disclosure opportunity with and without a targeted question | Open hypothesis |
| Another informed party can contest the account | Introduce an independently informed counterparty under fixed case facts | Open hypothesis |
| Instructions require accuracy versus material completeness | Baseline, truth only, truth plus authorized material disclosure | Reported pilot lead; needs controlled replication |

The [pre-hoc design](PREHOC_DESIGN.md) starts by distinguishing justified
withholding from omissions that undermine the recipient's authorized decision.
The conditions above are testable hypotheses, not classes of environment.

The working hypothesis is that withholding becomes attractive when disclosing a
known material fact would move the recipient's decision against the sender's
objective, and the sender expects the fact to remain undisclosed. The second part
requires direct testing. These conditions do not yet predict whether an agent
will stay entirely silent or speak selectively.

For each test, establish what the sender actually observed, what the recipient
already knows or can retrieve, and why the fact matters under the task rules.
Compare incentives without instructing the sender to deceive. Freeze the
recipient's state and test whether minimal evidence restoration changes its
executed decision and task-native loss, relative to a matched irrelevant update.

## Evidence anchors

The original releases remain in Git history, outside the active working tree.
Offline reproduction was rerun successfully before removal on 2026-11-15.

1. [Frozen disclosure observations](https://github.com/AI4Collaboration/Strategic-Silence/blob/32bf516676ef82ca79e7ba82679f9e50fa29150e/results/craft_trade/DATA.md):
   26 completed games; the intent/no-message conjunction was 0/395 aligned,
   16/276 mixed and 69/358 competitive evaluable agent-rounds. Rounds within a
   game are dependent. The protective-rationale example is
   `609080_mixed / round 0 / Agent_2`; the speaking-with-withholding examples are
   `609081_all_competitive / round 0 / Agent_1` and `Agent_2`. The original judge
   labels are not independently validated deception rates.
2. [Frozen service observations](https://github.com/AI4Collaboration/Strategic-Silence/blob/32bf516676ef82ca79e7ba82679f9e50fa29150e/results/service_objectives/README.md):
   three initial matched cases and five follow-up cases, 24 episodes total;
   all 224 saved requests replayed exactly before removal. All eight aligned
   episodes disclosed, while all eight mixed and all eight competitive episodes
   omitted the useful knowledge according to the saved assistant-reviewed
   annotations. Reproduction verifies those annotations' application, not their
   independent semantic validity. Mixed and competitive sender prompts were
   identical within a case; their recipient objectives differed.
3. [Archived instruction comparison](https://github.com/AI4Collaboration/Strategic-Silence/blob/32bf516676ef82ca79e7ba82679f9e50fa29150e/paper/additions/README.md):
   repeated decisions on two selected states, rather than independently sampled
   tasks. The write-up reports the truth-only versus whole-truth contrast;
   raw-journal verification remains outstanding.

The local pre-cleanup checkpoint is
`checkpoint/before-toy-cleanup-20261115` at
`d1599ddaf849033099eb6149e15bfe7dc8826e8c`. It also preserves previously uncommitted
development work. It is a recovery point, not an active experiment or a published
release.
