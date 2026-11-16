# Evaluating Selective Disclosure and Strategic Silence in LLM Agent Swarms

We evaluate what collaborating agents share or withhold, how incentives change
those choices, and how they affect executed task outcomes. Appropriate selective
disclosure includes protecting private information. Strategic silence, deceptive
communication and harmful omission require separate evidence.

**Status:** research design and two offline evidence utilities. Native swarm
backends, admitted case collections and model runners are not implemented.
The current six-family catalog and implementation order are proposals awaiting
source and execution validation.

## Current design

1. **Scalable swarms.** Agent count is a parameter. Every member owns real work,
   information and action authority in one connected task. Role types may repeat
   across arbitrary supported sizes; adding spectators or duplicating dyads
   does not provide scale.
2. **Principled task structure.** The current taxonomy proposal uses flow,
   sharing and fit dependencies from
   [coordination theory](https://doi.org/10.1287/mnsc.45.3.425).
   A workflow may contain several dependency types. Application domains and
   disclosure duties are recorded separately.
3. **Recipient-specific disclosure.** Score required omissions, prohibited
   disclosures and legitimate withholding against documented task rules.
   Preserve ordinary retrieval, verification, repair and refusal options.
4. **Evaluation, not mitigation.** Compare baseline, truthfulness and scoped
   completeness instructions; vary local incentives with task facts and duties
   fixed. Whether truthfulness leaves harmful omissions is a hypothesis.
5. **Executed consequences.** Restore minimal missing authorized information
   through the ordinary sender route and compare with a matched nonmaterial
   update. Resume the entire swarm. This diagnoses information-caused loss;
   it is not a proposed defense.

Research questions:

- Can agents distinguish what to share from what to withhold?
- How do conflicting incentives change disclosure decisions?
- How do these choices affect collaborators' actions and collective outcomes?

The utility sweep measures response curves and supported crossing ranges.
Its threshold is a behavioral summary, not a rule defining when disclosure is
required. Swarm-size comparisons separately test fixed and growing workloads.

## Proposed environments

| Dependency | Application families |
| --- | --- |
| Flow: consume another member's output | Scientific reanalysis; civil evidence production |
| Sharing: allocate a common resource | Coordinated procurement; distributed dispatch |
| Fit: integrate compatible contributions | Software migration; assembly conformance |

Start native implementation with **E5 distributed dispatch**, then E2 software
migration after admitting connected change campaigns. The other families need
additional source or domain-review work. A parameterized interface does not
establish that existing data supports every requested size.

## Where the details live

| File | Responsibility |
| --- | --- |
| [ENVIRONMENTS.md](docs/ENVIRONMENTS.md) | Taxonomy, scalable roles, knowledge/actions/dependencies, examples and source gaps |
| [PREHOC_DESIGN.md](docs/PREHOC_DESIGN.md) | Definitions, case manifest, evidence requirements and restoration protocol |
| [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md) | Research comparisons, utility/size analysis, validation stages and prior-work positioning |
| [TAKEAWAYS.md](docs/TAKEAWAYS.md) | Historical observations and evidence links; not current environments or new results |

Read the relevant source document rather than maintaining additional copies of
the same protocol. Earlier games and manuscript drafts are historical context;
they do not define the active design.

## Code and checks

`restoration_inputs` copies multi-actor checkpoint metadata and specifies a
source, recipients and delivery route. `validate_action_evidence` checks
references from outcomes to registered actors, native receipts and state.
Neither utility executes a task, verifies semantic correctness or proves native
environment scalability. The proposed `build_case(...)` adapter remains unbuilt.

Python 3.10 or later; dependency declarations live in `pyproject.toml`:

```sh
python -m pip install -e ".[test]"
python -m pytest -q -p no:cacheprovider
```

Tests make no network calls. Paid model runs are outside the current scope.
The manuscript and its protected ICML template are maintained separately.
