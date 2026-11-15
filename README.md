# Strategic Silence

Research on when agents withhold decision-relevant information, whether truthful
communication remains materially incomplete, and how omissions affect another
agent's decisions.

## Read first

- [Takeaways](docs/TAKEAWAYS.md): what the earlier pilots suggest about when
  silence and selective disclosure occur, with evidence status and source links.
- [Experiment plan](docs/EXPERIMENT_PLAN.md): candidate legal, procurement and
  scientific-review workflows, plus an existing customer-service benchmark.

## Current implementation

The package contains two shared utilities: restoration-input construction and
execution-evidence validation. They preserve independent branch state and check
that reported outcomes reference actual tool receipts. Native environments,
validated case collections and model runners are not implemented here yet.

The earlier games, mapping tasks, synthetic experiment runners, results, figures,
launchers and superseded taxonomies have been removed from the working tree.
Their research takeaways are retained in the document above. Historical evidence
remains addressable through Git history; it is not part of the active suite.

## Offline checks

Python 3.10 or later:

```sh
python -m pip install -e ".[test]"
python -m pytest -q
```

The tests exercise metadata checks and independent copies, not simulated research
environments. They make no model requests. No paid experiment is authorized.

```text
docs/                         Takeaways and current experiment design
src/disclosure_causality/      Scenario-independent evidence utilities
tests/                        Offline regression checks
.github/workflows/offline.yml  CI for the retained utilities
```
