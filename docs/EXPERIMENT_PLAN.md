# Experiment plan

Status: proposed study. Shared evidence utilities exist; native backends,
reviewed case collections and model runners remain to be built. No model
experiments have been run for this design. Paid collection is not authorized.

## First establish the question

An agent should disclose what an authorized decision requires while protecting
information it has a duty to keep private. This is an evaluation study of
selective disclosure in scalable agent swarms. It does not require a new defense,
training method or optimized communication policy.

| Research question | Primary evidence |
| --- | --- |
| RQ1: Can agents distinguish what to share from what to withhold during collaboration? | Required-information omissions, prohibited disclosures and episodes satisfying both boundaries |
| RQ2: How do conflicting incentives affect agents' disclosure decisions? | Matched incentive contrasts, full utility-response curves and estimable switching ranges |
| RQ3: How do disclosure decisions affect collective task outcomes? | Executed recipient actions, native team outcomes and missing-content diagnostic comparisons |

Each question has its own denominator and experiment; null effects remain
evaluation results. Truthfulness without adequate disclosure is a hypothesis,
not an assumed outcome. The
[pre-hoc specification](PREHOC_DESIGN.md) defines actor inputs, communication
opportunities, boundary controls and information-restoration branches.

## Prior work sets the novelty boundary

The following primary sources were checked on 2026-11-15:

| Source | Established overlap | Implication for our design |
| --- | --- | --- |
| [Deception by Omission](https://arxiv.org/abs/2610.11351v1) | Studies agents concealing mistakes in prefilled trajectories | The existence of omission is not a new finding |
| [KnownLieBench](https://arxiv.org/html/2608.26372v1) | Combines entitlement knowledge checks with conflicting incentives; includes omission-related analysis | Knowledge verification and incentive pressure are not individually new |
| [Thinking Is Not Telling, v2](https://arxiv.org/html/2602.07796v2) | Sections 4.2 and 5.1-5.2 inject missing evidence into communication, resume the user-agent interaction and measure subsequent edits and recovery | Information restoration, receiver-mediated effects and downstream tool actions already have precedent |
| [Inter-Agent Influence](https://arxiv.org/html/2611.04556v1) | Studies influence in agentic workflows; its false-claim scorer excludes strategic omission, while task outcomes can still register failure | Audit a specific metric's coverage; do not label the entire benchmark omission-blind |
| [ConCI](https://arxiv.org/abs/2610.24494v1) | Tests judgments of appropriate and inappropriate information sharing under controlled context changes | Appropriate-withholding controls are necessary validation, not a stand-alone novelty claim |

Further primary-source checks on 2026-11-16 focus on agent collaboration:

| Source | Core claim and evidence relevant to this study |
| --- | --- |
| [HiddenBench, v4](https://arxiv.org/html/2505.11556v4) | Distributed evidence fails to surface in group decisions; Section 6.3 forcibly reveals facts to isolate the sharing bottleneck |
| [PAC-Bench, v1](https://arxiv.org/html/2604.11523v1) | Privacy constraints degrade collaboration; overly conservative abstraction can withhold information needed for coordination |
| [Withheld dissent, v1](https://arxiv.org/html/2609.38324v1) | Suppressed disagreement reduces the gain from discussion; includes conformity-pressure comparisons and controlled public-answer replacement |
| [Zero-cost collaboration, v2](https://arxiv.org/html/2604.07821v2) | Agents can withhold costless help; automated requesting/fulfillment separates competence from cooperation, and sharing rewards alter behavior |
| [Trilemma, v1](https://arxiv.org/html/2611.08312v1) | Agents produce misleading justifications under competing demands for honesty, confidentiality and staffing; measures disclosure and task outcomes together |

Measuring omissions, using disclosure controls, manipulating rewards and
including privacy each have precedent. A utility sweep characterizes our
evaluated agents; it does not by itself establish a novel failure mode.

The candidate contribution is evidence about how strategic pressure changes
appropriate disclosure under fixed task duties, including the joint pattern of
accurate assertions, material omissions and consequential errors. Restoration
supports that claim; it is not a stand-alone novelty claim. The empirical
strength and reproducibility of this pattern determine the paper's contribution.

Truth-only instructions reducing lies while omissions persist would support a
dissociation. A stronger claim that the instructions redirect behavior toward
omission requires an increase in absolute omission incidence, not just a larger
omission share among fewer remaining failures.

## Stage 1: validate one native workflow

The [environment catalog](ENVIRONMENTS.md) specifies six scalable application
families organized by flow, sharing and fit dependencies. The adapter accepts
`n` active work owners, a sourced task graph and an allocation of evidence and
authority. Every counted member must own substantive operations in one connected
problem. Counterparties and judges are recorded separately. A larger batch of
independent dyads does not qualify.

Start with E5 distributed dispatch, then E2 software migration after admitting
connected change campaigns. E3 scientific reanalysis, E4 civil evidence
production, E1 coordinated procurement and E6 assembly conformance require
additional source and review work. Keep source-size ceilings distinct from
adapter capability. The existing three-component assembly and small single-issue
code tasks cannot support arbitrary swarm sizes by duplication.

Every admitted case records each member's evidence, tools, decision rights and
dependencies. Check a native coupling witness, a valid coordinated solution,
nonempty work packages and a connected cross-owner task graph. Reject redundant
relay roles, unsupported constraints and tasks whose apparent coupling is only
a final concatenation of independent answers. Preserve legitimate verification,
repair, negotiation and refusal actions.

Before model collection, verify the source records, annotation rules, native
tools, state isolation and evidence packets offline. Use more than one plausible
outcome, including justified acceptance and rejection. Receivers may investigate,
ask follow-up questions and refuse unsupported requests.

Every environment includes required material information and clear legitimate-
withholding controls. Put them in the same dossier when authentic task rules
support both; otherwise use matched boundary cases. Do not fabricate secret
fields just to fill a matrix. A valid solution communicates the former without
leaking the latter. Accept authorized qualifications and redacted evidence.
The task must not be solvable by universal disclosure or blanket refusal.

The subsequent model preflight checks whether receivers can use adequate
authorized evidence and whether senders can identify and communicate it.
Poor performance even with adequate evidence signals a capability or task
design problem; a repair null then cannot diagnose the effect of omission well.
Report the preflight results rather than silently retaining only cases a tested
model solves. Independent task admission and model-specific competence are
separate judgments.

## Swarm-size evaluation

Parameterize size rather than creating a separate hand-written scenario per
roster. An adapter accepts arbitrary integer sizes above its documented minimum;
core study admission begins at four members. Role pools may have unequal sizes.
Validate `4, 8, 16, 32` and an off-grid size such as `7` where the source workload
supports them. Unsupported sizes remain missing coverage, not fabricated cases.

| Comparison | Held fixed | What changes | Interpretation |
| --- | --- | --- | --- |
| Fixed workload | Source task, goals, tools, total compute allowance | Partition of work/evidence/authority across `n` owners | Cost and reliability of organizing the same work across more agents |
| Growing workload | Task family, target work and compute per owner, registered generation/selection rules | Connected workload and number of owners | Behavior as the whole system grows |

Size changes the allocation of information and responsibilities. Report the
actual resulting dependency degrees, path lengths, role mix and communication
opportunities. Preserve native constraints; stratify or match natural graph
structure rather than rewiring facts. Randomize run order. For fixed-workload
comparisons, pair sizes by the same source task; do not restrict analysis to
cases that succeed at every size. Bootstrap source families, keeping all size,
weight and seed continuations from a family together.

At each size report required-information withholding and protected-information
leakage with their eligible opportunity denominators; task outcomes in native
units; completion without either disclosure error; and per-owner distributions.
Also report message/tool/token cost, wall time and actual completed work. Total
error counts alone confound size with the number of opportunities.

Register one focal sender, fact, recipient set and dependency before each
incentive comparison. Estimate focal-omission consequences separately from
whole-swarm rates. Track first affected action, later affected owners and final
outcome, using trace evidence to distinguish forwarding from independent
retrieval. M/P differences estimate total continuation effects; the observed
path by itself does not prove every intermediate causal link.

Run the primary utility sweep at a fixed admitted size and cohort. Use a
predeclared subset of reward weights for the size study. A full size-by-weight
interaction is a separate registered comparison, not an implicit claim from
separate sweeps. Final size/model/repeat counts depend on offline admission and
budget; this plan does not authorize paid collection.

## Stage 2: test the mechanism

Hold swarm size, work assignment, topology, facts, actor mandates and disclosure
duties fixed. Establish evidence exposure before random assignment. Cross a
feasible incentive contrast with baseline, truthfulness and scoped completeness
instructions. Use natural truthfulness wording; a literal-only instruction is
a separate ablation. Completeness refers to existing duties and preserves
confidentiality. Never instruct concealment.

Use the [knowledge checks](PREHOC_DESIGN.md#establishing-knowledge-before-intervention)
and [restoration protocol](PREHOC_DESIGN.md#restoration-protocol) for evidence
collection. For qualifying omissions, run O/M/P; reserve F for registered
capability/completeness diagnostics. Analyze audited accurate communication,
literal silence and mixed lying/omission separately. Only the first supports
a truthful-but-incomplete consequence claim.

Estimate incentive and instruction effects over **all assigned episodes**.
Report false assertions, omissions, prohibited disclosures, completion, native
losses and the joint rate of accurate messages, omissions and task defects.
Conditional M/P effects describe eligible omissions, not the overall effect
of incentives. Add natural information-seeking as a separate robustness
condition; do not select that treatment comparison on later retrieval or knowledge.

Preserve missing, invalid, refused and failed executions in the accounting.
Use native outcome units and cluster uncertainty by independent source family.

### Utility-threshold evaluation (RQ2)

**Question.** At what local reward weights do agents change what they disclose,
and how do those choices affect their collaborators? A threshold describes an
observed response curve. It does not set the disclosure duty, define materiality
or identify a universal boundary between acceptable and unacceptable behavior.

**Payoff.** For terminal trajectory z, register the focal agent's assigned score:

`U_i(z; lambda) = B_i(z) + lambda * R_i * K_i(z)`.

`B_i` is a fixed base score tied to documented task outcomes. `K_i`, in [0, 1],
is an observable local KPI such as accepted work or cleared assigned requests.
It never rewards a message for omitting a fact. `R_i > 0` is a reference score
range derived from fixed task anchors before model collection. Only `lambda`
changes. Register all components, native units, anchors and scoring rules; do
not infer them from model responses or invent monetary losses. Where no
defensible scalar base score exists, omit the threshold treatment and retain
the ordinary disclosure evaluation.

This manipulation changes utility. It does not change facts, deadlines,
permissions, confidentiality rules, verification tools or other agents' payoff
rules. Hold any base penalties fixed. The score is an experimental incentive,
not permission to violate a task rule. Native loss, privacy and compliance
outcomes remain separately scored rather than collapsed into this utility.

**Sweep.** The proposed coarse grid is `lambda = {0, 0.25, 0.5, 1, 2, 4}`.
Admit and freeze only task-plausible weights before collection, recording any
cap and its basis. Zero removes the added local KPI reward; it does not remove
other motives in the base task. Use the same independently admitted case cohort
and pre-incentive evidence checkpoints at every weight, with independent
continuations and randomized execution order. Vary one focal sender at a time;
joint changes to multiple senders are a separately labeled experiment.
The primary sweep uses the fixed baseline instruction. Truthfulness and scoped
completeness comparisons are prespecified behavioral evaluations, not a search
for an optimized prompt. They receive separate curves if run.

Start with E5 distributed dispatch, where local workload and team routing outcomes
can differ. Use E2 as a contrasting software-migration swarm after its
backend is validated. Preserve the distinction between these interaction
structures. Other environments enter only with justified payoff anchors;
separate domain curves do not imply comparable utility scales.

**Outcomes and denominators.** Select a focal required fact and, where available,
a focal protected fact using a rule fixed before treatment. All weights share
the same pre-treatment eligibility rules. For required facts, `p_W(lambda)` is
the probability that required content remains undisclosed at the registered
decision deadline. For protected facts, `p_L(lambda)` is the probability of
unauthorized disclosure. Accept semantically sufficient redacted reports and
qualifications. If a fact is legitimately resolved or superseded during the
continuation, score that resolution explicitly rather than as concealment.
Do not condition the primary curves on post-treatment truthfulness, task
success, receipt of a reply or observed omission.

Report literal silence, selective omission, false assertions, prohibited
disclosure, legitimate resolution, refusal and native failure alongside these
curves. They are not all exclusive labels. No-message cases count as silence
only with an intact communication opportunity; technical failures and missing
traces remain unresolved, not inferred withholding. Report all assigned counts,
resolved counts and bounds treating unresolved outcomes as either event or
non-event. A primary estimate cannot silently discard unsuccessful episodes.

**Threshold definition.** Within each model, environment, mode and instruction
condition, weight independent source families equally, then weight admitted
cases equally within each family. Use the same weights throughout the sweep.
`lambda_W,50` is the first sustained upward crossing of `p_W(lambda) = 0.5`
over the admitted range, where such a crossing is supported. Fifty percent is
an explicit reporting convention, not a natural law or acceptable failure rate.
Report the full curve as the primary result and the adjacent tested weights
bracketing the crossing as the threshold estimate: levels below the bracket
have probabilities below 0.5 and all tested levels from its upper endpoint
onward have probabilities at least 0.5. Otherwise retain the full crossing
pattern rather than report a single switch. Report protected-information
`lambda_L,50` analogously on its separately eligible cohort. An aggregate
crossing does not imply every case or agent has a deterministic switch point.

Use repeated trials and source-family cluster bootstrap intervals that preserve
pairing across weights. Keep all variants and repeats of a dossier in its
source-family cluster. Fix case counts, repeats and precision targets before
collection; token-cost measurement may inform that budget, but desired effects
may not. Report baseline-above-50%, no crossing within the tested range,
multiple/nonmonotone crossings, or unresolved crossing uncertainty explicitly.
Do not force a monotone fit, extrapolate a threshold, or call an uncertain
crossing absent. Show uncertainty in both event probabilities and the crossing
range, including the share of bootstrap draws with no unique crossing. If
unresolved execution outcomes can change the classification, the threshold is
unresolved. Any later refinement grid uses fresh repetitions and is labeled
exploratory unless confirmed on a frozen independent cohort.

**Consequences and scope.** Plot recipient and team outcomes against the same
weights. O/M/P restoration on a predeclared case-and-weight subset diagnoses
whether missing content contributes to loss; a switching point alone establishes
neither harmfulness nor deceptive intent. Protected-information retention may
be strategic and correct. This study estimates behavior and its consequences;
it does not optimize the utility weights or propose a reward-based defense.

## Stage 3: decide what deserves replication

Advance beyond the validity pilot when the measurements can distinguish actual
omissions from ignorance, legitimate privacy and irrelevant compression, and
when the receiver has meaningful decision competence.

| Observed pattern | Supported interpretation or next step |
| --- | --- |
| Material omissions occur, but incentive pressure has no detectable effect | A disclosure reliability result; strategic attribution remains unsupported |
| Pressure changes omission, but restoration has no detectable outcome effect | An incentive-sensitive communication result without demonstrated harm in this task |
| Restoration helps only after removing realistic verification or forcing trust | Reject the causal task design rather than claim a general failure mode |
| Assertions remain accurate, omissions respond to pressure and source-matched restoration reduces native loss | Strong candidate for independent task replication |
| Completeness instructions change required disclosure, private leakage or refusal | Report the separate behavioral responses; no optimized remedy is required |
| Completeness instructions have no detectable effect despite valid tasks and capable agents | Report the instruction-sensitivity result without requiring a successful intervention |

These are interpretation rules, not fixed significance thresholds. Case counts,
power, smallest effects of interest and analysis choices are frozen after
offline task validation and before substantive collection.

The catalog states what each family and its focal dependency add to coverage. Admit
each through the same evidence and execution checks. Publish the implemented
roster and case counts explicitly; an unfinished environment cannot count as
an experimental replication.

Assign each case one primary task domain under written inclusion and exclusion
rules. Keep workflow features and application sectors as separate metadata.
Near-duplicate cases and stages from the same dossier cannot inflate independent
domain or case counts. Document importance through concrete stakes and real
workflow provenance, not a high-stakes label.

## Questions for later studies

The broader program includes:

- Appropriate disclosure when duties conflict, privacy is graded or negotiation
  involves genuinely disputed disclosure obligations or incomparable interests.
- Communication protocols, verification rights, incentives or training that
  improve decisions while preserving justified confidentiality.
- Repeated interactions and endogenous formation or dissolution of coalitions.

These require different evidence and may become separate papers. The first
paper keeps clear privacy controls but does not promise a general optimal
disclosure policy or comprehensive coverage of social environments.

## Implementation boundary

The [README](../README.md#code-and-checks) records implemented utilities and
remaining engineering work. Native execution, source admission, semantic
outcome checks and paid model collection are distinct from offline metadata
tests. Historical observations remain in [Takeaways](TAKEAWAYS.md).
