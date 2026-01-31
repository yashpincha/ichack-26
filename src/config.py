"""Configuration constants, payoff matrix, and prompts for DarwinLM."""

import os
from typing import Literal
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# LLM Configuration
# =============================================================================

LLM_PROVIDER: Literal["openai", "anthropic"] = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE: float = 0.7
LLM_MAX_TOKENS: int = 200

# API Keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# =============================================================================
# Game Configuration
# =============================================================================

NUM_AGENTS: int = int(os.getenv("NUM_AGENTS", "8"))
ROUNDS_PER_MATCH: int = int(os.getenv("ROUNDS_PER_MATCH", "10"))
NUM_GENERATIONS: int = int(os.getenv("NUM_GENERATIONS", "10"))

# Payoff Matrix: (player_payoff, opponent_payoff)
# Format: PAYOFF_MATRIX[player_move][opponent_move]
PAYOFF_MATRIX: dict[str, dict[str, tuple[int, int]]] = {
    "COOPERATE": {
        "COOPERATE": (3, 3),  # Mutual cooperation
        "DEFECT": (0, 5),     # Sucker's payoff
    },
    "DEFECT": {
        "COOPERATE": (5, 0),  # Temptation payoff
        "DEFECT": (1, 1),     # Mutual defection
    },
}

# =============================================================================
# Evolution Configuration
# =============================================================================

MUTATION_RATE: float = float(os.getenv("MUTATION_RATE", "0.15"))
MUTATION_SIGMA: float = 0.15  # Standard deviation for Gaussian mutation
SURVIVORS_PER_GENERATION: int = 4  # Top N agents survive
BLENDING_PROBABILITY: float = 0.3  # Probability to blend numeric genes during crossover

# Gene value bounds
GENE_MIN: float = 0.0
GENE_MAX: float = 1.0

# Strategy keyword pool for mutation
STRATEGY_KEYWORD_POOL: list[str] = [
    "aggressive", "forgiving", "strategic", "cautious",
    "optimistic", "pessimistic", "adaptive", "stubborn",
    "calculating", "trusting", "vengeful", "diplomatic",
    "unpredictable", "consistent", "patient", "reactive"
]

REASONING_DEPTH_OPTIONS: list[str] = ["shallow", "medium", "deep"]

# =============================================================================
# Default Gene Values (Baseline Agent)
# =============================================================================

DEFAULT_GENES: dict = {
    "cooperation_bias": 0.5,
    "retaliation_sensitivity": 0.5,
    "forgiveness_rate": 0.5,
    "memory_weight": 0.5,
    "reasoning_depth": "medium",
    "strategy_keywords": ["neutral"],
    "message_honesty": 0.5,
    "threat_frequency": 0.0,
}

# =============================================================================
# Prompts
# =============================================================================

DECISION_PROMPT: str = """You are Agent {agent_id} in a Prisoner's Dilemma tournament.

YOUR PERSONALITY:
- Cooperation tendency: {cooperation_bias:.0%}
- Retaliation sensitivity: {retaliation_sensitivity:.0%} (higher = punish defection quickly)
- Forgiveness rate: {forgiveness_rate:.0%} (higher = forgive past defections)
- Memory weight: {memory_weight:.0%} (higher = history matters more)
- Strategy style: {strategy_keywords}
- Reasoning depth: {reasoning_depth}

GAME RULES:
- If you both COOPERATE: You each get 3 points
- If you DEFECT and they COOPERATE: You get 5, they get 0
- If you COOPERATE and they DEFECT: You get 0, they get 5
- If you both DEFECT: You each get 1 point

CURRENT MATCH: Round {current_round}/{total_rounds} against {opponent_id}

HISTORY WITH THIS OPPONENT:
{round_history}

{opponent_message_section}

Based on your personality traits and the history, decide your move.
Consider: What would an agent with YOUR specific traits do here?

Respond in this EXACT format:
DECISION: [COOPERATE or DEFECT]
MESSAGE: [Optional message to opponent for next round, max 50 chars, or NONE]
REASONING: [1-2 sentence explanation based on your personality]"""

OPPONENT_MESSAGE_SECTION: str = """OPPONENT'S MESSAGE TO YOU: "{opponent_message}"
(Consider: How does this align with their past behavior? Is it trustworthy?)"""

NO_HISTORY_TEXT: str = "No previous rounds yet. This is your first interaction."

HISTORY_ENTRY_TEMPLATE: str = "Round {round_num}: You {your_move} | They {their_move} | You scored {your_score}"

# =============================================================================
# Logging Configuration
# =============================================================================

LOGS_DIR: str = "logs"
LOG_FORMAT: str = "json"  # "json" or "csv"

# =============================================================================
# Visualization Configuration
# =============================================================================

COOPERATE_COLOR: str = "#22c55e"  # Green
DEFECT_COLOR: str = "#ef4444"     # Red
NEUTRAL_COLOR: str = "#6b7280"    # Gray
BACKGROUND_COLOR: str = "#1f2937" # Dark gray
