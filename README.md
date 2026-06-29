# Information Marketplace: LLM Agent Deception Study

An AI agent simulation studying emergent deception in resource-gathering games. This project investigates how LLM-based agents deceive under different goal structures (aligned, mixed, competitive) in a multi-agent survival environment.

## Project Overview

**Information Marketplace** simulates 4 AI agents collaborating in a 10-round resource-gathering game. Agents must:
- Explore 4 regions (Forest, River, Plains, Mines)
- Gather food, water, and gold
- Share information through messaging
- Maintain a shared settlement to survive

The simulation tests three conditions:
- **all_aligned**: All agents prioritize settlement survival
- **mixed**: 2 aligned + 2 competitive agents
- **all_competitive**: All agents compete for personal resources

Key research questions:
- When and why do LLM agents deceive?
- Does goal structure determine deception strategy (impulsive vs. strategic)?
- How do agents use strategic silence vs. deceptive messaging?

## Quick Start

### Prerequisites
- Python 3.8+ (developed with Python 3.13)
- Conda (recommended for environment management)
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Jerick-1380/LLM-Emergent-Deception.git
cd Emergent-Deception
```

2. Create and activate conda environment:
```bash
conda create -n wordplay python=3.13
conda activate wordplay
```

3. Install dependencies:
```bash
pip install -e .
pip install openai pygame scipy numpy
```

4. Set up OpenAI API key:
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

### Running Experiments

Run a single condition with 50 trials:
```bash
conda activate wordplay
python -m info_marketplace.experiment --condition mixed --trials 50 --workers 10
```

Results are saved to `results/[condition]_gpt-5.4-mini_[timestamp]/`

### Analyzing Results

Generate comprehensive analysis across all conditions:
```bash
conda activate wordplay
python scripts/analyze_experiment.py
```

Quick survival rate check:
```bash
python scripts/analyze_trials.py
```

### Visualizing Trials

Convert any trial to a video visualization:
```bash
python -m info_marketplace.visualizer results/[exp_dir]/trial_XXX.json 2
```

Batch process all trials in a directory:
```bash
python -m info_marketplace.visualizer --batch results/[exp_dir] 2
```

## Project Structure

```
Word_Play/
├── info_marketplace/          # Core simulation package
│   ├── marketplace_env.py     # Game loop and mechanics
│   ├── world.py               # Regions, events, threats
│   ├── settlement.py          # Shared settlement logic
│   ├── config.py              # Resource configuration
│   ├── conditions.py          # Goal definitions
│   ├── prompts.py             # Agent prompt templates
│   ├── scout_llm_policy.py    # LLM-based agent policy
│   ├── classifier.py          # Deception detection (LLM-based)
│   └── visualizer.py          # Video generation
├── scripts/                   # Utility scripts
│   ├── analyze_experiment.py  # Main analysis script
│   ├── analyze_trials.py      # Quick survival check
│   └── reclassify_with_llm.py # Reclassify trials with updated detector
├── docs/                      # Documentation
│   ├── CLAUDE.md              # Session guide and findings
│   └── SYSTEM_ARCHITECTURE.md # Technical documentation
├── tests/                     # Unit tests
├── sprites/                   # Visualization assets
├── benchmarks/                # Performance benchmarks
├── examples/                  # Example scripts
└── results/                   # Experiment outputs (gitignored)
```

## Key Findings

**Message-Level Deception Rates:**
- All Aligned: 28.65% (SD=10.21%)
- Mixed: 20.99% (SD=10.24%)
- All Competitive: 21.65% (SD=11.35%)

**Premeditation (Agent-Round Level):**
- **Aligned**: 4.75% premeditated, 20.10% impulsive → 4.2:1 impulsive:premeditated (reactive)
- **Mixed**: 10.15% premeditated, 12.20% impulsive → 1.2:1 balanced
- **Competitive**: 24.65% premeditated, 6.15% impulsive → 4.0:1 premeditated:impulsive (strategic)

**Strategic Silence:**
- 61-93% of premeditated deception involves zero deceptive messages
- Competitive agents: 92.9% silent premeditation (hiding gold via silence)
- Most deception occurs through NOT communicating, not through lies

**Temporal Escalation:**
- Aligned: 2.1x escalation, ρ = 0.733 (p = 0.016)
- Mixed: 7.1x escalation, ρ = 0.976 (p < 0.001)
- Competitive: 5.0x escalation, ρ = 0.879 (p < 0.001)

**Survival Rates:**
- All Aligned: 100% (50/50)
- Mixed: 100% (50/50)
- All Competitive: 94% (47/50)

## Core Insight

**Goal structure determines deception strategy, not just rate.**

Aligned agents deceive reactively under pressure (4.2:1 impulsive:premeditated), while competitive agents plan strategically (4.0:1 premeditated:impulsive). This challenges the assumption that emergent AI deception is uniformly impulsive.
