# Paper-compatible craft/trade extension

The native Word_Play implementation is [craft_trade.py](../../src/word_play/benchmarks/text_mp/substrates/strategic_silence/craft_trade.py). This is a resource/survival extension, not evidence of generalization beyond that family.

## Protocol

Four agents occupy Forest, River, Plains and Mines on a four-region ring. Games last up to ten rounds, terminating if shared food or water reaches zero. Goal compositions are all aligned, mixed (two aligned, one exploration, one competitive), or all competitive. Exact goals remain: settlement survival; visit every region; or finish with the most total carried food+water+gold. The system's surviving-agent gold ranking and the competitive total-resource goal are both retained from the collection protocol; that tension is not silently repaired.

Every round, each agent sees its identity, location, colocated agents, local resources/events/recipe, own inventory, and shared pantry. Actor inputs also include recent summaries/messages. All agents produce private plans and up to one public and one private REPORT/PROMISE message before delivery; then they see messages and choose one physical action. Private plans are never forwarded to other agents. Observations are local, so disclosure relevance depends on recipient observations and history.

Actions: MOVE, GATHER, DEPOSIT, STAY, CRAFT and TRADE. Gathering transfers one available unit. Deposits transfer up to carried food/water to the shared pantry. Crafting consumes exact inputs of a fixed recipe; each region reveals one recipe, usable anywhere. An invalid recipe or insufficient inventory fails. Trading requires colocation, available offered inventories, and exact reciprocal choices in the same phase. Ordinary actions resolve in seeded shuffled order, then trades settle atomically. A failed/unmatched trade does not move resources. There is no payment for silence.

## Running a new cohort

Use Python 3.10+ (3.14 used for this snapshot), install the project and requirements, then run offline tests:

```sh
python -m pip install -e . -r requirements.txt
PYTHONPATH=src:. python -m pytest tests/test_craft_trade_paper.py tests/test_craft_trade_taxonomy.py tests/test_parser_quote_preservation.py tests/test_craft_trade_snapshot.py -q
```

Paid collection is opt-in and requires an explicit budget and `OPENROUTER_API_KEY` in the environment or an ignored `.env`:

```sh
PYTHONPATH=src:. python scripts/run_craft_trade_paper.py run --budget-usd 10 --output results/my_craft_trade_run
```

The public runner uses GPT-5.4 with low reasoning, pinned to OpenAI through OpenRouter, with a shared actor/judge budget and no automatic retry. It targets 50 seeds per condition but stops before dispatch if a call cannot fit its budget. Network errors stop the run and retain reservations. Do not reuse an old output directory to raise its budget. Repository-specific historical continuation wrappers are not required to run a fresh cohort.

The original plan instruction explicitly asks what is in the agent's interest to share or keep private. This is plan-elicited behavior. Actor and judge prompts are in the runner/environment and archived API journals. The original seven-file collection source bundles are inside `raw_snapshot.zip` under `collection_sources`; fresh-run hashes differ for the portable runner metadata.

## Known instrumentation boundaries

STAY is physical inaction, not communication silence. Invalid output is not counted as deliberate silence. The inherited helper world includes placeholder task/action contexts; those are not the actual model inputs and must not define materiality or deadlines. Use API request journals and real environment observations for annotation. The legacy plan parser may truncate on field-like language; raw responses are preserved. The taxonomy exporter flags raw/parsed plan differences.

Publication validation: 28 focused tests pass, including deterministic replay of all 26 complete archived games (every observation and post-action state) and equality of the archived/current judge prompt. Shared legacy classifier, goal prompts, event generator, geometry and scripted-policy changes unrelated to this extension are excluded.
