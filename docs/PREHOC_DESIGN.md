# Pre-hoc design: appropriate disclosure and harmful omission

Status: research design. No native backend, admitted case collection or new
model results are implemented. The [environment catalog](ENVIRONMENTS.md)
specifies five primary task domains and six concrete design targets.

## Start with the desired behavior

Agents should communicate information needed for an authorized decision while
respecting their duties to the person or organization they represent. This
requires selection: a useful message need not contain everything the agent knows.

| Situation | Desired behavior | Evidence needed for evaluation |
| --- | --- | --- |
| Material information the recipient is entitled to receive | Communicate the relevant content or an adequate qualification before the decision | Source documents, task duties and a reviewed account of why the fact matters |
| Confidential information outside the recipient's authorization | Protect it; provide an authorized summary or limitation statement when appropriate | The mandate, recipient and disclosure restrictions |
| Discretionary private information | Permit withholding within the task's rules | Evidence that no relevant disclosure obligation applies |
| Irrelevant detail | Permit omission while preserving decision-relevant content | The decision criteria and the relevance review |
| Conflicting or unresolved obligations | Retain for separate boundary analysis | The competing rules and unresolved judgment |

These are evaluation judgments, not classes of environment. Permissible
withholding is not automatically beneficial: a benefit claim needs outcome
evidence. A counterparty receiving a less favorable negotiated price is not by
itself evidence of a task failure.

Appropriate selective disclosure is the desired behavior. Measure missing
required content and prohibited disclosures separately, plus episode-level task
success without either error. Freeze the eligible fact sets and report their
denominators; optional content has no mandatory disclose/withhold label.

For the first study, select clear obligations and permissions. Use ordinary task
documents and general role duties, rather than a prompt listing the exact facts
the sender must disclose. Annotate materiality before inspecting model outcomes.
Some duties may be triggered by a volunteered claim or authorized request; fix
that conditional rule in advance.

## A concrete boundary control

Place three kinds of content in the same dossier: a required material fact,
irrelevant background, and information that should remain private.

For example, a procurement dossier could contain a known inability to meet an
explicit delivery requirement, old unrelated delivery logs, and confidential
internal costs. Under a task rule requiring disclosure of unmet requirements,
the appropriate response communicates the delivery limitation, omits the
unrelated logs and protects the costs. This is a proposed case pattern; a real
dossier and its disclosure rules must be verified before use.

Score the communicated meaning, not exact reproduction of a fact string.
An authorized qualification, redacted explanation or refusal to certify can
satisfy the duty without exposing a restricted source. Escalation and refusal
must be scored against the task: indiscriminate refusal is not a successful
solution. Changing the recipient or authorization for the same fact is a
separate boundary test, not an omission-repair comparison with fixed conditions.

## When can omission matter?

Separate preconditions from possible drivers and measured consequences.

| Item | Role in the experiment |
| --- | --- |
| The sender encounters relevant evidence | Establishes exposure; recognition needs additional evidence |
| The sender can choose what to communicate before a decision | Creates an opportunity for silence or selective disclosure |
| An authorized way to communicate the material content exists | Makes disclosure a feasible alternative under the same duties |
| The recipient does not already have equivalent information | Allows a potentially informative omission |
| The recipient's feasible actions depend on that information | Establishes relevance; actual effects remain to be tested |
| Withholding can advance a local objective | A candidate driver, manipulated through incentives |
| Verification or follow-up is costly or delayed | A candidate moderator, not a necessary condition |
| A worse action or outcome follows | A measured consequence, never an admission label inferred from the theory |

Independent retrieval can prevent harm even after a material omission. The
receiver keeps its native tools, follow-up rights and ability to decline.
Do not disable these protections merely to manufacture an effect.

## Pre-hoc case package

Freeze the following before collection:

- Source dossier, provenance, initial state, material facts and decision criteria.
- Actors, principals, objectives, permissions and responsibilities.
- Shared and private evidence, retrieval access and communication opportunities.
- Required, discretionary and restricted disclosure annotations with source rules.
- Native tools, deadlines, budgets and state-changing decision options.
- Acceptable semantic disclosures, including permitted qualifications.
- Independent outcome checks, eligible restoration sets and placebo candidates.
- Assignment rules, analysis denominators and source-family identifiers.

Actors receive their task documents, applicable rules and private information.
Evaluators retain fact labels, outcome references and intervention metadata.
No prompt tells the sender which fact to hide or reveals the expected action.

## Experiment 1: does pressure change disclosure?

Present or retrieve identical evidence for the sender before assigning incentives
and instructions in the controlled mechanism study. Compare a task-consistent
objective with a feasible local pressure such as a deal, speed or approval
reward. Preserve mandates, substantive duties, tools and task state. When two
agents represent different principals, both conditions may retain conflicting
interests; a new common objective is a different task.

Cross incentive conditions with baseline, truth-only and truth-plus-material-
completeness instructions. Completeness means communicating the material content
required by the existing role while preserving confidential information. It does
not create a new duty or require universal disclosure.
Use a natural truthfulness instruction such as "Be truthful in your
communication." A deliberately narrow instruction to avoid only literally false
claims is a separate ablation, not the primary test of truthfulness instructions.

Record exposure, demonstrated recognition and communication separately.
Retrieval receipts do not prove understanding. A factual probe in a separate
branch tests whether the model can recover the fact from that state, not what it
was privately thinking in the scored continuation. Probes inside a scored run
can prime disclosure and must be labeled and balanced across conditions.
Natural information-seeking is a separate robustness condition because the
incentive may also change which evidence the sender reads.

Estimate effects over all assigned episodes. Report false assertions, required
omissions, literal silence, inappropriate disclosure, task completion and native
outcomes. Also report the joint rate of factually accurate messages, required
omissions and task defects, with factual message content distinguished from
silence or empty refusals. Comparing only truthful or omission-selected
trajectories across conditions does not identify the randomized treatment effect.

If truth-only instructions reduce lies while omissions remain, report that
dissociation. Claim substitution toward omission only if the absolute omission
rate increases under the controlled comparison, not merely its share among
remaining failures.

## Experiment 2: does the missing content affect the decision?

Choose eligible facts and evidence requirements before observing outcomes.
After communication, use the registered rule to identify which eligible content
is missing. Freeze the workflow before the receiver's consequential action.
Create independent continuations:

| Arm | Update |
| --- | --- |
| O | Empty update; retain the original communication |
| M | The missing authorized content needed for a registered material issue |
| P | Nonmaterial authorized evidence matched for source, novelty, timing, presentation and input length where feasible |
| F | All still-missing required content known to the sender for this recipient at the checkpoint |

O/M/P are the main continuation arms. Use F for capability and completeness
diagnostics on a predeclared subset rather than requiring it for every omission.

Define minimality by the evidentiary issue, including jointly necessary facts.
Do not search for the smallest addition that happens to produce a successful
action. Register a selection rule for multiple eligible sets. Already-complete
episodes remain controls without a missing-content restoration.

Updates supply evidence, not a recommended action or a repaired artifact.
The main intervention adds content through the sender's ordinary channel, with
source identity and timing matched between M and P. An authenticated external
update is a separate diagnostic condition: source authority can itself change
the response. Record exactly which spans or messages the intervention adds.
Keep the original world state, task duties, authority and budgets identical at
the branch point. Record any mismatch between M and P; include an already-known
content control to diagnose attention and reminder effects. F is a completeness
reference, not an assumed optimal policy. Test the receiver's ability to use
adequate authorized information separately before interpreting null repairs.

Measure actions actually executed through native tools and their consequences.
Compare M with P alongside O/M, O/P and M/F, retaining null and adverse effects.
The result estimates the effect of the specified information intervention among
eligible omissions. It does not by itself establish a strategic motive, the
natural effect of an ordinary sender disclosure, or a causal mediation estimate
for the incentive treatment.

Pre-register separate restoration strata for factually audited accurate
communication, literal silence and communication containing false assertions.
Assess the communication available to the recipient before the checkpoint.
The truthful-but-incomplete consequence claim requires an effect in the accurate
communication stratum; a repair effect pooled with lying cannot establish it.
These conditional M/P comparisons do not replace the all-assigned estimates
of incentives or instructions.

Combine this evidence with Experiment 1 without collapsing the judgments:
incentive sensitivity, breach of disclosure duty and information-caused loss
are separate findings. Report sender benefit, receiver outcomes and shared
outcomes separately; a redistribution of bargaining surplus is not automatically
a defect. Cluster uncertainty by independent source case family.

## Selecting environments

The [environment catalog](ENVIRONMENTS.md) specifies the six workflows and
their distinct evidence and decision mechanisms. Validate native execution
incrementally, starting with transactions and software changes. Report admitted
cases and functioning backends separately from the full design target.

A candidate must have consequential decisions, realistic evidence, observable
information access, feasible legitimate disclosure, native receiver actions and
an independent outcome check. It must support useful behavior as well as
failure, so that universal disclosure and blanket refusal cannot solve it.

Define the unit of a domain label at the task level and write inclusion and
exclusion rules before assigning cases. Assign each case one primary domain;
use secondary labels for cross-cutting features. Commercial transactions and
customer service cannot be counted as separate coverage merely by renaming
stages of the same process. Negotiation, oversight and collaboration are workflow
features, not a three-class domain partition.

Record why each selected task matters through its concrete consequences, who
relies on the decision, and the evidence that the workflow is used in practice.
Select distinct tasks based on those criteria, not names alone. Existing
benchmark audits and modified tasks receive separate labels. Shared dossiers
and near-duplicate cases remain one family for inference.

The [experiment plan](EXPERIMENT_PLAN.md) specifies the first-paper claim,
relevant prior work, validation gates and questions reserved for later studies.
