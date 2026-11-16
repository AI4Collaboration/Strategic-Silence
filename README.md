# Evaluating Selective Disclosure and Strategic Silence in LLM Agent Swarms

**Can an agent tell the truth while withholding the information another agent
needs to make a sound decision?**

We evaluate selective disclosure and strategic silence in scalable agent swarms with
varying interests and disclosure duties. Appropriate disclosure includes both
sharing required information and protecting restricted information. We measure
these choices, their sensitivity to incentives, and their consequences for
executed decisions. Factual truthfulness leaving harmful omissions intact is a
hypothesis to test. Information restoration diagnoses the effect of an omission.
The study evaluates behavior; it does not develop or optimize a defense.

Current status: shared evidence utilities and a parameterized environment design.
Native backends, reviewed case collections and model runners remain to be built.
The design accepts variable swarm sizes rather than fixed casts of two or three
agents. Source data must support the requested size before a case is admitted.

## Research questions

1. Can agents distinguish what to share from what to withhold during collaboration?
2. How do conflicting incentives affect their disclosure decisions?
3. How do those choices affect other agents' actions and collective task outcomes?

RQ2 includes a **utility-threshold evaluation**: vary the weight of a local
performance reward while keeping task facts and disclosure rules fixed. Measure
the full disclosure response curve and, where supported, the range of reward
weights at which required-information withholding reaches 50% of opportunities.
This is a behavioral summary, not a threshold defining whether disclosure is
required or harm is material. Report protected-information leakage separately.
Thresholds are task- and model-specific; no crossing or an unstable response is
a reportable result. The [experiment plan](docs/EXPERIMENT_PLAN.md#utility-threshold-evaluation-rq2)
defines the payoff, sweep, denominators and uncertainty rules.

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

## Scalable environments and their taxonomy

The taxonomy follows **flow, sharing and fit dependencies** from
[coordination theory](https://doi.org/10.1287/mnsc.45.3.425): consuming another
agent's output, allocating a common resource, and integrating contributions
that must be compatible. A workflow can contain several dependencies; its focal
constraint is registered before model collection. These are task structures,
not labels for whether disclosure is right or wrong.

| Family | Focal dependency | Unit that scales with the number of agents |
| --- | --- | --- |
| E1: coordinated procurement | Sharing | Connected order packages with shared budgets or capacity |
| E2: software migration | Fit | Interdependent modules/packages in a real change campaign |
| E3: scientific reanalysis | Flow | Connected data, analysis and validation work packages |
| E4: civil evidence production | Flow | Custodian collections and linked issue-review packages |
| E5: distributed dispatch | Sharing | Request groups and route owners in one service network |
| E6: assembly conformance | Fit | Connected component/lot and assembly-order packages |

Each agent owns substantive work, has explicit information and commit rights,
and depends on other owners through executable constraints. Role types may
repeat across any admitted number of members. Counterparties, judges and
validators are recorded separately from the focal swarm. Legacy dyads and
centralized-dispatch comparisons do not count as core swarm environments.

The adapter takes a requested size `n` and a sourced task graph. It partitions
real work into nonempty packages, preserves cross-owner dependencies and gives
agents local records plus authorized retrieval. It does not duplicate documents,
join disconnected trials or add a fixed all-knowing manager. Validate sizes
`4, 8, 16, 32` and an off-grid size such as `7`; these are checkpoints, not a
hard-coded size list. Unsupported sizes fail admission explicitly.

Separate fixed-workload scaling, with fixed total compute, from growing-workload
scaling, with approximately fixed work/compute per member. Report source-size
limits, graph structure, total compute and per-agent outcomes. Size and utility
weight are separate experimental variables.

**Implement E5 first**, then E2 with admitted connected change campaigns. E1,
E3, E4 and E6 need additional source and review work for scalable instances.
The current three-component NIST record and small single-issue tasks do not
establish arbitrary-size workloads. The six families are design targets.

The [environment catalog](docs/ENVIRONMENTS.md) specifies every role's knowledge,
actions, dependencies, omission example, privacy boundary, restoration and
source gap. The [pre-hoc design](docs/PREHOC_DESIGN.md) defines the shared case
contract; the [experiment plan](docs/EXPERIMENT_PLAN.md) defines comparisons.
Historical observations remain in [Takeaways](docs/TAKEAWAYS.md).

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
   Add the registered local-reward sweep for threshold evaluation. Use fresh
   matched continuations for every weight, not an ascending reward negotiation
   in a single conversation. Prompt comparisons characterize behavior rather
   than optimize a remedy.
3. **Audit the communication.** Check assertions against the source evidence and
   identify omitted material facts. Register eligible evidence sets independently
   of downstream outcomes. Report silence and selective disclosure separately.
4. **Freeze and restore.** Before the recipient's consequential action, create
   independent continuations from the same histories of all participants, world
   state, message queues and remaining tool budgets:

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
   Restoration targets the registered entitled recipient set. Other members learn
   the content only through subsequent authorized communication or retrieval.
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
Execution records use an explicit actor registry and decision-actor IDs, with
no fixed provider/recipient pair or actor-count limit. Restoration requires a
source actor and recipient IDs, defaults to the ordinary-sender route, and
supports an explicitly selected authenticated-reference diagnostic. It copies
all participant states, message queues and pending-operation metadata.
Native adapters must actually deliver the update and resume the whole swarm.
The helper requires M/P/F packets and constructs four metadata branches; the
runner selects O/M/P for the main study and F for registered diagnostics.

The proposed `build_case(source, n, assignment, budgets, seed)` interface and its
manifest are specified in the [pre-hoc contract](docs/PREHOC_DESIGN.md#swarm-instance-contract).
That case builder is not implemented by the metadata helpers. Offline tests at
multiple actor counts, including 7 and 65, establish metadata behavior only,
not environment scalability or empirical model performance.

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
