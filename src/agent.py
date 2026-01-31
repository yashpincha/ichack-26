"""Agent class with personality traits for AI r/place simulation."""

from __future__ import annotations

import uuid
import random
from dataclasses import dataclass, field
from typing import Any, Optional

from src.grid import COLORS


# Trait descriptions for prompt generation
TRAIT_DESCRIPTIONS = {
    "territoriality": {
        "low": "prefers spreading out, doesn't care about clustering",
        "mid": "balances expansion with some clustering",
        "high": "strongly prefers placing pixels near own territory",
    },
    "aggression": {
        "low": "avoids overwriting others, prefers empty spaces",
        "mid": "will overwrite others when strategic",
        "high": "actively targets and overwrites other agents' pixels",
    },
    "creativity": {
        "low": "expands existing areas, doesn't create new patterns",
        "mid": "mixes expansion with occasional new placements",
        "high": "loves creating new patterns and shapes",
    },
    "cooperation": {
        "low": "ignores others' work, purely self-focused",
        "mid": "sometimes builds on others' patterns",
        "high": "actively complements and builds on others' work",
    },
    "exploration": {
        "low": "sticks to familiar areas, conservative",
        "mid": "occasionally ventures to new areas",
        "high": "loves exploring empty/distant areas of the canvas",
    },
    "color_loyalty": {
        "low": "uses many colors freely, no preference",
        "mid": "mostly uses preferred color but varies",
        "high": "almost always uses preferred color",
    },
}

# Possible loose goals for agents
LOOSE_GOALS = [
    "fill the corners",
    "create a diagonal line",
    "defend the center",
    "spread across edges",
    "create a pattern",
    "maximize territory",
    "surround other colors",
    "create symmetry",
    None,  # No specific goal
]


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
    """Personality traits for canvas-based AI agents."""
    
    # Core behavioral traits (0.0 to 1.0)
    territoriality: float = 0.5    # Tendency to cluster pixels together
    aggression: float = 0.5        # Willingness to overwrite others
    creativity: float = 0.5        # Creates patterns vs expands
    cooperation: float = 0.5       # Builds on others' work
    exploration: float = 0.5       # Ventures to new areas
    color_loyalty: float = 0.5     # Sticks to preferred color
    
    # Color preference
    preferred_color: str = "red"
    
    # Shape assignment (for competitive shape battle mode)
    assigned_shape: str = "heart"  # The shape this agent must draw
    shape_position: tuple[int, int] = (0, 0)  # Where to draw the shape (x, y offset)
    
    # Optional loose goal (legacy, now secondary to shape)
    loose_goal: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert personality to dictionary."""
        return {
            "territoriality": self.territoriality,
            "aggression": self.aggression,
            "creativity": self.creativity,
            "cooperation": self.cooperation,
            "exploration": self.exploration,
            "color_loyalty": self.color_loyalty,
            "preferred_color": self.preferred_color,
            "assigned_shape": self.assigned_shape,
            "shape_position": list(self.shape_position),
            "loose_goal": self.loose_goal,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentPersonality":
        """Create personality from dictionary."""
        shape_pos = data.get("shape_position", [0, 0])
        if isinstance(shape_pos, list):
            shape_pos = tuple(shape_pos)
        return cls(
            territoriality=data.get("territoriality", 0.5),
            aggression=data.get("aggression", 0.5),
            creativity=data.get("creativity", 0.5),
            cooperation=data.get("cooperation", 0.5),
            exploration=data.get("exploration", 0.5),
            color_loyalty=data.get("color_loyalty", 0.5),
            preferred_color=data.get("preferred_color", "red"),
            assigned_shape=data.get("assigned_shape", "heart"),
            shape_position=shape_pos,
            loose_goal=data.get("loose_goal"),
        )
    
    @classmethod
    def random(cls, assigned_shape: str = "heart", shape_position: tuple[int, int] = (0, 0)) -> "AgentPersonality":
        """Create a completely random personality with assigned shape."""
        from src.shapes import SHAPE_NAMES
        return cls(
            territoriality=random.random(),
            aggression=random.random(),
            creativity=random.random(),
            cooperation=random.random(),
            exploration=random.random(),
            color_loyalty=random.random(),
            preferred_color=random.choice(COLORS),
            assigned_shape=assigned_shape,
            shape_position=shape_position,
            loose_goal=None,  # Shape is now the main goal
        )
    
    def get_prompt_description(self) -> str:
        """Generate personality description for the AI prompt."""
        lines = []
        
        # Numeric traits
        traits = {
            "territoriality": self.territoriality,
            "aggression": self.aggression,
            "creativity": self.creativity,
            "cooperation": self.cooperation,
            "exploration": self.exploration,
            "color_loyalty": self.color_loyalty,
        }
        
        for trait, value in traits.items():
            pct = int(value * 100)
            desc = get_trait_description(trait, value)
            trait_name = trait.replace("_", " ").title()
            lines.append(f"- {trait_name}: {pct}% ({desc})")
        
        lines.append(f"- Preferred Color: {self.preferred_color}")
        lines.append(f"- Assigned Shape: {self.assigned_shape}")
        
        return "\n".join(lines)
    
    def get_short_description(self) -> str:
        """Get a short 2-3 word personality summary."""
        descriptors = []
        
        # Pick most extreme traits
        traits = {
            "territoriality": self.territoriality,
            "aggression": self.aggression,
            "creativity": self.creativity,
            "cooperation": self.cooperation,
            "exploration": self.exploration,
            "color_loyalty": self.color_loyalty,
        }
        
        sorted_traits = sorted(traits.items(), key=lambda x: abs(x[1] - 0.5), reverse=True)
        
        for trait, value in sorted_traits[:2]:
            if value < 0.3:
                if trait == "territoriality":
                    descriptors.append("Scattered")
                elif trait == "aggression":
                    descriptors.append("Peaceful")
                elif trait == "creativity":
                    descriptors.append("Expansive")
                elif trait == "cooperation":
                    descriptors.append("Solo")
                elif trait == "exploration":
                    descriptors.append("Homebody")
                elif trait == "color_loyalty":
                    descriptors.append("Colorful")
            elif value > 0.7:
                if trait == "territoriality":
                    descriptors.append("Territorial")
                elif trait == "aggression":
                    descriptors.append("Aggressive")
                elif trait == "creativity":
                    descriptors.append("Creative")
                elif trait == "cooperation":
                    descriptors.append("Cooperative")
                elif trait == "exploration":
                    descriptors.append("Explorer")
                elif trait == "color_loyalty":
                    descriptors.append("Loyal")
        
        if not descriptors:
            descriptors = ["Balanced"]
        
        return ", ".join(descriptors[:2])
    
    def get_trait_list(self) -> list[str]:
        """Get list of numeric trait names."""
        return ["territoriality", "aggression", "creativity", "cooperation", "exploration", "color_loyalty"]


# Alias for compatibility
AgentDNA = AgentPersonality


@dataclass
class Agent:
    """An AI agent that places pixels on the canvas."""
    
    id: str
    generation: int
    personality: AgentPersonality
    parent_ids: list[str] = field(default_factory=list)
    fitness: int = 0
    
    # Track statistics
    pixels_placed: int = 0
    pixels_lost: int = 0  # Overwritten by others
    overwrites: int = 0   # Times overwriting others
    
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
    def preferred_color(self) -> str:
        """Get agent's preferred color."""
        return self.personality.preferred_color
    
    @property
    def assigned_shape(self) -> str:
        """Get agent's assigned shape."""
        return self.personality.assigned_shape
    
    @property
    def shape_position(self) -> tuple[int, int]:
        """Get agent's shape position."""
        return self.personality.shape_position
    
    @property
    def survival_rate(self) -> float:
        """Calculate what percentage of placed pixels survived."""
        if self.pixels_placed == 0:
            return 0.0
        survived = self.pixels_placed - self.pixels_lost
        return max(0, survived) / self.pixels_placed
    
    def record_placement(self) -> None:
        """Record that agent placed a pixel."""
        self.pixels_placed += 1
    
    def record_pixel_lost(self) -> None:
        """Record that one of agent's pixels was overwritten."""
        self.pixels_lost += 1
    
    def record_overwrite(self) -> None:
        """Record that agent overwrote another's pixel."""
        self.overwrites += 1
    
    def add_fitness(self, points: int) -> None:
        """Add points to fitness score."""
        self.fitness += points
    
    def reset_fitness(self) -> None:
        """Reset fitness and stats for new generation."""
        self.fitness = 0
        self.pixels_placed = 0
        self.pixels_lost = 0
        self.overwrites = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize agent to dictionary."""
        return {
            "id": self.id,
            "generation": self.generation,
            "personality": self.personality.to_dict(),
            "parent_ids": self.parent_ids.copy(),
            "fitness": self.fitness,
            "pixels_placed": self.pixels_placed,
            "pixels_lost": self.pixels_lost,
            "overwrites": self.overwrites,
            "short_description": self.personality.get_short_description(),
            "assigned_shape": self.assigned_shape,
            "shape_position": list(self.shape_position),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Agent":
        """Deserialize agent from dictionary."""
        personality_data = data.get("personality", data.get("dna", {}))
        
        return cls(
            id=data["id"],
            generation=data["generation"],
            personality=AgentPersonality.from_dict(personality_data),
            parent_ids=data.get("parent_ids", []),
            fitness=data.get("fitness", 0),
            pixels_placed=data.get("pixels_placed", 0),
            pixels_lost=data.get("pixels_lost", 0),
            overwrites=data.get("overwrites", 0),
        )
    
    @classmethod
    def create_random(
        cls,
        generation: int = 0,
        assigned_shape: str = "heart",
        shape_position: tuple[int, int] = (0, 0),
    ) -> "Agent":
        """Create a new agent with random personality and assigned shape."""
        return cls(
            id=f"agent_{uuid.uuid4().hex[:8]}",
            generation=generation,
            personality=AgentPersonality.random(assigned_shape, shape_position),
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
            pixels_placed=self.pixels_placed,
            pixels_lost=self.pixels_lost,
            overwrites=self.overwrites,
        )
    
    def __repr__(self) -> str:
        desc = self.personality.get_short_description()
        return f"Agent({self.id[:12]}, {self.preferred_color}, {desc}, fitness={self.fitness})"
    
    def summary(self) -> str:
        """Get a human-readable summary of the agent."""
        desc = self.personality.get_short_description()
        return (
            f"Agent {self.id} (Gen {self.generation}) - {desc}\n"
            f"  Color: {self.preferred_color}\n"
            f"  Shape: {self.assigned_shape} at {self.shape_position}\n"
            f"  Fitness: {self.fitness}\n"
            f"  Pixels Placed: {self.pixels_placed}, Lost: {self.pixels_lost}\n"
            f"  Survival Rate: {self.survival_rate:.1%}"
        )


def create_initial_population(
    num_agents: int = 4,
    grid_width: int = 32,
    grid_height: int = 32,
) -> list[Agent]:
    """Create the initial population with assigned shapes."""
    from src.shapes import get_shapes_for_agents, calculate_shape_positions
    
    # Get shapes and positions for each agent
    shapes = get_shapes_for_agents(num_agents)
    positions = calculate_shape_positions(num_agents, grid_width, grid_height, shapes)
    
    agents = []
    for i in range(num_agents):
        agent = Agent.create_random(
            generation=0,
            assigned_shape=shapes[i],
            shape_position=positions[i],
        )
        agents.append(agent)
    
    return agents
