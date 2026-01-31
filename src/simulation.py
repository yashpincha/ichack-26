"""Simulation loop for AI r/place canvas."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

from src.agent import Agent
from src.grid import Grid, PlacementRecord
from src.llm import get_pixel_decision, LLMClient
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
        }


@dataclass
class GenerationResult:
    """Result of a complete generation."""
    generation: int
    turns: list[TurnResult] = field(default_factory=list)
    final_grid: Optional[Grid] = None
    agent_fitness: dict[str, int] = field(default_factory=dict)
    agent_territory: dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "total_turns": len(self.turns),
            "turns": [t.to_dict() for t in self.turns],
            "agent_fitness": self.agent_fitness,
            "agent_territory": self.agent_territory,
            "final_grid": self.final_grid.to_dict() if self.final_grid else None,
        }


def evaluate_fitness(agent: Agent, grid: Grid) -> int:
    """
    Evaluate fitness for an agent based on grid state.
    
    Fitness = (territory * weight) + (persistence * weight)
    """
    territory = grid.get_territory_count(agent.id)
    persistence = grid.get_average_pixel_lifespan(agent.id)
    
    fitness = int(
        territory * FITNESS_TERRITORY_WEIGHT +
        persistence * FITNESS_PERSISTENCE_WEIGHT
    )
    
    return fitness


async def run_agent_turn(
    agent: Agent,
    grid: Grid,
    turn: int,
    llm_client: LLMClient,
) -> TurnResult:
    """Execute a single agent's turn."""
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
        total_turns=TURNS_PER_GENERATION,
        recent_history=recent_history,
        goal=agent.personality.loose_goal,
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
    
    return TurnResult(
        turn=turn,
        agent_id=agent.id,
        x=decision.x,
        y=decision.y,
        color=decision.color,
        thinking=decision.thinking,
        overwrote=overwrote,
        valid=decision.valid and success,
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
    Run a complete generation of the simulation.
    
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
    
    # Calculate final fitness
    for agent in agents:
        fitness = evaluate_fitness(agent, grid)
        agent.add_fitness(fitness)
        result.agent_fitness[agent.id] = fitness
        result.agent_territory[agent.id] = grid.get_territory_count(agent.id)
    
    result.final_grid = grid.clone()
    
    return result


def get_generation_statistics(result: GenerationResult, agents: list[Agent]) -> dict:
    """Get statistics for a completed generation."""
    if not result.final_grid:
        return {}
    
    grid = result.final_grid
    
    # Calculate various statistics
    total_pixels = grid.width * grid.height
    filled_pixels = total_pixels - grid.get_empty_count()
    
    # Agent rankings by fitness
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
            }
            for agent in agents
        ],
        key=lambda x: x["fitness"],
        reverse=True,
    )
    
    # Add ranks
    for i, ranking in enumerate(agent_rankings, 1):
        ranking["rank"] = i
    
    return {
        "generation": result.generation,
        "total_turns": len(result.turns),
        "total_pixels": total_pixels,
        "filled_pixels": filled_pixels,
        "fill_rate": filled_pixels / total_pixels if total_pixels > 0 else 0,
        "agent_rankings": agent_rankings,
        "territory_by_agent": result.agent_territory,
    }
