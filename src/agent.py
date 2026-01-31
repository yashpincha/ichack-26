"""Agent class with 12-trait personality system for true AI agents."""

from __future__ import annotations

import uuid
import random
from dataclasses import dataclass, field
from typing import Any, Optional


# Trait descriptions for prompt generation
TRAIT_DESCRIPTIONS = {
    "trust": {
        "low": "highly suspicious of others, assumes bad intent",
        "mid": "cautiously trusting, gives benefit of doubt",
        "high": "very trusting, believes others are honest",
    },
    "forgiveness": {
        "low": "never forgives betrayal, holds grudges forever",
        "mid": "forgives after appropriate punishment",
        "high": "forgives easily, quick to move past betrayal",
    },
    "vengefulness": {
        "low": "rarely retaliates, turns the other cheek",
        "mid": "retaliates proportionally to offense",
        "high": "aggressively retaliates, punishes harshly",
    },
    "risk_tolerance": {
        "low": "very risk-averse, plays it safe",
        "mid": "takes calculated risks when odds are good",
        "high": "loves risk, gambles for big rewards",
    },
    "patience": {
        "low": "wants immediate rewards, short-term thinker",
        "mid": "balances short and long-term gains",
        "high": "patient strategist, invests in future",
    },
    "empathy": {
        "low": "cares only about own score, ruthless",
        "mid": "considers mutual benefit when convenient",
        "high": "genuinely cares about mutual outcomes",
    },
    "honesty": {
        "low": "lies freely, says whatever helps",
        "mid": "honest when it doesn't cost much",
        "high": "strongly values honesty, rarely lies",
    },
    "verbosity": {
        "low": "silent or terse, few words",
        "mid": "communicates key points clearly",
        "high": "very talkative, explains reasoning",
    },
    "aggression": {
        "low": "gentle, friendly communication",
        "mid": "firm but fair communication",
        "high": "threatening, intimidating tone",
    },
    "analytical": {
        "low": "goes with gut feeling, intuitive",
        "mid": "uses both analysis and intuition",
        "high": "heavily analyzes patterns and data",
    },
    "adaptability": {
        "low": "sticks to one strategy regardless",
        "mid": "adjusts strategy when needed",
        "high": "constantly adapts to opponent",
    },
    "endgame_awareness": {
        "low": "ignores that game will end",
        "mid": "aware of endgame implications",
        "high": "always thinking about final rounds",
    },
}


def get_trait_level(value: float) -> str:
    """Get trait level (low/mid/high) from 0-1 value."""
    if value < 0.33:
        return "low"
    elif value < 0.67:
        return "mid"
    else:
        return "high"


def get_trait_description(trait: str, value: float) -> str:
    """Get human-readable description for a trait value."""
    level = get_trait_level(value)
    return TRAIT_DESCRIPTIONS.get(trait, {}).get(level, f"{trait}: {value:.0%}")


@dataclass
class AgentPersonality:
    """12-trait personality system for AI agents."""
    
    # Core behavioral traits (0.0 to 1.0)
    trust: float = 0.5              # How trusting of strangers
    forgiveness: float = 0.5        # How easily forgives betrayal
    vengefulness: float = 0.5       # How strongly retaliates
    risk_tolerance: float = 0.5     # Willingness to take chances
    patience: float = 0.5           # Long-term vs short-term thinking
    empathy: float = 0.5            # Cares about opponent's outcome
    
    # Communication style (0.0 to 1.0)
    honesty: float = 0.5            # How truthful in messages
    verbosity: float = 0.5          # How much they communicate
    aggression: float = 0.5         # Threatening vs friendly tone
    
    # Strategic style (0.0 to 1.0)
    analytical: float = 0.5         # Relies on patterns vs intuition
    adaptability: float = 0.5       # Changes strategy vs consistent
    endgame_awareness: float = 0.5  # Thinks about final rounds
    
    def to_dict(self) -> dict[str, float]:
        """Convert personality to dictionary."""
        return {
            "trust": self.trust,
            "forgiveness": self.forgiveness,
            "vengefulness": self.vengefulness,
            "risk_tolerance": self.risk_tolerance,
            "patience": self.patience,
            "empathy": self.empathy,
            "honesty": self.honesty,
            "verbosity": self.verbosity,
            "aggression": self.aggression,
            "analytical": self.analytical,
            "adaptability": self.adaptability,
            "endgame_awareness": self.endgame_awareness,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentPersonality":
        """Create personality from dictionary."""
        return cls(
            trust=data.get("trust", 0.5),
            forgiveness=data.get("forgiveness", 0.5),
            vengefulness=data.get("vengefulness", 0.5),
            risk_tolerance=data.get("risk_tolerance", 0.5),
            patience=data.get("patience", 0.5),
            empathy=data.get("empathy", 0.5),
            honesty=data.get("honesty", 0.5),
            verbosity=data.get("verbosity", 0.5),
            aggression=data.get("aggression", 0.5),
            analytical=data.get("analytical", 0.5),
            adaptability=data.get("adaptability", 0.5),
            endgame_awareness=data.get("endgame_awareness", 0.5),
        )
    
    @classmethod
    def random(cls) -> "AgentPersonality":
        """Create a completely random personality."""
        return cls(
            trust=random.random(),
            forgiveness=random.random(),
            vengefulness=random.random(),
            risk_tolerance=random.random(),
            patience=random.random(),
            empathy=random.random(),
            honesty=random.random(),
            verbosity=random.random(),
            aggression=random.random(),
            analytical=random.random(),
            adaptability=random.random(),
            endgame_awareness=random.random(),
        )
    
    def get_prompt_description(self) -> str:
        """Generate personality description for the AI prompt."""
        lines = []
        traits = self.to_dict()
        
        for trait, value in traits.items():
            pct = int(value * 100)
            desc = get_trait_description(trait, value)
            trait_name = trait.replace("_", " ").title()
            lines.append(f"- {trait_name}: {pct}% ({desc})")
        
        return "\n".join(lines)
    
    def get_short_description(self) -> str:
        """Get a short 2-3 word personality summary."""
        descriptors = []
        
        # Pick most extreme traits
        traits = self.to_dict()
        sorted_traits = sorted(traits.items(), key=lambda x: abs(x[1] - 0.5), reverse=True)
        
        for trait, value in sorted_traits[:3]:
            if value < 0.3:
                if trait == "trust":
                    descriptors.append("Suspicious")
                elif trait == "honesty":
                    descriptors.append("Deceptive")
                elif trait == "patience":
                    descriptors.append("Impulsive")
                elif trait == "empathy":
                    descriptors.append("Ruthless")
                elif trait == "forgiveness":
                    descriptors.append("Grudging")
            elif value > 0.7:
                if trait == "trust":
                    descriptors.append("Trusting")
                elif trait == "honesty":
                    descriptors.append("Honest")
                elif trait == "patience":
                    descriptors.append("Patient")
                elif trait == "empathy":
                    descriptors.append("Empathetic")
                elif trait == "vengefulness":
                    descriptors.append("Vengeful")
                elif trait == "risk_tolerance":
                    descriptors.append("Risk-Taker")
                elif trait == "aggression":
                    descriptors.append("Aggressive")
                elif trait == "analytical":
                    descriptors.append("Analytical")
        
        if not descriptors:
            descriptors = ["Balanced"]
        
        return ", ".join(descriptors[:2])
    
    def get_trait_list(self) -> list[str]:
        """Get list of trait names."""
        return list(self.to_dict().keys())


# Legacy alias for backward compatibility
AgentDNA = AgentPersonality


@dataclass
class Agent:
    """An AI agent with personality that competes in Prisoner's Dilemma."""
    
    id: str
    generation: int
    personality: AgentPersonality
    parent_ids: list[str] = field(default_factory=list)
    fitness: int = 0
    matches_played: int = 0
    
    # Track statistics
    total_cooperations: int = 0
    total_defections: int = 0
    
    # Track deception (new)
    lies_told: int = 0
    promises_kept: int = 0
    promises_broken: int = 0
    
    def __post_init__(self):
        """Ensure parent_ids is a list."""
        if self.parent_ids is None:
            self.parent_ids = []
    
    @property
    def dna(self) -> AgentPersonality:
        """Alias for backward compatibility."""
        return self.personality
    
    @property
    def genes(self) -> dict[str, Any]:
        """Get personality as dictionary."""
        return self.personality.to_dict()
    
    @property
    def cooperation_rate(self) -> float:
        """Calculate cooperation rate from history."""
        total = self.total_cooperations + self.total_defections
        if total == 0:
            return 0.5
        return self.total_cooperations / total
    
    @property
    def avg_fitness_per_match(self) -> float:
        """Calculate average fitness per match."""
        if self.matches_played == 0:
            return 0.0
        return self.fitness / self.matches_played
    
    @property
    def deception_rate(self) -> float:
        """Calculate how often agent breaks promises."""
        total = self.promises_kept + self.promises_broken
        if total == 0:
            return 0.0
        return self.promises_broken / total
    
    def record_move(self, move: str) -> None:
        """Record a move for statistics."""
        if move == "COOPERATE":
            self.total_cooperations += 1
        else:
            self.total_defections += 1
    
    def record_lie(self) -> None:
        """Record that the agent lied."""
        self.lies_told += 1
    
    def record_promise_kept(self) -> None:
        """Record that agent kept a promise."""
        self.promises_kept += 1
    
    def record_promise_broken(self) -> None:
        """Record that agent broke a promise."""
        self.promises_broken += 1
    
    def add_fitness(self, points: int) -> None:
        """Add points to fitness score."""
        self.fitness += points
    
    def increment_matches(self) -> None:
        """Increment match counter."""
        self.matches_played += 1
    
    def reset_fitness(self) -> None:
        """Reset fitness for new generation (keep stats for analysis)."""
        self.fitness = 0
        self.matches_played = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "id": self.id,
            "generation": self.generation,
            "personality": self.personality.to_dict(),
            "dna": self.personality.to_dict(),  # Legacy compatibility
            "parent_ids": self.parent_ids.copy(),
            "fitness": self.fitness,
            "matches_played": self.matches_played,
            "total_cooperations": self.total_cooperations,
            "total_defections": self.total_defections,
            "lies_told": self.lies_told,
            "promises_kept": self.promises_kept,
            "promises_broken": self.promises_broken,
            "short_description": self.personality.get_short_description(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        """Deserialize agent from dictionary."""
        # Support both "personality" and legacy "dna" keys
        personality_data = data.get("personality", data.get("dna", {}))
        
        return cls(
            id=data["id"],
            generation=data["generation"],
            personality=AgentPersonality.from_dict(personality_data),
            parent_ids=data.get("parent_ids", []),
            fitness=data.get("fitness", 0),
            matches_played=data.get("matches_played", 0),
            total_cooperations=data.get("total_cooperations", 0),
            total_defections=data.get("total_defections", 0),
            lies_told=data.get("lies_told", 0),
            promises_kept=data.get("promises_kept", 0),
            promises_broken=data.get("promises_broken", 0),
        )
    
    @classmethod
    def create_random(cls, generation: int = 0) -> "Agent":
        """Create a new agent with completely random personality."""
        return cls(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            generation=generation,
            personality=AgentPersonality.random(),
        )
    
    @classmethod
    def create_baseline(cls) -> "Agent":
        """Create a baseline agent with neutral personality."""
        return cls(
            id="baseline_agent",
            generation=-1,
            personality=AgentPersonality(),  # All 0.5 values
        )
    
    def clone(self) -> "Agent":
        """Create a deep copy of this agent."""
        return Agent(
            id=self.id,
            generation=self.generation,
            personality=AgentPersonality.from_dict(self.personality.to_dict()),
            parent_ids=self.parent_ids.copy(),
            fitness=self.fitness,
            matches_played=self.matches_played,
            total_cooperations=self.total_cooperations,
            total_defections=self.total_defections,
            lies_told=self.lies_told,
            promises_kept=self.promises_kept,
            promises_broken=self.promises_broken,
        )
    
    def __repr__(self) -> str:
        desc = self.personality.get_short_description()
        return f"Agent({self.id[:12]}, {desc}, fitness={self.fitness})"
    
    def summary(self) -> str:
        """Get a human-readable summary of the agent."""
        desc = self.personality.get_short_description()
        return (
            f"Agent {self.id} (Gen {self.generation}) - {desc}\n"
            f"  Fitness: {self.fitness} ({self.avg_fitness_per_match:.1f}/match)\n"
            f"  Cooperation Rate: {self.cooperation_rate:.1%}\n"
            f"  Deception Rate: {self.deception_rate:.1%}\n"
            f"  Key Traits: Trust={self.personality.trust:.0%}, "
            f"Vengefulness={self.personality.vengefulness:.0%}, "
            f"Honesty={self.personality.honesty:.0%}"
        )


def create_initial_population(num_agents: int = 8) -> list[Agent]:
    """Create the initial population of completely random agents."""
    return [Agent.create_random(generation=0) for _ in range(num_agents)]
