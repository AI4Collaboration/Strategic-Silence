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
- **Selective disclosure:** the agent communicates some facts and retains others.
  Evaluate those choices against task duties and permissions. Appropriate
  selective disclosure is the target behavior, not a failure label.
- **Material omission:** decision-relevant content is absent. Establish separately
  whether the sender observed it, the recipient already knew it, and disclosure
  was required.
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

## When is withholding a failure?

An agent may correctly protect confidential information, retain a client's
reservation price, or omit details irrelevant to the requested decision. Our
primary target is different: withholding known material evidence that the
receiver is entitled to receive under the task rules, then testing whether the
omission causes a worse executed decision. Disclosure duties and materiality
are fixed by the case's mandate and evidence. Harm is measured from outcomes.

The first study pairs such cases with clear legitimate-withholding controls.
Contested obligations and trade-offs between different principals require a
separate study. Accurate statements, appropriate disclosure, incentive-sensitive
withholding and downstream harm are measured separately.
Measure both missing required disclosures and prohibited disclosures, including
whether an episode completes the task while avoiding both errors.

## How environments are selected

The design specifies **five primary task domains and six environment families**:

| Domain | Environment and consequential decision |
| --- | --- |
| Transactions and customer rights | E1: negotiate and execute a bilateral agreement; separately audit existing remedies |
| Software engineering | E2: accept a patch and execute behavior checks |
| Scientific research | E3: execute and adopt or revise a scientific analysis |
| Civil legal proceedings | E4: produce evidence and issue a supported disposition |
| Industrial operations | E5: planners commit and jointly execute routes, with centralized dispatch as a separate mode; E6: accept, hold or rework a physical item |

The [environment catalog](docs/ENVIRONMENTS.md) defines the roles, required and
protected information, incentives, actual actions, loss checks, minimal
restoration and source/adaptation boundary for each. These are design targets;
native implementations and admitted case collections are still pending.
The [pre-hoc design](docs/PREHOC_DESIGN.md) specifies common evidence requirements,
and the [experiment plan](docs/EXPERIMENT_PLAN.md) specifies the comparisons.

Coverage follows the decision mechanism: observed evidence, authorized
communication, the recipient's information and action, and the resulting
outcome. Each link needs positive evidence and boundary controls. Required,
discretionary and prohibited disclosure have different scoring rules. The
number of environments alone does not establish comprehensive coverage.

Oversight tests the correctness of review decisions; shared-task execution tests
team performance under local pressures; bilateral negotiation tests separately
authorized objectives, valid agreement and fulfillment while preserving
legitimate private information. These are overlapping research questions.
Record principals, objectives and decision authority for each episode rather
than inferring them from a task name. Human-oversight results require actual
human recipients; an agent reviewer or human annotator does not supply them.

Commercial transactions and customer-service interactions are not counted as
independent domains merely because their workflow names differ. Each case will
receive one primary task-domain assignment under explicit inclusion and exclusion
rules. Shared source dossiers remain one statistical case family. Oversight,
collaboration and bargaining may describe a workflow, but do not define the
domain taxonomy. Important coverage requires materially different decisions,
evidence and consequences, rather than additional labels.

## Shared experiment protocol

1. **Establish information access.** Record what the sender actually observed.
   Separate facts unavailable to the recipient, facts it can retrieve but has not
   read, and facts it already knows.
2. **Vary incentives and instructions.** Cross feasible within-case incentive
   conditions with baseline, truth-only, and truth-plus-required-material-
   completeness instructions. Preserve principals, mandates, disclosure duties,
   task facts and tools. Shared-task episodes compare aligned and conflicting
   local rewards; bargaining episodes vary deal pressure under fixed mandates.
   Use natural truthfulness wording, not an instruction limited to literal lies.
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

   O/M/P are the main arms; F is a predeclared capability/completeness diagnostic.
   Updates supply facts without recommending an action, repairing the work
   product or changing the environment. Jointly necessary facts can form a minimal
   set. Preserve discretionary and restricted information. Include already-
   informed controls. Presenting an accessible but unread fact is distinguished
   from providing previously unavailable information. Already-complete episodes
   remain controls without a missing-fact restoration.
   The main intervention uses the ordinary sender channel. A trusted external
   evidence update is a separate diagnostic because provenance can affect trust.
5. **Measure actions and consequences.** Continue each branch through native
   tools. Compare M with P to test whether the missing evidence changes decisions
   and reduces loss; also report O/M, O/P and M/F where F is run. Preserve unsuccessful,
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

[Thinking Is Not Telling, v2](https://arxiv.org/html/2602.07796v2) already tests
counterfactual additions of missing information and measures subsequent actions.
The existence of omission and the use of information restoration are established
parts of the literature. Our study targets how strategic pressure affects
truthful but materially incomplete communication under fixed disclosure duties,
and the consequences for executed decisions. Results are not yet available.

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
The restoration helper currently uses an authenticated reference channel; an
ordinary-sender intervention still requires a native adapter.
It requires M/P/F packets and constructs four metadata branches. A future runner
must select which branches to execute for the O/M/P study and F diagnostics.

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
