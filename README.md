# Evaluating Selective Disclosure and Strategic Silence in LLM Agent Swarms

A shared framework for measuring **what agents should disclose, what they must
protect, and how missing information changes other agents' actions**.

Implemented: six offline workflow simulators, permission checks, action traces
and counterfactual replay. Uses synthetic records and scripted policies.
**No model/API experiments have been run for these six environments.**

## Six environments

Two domains × three dependencies from [Malone et al. (1999)](https://doi.org/10.1287/mnsc.45.3.425):
**flow** consumes upstream output; **sharing** uses a common resource; **fit**
requires compatible contributions.

| ID | Domain / dependency | Workflow | Required evidence | Native loss |
| --- | --- | --- | --- | --- |
| M1 | Manufacturing / flow | [Quality handoff](https://catenax-ev.github.io/docs/Io/standards/CX-0123-QualityUseCaseStandard) | Lot's retest requirement | Nonconforming downstream outputs |
| M2 | Manufacturing / sharing | [Capacity allocation](https://catenax-ev.github.io/docs/Io/standards/CX-0128-DemandandCapacityManagementDataExchange) | Actual usable capacity | Rejected allocations |
| M3 | Manufacturing / fit | [Configuration release](https://catenax-ev.github.io/docs/Io/standards/CX-0030-DataModelBoMAsSpecified) | Current component revision | Incompatible interfaces |
| L1 | Logistics / flow | [Transport handoff](https://dcsa.org/standards/track-and-trace) | Updated arrival | Empty dispatches |
| L2 | Logistics / sharing | [Port scheduling](https://reference.dcsa.org/content/standards/releases/port-call/v2/pc-v2-use-cases) | Berth availability | Anchorage waiting |
| L3 | Logistics / fit | [Document reconciliation](https://reference.dcsa.org/content/standards/guidelines/implementation-guides/implementing-booking-and-bill-of-lading) | Changed destination and quantity | Stale documents |

Every task also contains **protected customer and price records** used in local
accounting; M1 additionally protects a process parameter. Required evidence goes
to authorized recipients. A compliant path satisfies both duties.

The sources ground the workflows. Simulation dynamics are authored. Each agent
owns executable work in a connected task; shared capacity, berth occupancy and
container checks create consequences across owners.

## Evaluation

1. Agents inspect local records, query authorized evidence, communicate and act.
2. At each recipient's first dependent action, score missing required evidence.
   Separately count unauthorized fact–recipient deliveries, including forwarding.
3. Freeze the whole swarm before the affected decision. Compare **O** (empty
   update), **M** (missing authorized record) and **P** (nonmaterial record).
4. Resume all agents and measure native loss. Keep world state, permissions,
   timing and budgets matched at the fork; updates are matched in UTF-8 bytes.

Controls cover compliant disclosure, silence, truthful partial reporting and
oversharing. Clean, query-recovery and already-informed cases test null effects.
Exposure, omission, strategic intent and harm remain separate measurements.

## Run

Python 3.10+. Runtime dependencies: standard library only.

```sh
python -m pip install -e ".[test]"
python -m pytest -q -p no:cacheprovider
python -m disclosure_causality offline --output output/offline
python -m disclosure_causality replay output/offline/examples.json
```

Default: all six environments, sizes **4, 7, 8, 16, 32**, seeds **0, 1**.
For a smoke run, add `--sizes 4 --seeds 0`. To repartition a fixed workload:

```sh
python -m disclosure_causality offline --work-units 32 --seeds 0 --output output/fixed-work
python -m disclosure_causality replay output/fixed-work/examples.json
```

The builder accepts `n >= 4` and `work_units >= n`. Fixed-work checks preserve
workload, not total compute. Execution uses structured factual messages and a
deterministic work order; free-form model communication remains future work.

## Validation and next experiments

[Saved validation](results/offline/validation.json): **738 scripted episodes**
across growing and fixed workloads, including 108 null-control episodes;
**36 matching continuation replays**. The current test suite has **83 tests**.

Next: compare ordinary, truthfulness and scoped-completeness instructions under
aligned and conflicting incentives. Measure disclosure, confidentiality and
native outcomes with three closed-weight and three open-weight models.
Incentive sweeps and threshold estimates require task-specific reward anchors;
the current incentive field is metadata only.

[Code](src/disclosure_causality/) · [Tests](tests/) ·
[Offline evidence](results/offline/) · [Retained takeaways](docs/TAKEAWAYS.md)
