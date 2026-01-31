"""Agent class with genetic DNA for the evolutionary tournament."""

from __future__ import annotations

import uuid
import copy
from dataclasses import dataclass, field
from typing import Any

from src.config import DEFAULT_GENES


@dataclass
class AgentDNA:
    """Genetic representation of an agent's behavioral traits."""
    
    # Behavioral traits (0.0 to 1.0)
    cooperation_bias: float = 0.5        # Base tendency to cooperate
    retaliation_sensitivity: float = 0.5  # How quickly to punish defection
    forgiveness_rate: float = 0.3         # Probability to forgive after punishment
    memory_weight: float = 0.7            # How much history influences decisions
    
    # Reasoning style
    reasoning_depth: str = "medium"       # "shallow" | "medium" | "deep"
    strategy_keywords: list[str] = field(default_factory=lambda: ["adaptive", "cautious"])
    
    # Message behavior
    message_honesty: float = 0.5          # How truthful in messages
    threat_frequency: float = 0.2         # How often to threaten
    
    def to_dict(self) -> dict[str, Any]:
        """Convert DNA to dictionary."""
        return {
            "cooperation_bias": self.cooperation_bias,
            "retaliation_sensitivity": self.retaliation_sensitivity,
            "forgiveness_rate": self.forgiveness_rate,
            "memory_weight": self.memory_weight,
            "reasoning_depth": self.reasoning_depth,
            "strategy_keywords": self.strategy_keywords.copy(),
            "message_honesty": self.message_honesty,
            "threat_frequency": self.threat_frequency,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentDNA:
        """Create DNA from dictionary."""
        return cls(
            cooperation_bias=data.get("cooperation_bias", 0.5),
            retaliation_sensitivity=data.get("retaliation_sensitivity", 0.5),
            forgiveness_rate=data.get("forgiveness_rate", 0.3),
            memory_weight=data.get("memory_weight", 0.7),
            reasoning_depth=data.get("reasoning_depth", "medium"),
            strategy_keywords=data.get("strategy_keywords", ["adaptive", "cautious"]).copy(),
            message_honesty=data.get("message_honesty", 0.5),
            threat_frequency=data.get("threat_frequency", 0.2),
        )
    
    @classmethod
    def random(cls) -> AgentDNA:
        """Create DNA with random gene values."""
        import random
        from src.config import STRATEGY_KEYWORD_POOL, REASONING_DEPTH_OPTIONS
        
        num_keywords = random.randint(1, 3)
        keywords = random.sample(STRATEGY_KEYWORD_POOL, num_keywords)
        
        return cls(
            cooperation_bias=random.random(),
            retaliation_sensitivity=random.random(),
            forgiveness_rate=random.random(),
            memory_weight=random.random(),
            reasoning_depth=random.choice(REASONING_DEPTH_OPTIONS),
            strategy_keywords=keywords,
            message_honesty=random.random(),
            threat_frequency=random.random(),
        )


@dataclass
class Agent:
    """An AI agent with genetic DNA that competes in Prisoner's Dilemma."""
    
    id: str
    generation: int
    dna: AgentDNA
    parent_ids: list[str] = field(default_factory=list)
    fitness: int = 0
    matches_played: int = 0
    
    # Track statistics
    total_cooperations: int = 0
    total_defections: int = 0
    
    def __post_init__(self):
        """Ensure parent_ids is a list."""
        if self.parent_ids is None:
            self.parent_ids = []
    
    @property
    def genes(self) -> dict[str, Any]:
        """Get DNA as dictionary (for backward compatibility)."""
        return self.dna.to_dict()
    
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
    
    def record_move(self, move: str) -> None:
        """Record a move for statistics."""
        if move == "COOPERATE":
            self.total_cooperations += 1
        else:
            self.total_defections += 1
    
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
            "dna": self.dna.to_dict(),
            "parent_ids": self.parent_ids.copy(),
            "fitness": self.fitness,
            "matches_played": self.matches_played,
            "total_cooperations": self.total_cooperations,
            "total_defections": self.total_defections,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Agent:
        """Deserialize agent from dictionary."""
        return cls(
            id=data["id"],
            generation=data["generation"],
            dna=AgentDNA.from_dict(data["dna"]),
            parent_ids=data.get("parent_ids", []),
            fitness=data.get("fitness", 0),
            matches_played=data.get("matches_played", 0),
            total_cooperations=data.get("total_cooperations", 0),
            total_defections=data.get("total_defections", 0),
        )
    
    @classmethod
    def create_random(cls, generation: int = 0) -> Agent:
        """Create a new agent with random DNA."""
        return cls(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            generation=generation,
            dna=AgentDNA.random(),
        )
    
    @classmethod
    def create_baseline(cls) -> Agent:
        """Create a baseline agent with default/neutral genes."""
        return cls(
            id="baseline_agent",
            generation=-1,  # Special marker for baseline
            dna=AgentDNA.from_dict(DEFAULT_GENES),
        )
    
    def clone(self) -> Agent:
        """Create a deep copy of this agent."""
        return Agent(
            id=self.id,
            generation=self.generation,
            dna=AgentDNA.from_dict(self.dna.to_dict()),
            parent_ids=self.parent_ids.copy(),
            fitness=self.fitness,
            matches_played=self.matches_played,
            total_cooperations=self.total_cooperations,
            total_defections=self.total_defections,
        )
    
    def __repr__(self) -> str:
        return f"Agent(id={self.id}, gen={self.generation}, fitness={self.fitness})"
    
    def summary(self) -> str:
        """Get a human-readable summary of the agent."""
        return (
            f"Agent {self.id} (Gen {self.generation})\n"
            f"  Fitness: {self.fitness} ({self.avg_fitness_per_match:.1f}/match)\n"
            f"  Cooperation Rate: {self.cooperation_rate:.1%}\n"
            f"  Traits: coop={self.dna.cooperation_bias:.2f}, "
            f"retaliation={self.dna.retaliation_sensitivity:.2f}, "
            f"forgiveness={self.dna.forgiveness_rate:.2f}\n"
            f"  Style: {', '.join(self.dna.strategy_keywords)}"
        )


def create_initial_population(num_agents: int = 8) -> list[Agent]:
    """Create the initial population of random agents."""
    return [Agent.create_random(generation=0) for _ in range(num_agents)]
