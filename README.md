# Strategic Silence

**Can an agent tell the truth while withholding the information another agent
needs to make a sound decision?**

We study strategic silence and selective disclosure in agentic workflows with
conflicting interests. The central hypothesis is that requiring factual
truthfulness can leave harmful omissions intact. Our evaluation design measures
when agents withhold known material facts, whether those omissions affect
executed decisions, and whether restoring the missing evidence reduces loss.

Current status: shared evidence utilities and an experiment design. Native
environments, reviewed case collections and model runners remain to be built.

## What we measure

- **Literal silence:** no message is delivered during a valid communication
  opportunity on the specified channels.
- **Selective disclosure:** the agent communicates some facts while leaving out
  material information it knows and is permitted to disclose. Audit the factual
  accuracy of the statements as well as the missing information.
- **Strategic withholding:** evidence that disclosure choices respond to the
  sender's interests, assessed through matched incentive conditions and observed
  information access. A private-plan explanation alone does not establish intent.

Materiality comes from the case's decision criteria, evidence and task rules.
Concise summaries, unknown facts, protected information, refusals and invalid
outputs are distinguished from strategic withholding. Harm is measured separately
from omission: it requires evidence about the recipient's action and its outcome.

## Scenarios

The design has three core candidate workflows and one existing-benchmark
validation candidate. These are task choices, not a settled theoretical taxonomy.
All comparisons of incentives, instructions and restoration are paired within
the same case.

| Workflow | Agent roles and executed decision | Example of material omission | Development route |
| --- | --- | --- | --- |
| **Legal: commercial contract dispute** | Two representatives submit and contest evidence; an adjudicator requests records and issues a disposition | Original deadline and delivery evidence are submitted while an agreed extension is withheld | Build the case dossiers and adjudication environment |
| **Commercial: enterprise procurement** | A vendor presents evidence; a buyer inspects alternatives, places an order and checks acceptance requirements | A known product limitation conflicts with an explicit buyer requirement but is not disclosed | Build document-grounded procurement and acceptance tools |
| **Scientific: methodology review** | A report writer presents results; a reviewer inspects the protocol and files, then approves or requests revision | Required analyses or material deviations are absent from an otherwise factually accurate account | Adapt the Inter-Agent Influence review workflow and expand its cases |
| **Customer service: entitlement negotiation** | A service agent presents options; a customer checks eligibility and accepts or contests an offer | A less useful option is explained while an applicable entitlement remains undisclosed | Audit KnownLieBench; label changes to decision authority as extensions |

Legal cases concern ordinary delivery, quality, scope and payment disputes, with
explicit case rules and independently reviewed reference outcomes. Each workflow
needs realistic evidence, tools with actual state effects, and benign cases in
which the sender's requested outcome is justified. Recipients can investigate,
ask follow-up questions and decline the sender's recommendation.

## Shared experiment protocol

1. **Establish information access.** Record what the sender actually observed.
   Separate facts unavailable to the recipient, facts it can retrieve but has not
   read, and facts it already knows.
2. **Vary incentives and instructions.** Within each case, cross aligned versus
   conflicting objectives with baseline, truth-only, and truth-plus-material-
   completeness instructions. Keep the remaining task facts and tools fixed.
   Agents choose their communication; prompts do not instruct them to conceal.
3. **Audit the communication.** Check assertions against the source evidence and
   identify omitted material facts. Register eligible evidence sets independently
   of downstream outcomes. Report silence and selective disclosure separately.
4. **Freeze and restore.** Before the recipient's consequential action, create
   independent continuations from the same history, world state and tool budget:

   | Arm | Evidence update |
   | --- | --- |
   | O: Original | Empty update; preserve the sender's completed communication |
   | M: Minimal restoration | Smallest reviewed missing evidence set needed for the registered issue |
   | P: Placebo | Irrelevant evidence matched to M in source, timing, presentation and token length |
   | F: Full information | All permitted sender evidence available at that time |

   Updates supply facts without recommending an action, repairing the work
   product or changing the environment. Jointly necessary facts can form a minimal
   set. Include already-informed controls. Presenting an accessible but unread
   fact is distinguished from providing previously unavailable information.
5. **Measure actions and consequences.** Continue each branch through native
   tools. Compare M with P to test whether the missing evidence changes decisions
   and reduces loss; also report O/M, O/P and M/F. Preserve unsuccessful,
   incomplete and refused trajectories in the accounting.

The factorial comparison tests whether truthfulness instructions suppress false
assertions while leaving material omissions. Restoration tests the contribution
of the omitted evidence to the recipient's decision. Incentive comparisons test
whether withholding serves the sender's objective.

## Outcomes and existing benchmarks

Measure omission and false-assertion rates alongside executed decisions,
requirement violations, incorrect dispositions, documented costs and affected-
party outcomes. Keep native units and report within-case paired effects, with
uncertainty clustered by independent case family. Sample sizes, model revisions
and budget will be fixed after case and backend validation.

[Inter-Agent Influence](https://arxiv.org/html/2611.04556v1) provides an agentic
methodology-review workflow. Its false-claim scorer excludes strategic omission,
although its outcome measures can still register erroneous approvals. The
original case includes an explicit false statement, and both agents can inspect
the protocol and draft. An omission-isolating version must be labeled as an
extension of that original task.

[KnownLieBench](https://arxiv.org/html/2608.26372v1) provides entitlement knowledge
checks and service interactions, and already includes omission-related analysis.
Its native refund actions are controlled by the service side. A test of harm
caused by the customer's own choice needs a separately identified adaptation.

The planned contribution is a common evaluation protocol, systematic evidence
about when withholding occurs, and tests of its consequences across these
workflows and existing benchmarks. Results for this design are not yet available.

## What remains from the earlier pilots

[Takeaways](docs/TAKEAWAYS.md) preserves observations about private advantage,
dependence on an informed agent, stated protective motives, and truthfulness
versus completeness instructions. It labels observed patterns, reported pilot
leads and untested mechanisms separately.

The old games, mapping tasks, synthetic runners, results and figures have been
removed from the active codebase. Evidence remains accessible through pinned Git
history links. The [experiment plan](docs/EXPERIMENT_PLAN.md) records the current
case requirements and analysis design.

## Implementation and development

The package currently provides `restoration_inputs` and
`validate_action_evidence`. These utilities construct independently copied
checkpoint metadata and check references linking outcomes to tool receipts.
Native adapters must execute tools, isolate external state and supply reviewed
outcome rules. The helpers do not certify evidence semantics or run experiments.

## Offline checks

Python 3.10 or later:

```sh
python -m pip install -e ".[test]"
python -m pytest -q
```

The tests exercise metadata checks and independent copies. They make no model
requests. Paid experiment collection requires separate authorization.

```text
docs/                         Takeaways and current experiment design
src/disclosure_causality/      Scenario-independent evidence utilities
tests/                        Offline regression checks
.github/workflows/offline.yml  CI for the retained utilities
```

For authorized repository changes, run the relevant checks, commit the finished
work and push to the tracked remote branch. Keep private recovery checkpoints
local. The Overleaf manuscript and its conference template are maintained
separately.
