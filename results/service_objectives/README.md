# GPT-5.4 service objective experiment

With the service payment rules fixed, GPT-5.4 disclosed the useful mappings under a team objective and withheld them under an individual expert objective. The new follow-up completed **15/15 episodes: five per condition**, with zero format failures. All five matched triplets showed the same contrast.

| Cohort | Aligned: disclosed | Mixed: withheld | Competitive: withheld | Invalid |
|---|---:|---:|---:|---:|
| Initial pilot, 3 cases | 3/3 | 3/3 | 3/3 | 0 |
| Fresh follow-up, 5 cases | 5/5 | 5/5 | 5/5 | 0 |
| Combined descriptive total | 8/8 | 8/8 | 8/8 | 0 |

The follow-up was fixed after observing the pilot; the cohorts remain separate for interpretation. The unit is the case triplet, not the two dependent clients per episode. No claims of statistical confirmation or population prevalence are made from eight cases.

## Objectives and mechanics

Three agents: one expert privately knows randomized diagnostic-to-setting mappings, and two clients must solve later jobs. Public/private messages and authenticated document publication are available. Requested private plans are not delivered to clients. Every communication phase precedes a separate action phase; later clients choose independent submission or service.

- **Aligned:** expert and both clients maximize the sum of all three agents' points.
- **Mixed:** expert maximizes individual points; both clients maximize team total.
- **Competitive:** each actor maximizes individual points, not relative rank or sabotage.

The objectives appear in system prompts for the expert's communication/action and both actual/full-reference client branches. No objective tells the agent to disclose or withhold. Agents are not told other agents' assigned objective types. Mixed and competitive use identical expert prompts for a given case; their distinction changes downstream client objectives, not the expert's knowledge of the roster.

Both roles use `openai/gpt-5.4` via the OpenAI endpoint on OpenRouter, low reasoning, 3,000-token output cap. The per-call payment contract is constant. Seeds 609500–609502 form the pilot; 609600–609604 form the follow-up. Condition order cycles across cases. Factory/pipeline are surface variants within service, not separate environments. No invalid-output replacements or outcome-based stopping were used.

## Taxonomy and downstream choices

All aligned episodes provide useful delivery to both clients. All mixed/competitive episodes communicate without the needed mappings: **content omission**, rather than literal silence. This yields 16 useful-delivery and 32 content-omission recipient records across both cohorts. All initial stated plans match the broad terminal disclosure/withholding choice; these are elicited strategies, not hidden reasoning or ground-truth intent. Several messages openly announce withholding. Semantic annotations were reviewed by Codex and source-hashed, not independently human-calibrated.

| Follow-up condition | Actual service requests | With full references |
|---|---:|---:|
| Aligned | 0/10 | 0/10 |
| Mixed | 10/10 | 4/10 |
| Competitive | 10/10 | 0/10 |

Full-reference branches retain actual expert messages. Service use is not itself an information-gap measure: team-oriented clients sometimes use service even when they have complete references.

**Scoring limitation:** independent success gives client 6 + expert 0 = 6; service gives client 3 + expert 3 = 6. These routes tie in team payoff. Aligned disclosure was observed, not uniquely optimal; some model plans incorrectly claim independent work produces a higher team total. No team-total harm from withholding is established here. This objective manipulation is separate from earlier experiments that changed payment contracts.

Service and native crafting/trading are two distinct environments. This release adds service evidence; it neither revalidates all crafting/trading annotations nor establishes cross-model generalization. Kimi K3 replication is not part of this release.

## Offline reproduction

From the repository root, using Python 3.10+:

```sh
python scripts/reproduce_service_objectives.py
python -m pytest -q tests/test_service_objectives.py tests/test_service_communication_v2.py tests/test_service_gpt54_pairs.py tests/test_apply_service_taxonomy_review.py tests/test_taxonomy_core.py
```

No API key or network access is needed for reproduction. The script verifies the archive and member hashes, extracts to a temporary directory, replays all **224 requests across 24 episodes**, regenerates taxonomy outputs from the saved annotations, and compares both cohort summaries. This checks faithful application of the annotations, not independent semantic correctness. All **47 focused tests passed**.

`evidence.zip` contains the two objective cohorts' raw synthetic trajectories, provider request/response journals, configurations, source snapshots, and semantic annotations. Prior journals preserve cumulative budget accounting and are not pooled as behavioral results. The manifest lists every member/hash. Private plans are model-generated experimental artifacts. No credentials are included.

The frozen phase-one template is isolated in `scripts/service_phase1_prompt.py` so unrelated world-prompt edits are not included in this PR. Original collection snapshots remain byte-preserved in the archive; offline replay verifies the packaged implementation produces the identical requests. Original live configurations contain collection-machine paths and historical source hashes: the supported release entrypoint is offline reproduction, not blindly relaunching those configurations. New paid collection requires a new frozen configuration and explicit budget.

## Cost

The 15-episode follow-up accounted for **$0.795485** (provider-reported $0.78753015). The preceding nine-episode objective pilot accounted for $0.484575. Cumulative spending across all earlier service attempts, including retained failed reservations, is **$4.4410699 / $5**, leaving $0.5589301. No more live collection is running.

Files: [machine-readable reproduced summary](reproduced_summary.json), [archive manifest](manifest.json), [raw evidence](evidence.zip).
