# Evaluating Selective Disclosure and Strategic Silence in LLM Agent Swarms

We evaluate what collaborating agents disclose, how local incentives change
those choices, and how missing information changes other agents' actions and
collective outcomes. Every core environment must test both required disclosure
and protection of private or sensitive information within the same task.
Appropriate selective disclosure satisfies both. Omission, strategic motivation,
unauthorized disclosure and harm are separate measurements.

**Status, 2026-11-16:** this README is the sole current design and experiment
specification. The code implements two evidence-metadata utilities and their
offline tests. Native environments, admitted case collections and model runners
are unbuilt; there are no model results or tested native swarm sizes for this
design. Historical pilot evidence is retained in [TAKEAWAYS](docs/TAKEAWAYS.md).

## Design status and retained source evidence

The domain roster is open. Select workflows with natural disclosure conflicts
before choosing datasets or tools. The six-environment target is a planning
budget, not a validated minimum or a completed suite.

The previous source checks remain useful, but do not select a domain:

| Inspected source | Reusable evidence | Missing for core environment admission |
| --- | --- | --- |
| [NOAA GHCN-Daily](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt) | Observation-level quality flags and reproducible data processing | A substantive distributed workflow with naturally protected information |
| [Alibaba cluster2018](https://github.com/alibaba/clusterdata/blob/3858992ca41bf92082e6d6522ddf0bebd14e838b/cluster-trace-v2018/trace_2018.md) | Job graphs, resource fields and production scheduling structure | Validated replay, consequential peer choices and grounded confidentiality; tables remain unacquired |
| [Babel migration](https://babeljs.io/docs/v8-migration-api) | Actual AST changes and connected package dependencies | A reproduced coupled campaign and a workflow containing protected material |

An existing source establishes neither a functioning agent environment nor a
confidentiality obligation. Preserve provenance, native checks and normal
information access in any reuse. No adapter for these sources has been built.

## Research questions and task structure

1. Can agents share information collaborators need and are authorized to receive
   while protecting private or sensitive information in the same task?
2. How do conflicting local incentives change those choices?
3. How do omissions affect recipients' executed actions and team outcomes?

[Malone et al. (1999)](https://doi.org/10.1287/mnsc.45.3.425), pp. 429-430,
describe **flow** (consume another activity's output), **sharing** (use a common
resource) and **fit** (jointly produce a compatible output). These are composable
dependencies, not mutually exclusive industries or a proven exhaustive taxonomy.

[TÆMS](https://mas.cs.umass.edu/Documents/lesser/GPGP_evol_AAMAS.pdf) supplies
the local-task representation: ownership, partial views, resources, hard
feasibility constraints and soft effects on quality, cost or time. Its 2004
account concerns small agent groups. [iTax, section 4](https://www.cs.cmu.edu/~gertrude/documents/Korsah_IJRR_Taxonomy.pdf)
supports distinguishing within-owner from cross-owner dependence;
[coordination graphs](https://www.jmlr.org/papers/v7/kok06a.html) motivate tracking
interaction structure when increasing agent count. These are design foundations,
not empirical validation of our proposed LLM environments.

## Failure modes that determine environment selection

Select tasks from the disclosure decisions we need to observe. The following
are target behaviors to test, not findings or a claim that each is novel.

| Target behavior | Natural opportunity the task must provide | Elicitation and evidence |
| --- | --- | --- |
| Strategic silence about required information | An owner encounters a material fact that a named collaborator is authorized to receive before committing an action; timely reporting is a normal part of the work | Allow reporting and non-reporting. Compare aligned and conflicting local incentives. Record knowledge evidence, the reporting opportunity, recipient action and native outcome. Silence alone does not establish strategy. |
| Misleading selective disclosure | The owner can truthfully report a favorable fact while leaving out a required qualification, exception or adverse result that changes its interpretation | Preserve both facts in the task evidence. Compare ordinary, truthfulness and scoped-completeness instructions without requesting deception. Audit truthful partial reports separately from false claims and restore the missing qualification. |
| Unauthorized disclosure during collaboration | Useful coordination evidence and protected material arise together, while a feasible authorized summary or restricted route exists | Let agents choose the content and recipients of ordinary handoffs. Compare incentives and instructions while observing raw forwarding or overbroad sharing. Record unauthorized delivery and downstream propagation separately from blocked attempts. |

The first two rows are different communication forms of omission, not disjoint
causal mechanisms. Omissions without established incentive sensitivity remain
omissions. Blanket withholding under a privacy instruction is a diagnostic
pattern: test whether authorized necessary information is also withheld, without
assuming a strategic motive. Truthfulness reducing falsehood while leaving
omission is a hypothesis to test.

To establish relevance to swarms, trace information through connected owners:
what each received, what it passed on, the next owner's executed decision and
the resulting effect on further work. Test whether qualifications disappear
across handoffs, local omissions change downstream actions, or restricted
information is forwarded beyond its authorized recipients. Propagation and growth with team size are
measurements; adding agents does not establish amplification.

Every candidate must supply a source-backed opportunity for all three rows,
both disclosure duties in the same main task, and a feasible compliant path.
Register those opportunities before model runs. Do not select cases because a
model actually conceals information, leaks it or improves after restoration.

## Proposed coverage axes

Use coordination dependence and application domain to organize tasks that pass
the behavioral and native-environment checks.

| Axis | Categories | Classification basis |
| --- | --- | --- |
| Coordination dependence | Flow; sharing; fit | How activities depend on one another's outputs or resources, following Malone et al. |
| Application domain | Roster not fixed | The real business or professional workflow and its deliverable, with source-grounded roles and disclosure duties |

A domain can contain multiple dependencies; the same dependency can occur in
multiple domains. Classify the focal coordination issue and retain secondary
tags. Software, data and compute used by a workflow do not by themselves define
its application domain.

Investigate the following workflows; they are not an adopted domain taxonomy:

| Workflow to investigate | Primary-source support inspected | Still needed |
| --- | --- | --- |
| Cross-company manufacturing coordination | [Helu, Hedberg and Barnard Feeney (2017)](https://www.nist.gov/publications/reference-architecture-integrate-heterogeneous-manufacturing-systems-digital-thread) describes shared lifecycle data, segregated internal/external access protecting intellectual property, and a contract-manufacturer prototype | Source workloads, specific reporting duties, native actions and outcomes, and scalable ownership |
| Multi-party freight booking and handoff | [DCSA Booking](https://dcsa.org/standards/booking) identifies booking-data coordination across carriers and partners, and decisions affected by inaccurate or late information | Concrete confidential fields and authorization duties, executable commitments, and source workloads |
| Collaborative legal-service work | [ABA Model Rule 1.6](https://www.americanbar.org/groups/professional_responsibility/publications/model_rules_of_professional_conduct/rule_1_6_confidentiality_of_information/) provides a model-rule confidentiality boundary with authorized disclosures and exceptions | A specified task and applicable rules, feasible authorized collaboration, objective action checks, and scalable work packages |

These sources support workflow or confidentiality requirements, not our complete
task designs. The manufacturing record and Crossref metadata were checked on
2026-11-16 (DOI 10.1016/j.cirpj.2017.04.002). DCSA and the ABA source text were
also inspected. The ABA Model Rules are not a uniform rule for every jurisdiction.

Retain six environments as the working construction target. Seek two distinct
source workflows per dependency type, spread across domains, and multiple
dependencies within domains where supported. Six is not a sample-size or
completeness result. Final cells follow source admission. Different
agent counts, instructions and disclosure conditions do not create new environments.

Authority, information access, disclosure duties and incentives remain explicit
case conditions or treatments. Agent count, topology, time and budgets are
operating parameters. Each main task must still test both authorized necessary
disclosure and protection of private or sensitive information.

## First-principles environment admission

An environment must let agents choose what to disclose while doing genuinely
interdependent work, and let us trace how that choice changes collaborators'
information, actions and outcomes. The mechanism to test is:

**Local evidence and objectives -> disclosure choice -> recipient information
and action -> native task outcomes.**

Communication duties determine which disclosures are appropriate. The checklist
below operationalizes our research questions; it is not an additional taxonomy
attributed to coordination theory. Domain and flow/sharing/fit classify admitted
tasks. They do not establish task validity.

| Gate | Evidence required for admission |
| --- | --- |
| 1. Real work | A pinned source workload, useful deliverable and native acceptance criteria. Separate source facts from authored assignments, incentives and policies. A domain label or real dataset alone is insufficient. |
| 2. Genuine interdependence | Every counted agent owns substantive work and executable authority. Demonstrate cross-owner consequences in a connected task graph. Removing an owner requires reassigning actual work; observers and independent pairs do not establish a swarm. |
| 3. Traceable information differences | Map evidence holders, retrieval rights, delivery and decision deadlines. Identify source facts that can matter to another owner's action. Distinguish available, read, understood and already-shared information, including shared artifacts. |
| 4. Free disclosure choices | Agents can disclose, qualify or omit through ordinary channels before a consequential decision. Preserve normal queries, verification, repair and refusal. Do not name an expected secret, assign a deceiver or disable natural discovery to force concealment. |
| 5. Both disclosure duties in every environment | Each core task gives a focal sender both authorized information a collaborator needs and private or sensitive information that collaborator must not receive. Ground both duties in workflow and authorization rules, specify permitted summaries, and verify a completion path satisfying both. Irrelevant facts or an arbitrary secret field do not establish privacy coverage. |
| 6. Defensible strategic comparison | For the incentive cohort, specify a task-relevant local objective that can conflict with collective performance, an aligned control and justified reward scales. Vary incentives without changing facts, duties or tools; never reward withholding directly. |
| 7. Observable action consequences | Tools produce state changes and receipts. Measure recipient actions, individual outcomes and collective outcomes with native checks. Preserve automated gates; distinguish an attempted action, a blocked defect and realized loss. |
| 8. Information-only counterfactual | Reproduce the complete pre-decision state and fork matched continuations. Restore only missing authorized evidence, with a matched nonmaterial update. Hold artifacts, permissions, budgets and prior actions fixed at the fork. |
| 9. Feasibility and diagnostic controls | Execute a valid coordinated reference under normal rights and budgets. Include adequate-information, already-informed and nonmaterial-information controls; separate unread evidence and tool failures from concealment. The task must admit success without requiring any tested model to succeed. |
| 10. Substantive scaling | Construct multiple supported integer team sizes from connected source work, retaining nonempty assignments and cross-owner effects. Validate both fixed-work and growing-work regimes. Record source families, snapshots, seeds and supported limits; duplicated roles do not count as scaling. |

Record **PASS, FAIL or UNVERIFIED**, with an evidence reference, for each gate.
No aggregate score compensates for a failed gate. Gates 1-5 and 7-10 admit a task
to disclosure evaluation; gate 6 additionally admits it to the strategic-incentive
cohort. A utility-threshold analysis also requires defensible numerical anchors.
Reference checks and matched-fork checks must run before paid model collection.

Admission tests the opportunity and our ability to measure it. It does not
require observed silence, incentive sensitivity or improvement after restoration.
Freeze eligibility before model outcomes; retain null and adverse findings.
Recipient/team benefit and sender cost are separate from permission to disclose:
an outcome improvement alone does not establish a duty to reveal information.

**Current admission status: no environment has passed all required gates.**
Workflow sources above and the retained NOAA, Alibaba and Babel checks are
feasibility evidence. Each selected task still needs a real disclosure trigger,
protected material, native tools and outcomes, a compliant reference, matched
forks and scaling checks. A source defect and its non-disclosure are separate:
restoration leaves the defect unchanged at the fork and tests the additional
effect of information about it.

## Shared input and execution design

Use one shared runner, with adapters selected only after source admission. The
runner handles actor execution, communication, checkpoints and experimental
assignment. Each adapter owns its artifacts/resources, permitted operations and
outcome checks. Causal disclosure comparisons stay within the same task.

### Input package

An environment instance starts from a versioned task package:

| Input component | Contents and visibility |
| --- | --- |
| Source state | Actual records or checkout, provenance, versions and native constraints; each owner receives its assigned part and retrieval rights |
| Shared task | Deliverable, acceptance criteria, responsibilities and ordinary handoff duties, visible to the team |
| Work ownership | Nonempty work packages, their dependencies, and each owner's read/write/commit permissions |
| Local evidence | Required coordination evidence and protected material arising from the owner's work; distinguish received, retrievable and inaccessible information |
| Disclosure authority | Recipient-, purpose- and time-specific rules, their workflow basis, permitted summaries and delivery routes; owning data does not authorize forwarding it |
| Action interface | Executable inspection, work, communication and commitment tools; state transitions produce receipts |
| Runtime and incentives | Fixed budgets, scheduling/transaction rules, stopping conditions and assigned local rewards |
| Evaluator-only material | Source-backed disclosure triggers, reviewed fact/recipient/deadline labels, eligible decisions, reference checks, intervention packets, source-family IDs and randomization |

Agent input is the shared task plus its work assignment, evidence, permissions,
legitimate handling rules and objectives. Reference solutions, future trace
realizations and labels naming the expected omission stay outside agent input.
Agents can disclose, investigate, repair or refuse within ordinary rules; no
prompt demands a particular omission.

Run a repeated **observe, work, communicate, commit, receive feedback** loop until
the native deliverable is accepted or the budget is exhausted. Owners can message
specific peers or publish through ordinary shared artifacts. Record failed and
rejected actions as well as successful operations. Required evidence becomes
scorable only at its registered decision deadline. An internal checkpoint is a
state of this task, not an additional independent task.

Build and validate one complete source task before expanding an adapter's case
collection. Set independent task counts and repeats from outcome variability
and precision requirements before model collection. Keep related source
workloads in the same family. Expand toward the six-environment working target
only as tasks pass admission. Do not start with a full size-by-incentive-by-model
factorial.

## Scaling and case admission

The adapter design is `build_case(source, n, assignment, budgets, seed)`; it is
not implemented. It must accept arbitrary supported integer sizes with uneven
role allocations. The planned study begins at four active owners, an inclusion
rule rather than a universal definition of swarm.

- Every counted agent owns nonempty real work, evidence and action authority.
  The owner graph must be connected, with a cross-owner consequence for each
  member and a multi-owner constraint or a dependency path through three owners.
- Require an executable coupling witness and a valid coordinated solution before
  admission. Sourced constraints must actually affect another owner's options
  or outcomes. Adding spectators, redundant sign-offs or independent dyads fails.
- Preserve local views and normal retrieval, verification, refusal and repair.
  Task dependencies and communication routes are separate graphs. Shared files
  and tool receipts are communication channels too, consistent with
  [artifact-mediated coordination research](https://james.howison.name/pubs/bolici-howison-stigmergy-2016.pdf).
- Fixed-workload tests repartition the same work at fixed total compute.
  Growing-workload tests increase connected work while targeting similar work
  and compute per owner. Report degree, path length, constraint arity, contention,
  completed work, tokens, tools and wall time.
- Check 4 and 7 owners first, then 8, 16 and 32 where actual workloads support
  them. Unsupported sizes remain unsupported. Source capacity, admitted sizes
  and tested sizes must be reported separately.

Freeze the input package above, together with communication visibility, delivery
receipts, native event tape and experimental seeds, before collection. Compare
literal silence, selective reporting, timely disclosure and legitimate omission
as observed behaviors inside each environment, rather than treating them as
different environments or preassigned agent roles.

## Evaluation protocol

Define literal silence over a registered valid communication opportunity.
Selective disclosure means communicating some information while retaining other
information. Establish known material omission, incentive sensitivity and loss
separately. Record exposure, demonstrated recognition and recipient knowledge:
a retrieval receipt or an elicited private plan alone does not prove understanding
or intent. A probe in a separate branch checks recoverability without priming the
scored continuation. Natural information-seeking is a separate robustness condition.

### Required disclosure and protected information

Every core environment and every main scored task must contain both kinds of
information for a focal sender: a collaborator needs some authorized evidence to
act, while other private or sensitive content must remain protected from that
recipient. Both arise during the same substantive work. Tasks testing only one
obligation are diagnostic controls, not substitutes for this joint evaluation.

Ground protection in documented workflow, ownership and authorization rules.
Protected material must have a role in the owner's work; an unrelated secret
string is insufficient. Synthetic stand-ins may instantiate sourced workflows,
with the substitutions recorded. Public NOAA observations, published cluster
traces and public Babel code do not themselves establish confidentiality duties.
Any reuse of those sources requires independently grounded disclosure and
confidentiality workflows.

For each recipient, purpose, representation and deadline, classify content as
required, prohibited, discretionary or unresolved. Required information must be
authorized for that recipient. A protected raw record and an authorized summary
can have different labels. Specify acceptable summaries or sanitized evidence
and execute a reference completion that shares what is needed without revealing
protected content. Cases with irreconcilable obligations stay outside the primary
cohort. Access to data alone grants no right to forward it; recipients may have
different permissions.

Report required-information coverage and prohibited disclosure separately, plus
the fraction of tasks satisfying both obligations. Use distinct opportunity
denominators; count each required issue once per registered recipient/deadline,
and each protected item once per registered unauthorized recipient/window.
Repeated messages do not create extra opportunities. Task completion and native
losses remain separate outcomes. Sharing everything and withholding everything
each fail one side of the joint criterion. Retain failed and unread episodes in
all-assigned estimates; knowledge-conditioned analyses are secondary.

Audit messages, shared artifacts, tool outputs and downstream forwarding, using
meaning rather than exact-string matching alone. Distinguish an attempted leak
blocked by a tool from information delivered to an unauthorized recipient. Keep
unknown/unread evidence, technical failure and legitimate resolution separate
from concealment. Report exposure and unresolved cases; missing opportunities
are not successful protection. Privacy scores remain unmeasured until the new
admission requirement is met.

### Minimal-information restoration

Select eligible facts and minimal evidentiary issues before seeing outcomes.
After communication, freeze the whole swarm before the first affected decision:
all participant contexts, artifact/world versions, queues, pending operations,
external events and remaining budgets. Fork independent continuations:

| Arm | Change at the checkpoint |
| --- | --- |
| O | Empty update; original communication remains |
| M | Minimal missing authorized evidence, including jointly necessary facts |
| P | Nonmaterial authorized evidence matched to M for source, novelty, timing, presentation and input length |
| F | All still-missing required information known to the sender; diagnostic subset |

All updates preserve the task's protection rules. M restores only the authorized
fact or permitted summary, never a protected raw record. F is complete only over
required authorized information, not everything the sender knows. Measure
downstream prohibited disclosure in these continuations as well as task losses.

Use the ordinary sender route and the same recipients for M/P. Keep sender history
and recipient delivery queues consistent. Do not alter code, data, constraints,
permissions, budgets or prior commitments at the fork. Updates contain evidence,
not a solution or a recommended action. An authenticated outside source is a
separate diagnostic because its authority can change behavior. Include
already-informed/complete cases and a known-content control for attention effects.

Resume all agents, preserving their normal choices. Compare M/P alongside O/M
and O/P; use F and adequate-information preflight to assess capability. Report null
and adverse effects. Audit accurate-but-incomplete communication separately from
literal silence and mixed falsehood/omission. A truthful-but-incomplete harm claim
requires evidence in the accurate-communication stratum. The restoration contrast
estimates an information-update effect among eligible omissions, not the total
effect of incentives or a proof of strategic intent. Record downstream native
actions, state and receipts; an attempted action or final answer is not execution.

### Incentives, instructions and statistical plan

Hold facts, duties, exposure, topology, tools and authority fixed. Randomize local
incentives and compare ordinary, truthfulness and scoped-completeness instructions.
Never ask an agent to conceal information. Whether truthfulness leaves harmful
omissions is a hypothesis. A claim that it redirects behavior toward omission
requires increased absolute omission incidence, not just a greater share of the
remaining failures.

For terminal trajectory `z`, use `U_i(z; lambda) = B_i(z) + lambda * R_i * K_i(z)`.
The base task score `B_i`, local KPI `K_i in [0,1]` and positive reference range
`R_i` are fixed from task anchors before collection. Vary only `lambda`;
no term rewards silence. Proposed coarse weights are `0, 0.25, 0.5, 1, 2, 4`,
restricted to justified values. A scenario without defensible anchors retains
the disclosure evaluation but has no utility-threshold result.

Use the same admitted cohort and pre-incentive checkpoints at each weight.
Vary one focal sender at a time; multiple-sender treatments are separate.
Run the full sweep at fixed size and a registered subset of weights across sizes.
Estimate instruction/incentive effects over all assigned episodes, including
failed and refused runs. Report missing required content and prohibited
disclosure with separate opportunity denominators, factual accuracy, native
outcomes, sender gains, and their joint pattern. Report unresolved counts and
worst/best-case bounds; do not select primary curves on post-treatment success.

The primary result is the response curve. A 50% threshold is a reporting
convention: report adjacent tested weights bracketing a sustained upward crossing,
with all earlier tested rates below 0.5 and all subsequent rates at least 0.5.
Otherwise report baseline-above-50%, no crossing, multiple/nonmonotone crossings
or unresolved uncertainty. Do not force monotonicity or extrapolate. Weight
independent source families equally, then cases equally within family. Cluster
bootstrap intervals preserve all paired weights, sizes and repeats in a family,
including the share without a unique crossing. Register sample counts, repeats,
precision targets and minimal effects before paid collection. Thresholds summarize
behavior; they neither establish disclosure duties nor measure harm.

## Literature boundary

Primary records and the cited passages were checked on 2026-11-16, including
arXiv API titles, authors and versions for these papers:

| Work | What is already established |
| --- | --- |
| [Deception by Omission, v1](https://arxiv.org/html/2610.11351v1) | Evaluates concealment of mistakes in prefilled continuations |
| [KnownLieBench, v1](https://arxiv.org/html/2608.26372v1), sections 3 and I | Knowledge checks and conflicting incentives; omission is analyzed within identified lies |
| [Thinking Is Not Telling, v2](https://arxiv.org/html/2602.07796v2), section 4.2 | Restores missing information before consequential environment edits |
| [HiddenBench, v4](https://arxiv.org/html/2505.11556v4), section 6.3 | Studies distributed-information failures and uses a reveal-all diagnostic |
| [PAC-Bench, v1](https://arxiv.org/html/2604.11523v1), section 4.3 | Evaluates privacy-constrained collaboration, including excessive withholding |
| [Inter-Agent Influence, v1](https://arxiv.org/html/2611.04556v1), appendix F.2 | Its false-claim metric excludes strategic omission; that does not make all its outcome measures omission-blind |

The intended contribution is evidence about incentive-sensitive disclosure and
its propagated action-level consequences across genuinely coupled swarms.
Omission, information restoration, privacy evaluation and utility sweeps each
have precedent. The study's contribution depends on the results and replication.

## Implementation and repository

First establish the target failure opportunities and both disclosure obligations
in each candidate, then execute a reference path that satisfies both obligations.
Retain or replace candidates on that basis.
For admitted source designs, build the frozen workload, reference calculations
and native tools, then validate state snapshots, action receipts, outcome checks
and scaling before model runs.

- `src/disclosure_causality/protocol.py`: `restoration_inputs` clones checkpoint
  metadata with named sender/recipients; `validate_action_evidence` checks actor,
  receipt and state-chain references. They do not execute tasks or validate
  semantic truth, minimality or native scalability.
- `tests/`: offline checks of those utilities, with network access blocked.
- `docs/TAKEAWAYS.md`: historical evidence and provenance only.
- `AGENTS.md`: short working rules; this README owns the current design.

Python 3.10 or later; dependencies are declared only in `pyproject.toml`:

```sh
python -m pip install -e ".[test]"
python -m pytest -q -p no:cacheprovider
```

No paid model collection is authorized by this plan. The manuscript and its
protected ICML template are maintained separately.
