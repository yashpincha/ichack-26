"""Configuration constants and prompts for AI r/place simulation."""

import os
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# LLM Configuration
# =============================================================================

LLM_PROVIDER: Literal["openai", "anthropic"] = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE: float = 0.7  # Balanced for creativity + consistency
LLM_MAX_TOKENS: int = 300  # Shorter responses for pixel decisions

# API Keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# =============================================================================
# Grid Configuration
# =============================================================================

GRID_WIDTH: int = int(os.getenv("GRID_WIDTH", "16"))
GRID_HEIGHT: int = int(os.getenv("GRID_HEIGHT", "16"))

# Available colors for pixels
COLORS: list[str] = ["red", "blue", "green", "yellow", "purple", "orange", "cyan", "pink"]

# =============================================================================
# Simulation Configuration
# =============================================================================

NUM_AGENTS: int = int(os.getenv("NUM_AGENTS", "4"))
TURNS_PER_GENERATION: int = int(os.getenv("TURNS_PER_GENERATION", "50"))
NUM_GENERATIONS: int = int(os.getenv("NUM_GENERATIONS", "5"))

# =============================================================================
# Evolution Configuration
# =============================================================================

MUTATION_RATE: float = float(os.getenv("MUTATION_RATE", "0.2"))
MUTATION_SIGMA: float = 0.2  # Standard deviation for Gaussian mutation
SURVIVORS_PER_GENERATION: int = 2  # Top N agents survive (half of 4)
BLENDING_PROBABILITY: float = 0.3  # Probability to blend numeric genes during crossover

# Gene value bounds
GENE_MIN: float = 0.0
GENE_MAX: float = 1.0

# List of personality traits for evolution
PERSONALITY_TRAITS: list[str] = [
    "territoriality",
    "aggression",
    "creativity",
    "cooperation",
    "exploration",
    "color_loyalty",
]

# =============================================================================
# Fitness Weights
# =============================================================================

FITNESS_TERRITORY_WEIGHT: float = 2.0  # Points per pixel owned at end
FITNESS_PERSISTENCE_WEIGHT: float = 1.0  # Points per average turn survived
FITNESS_OVERWRITE_PENALTY: float = 0.0  # Optional penalty for aggression

# =============================================================================
# AI Agent Prompt for Pixel Decisions
# =============================================================================

PIXEL_DECISION_PROMPT: str = """You are an AI agent in an r/place-style canvas simulation. Your goal is to place pixels strategically based on your personality.

YOUR PERSONALITY:
{personality_description}

CURRENT CANVAS STATE ({width}x{height} grid):
{grid_ascii}

Legend: . = empty, R = red, B = blue, G = green, Y = yellow, P = purple, O = orange, C = cyan, K = pink

YOUR CURRENT STATUS:
- Your color: {agent_color}
- Your territory: {territory_count} pixels
- Turn: {current_turn} of {total_turns}

RECENT ACTIVITY:
{recent_history}

YOUR TASK:
Based on your personality traits and goals, decide where to place your next pixel.

Think about:
1. Your territoriality: Should you place near your existing pixels or spread out?
2. Your aggression: Should you overwrite others' pixels or avoid conflict?
3. Your exploration: Should you venture to empty/new areas?
4. Your goal: {goal_text}

Respond in this EXACT format:

THINKING: [1-2 sentences explaining your reasoning based on your personality]

PLACE: x,y,color

Where x is column (0-{max_x}), y is row (0-{max_y}), and color is one of: {colors}
If you're loyal to your color, prefer using {agent_color}."""

NO_HISTORY_TEXT: str = "No pixels placed yet - this is the start of the generation."

HISTORY_ENTRY_TEMPLATE: str = "Turn {turn}: {agent_id} placed {color} at ({x},{y})"

# =============================================================================
# Logging Configuration
# =============================================================================

# Use absolute path to ensure consistency across different working directories
_PROJECT_ROOT = Path(__file__).parent.parent
LOGS_DIR: str = str(_PROJECT_ROOT / "logs")
LOG_FORMAT: str = "json"

# =============================================================================
# Visualization Configuration
# =============================================================================

# Color hex codes for visualization
COLOR_HEX = {
    "red": "#ef4444",
    "blue": "#3b82f6",
    "green": "#22c55e",
    "yellow": "#eab308",
    "purple": "#a855f7",
    "orange": "#f97316",
    "cyan": "#06b6d4",
    "pink": "#ec4899",
    "empty": "#1f2937",
}

BACKGROUND_COLOR: str = "#0f172a"
GRID_LINE_COLOR: str = "#334155"

# =============================================================================
# Live State Configuration
# =============================================================================

LIVE_STATE_FILE: str = str(_PROJECT_ROOT / ".live_state.json")
