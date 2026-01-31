"""Simulation loop for AI r/place canvas - Shape Battle Mode."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

from src.agent import Agent
from src.grid import Grid, PlacementRecord
from src.llm import get_pixel_decision, LLMClient
from src.shapes import get_shape_pixels, shape_to_ascii, get_shape_pixel_count
from src.config import (
    GRID_WIDTH,
    GRID_HEIGHT,
    TURNS_PER_GENERATION,
    FITNESS_TERRITORY_WEIGHT,
    FITNESS_PERSISTENCE_WEIGHT,
)


@dataclass
class TurnResult:
    """Result of a single turn."""
    turn: int
    agent_id: str
    x: int
    y: int
    color: str
    thinking: str
    overwrote: Optional[str] = None  # ID of agent that was overwritten
    valid: bool = True
    shape_completion: float = 0.0  # Current shape completion percentage
    
    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "agent_id": self.agent_id,
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "thinking": self.thinking,
            "overwrote": self.overwrote,
            "valid": self.valid,
            "shape_completion": self.shape_completion,
        }


@dataclass
class GenerationResult:
    """Result of a complete generation."""
    generation: int
    turns: list[TurnResult] = field(default_factory=list)
    final_grid: Optional[Grid] = None
    agent_fitness: dict[str, int] = field(default_factory=dict)
    agent_territory: dict[str, int] = field(default_factory=dict)
    agent_shape_completion: dict[str, dict] = field(default_factory=dict)  # Shape completion stats
    
    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "total_turns": len(self.turns),
            "turns": [t.to_dict() for t in self.turns],
            "agent_fitness": self.agent_fitness,
            "agent_territory": self.agent_territory,
            "agent_shape_completion": self.agent_shape_completion,
            "final_grid": self.final_grid.to_dict() if self.final_grid else None,
        }


def evaluate_fitness(agent: Agent, grid: Grid, shape_pixels: Optional[list] = None) -> int:
    """
    Evaluate fitness for an agent based on shape completion.
    
    In Shape Battle mode, fitness is primarily based on how complete
    the agent's assigned shape is at the end of the generation.
    
    Fitness = shape_completion_percentage * 10 (0-1000 range)
    """
    if shape_pixels:
        # Shape battle mode - fitness based on shape completion
        completion = grid.get_shape_completion(agent.id, shape_pixels)
        # Scale to 0-1000 range (percentage * 10)
        fitness = int(completion["percentage"] * 10)
    else:
        # Legacy mode - territory-based fitness
        territory = grid.get_territory_count(agent.id)
        persistence = grid.get_average_pixel_lifespan(agent.id)
        fitness = int(
            territory * FITNESS_TERRITORY_WEIGHT +
            persistence * FITNESS_PERSISTENCE_WEIGHT
        )
    
    return fitness


def get_agent_shape_pixels(agent: Agent) -> list[tuple[int, int, str]]:
    """Get the list of pixels for an agent's assigned shape."""
    return get_shape_pixels(
        shape_name=agent.assigned_shape,
        color=agent.preferred_color,
        offset_x=agent.shape_position[0],
        offset_y=agent.shape_position[1],
    )


async def run_agent_turn(
    agent: Agent,
    grid: Grid,
    turn: int,
    llm_client: LLMClient,
    total_turns: int = TURNS_PER_GENERATION,
) -> TurnResult:
    """Execute a single agent's turn in Shape Battle mode."""
    # Get recent history for context
    recent = grid.get_recent_history(10)
    recent_history = [
        {
            "turn": r.turn,
            "agent_id": r.agent_id,
            "x": r.x,
            "y": r.y,
            "color": r.color,
        }
        for r in recent
    ]
    
    # Get agent's shape information
    shape_pixels = get_agent_shape_pixels(agent)
    shape_completion = grid.get_shape_completion(agent.id, shape_pixels)
    shape_status = grid.get_shape_pixels_status(agent.id, shape_pixels)
    shape_ascii = shape_to_ascii(agent.assigned_shape, fill_char="X", empty_char=".")
    
    # Get pixel decision from LLM
    decision = await get_pixel_decision(
        agent_id=agent.id,
        personality_description=agent.personality.get_prompt_description(),
        agent_color=agent.preferred_color,
        grid_ascii=grid.to_ascii(),
        grid_width=grid.width,
        grid_height=grid.height,
        territory_count=grid.get_territory_count(agent.id),
        current_turn=turn,
        total_turns=total_turns,
        recent_history=recent_history,
        # Shape battle parameters
        shape_name=agent.assigned_shape,
        shape_ascii=shape_ascii,
        shape_x=agent.shape_position[0],
        shape_y=agent.shape_position[1],
        shape_completion=shape_completion,
        shape_status=shape_status,
        aggression=agent.personality.aggression,
        territoriality=agent.personality.territoriality,
        goal=None,
        client=llm_client,
    )
    
    # Check if overwriting another agent
    current_pixel = grid.get_pixel(decision.x, decision.y)
    overwrote = None
    if current_pixel and current_pixel.owner_id and current_pixel.owner_id != agent.id:
        overwrote = current_pixel.owner_id
        agent.record_overwrite()
    
    # Place the pixel
    success = grid.place_pixel(
        x=decision.x,
        y=decision.y,
        color=decision.color,
        agent_id=agent.id,
        turn=turn,
    )
    
    if success:
        agent.record_placement()
    
    # Get updated shape completion after placement
    updated_completion = grid.get_shape_completion(agent.id, shape_pixels)
    
    return TurnResult(
        turn=turn,
        agent_id=agent.id,
        x=decision.x,
        y=decision.y,
        color=decision.color,
        thinking=decision.thinking,
        overwrote=overwrote,
        valid=decision.valid and success,
        shape_completion=updated_completion["percentage"],
    )


async def run_generation(
    agents: list[Agent],
    grid: Grid,
    generation: int,
    turns_per_gen: int = TURNS_PER_GENERATION,
    llm_client: Optional[LLMClient] = None,
    on_turn_complete: Optional[Callable[[TurnResult, int, int], None]] = None,
    randomize_order: bool = True,
) -> GenerationResult:
    """
    Run a complete generation of the Shape Battle simulation.
    
    Args:
        agents: List of agents participating
        grid: The canvas grid
        generation: Generation number
        turns_per_gen: Number of turns per generation
        llm_client: LLM client for agent decisions
        on_turn_complete: Callback after each turn (turn_result, completed, total)
        randomize_order: Whether to randomize agent order each turn
    
    Returns:
        GenerationResult with all turn data and final fitness
    """
    if llm_client is None:
        from src.llm import get_llm_client
        llm_client = get_llm_client()
    
    result = GenerationResult(generation=generation)
    total_agent_turns = turns_per_gen * len(agents)
    completed = 0
    
    # Pre-compute shape pixels for each agent
    agent_shapes = {agent.id: get_agent_shape_pixels(agent) for agent in agents}
    
    for turn in range(1, turns_per_gen + 1):
        grid.current_turn = turn
        
        # Optionally randomize agent order each turn
        turn_agents = list(agents)
        if randomize_order:
            random.shuffle(turn_agents)
        
        # Each agent takes a turn
        for agent in turn_agents:
            turn_result = await run_agent_turn(
                agent=agent,
                grid=grid,
                turn=turn,
                llm_client=llm_client,
                total_turns=turns_per_gen,
            )
            result.turns.append(turn_result)
            
            # Update pixel loss tracking
            if turn_result.overwrote:
                for a in agents:
                    if a.id == turn_result.overwrote:
                        a.record_pixel_lost()
                        break
            
            completed += 1
            if on_turn_complete:
                on_turn_complete(turn_result, completed, total_agent_turns)
    
    # Calculate final fitness based on shape completion
    for agent in agents:
        shape_pixels = agent_shapes[agent.id]
        fitness = evaluate_fitness(agent, grid, shape_pixels)
        agent.add_fitness(fitness)
        result.agent_fitness[agent.id] = fitness
        result.agent_territory[agent.id] = grid.get_territory_count(agent.id)
        
        # Store shape completion stats
        completion = grid.get_shape_completion(agent.id, shape_pixels)
        result.agent_shape_completion[agent.id] = {
            "shape": agent.assigned_shape,
            "position": list(agent.shape_position),
            "completed": completion["completed"],
            "total": completion["total"],
            "percentage": completion["percentage"],
            "destroyed": completion["destroyed"],
        }
    
    result.final_grid = grid.clone()
    
    return result


def get_generation_statistics(result: GenerationResult, agents: list[Agent]) -> dict:
    """Get statistics for a completed generation including shape completion."""
    if not result.final_grid:
        return {}
    
    grid = result.final_grid
    
    # Calculate various statistics
    total_pixels = grid.width * grid.height
    filled_pixels = total_pixels - grid.get_empty_count()
    
    # Agent rankings by fitness (shape completion)
    agent_rankings = sorted(
        [
            {
                "agent_id": agent.id,
                "fitness": agent.fitness,
                "territory": grid.get_territory_count(agent.id),
                "pixels_placed": agent.pixels_placed,
                "pixels_lost": agent.pixels_lost,
                "overwrites": agent.overwrites,
                "survival_rate": agent.survival_rate,
                "color": agent.preferred_color,
                "personality": agent.personality.get_short_description(),
                "shape": agent.assigned_shape,
                "shape_position": list(agent.shape_position),
                "shape_completion": result.agent_shape_completion.get(agent.id, {}),
            }
            for agent in agents
        ],
        key=lambda x: x["fitness"],
        reverse=True,
    )
    
    # Add ranks
    for i, ranking in enumerate(agent_rankings, 1):
        ranking["rank"] = i
    
    # Determine winner
    winner = agent_rankings[0] if agent_rankings else None
    
    return {
        "generation": result.generation,
        "total_turns": len(result.turns),
        "total_pixels": total_pixels,
        "filled_pixels": filled_pixels,
        "fill_rate": filled_pixels / total_pixels if total_pixels > 0 else 0,
        "agent_rankings": agent_rankings,
        "territory_by_agent": result.agent_territory,
        "shape_completion_by_agent": result.agent_shape_completion,
        "winner": winner,
    }
