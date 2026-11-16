# Working context

Read `README.md` first. It is the short current-state summary. Follow its links
only for the part of the task being changed. Current user instructions override
earlier plans and this file.

## Scope

- Evaluate selective disclosure and strategic silence in scalable LLM swarms.
- Selective disclosure can be appropriate, including privacy preservation.
  Establish omission, strategic motivation and harm separately.
- Agent count must be parameterized. Every counted member owns real work,
  evidence and actions connected to other members' work.
- The only active scenarios are FLOW (climate data production), SHARING
  (shared compute scheduling) and FIT (repository migration). Their authoritative
  specifications are in `docs/ENVIRONMENTS.md`; they are designs, not results.
- Use flow/sharing/fit to label dependencies, TÆMS to specify local tasks and
  effects, and graph structure to report scale. Do not add parallel taxonomies.
- Only the evidence metadata utilities are implemented. Native backends,
  reviewed workloads and model runners remain to be built.
- Evaluate incentives and instruction sensitivity. Information restoration is
  a diagnostic; developing a mitigation is outside the current study.

## Keep one home for each detail

- `docs/ENVIRONMENTS.md`: dependencies, roles, scale and source gaps.
- `docs/PREHOC_DESIGN.md`: definitions, case contract and evidence protocol.
- `docs/EXPERIMENT_PLAN.md`: comparisons, statistics and literature positioning.
- `docs/TAKEAWAYS.md`: historical evidence only; preserve its provenance.

Do not restore the former six-family catalog, retired games, dyadic runners or
old taxonomies from Git history
unless the current request specifically calls for them. Keep rejected proposals
out of the active design and avoid creating duplicate plans or summary files.

## Delivery

Use the required academic-writing instructions for prose. Verify new citation
claims against retrieved primary sources. Avoid em dashes.
Preserve supplied manuscript templates. Do not run paid model experiments
without explicit authorization. Run the relevant offline checks, commit scoped
changes and push the tracked branch. Report implementation status accurately.
