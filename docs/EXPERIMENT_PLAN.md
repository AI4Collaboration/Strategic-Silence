# Experiment plan

Status: proposed study. Shared evidence utilities exist; native backends,
reviewed case collections and model runners remain to be built. No model
experiments have been run for this design. Paid collection is not authorized.

## First establish the question

An agent should disclose what an authorized decision requires while protecting
information it has a duty to keep private. The first study asks whether local
incentives cause agents to violate that boundary through materially incomplete
communication, including when their assertions are accurate, and whether the
omissions affect another agent's executed decisions.

This requires three distinct results: an effect of incentives on disclosure,
an accuracy-versus-completeness dissociation, and a consequence attributable to
missing information. Each result has its own denominator and experiment. The
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

Select one workflow with sourced documents, clear disclosure responsibilities
and a meaningful executed decision. The existing review and service tasks below
are candidates for validity checks, not a settled domain roster:

- Inter-Agent Influence's methodology review provides a native approval action.
  The original draft contains an explicit false statement, and both agents can
  inspect the protocol and draft. Keep the original as an audit condition;
  changes to documents or access are labeled extensions. Its single published
  methodology case cannot establish cross-case generalization.
- KnownLieBench provides knowledge checks, entitlement policies and service
  interactions. Native refunds are executed by the service agent. Evaluate the
  actual action holder; customer-controlled harm requires a separately labeled
  adapter. Service and commercial transactions count as overlapping candidate
  coverage, not independent domains.
- A new legal workflow remains an option after admission checks. It requires
  sourced case materials, explicit procedural duties, reviewed admissible
  evidence and an independently checked outcome. Selective advocacy alone is
  not a failure label. Do not add a court setting solely to increase the count.

Before model collection, verify the source records, annotation rules, native
tools, state isolation and evidence packets offline. Use more than one plausible
outcome, including justified acceptance and rejection. Receivers may investigate,
ask follow-up questions and refuse unsupported requests.

Each dossier should include required material information and clear legitimate-
withholding controls. A valid solution communicates the former without leaking
the latter. Accept authorized qualifications and redacted evidence. The task
must not be solvable by universal disclosure or blanket refusal.

The subsequent model preflight checks whether receivers can use adequate
authorized evidence and whether senders can identify and communicate it.
Poor performance even with adequate evidence signals a capability or task
design problem; a repair null then cannot diagnose the effect of omission well.
Report the preflight results rather than silently retaining only cases a tested
model solves. Independent task admission and model-specific competence are
separate judgments.

## Stage 2: test the mechanism

Hold the factual state, actor mandates and disclosure duties fixed. Establish
sender evidence exposure before random assignment in the controlled study.

1. Cross a feasible incentive contrast with baseline, truth-only and scoped
   completeness instructions. Prompts never instruct concealment. Separate
   factual exposure from demonstrated recognition. Use ordinary truthfulness
   wording; a deliberately literal-only instruction is a separate ablation.
2. Audit assertions, required information, legitimate withholding and native
   outcomes for every assigned episode. Record literal silence separately
   from truthful but incomplete messages.
3. For qualifying omissions, apply the registered O/M/P restoration protocol.
   Use F for receiver-capability and completeness diagnostics on a predeclared
   set of cases. Keep the environment, authority and resource budgets fixed.
   Use the ordinary sender channel for the primary comparison. A trusted
   external-source update is a separate diagnostic, not equivalent disclosure.
4. Compare missing-content restoration with matched nonmaterial updates and
   already-known-content controls. Select evidence from the case criteria,
   not from whichever successful trajectory produces the desired action.
   Report pre-registered M/P comparisons separately for audited accurate
   communication, literal silence and mixed lying/omission. Only the first
   supports a truthful-but-incomplete consequence claim.
5. Add natural information-seeking as a robustness condition. Incentives may
   affect retrieval as well as communication, so do not condition the causal
   incentive comparison on a post-treatment knowledge or omission subset.

The main incentive and instruction estimates use all assigned episodes.
Conditional restoration effects describe eligible omissions. Report missing,
invalid, refused and failed executions explicitly; none becomes an inferred
successful or harmless outcome. Use native losses and requirement violations,
with uncertainty clustered by independent source case family.

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
| Completeness improves required disclosure but leaks private information or increases indiscriminate refusal | Report the trade-off; do not call it a successful general remedy |
| Completeness does not improve disclosure despite valid tasks and capable agents | A substantive mitigation failure, not a reason to discard the result |

These are interpretation rules, not fixed significance thresholds. Case counts,
power, smallest effects of interest and analysis choices are frozen after
offline task validation and before substantive collection.

Add a second independently sourced workflow because it changes a mechanism
that matters, such as the evidence available or the consequential decision.
Further environments need a stated incremental question. The final number is
not fixed at six.

Assign each case one primary task domain under written inclusion and exclusion
rules. Keep workflow features and application sectors as separate metadata.
Near-duplicate cases and stages from the same dossier cannot inflate independent
domain or case counts. Document importance through concrete stakes and real
workflow provenance, not a high-stakes label.

## Questions for later studies

The broader program includes:

- Appropriate disclosure when duties conflict, privacy is graded or bargaining
  interests are genuinely contested.
- Communication protocols, verification rights, incentives or training that
  improve decisions while preserving justified confidentiality.
- Repeated interactions, coalition behavior and system-wide cooperation.

These require different evidence and may become separate papers. The first
paper keeps clear privacy controls but does not promise a general optimal
disclosure policy or comprehensive coverage of social environments.

## Implementation boundary

The retained helpers construct restoration metadata and validate references
between outcomes and tool receipts. They do not verify semantic truth, execute
native tools, isolate external databases or establish legal/scientific
correctness. The current restoration helper uses an authenticated reference
channel; the main ordinary-sender intervention requires a native adapter.
It requires M/P/F packets and constructs four metadata branches; a future runner
must select which branches to execute for the O/M/P study and F diagnostics.
The next engineering work is a selected native adapter, sourced
cases and independent outcome checks. Earlier observations remain in
[Takeaways](TAKEAWAYS.md); they motivate the study without standing in for its
results.
