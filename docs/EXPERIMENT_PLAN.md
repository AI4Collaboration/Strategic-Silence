# Experiment design

Status: candidate workflows and shared evidence utilities. No native environment
backend or admitted case collection is implemented. No model experiment has been
run for this design, and paid collection is not authorized.

## Research question

When do agents leave out known, decision-relevant information, including while
making only true statements? Does that omission alter another agent's action and
cause avoidable loss? [Takeaways](TAKEAWAYS.md) distinguish earlier observations
from conditions that remain hypotheses.

## Taxonomy and case admission

The [pre-hoc design](PREHOC_DESIGN.md) is the environment specification. It uses
Interdependence Theory's six dimensions to characterize each interaction before
collection. Oversight, peer collaboration and delegated bargaining are profiles
within that space. Application domains and human/LLM actor identity are recorded
separately. Profile differences describe coverage; matched within-case variants
support causal comparisons.

The initial development targets are six native episodes from three case families:

| Source case family | Candidate episodes | Required execution evidence |
| --- | --- | --- |
| Enterprise contracts and delivery | Procurement negotiation; cross-functional delivery collaboration | Accepted terms, orders, resource commitments, delivery state and acceptance checks |
| Research records and protocols | Distributed analysis; methodology oversight | Executed analyses, integrated artifacts, review actions and protocol-compliance checks |
| Commercial dispute dossiers | Settlement negotiation; adjudication | Evidence submissions, executed settlements or dispositions, and independently reviewed case outcomes |

Every episode needs a sourced dossier, a six-dimensional structural profile,
actor mandates, an information-access map, conditional disclosure rules, native
tools and reviewed outcome checks. Label facts as required, discretionary or
restricted for the specific recipient and time. Fix those rules before model
collection, including any requirement to qualify a volunteered claim. Preserve
unresolved normative cases separately from confirmatory failure analysis.

Legal cases cover ordinary delivery, quality, scope and payment disputes under
explicit case rules. An independent case review must establish the evidentiary
standard, permitted disclosure and reference outcome. A counterparty's partial
advocacy alone is not a failure label. Exclude protected communications from
restoration packets. The receiver can investigate and contest evidence; it is not
forced to trust the sender.

Use realistic documents, task-specific tools and independently checked outcomes.
Include benign cases where the sender's requested outcome is justified. Reject
case sets in which a blanket refusal policy solves the task. Previous game or
mapping inputs must not be relabeled as these workflows.

## Paired design within each workflow

1. Establish evidence exposure from actual observations or retrieval receipts;
   record demonstrated factual recognition separately. Separate sender-exclusive
   information, recipient-accessible but unread evidence, and information already
   seen by the recipient. Access permission alone is not knowledge.
2. Cross feasible within-case incentive conditions with baseline/truth-only/
   truth-plus-required-material-completeness instructions. In shared-task and
   oversight episodes, compare task-aligned incentives with conflicting local
   rewards. In bargaining, vary compensation or deal pressure while preserving
   each principal's mandate; both arms can remain mixed-interest interactions.
   Hold disclosure duties, documents, tools and decision options fixed. Record
   observed silence/omission behavior; do not instruct the agent to hide facts.
3. Audit factual assertions and material omissions against the case evidence.
   Missing information must matter under the task rules, not merely be omitted
   from a shorter summary. Record duties, outcome effects and incentive
   sensitivity separately. Legitimate confidentiality is a separate control.
4. Freeze the recipient before its consequential action. Create independent
   original (O), minimal required evidence (M), matched authorized nonmaterial
   evidence (P), and complete required-disclosure (F) continuations. F supplies
   all still-missing required evidence known to the sender for this recipient
   at this time. Keep discretionary and restricted information private. Updates
   contain facts without a recommended action and do not repair artifacts or
   change the world state. Cases without missing required facts remain controls
   without a restoration branch.
5. Test whether restoration affects the recipient's executed choice and native
   outcome. Register candidate minimal evidence sets before inspecting those
   outcomes; allow jointly necessary facts and fix a selection rule when several
   sets qualify. Define minimality from the evidentiary issue, not successful
   outcome repair. Match update source, timing and presentation, and review
   placebo irrelevance. Retain null and adverse restoration effects.
6. Add already-informed controls. When facts were accessible but unread, describe
   the intervention as presenting existing evidence rather than granting new
   information. Record access, reading and attention separately.

No-false-claim flags alone do not certify truthful transcripts. Invalid outputs,
refusals, unknown facts and failed operations retain their own denominators.
Report literal silence separately from communication containing material omissions.
Report total outcomes for all assigned episodes and omissions with both the
assigned-episode and knowledge-eligible opportunity denominators. Estimate
restoration effects conditional on qualifying omissions; omission-selected
subgroups can differ across incentive arms and cannot alone identify an incentive
effect. Study discretionary disclosure as information value, with its own
principal-specific costs, rather than treating all recipient gains as proof of
failure. F is a reference for required completeness, not an optimal-welfare oracle.

Information-access comparisons distinguish sender-exclusive, independently
retrievable and already-presented evidence. Initially record dependence, control
and temporal structure as case properties. Add matched variants only when the
native backend can isolate the intended dimension. Do not treat human and LLM
oversight as interchangeable observations or claim human validation from LLM runs.

## Existing benchmark reuse

[Inter-Agent Influence, Appendix B.3 and F.2-F.3](https://arxiv.org/html/2611.04556v1)
provides a methodology-review workflow and excludes strategic omission from its
false-claim score. The original draft also contains an explicit false statement,
and both agents can inspect the protocol and draft. Preserve the original task
for a benchmark audit; label altered documents or access conditions as our
extensions. The published methodology case is insufficient on its own for
cross-case generalization.

[KnownLieBench](https://arxiv.org/html/2608.26372v1) provides entitlement knowledge
checks and service interactions. It already includes omission-related analysis;
do not describe it as entirely omission-blind. Native refund actions are executed
by the service side. A customer-controlled outcome requires a separately labeled
extension, rather than attributing service-imposed outcomes to customer choices.

## Outcomes and implementation boundary

Measure case-defined incorrect dispositions, requirement violations, revision
failures, documented costs and recipient utility in their native units. Estimate
paired effects within cases and cluster inference by independent case family.
Keep downstream harm distinct from omission frequency and from the sender's
benefit. Do not pool unrelated losses into arbitrary points.

The current package only validates execution-record structure and constructs
restoration inputs with independent copied metadata. Its helpers do not validate
semantic truth, evidence minimality or legal/scientific correctness, fork an
external database, execute tools, or run model experiments. Native adapters and
reviewed cases must provide those capabilities before any substantive run.

Next deliverables are sourced development cases, native tool execution, reviewed
outcome rules, and a frozen within-case protocol. Model revisions, case counts,
statistical power and budget remain to be set after those checks.
