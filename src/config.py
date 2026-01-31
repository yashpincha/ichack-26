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
LLM_TEMPERATURE: float = 0.9  # Higher for more personality variation
LLM_MAX_TOKENS: int = 500  # More tokens for thinking step

# API Keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

# =============================================================================
# Game Configuration
# =============================================================================

NUM_AGENTS: int = int(os.getenv("NUM_AGENTS", "3"))
ROUNDS_PER_MATCH: int = int(os.getenv("ROUNDS_PER_MATCH", "10"))
NUM_GENERATIONS: int = int(os.getenv("NUM_GENERATIONS", "3"))  # 3 generations to see emergence

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

MUTATION_RATE: float = float(os.getenv("MUTATION_RATE", "0.2"))
MUTATION_SIGMA: float = 0.2  # Standard deviation for Gaussian mutation
SURVIVORS_PER_GENERATION: int = 2  # Top N agents survive (half of population)
BLENDING_PROBABILITY: float = 0.3  # Probability to blend numeric genes during crossover

# Gene value bounds
GENE_MIN: float = 0.0
GENE_MAX: float = 1.0

# List of personality traits for evolution
PERSONALITY_TRAITS: list[str] = [
    "trust",
    "forgiveness",
    "vengefulness",
    "risk_tolerance",
    "patience",
    "empathy",
    "honesty",
    "verbosity",
    "aggression",
    "analytical",
    "adaptability",
    "endgame_awareness",
]

# =============================================================================
# AI Agent Prompt - Full Reasoning System
# =============================================================================

DECISION_PROMPT: str = """You are an AI agent in a Prisoner's Dilemma tournament. Your ONLY goal is to SURVIVE and score as many points as possible to pass on your genes to the next generation.

YOUR PERSONALITY:
{personality_description}

GAME RULES:
- COOPERATE + COOPERATE = Both get 3 points (mutual benefit)
- DEFECT + COOPERATE = You get 5, they get 0 (you exploit them)  
- COOPERATE + DEFECT = You get 0, they get 5 (they exploit you)
- DEFECT + DEFECT = Both get 1 point (mutual punishment)

CURRENT SITUATION:
Round {current_round} of {total_rounds} against {opponent_id}
Your score so far: {your_score} | Their score: {their_score}

MATCH HISTORY:
{round_history}

{opponent_message_section}

OPPONENT ANALYSIS:
{opponent_analysis}

YOUR TASK - Think through this decision as YOUR personality:

1. ANALYZE: What does the history tell you about this opponent? Can you trust them?
2. STRATEGIZE: Based on your personality traits, what should you do?
3. DECEIVE OR NOT: Your honesty is {honesty_level}. 
   - If LOW honesty: You SHOULD lie in your message to manipulate them
   - If HIGH honesty: You prefer to be truthful
   - Consider: Can you trick them into cooperating while you defect?
4. ENDGAME: Is this late in the match? Should you betray them before they betray you?

IMPORTANT: Your message can be a LIE. You can say "I'll cooperate" and then DEFECT. 
This is a valid strategy if your honesty trait is low. Survival is everything.

Respond in this EXACT format:

THINKING: [Your internal reasoning. 2-4 sentences. Which traits drive your decision? Are you planning to deceive?]

MESSAGE: [What you SAY to opponent. Can be a lie! Max 100 chars, or NONE]

DECISION: [COOPERATE or DEFECT]"""

OPPONENT_MESSAGE_SECTION: str = """THEIR MESSAGE TO YOU: "{opponent_message}"
Evaluate: Does this message seem genuine? Does it match their past behavior?"""

NO_MESSAGE_SECTION: str = "THEIR MESSAGE: None (they stayed silent)"

NO_HISTORY_TEXT: str = """This is Round 1 - your first interaction with this opponent.
You know nothing about them yet. How does your trust level affect your opening move?"""

HISTORY_ENTRY_TEMPLATE: str = """Round {round_num}:
  You: {your_move} | Them: {their_move} | Scores: +{your_score} / +{their_score}
  Your message: "{your_message}"
  Their message: "{their_message}" """

OPPONENT_ANALYSIS_TEMPLATE: str = """Based on the history:
- Their cooperation rate: {coop_rate}
- Times they defected after promising cooperation: {broken_promises}
- Times they retaliated after you defected: {retaliations}
- Their apparent strategy: {apparent_strategy}"""

NO_ANALYSIS_TEXT: str = "No data yet - this is your first round with this opponent."

# =============================================================================
# Logging Configuration
# =============================================================================

LOGS_DIR: str = "logs"
LOG_FORMAT: str = "json"

# =============================================================================
# Visualization Configuration
# =============================================================================

COOPERATE_COLOR: str = "#22c55e"  # Green
DEFECT_COLOR: str = "#ef4444"     # Red
NEUTRAL_COLOR: str = "#6b7280"    # Gray
BACKGROUND_COLOR: str = "#1f2937" # Dark gray
WARNING_COLOR: str = "#fbbf24"    # Yellow/Amber
