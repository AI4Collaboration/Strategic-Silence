# Evaluating Selective Disclosure and Strategic Silence in LLM Agent Swarms

We evaluate what collaborating agents share or withhold, how incentives change
those choices, and how their communication affects others' executed actions.
Appropriate selective disclosure includes omitting irrelevant detail and
protecting authorized private information. Omission, strategic motivation and
harm require separate evidence.

**Current design: 2026-11-16.** This README is the current-state entry point.
The three scenarios below replace the former six-family catalog. Native
environments, admitted case collections and model runners remain unimplemented.
The repository contains two offline evidence utilities and their tests.

## Three active scenarios

| ID / dependency | Concrete workflow | Why collaboration is necessary |
| --- | --- | --- |
| FLOW | Produce quality-controlled regional climate summaries from NOAA GHCN-Daily station records | Downstream calculations consume upstream datasets and their quality/provenance information |
| SHARING | Coordinate batch workloads on a finite compute cluster, using Alibaba production-trace structure | Owners' admissions and resource commitments change peers' waiting time and feasible schedules |
| FIT | Migrate connected packages in a real repository, starting with a Babel API/AST change campaign | Parser, transformation and output packages must satisfy joint interface and behavior checks |

[ENVIRONMENTS.md](docs/ENVIRONMENTS.md) is the sole specification of each
scenario's sources, local knowledge, tools, coordination mechanism, omission
example, outcome checks and scaling limits. Real source data grounds the tasks;
agent assignments, communication duties and experimental rewards are our design.

## Shared design

1. **Real work for every member.** Parameterize agent count `n`; partition one
   connected workload into nonempty ownership packages. Every member can inspect
   evidence and execute consequential operations. Count neither spectators nor
   external services as swarm members.
2. **Cross-owner dependencies.** Flow, sharing and fit describe constraints,
   not mutually exclusive industries. Use local task views and hard/soft effects
   from TÆMS. Audit both task structure and communication routes.
3. **Disclosure with boundaries.** Fix recipient, purpose and deadline. Inspect
   messages, shared artifacts and tool receipts. Public but unread evidence is
   different from confidential evidence. Do not invent privacy duties for public
   data; report protected-information coverage only where sourced rules exist.
4. **Evaluation, not mitigation.** Compare ordinary, truthfulness and scoped
   completeness instructions, and vary local incentives with facts and duties
   fixed. Whether truthfulness leaves harmful omissions remains a hypothesis.
5. **Executed consequences.** Restore minimal missing information through the
   ordinary sender route, compare a matched nonmaterial update, and resume the
   whole swarm. Recipients retain retrieval, verification and repair options.
6. **Measured scale.** Separate fixed-workload and growing-workload experiments.
   Report work per owner, dependency degree/arity, communication and compute.
   Source capacity, admitted sizes and tested sizes are different quantities.

Research questions:

- Can agents distinguish what to share from what to withhold?
- How do conflicting incentives change disclosure decisions?
- How do these choices affect collaborators' actions and collective outcomes?

The utility sweep reports response curves and supported switching ranges. Its
threshold summarizes behavior; it does not determine a disclosure obligation.

## Where the details live

| File | Responsibility |
| --- | --- |
| [ENVIRONMENTS.md](docs/ENVIRONMENTS.md) | The three scenarios, theoretical grounding, source checks and scale contract |
| [PREHOC_DESIGN.md](docs/PREHOC_DESIGN.md) | Definitions, case manifest, evidence and restoration protocol |
| [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md) | Comparisons, statistics, implementation sequence and prior-work positioning |
| [TAKEAWAYS.md](docs/TAKEAWAYS.md) | Preserved historical observations; not active scenarios or new results |

Earlier catalogs, games and manuscript drafts do not define the active design.
Keep one home for each detail rather than creating parallel plans or summaries.

## Code and checks

`restoration_inputs` copies checkpoint metadata and specifies a sender, recipients
and delivery route. `validate_action_evidence` checks links between outcomes,
registered actors, native receipts and state transitions. Neither executes an
environment or validates semantic correctness. `build_case(...)` remains a
specified adapter interface, not an implemented function.

Python 3.10 or later; dependencies are declared in `pyproject.toml`:

```sh
python -m pip install -e ".[test]"
python -m pytest -q -p no:cacheprovider
```

Tests make no network calls. Paid model runs are outside the current scope.
The manuscript and its protected ICML template are maintained separately.
