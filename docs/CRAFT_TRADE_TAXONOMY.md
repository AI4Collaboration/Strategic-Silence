# Exploratory disclosure taxonomy, not yet benchmark ground truth

The organizing question is how stated withholding motives relate to disclosure methods. The intended display is intent -> stated motive -> method -> recipient-specific outcome. Store these as separate dimensions, allowing multiple values and unknowns, rather than forcing a single mutually exclusive tree label.

| Dimension | Evidence and candidate values |
|---|---|
| Stated intent/motive | Exact private-plan passage; personal advantage, collective protection, other/unclear. A stated reason is not an established cause. |
| Information targeted | Recipe, resource stock, inventory, personal objective, intended action. Concealing an objective is **what** is withheld, not a motive parallel to protecting personal advantage. |
| Disclosure method | No messages; selective content omission; restricted audience; explicit acknowledgment of withholding. Vagueness, false cover stories and delayed disclosure remain possible methods requiring evidence, not established findings. |
| Recipient/outcome | Who needed which information by what decision; own observations/prior messages; realized, unsuccessful, abandoned or unknown withholding. |
| Truthfulness | Accuracy assessed separately from completeness. A true statement can be incomplete; a false statement is not automatically evidence of strategic withholding. |

For observable completeness, retain no communication, incomplete relevant disclosure, complete relevant disclosure, unknown and not-applicable. Timing and audience can overlap the content labels. No information gap is established when the recipient already knows the fact or it is irrelevant to the specified decision. The original paper endpoint (withholding-plan intent AND no messages across both channels) remains separately reported.

The LLM judge currently identifies candidates. It does not independently establish fact-level omission or a causal motive. Develop coding rules on an explicitly declared development subset; freeze them; validate against independent annotation and evaluate held-out games. Assess actual disclosure from messages/observations separately from plan-based motive coding to avoid using the same interpretation as both explanation and ground truth. These logs have already been inspected for examples and are not automatically a held-out benchmark.

The offline exporter `scripts/export_craft_trade_taxonomy.py` retains evidence and blank review fields. It operates on a local uncompressed run folder and creates immutable annotation packets without API calls. It does not output verified semantic labels. The published gzip snapshot can be inspected directly with Python's gzip/json modules; source traces and raw requests are retained.

Topic-versus-prompt analysis: topics vary here, but the actor prompt style is fixed. Motive/topic associations with methods can be described after review with game-level dependence handled. A prompt-style effect requires a matched intervention. Postgame interviews were proposed but **were not collected**. No causal claims or novelty claims are established by this tree.
