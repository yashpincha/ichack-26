# 🎨 AI r/place - Emergent Pixel Art with Evolving AI Agents

> **ICHack 2026 - Marshall Wace Challenge: Emergent Behaviour**
> 
> *"Design a system that evolves or adapts through interactions to produce something greater than the sum of its parts"*

## Overview

AI r/place simulates Reddit's famous r/place experiment, but with AI agents that have evolving personalities. Agents compete on a shared pixel canvas, placing pixels based on their unique traits. Through natural selection, winning strategies emerge organically.

**Key Innovation:** Visual patterns and strategies **emerge** from evolutionary pressure rather than being programmed.

## Demo

Watch AI agents battle for territory on a shared canvas:

```bash
# Run simulation with live visualization
python main.py simulate --generations 5 --live

# Launch dashboard
streamlit run viz/dashboard.py
```

## How It Works

### 1. Agent Personality

Each agent has genetic traits that influence their pixel placement strategy:

```python
AgentPersonality:
  territoriality: 0.7     # Tendency to cluster pixels together
  aggression: 0.4         # Willingness to overwrite others
  creativity: 0.6         # Creates patterns vs expands
  cooperation: 0.3        # Builds on others' work
  exploration: 0.8        # Ventures to new areas
  color_loyalty: 0.9      # Sticks to preferred color
  preferred_color: "blue"
  loose_goal: "fill corners"
```

### 2. The Canvas

- Agents share a pixel grid (default 16x16)
- Each turn, every agent places one pixel
- Agents can overwrite each other's pixels
- The LLM sees the ASCII grid and decides placement

```
  0123456789...
0 .R.B..G.....
1 ..RR.BB.....
2 .RRR.BBB....
...
```

### 3. Evolution

After each generation:
1. **Fitness Evaluation:** Territory owned + pixel survival time
2. **Selection:** Top 2 agents survive
3. **Crossover:** Parents create offspring with mixed genes
4. **Mutation:** Random trait changes
5. **Reset Canvas:** New generation starts fresh

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
# Run simulation (default: 5 generations, 4 agents, 16x16 grid)
python main.py simulate

# Custom settings
python main.py simulate --generations 10 --agents 6 --grid-size 20

# View specific generation
python main.py show 3

# Replay a generation turn-by-turn
python main.py replay 4 --speed 0.2

# Launch dashboard
streamlit run viz/dashboard.py
```

## Project Structure

```
ichack-26/
├── src/
│   ├── agent.py        # Agent class with personality traits
│   ├── grid.py         # Pixel canvas implementation
│   ├── simulation.py   # Turn-based simulation loop
│   ├── evolution.py    # Selection, crossover, mutation
│   ├── llm.py          # OpenAI/Anthropic integration
│   ├── config.py       # Settings and prompts
│   └── live_state.py   # Real-time state for dashboard
├── viz/
│   ├── dashboard.py    # Streamlit visualization
│   └── components.py   # Reusable UI components
├── logs/               # Generation JSON logs
├── tests/              # Unit tests
├── main.py             # CLI entry point
├── requirements.txt
└── README.md
```

## Key Features

### Emergent Strategies

Watch agents naturally develop strategies:

- **Territorial:** Clusters pixels, defends area
- **Explorer:** Spreads across the canvas
- **Aggressive:** Actively overwrites others
- **Cooperative:** Builds patterns with others

### Personality Traits

| Trait | Low | High |
|-------|-----|------|
| Territoriality | Spreads out randomly | Clusters near own pixels |
| Aggression | Avoids others' pixels | Overwrites aggressively |
| Creativity | Expands existing areas | Creates new patterns |
| Cooperation | Ignores others | Builds on others' work |
| Exploration | Stays in familiar areas | Ventures to empty areas |
| Color Loyalty | Uses many colors | Sticks to preferred color |

### Visualization Dashboard

- 🖼️ Live canvas updates
- 🏆 Real-time leaderboard
- 📊 Territory statistics
- 🧬 Evolution analysis
- 🔄 Generation replay

## Configuration

Edit `.env` or `src/config.py`:

```env
# LLM Settings
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini

# Grid Settings
GRID_WIDTH=16
GRID_HEIGHT=16

# Simulation Settings
NUM_AGENTS=4
TURNS_PER_GENERATION=50
NUM_GENERATIONS=5
MUTATION_RATE=0.2
```

## Success Metrics

1. **Territory Growth:** Evolved agents control more territory over generations
2. **Strategy Emergence:** Recognizable patterns develop (clustering, expansion)
3. **Personality Divergence:** Traits evolve away from neutral (0.5)
4. **Fitness Improvement:** Generation N fitness > Generation 0 fitness

## Technical Details

### LLM Decision Prompt

Agents receive:
- ASCII grid state
- Their personality traits
- Current territory count
- Recent placement history
- Their loose goal

```
YOUR PERSONALITY:
- Territoriality: 70% (strongly prefers placing near own territory)
- Aggression: 30% (avoids overwriting others)
...

CURRENT CANVAS STATE (16x16):
  0123456789...
0 .R.B..G.....
...

Based on your personality, decide where to place your next pixel.
PLACE: x,y,color
```

### Fitness Function

```python
def evaluate_fitness(agent, grid):
    territory = grid.get_territory_count(agent.id)
    persistence = grid.get_average_pixel_lifespan(agent.id)
    return territory * 2 + persistence
```

### Crossover

```python
def crossover(parent1, parent2):
    child_traits = {}
    for trait in PERSONALITY_TRAITS:
        # 50/50 from each parent
        if random.random() < 0.5:
            child_traits[trait] = parent1.traits[trait]
        else:
            child_traits[trait] = parent2.traits[trait]
        
        # Occasionally blend
        if random.random() < 0.3:
            child_traits[trait] = (p1 + p2) / 2
    return child_traits
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

## Cost Estimation

- 16x16 grid, 4 agents, 50 turns/generation, 5 generations
- = 4 agents × 50 turns × 5 gens = **1,000 LLM calls**
- With gpt-4o-mini: ~$1-2 per full run
- Caching reduces repeated states significantly

## References

- [Reddit r/place](https://en.wikipedia.org/wiki/R/place)
- [Evolutionary Game Theory](https://en.wikipedia.org/wiki/Evolutionary_game_theory)
- [Genetic Algorithms](https://en.wikipedia.org/wiki/Genetic_algorithm)

## Team

ICHack 2026 Team - AI r/place

## License

MIT License - See LICENSE file
