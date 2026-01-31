# 🧬 DarwinLM: Evolutionary Prisoner's Dilemma Tournament

> **ICHack 2026 - Marshall Wace Challenge: Emergent Behaviour**
> 
> *"Design a system that evolves or adapts through interactions to produce something greater than the sum of its parts"*

## Overview

DarwinLM recreates Robert Axelrod's famous 1980 Prisoner's Dilemma tournament—but with AI agents that have genetic "DNA" controlling their behavior. Through evolution, agents discover optimal strategies (like tit-for-tat) **without human design**.

**Key Innovation:** Strategies **emerge** from evolutionary pressure rather than being programmed.

## Demo

Watch cooperation strategies evolve over generations:

```bash
# Run evolution
python main.py evolve --generations 10

# Launch visualization dashboard
streamlit run viz/dashboard.py
```

## How It Works

### 1. Agent DNA

Each agent has genetic traits that influence their decisions:

```python
AgentDNA:
  cooperation_bias: 0.7      # Tendency to cooperate
  retaliation_sensitivity: 0.8  # How quickly to punish defection
  forgiveness_rate: 0.3      # Probability to forgive
  memory_weight: 0.6         # How much history matters
  strategy_keywords: ["adaptive", "cautious"]
```

### 2. Tournament (Prisoner's Dilemma)

| Player A \ B | Cooperate | Defect |
|--------------|-----------|--------|
| **Cooperate** | 3, 3 | 0, 5 |
| **Defect** | 5, 0 | 1, 1 |

- 8 agents compete in round-robin (28 matchups)
- Each matchup is 10 rounds
- Agents can send messages to each other

### 3. Evolution

After each generation:
1. **Selection:** Top 4 agents survive
2. **Crossover:** Parents create 4 offspring with mixed genes
3. **Mutation:** Random changes to offspring DNA
4. **Repeat:** New population of 8 competes again

## Quick Start

### Installation

```bash
# Clone the repo
git clone https://github.com/your-team/ichack-26.git
cd ichack-26

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up API key
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Running

```bash
# Run evolution (default: 10 generations, 8 agents)
python main.py evolve

# Custom settings
python main.py evolve --generations 20 --agents 8

# View specific generation
python main.py show 5

# Compare evolved vs baseline agent
python main.py compare 9 --matches 10

# Launch dashboard
streamlit run viz/dashboard.py
```

## Project Structure

```
ichack-26/
├── src/
│   ├── agent.py        # Agent class with DNA
│   ├── game.py         # Prisoner's Dilemma logic
│   ├── tournament.py   # Round-robin orchestration
│   ├── evolution.py    # Selection, crossover, mutation
│   ├── llm.py          # OpenAI/Anthropic integration
│   └── config.py       # Settings and prompts
├── viz/
│   ├── dashboard.py    # Streamlit main app
│   └── components.py   # Reusable UI components
├── logs/               # Generation JSON logs
├── tests/              # Unit tests
├── main.py             # CLI entry point
├── requirements.txt
└── README.md
```

## Key Features

### Emergent Strategies

Watch agents discover classic strategies naturally:

- **Tit-for-Tat:** Mirror opponent's last move
- **Forgiving TFT:** Cooperate after punishment
- **Always Defect:** In harsh environments
- **Pavlov:** Win-stay, lose-switch

### Visualization Dashboard

- 📊 Fitness evolution charts
- 🤖 Agent DNA cards with trait bars
- 🎮 Live match viewer (round-by-round)
- 🌳 Lineage tree showing ancestry
- 📈 Gene evolution heatmaps

### Async LLM Calls

Parallel matchups for fast tournaments:

```python
matchups = list(itertools.combinations(agents, 2))
results = await asyncio.gather(*[play_match(a1, a2) for a1, a2 in matchups])
```

## Configuration

Edit `.env` or `src/config.py`:

```env
# LLM Settings
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Evolution Settings
NUM_AGENTS=8
ROUNDS_PER_MATCH=10
NUM_GENERATIONS=10
MUTATION_RATE=0.15
```

## Success Metrics

1. **Fitness Increase:** Generation 10 avg fitness > Generation 0
2. **Strategy Emergence:** Recognizable patterns (TFT-like behavior)
3. **Evolved Beats Baseline:** Best evolved agent wins >60% vs vanilla
4. **Cooperation Evolution:** Cooperation rate changes meaningfully

## Technical Details

### Decision Prompt

Agents receive their DNA traits as personality instructions:

```
YOUR PERSONALITY:
- Cooperation tendency: 70%
- Retaliation sensitivity: 80%
- Forgiveness rate: 30%
- Strategy style: adaptive, cautious

Based on your personality, decide: COOPERATE or DEFECT
```

### Crossover

```python
def crossover(parent1, parent2):
    child_genes = {}
    for gene in parent1.genes:
        # 50/50 from each parent
        if random.random() < 0.5:
            child_genes[gene] = parent1.genes[gene]
        else:
            child_genes[gene] = parent2.genes[gene]
        
        # Occasionally blend numeric genes
        if random.random() < 0.3:
            child_genes[gene] = (p1 + p2) / 2
    return child_genes
```

### Mutation

```python
def mutate(agent, rate=0.15):
    for gene, value in agent.genes.items():
        if random.random() < rate:
            if isinstance(value, float):
                # Gaussian mutation
                value += random.gauss(0, 0.15)
                value = clamp(value, 0, 1)
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_evolution.py -v
```

## References

- [Axelrod's Tournament (1980)](https://en.wikipedia.org/wiki/The_Evolution_of_Cooperation)
- [Prisoner's Dilemma](https://en.wikipedia.org/wiki/Prisoner%27s_dilemma)
- [Evolutionary Game Theory](https://en.wikipedia.org/wiki/Evolutionary_game_theory)

## Team

ICHack 2026 Team - DarwinLM

## License

MIT License - See LICENSE file
