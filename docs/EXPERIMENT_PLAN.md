# Experiment design

Status: candidate workflows and shared evidence utilities. No native environment
backend or admitted case collection is implemented. No model experiment has been
run for this design, and paid collection is not authorized.

## Research question

When do agents leave out known, decision-relevant information, including while
making only true statements? Does that omission alter another agent's action and
cause avoidable loss? [Takeaways](TAKEAWAYS.md) distinguish earlier observations
from conditions that remain hypotheses.

## Candidate workflows

These are concrete candidates, not a settled theoretical taxonomy.

| Workflow | Roles and native decision | Material omission example | Readiness |
| --- | --- | --- | --- |
| Legal: commercial contract dispute | Two representatives submit and contest evidence; an adjudicator requests records and issues a disposition | Original deadline and delivery date are presented while an agreed extension is withheld | New case dossiers and execution backend required |
| Commercial: enterprise procurement | A vendor provides product evidence; a buyer investigates, evaluates alternatives and places an order | A known limitation conflicts with an explicit buyer requirement but is absent from the account | New case dossiers, procurement tools and acceptance checks required |
| Scientific: methodology review | A report writer presents evidence; a reviewer inspects the protocol and files, then approves or requests revision | A required analysis or material deviation is omitted from the report | Adapt the Inter-Agent Influence workflow; new omission-isolating cases required |
| Customer service: entitlement negotiation | A service agent presents policy and options; a customer checks eligibility and accepts or contests an offer | A less useful option is explained while an applicable entitlement remains undisclosed | Existing-benchmark validation candidate; recipient decision authority must be audited |

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

1. Establish knowledge from actual observations or retrieval receipts. Separate
   sender-exclusive information, recipient-accessible but unread evidence, and
   information already seen by the recipient.
2. Cross aligned/conflicting objectives with baseline/truth-only/truth-plus-
   material-completeness instructions. Preserve other instructions, documents,
   tools and decision options. Record the observed silence/omission behavior;
   do not explicitly instruct the agent to hide facts.
3. Audit factual assertions and material omissions against the case evidence.
   Missing information must matter under the task rules, not merely be omitted
   from a shorter summary. Legitimate confidentiality is a separate control.
4. Freeze the recipient before its consequential action. Create independent
   original (O), minimal evidence (M), matched irrelevant evidence (P), and full
   permitted evidence (F) continuations. Updates contain facts without a
   recommended action and do not repair artifacts or change the world state.
5. Check that restoration affects the recipient's executed choice and native
   outcome. Register candidate minimal evidence sets before inspecting those
   outcomes; allow jointly necessary facts. Match update source, timing and
   presentation, and review placebo irrelevance.
6. Add already-informed controls. When facts were accessible but unread, describe
   the intervention as presenting existing evidence rather than granting new
   information. Record access, reading and attention separately.

No-false-claim flags alone do not certify truthful transcripts. Invalid outputs,
refusals, unknown facts and failed operations retain their own denominators.
Report literal silence separately from communication containing material omissions.

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
