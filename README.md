# Strategic Silence

**Can an agent tell the truth while withholding the information another agent
needs to make a sound decision?**

We study strategic silence and selective disclosure in agentic workflows with
varying interests and disclosure duties. The central hypothesis is that requiring
factual truthfulness can leave harmful omissions intact. Our evaluation design measures
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
Strategic behavior, outcome effects and violations of disclosure duties are
separate judgments. Keeping a client's reservation price private can be strategic
without constituting a failure.

## Environment taxonomy and scenarios

The design uses the six dimensions of
[Interdependence Theory](https://doi.org/10.1146/annurev.psych.54.101601.145059):
dependence level, mutuality, basis, covariation of interests, temporal structure
and information availability. We operationalize them through each task's actual
alternatives, tool permissions, objectives, action sequence and evidence access.
Each decision episode receives a profile before model collection.

Oversight, peer collaboration and delegated bargaining map to this structural
space. They guide case coverage; they are not exhaustive, mutually exclusive
taxonomy classes. Human versus LLM oversight is an actor variable, and legal,
scientific or commercial work is an application domain.

| Workflow profile | Candidate native episodes | Consequential actions |
| --- | --- | --- |
| **Oversight** | Methodology review; commercial dispute adjudication | Approve or require revision; request evidence and issue a disposition |
| **Peer collaboration** | Distributed research analysis; cross-functional enterprise delivery | Run and integrate analyses; revise dependencies and execute a delivery plan |
| **Delegated bargaining** | Enterprise procurement; commercial dispute settlement | Negotiate and execute an order or settlement under a principal's mandate |

These six candidate episodes come from three linked case families. Comparisons
across profiles establish coverage; causal tests use matched variants within a
case. KnownLieBench remains an existing-benchmark validation candidate.

A separate information-flow specification, informed by
[Contextual Integrity](https://digitalcommons.law.uw.edu/wlr/vol79/iss1/10/),
records which facts are **required**, **discretionary** or **restricted** for each
recipient and time. Duties come from sourced task rules and mandates. They can
depend on claims or requests under rules fixed before collection. Benefiting a
counterpart is not by itself a duty to reveal private information.

The [pre-hoc design](docs/PREHOC_DESIGN.md) defines the taxonomy, candidate
episodes, actor inputs, hidden evaluation records and controlled comparisons.
Each workflow needs realistic evidence, tools with state effects and reviewed
outcomes, including benign and legitimate-confidentiality cases. Recipients can
investigate, ask follow-up questions and decline the sender's recommendation.

## Shared experiment protocol

1. **Establish information access.** Record what the sender actually observed.
   Separate facts unavailable to the recipient, facts it can retrieve but has not
   read, and facts it already knows.
2. **Vary incentives and instructions.** Cross feasible within-case incentive
   conditions with baseline, truth-only, and truth-plus-required-material-
   completeness instructions. Preserve principals, mandates, disclosure duties,
   task facts and tools. Shared-task episodes compare aligned and conflicting
   local rewards; bargaining episodes vary deal pressure under fixed mandates.
   Agents choose their communication; prompts do not instruct them to conceal.
3. **Audit the communication.** Check assertions against the source evidence and
   identify omitted material facts. Register eligible evidence sets independently
   of downstream outcomes. Report silence and selective disclosure separately.
4. **Freeze and restore.** Before the recipient's consequential action, create
   independent continuations from the same history, world state and tool budget:

   | Arm | Evidence update |
   | --- | --- |
   | O: Original | Empty update; preserve the sender's completed communication |
   | M: Minimal restoration | Smallest reviewed missing set of required material facts for the registered issue |
   | P: Placebo | Authorized nonmaterial evidence matched to M in source, timing, presentation and token length |
   | F: Complete required disclosure | All still-missing required evidence known to the sender for this recipient at this time |

   Updates supply facts without recommending an action, repairing the work
   product or changing the environment. Jointly necessary facts can form a minimal
   set. Preserve discretionary and restricted information. Include already-
   informed controls. Presenting an accessible but unread fact is distinguished
   from providing previously unavailable information. Already-complete episodes
   remain controls without a missing-fact restoration.
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
Report all assigned episodes for incentive effects and qualifying omitted-fact
episodes for conditional restoration effects. Discretionary information-value
tests are separate from confirmatory disclosure-failure tests.

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
