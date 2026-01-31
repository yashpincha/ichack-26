"""Live state management for real-time dashboard updates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from src.config import LIVE_STATE_FILE


@dataclass
class LiveState:
    """Current state of the simulation for live visualization."""
    
    status: str = "idle"  # idle, running, evolving, complete
    generation: int = 0
    turn: int = 0
    total_turns: int = 0
    
    # Grid state
    grid_width: int = 16
    grid_height: int = 16
    grid_pixels: list[list[dict]] = field(default_factory=list)
    
    # Agent leaderboard
    leaderboard: list[dict] = field(default_factory=list)
    
    # Recent turn results
    recent_turns: list[dict] = field(default_factory=list)
    
    # Statistics
    total_pixels_placed: int = 0
    fill_rate: float = 0.0
    
    @property
    def progress_percent(self) -> float:
        if self.total_turns == 0:
            return 0.0
        return (self.turn / self.total_turns) * 100
    
    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "generation": self.generation,
            "turn": self.turn,
            "total_turns": self.total_turns,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "grid_pixels": self.grid_pixels,
            "leaderboard": self.leaderboard,
            "recent_turns": self.recent_turns,
            "total_pixels_placed": self.total_pixels_placed,
            "fill_rate": self.fill_rate,
            "progress_percent": self.progress_percent,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LiveState":
        return cls(
            status=data.get("status", "idle"),
            generation=data.get("generation", 0),
            turn=data.get("turn", 0),
            total_turns=data.get("total_turns", 0),
            grid_width=data.get("grid_width", 16),
            grid_height=data.get("grid_height", 16),
            grid_pixels=data.get("grid_pixels", []),
            leaderboard=data.get("leaderboard", []),
            recent_turns=data.get("recent_turns", []),
            total_pixels_placed=data.get("total_pixels_placed", 0),
            fill_rate=data.get("fill_rate", 0.0),
        )


def read_live_state() -> Optional[LiveState]:
    """Read the current live state from file."""
    state_file = Path(LIVE_STATE_FILE)
    if not state_file.exists():
        return None
    
    try:
        with open(state_file) as f:
            data = json.load(f)
        return LiveState.from_dict(data)
    except (json.JSONDecodeError, IOError):
        return None


def write_live_state(state: LiveState) -> None:
    """Write the current live state to file."""
    state_file = Path(LIVE_STATE_FILE)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w") as f:
        json.dump(state.to_dict(), f)


def reset_live_state(generation: int, grid_width: int = 16, grid_height: int = 16) -> None:
    """Reset live state for a new generation."""
    state = LiveState(
        status="running",
        generation=generation,
        turn=0,
        total_turns=0,
        grid_width=grid_width,
        grid_height=grid_height,
        grid_pixels=[
            [{"color": "empty", "owner_id": None} for _ in range(grid_width)]
            for _ in range(grid_height)
        ],
    )
    write_live_state(state)


def update_live_state(
    generation: int,
    turn: int,
    total_turns: int,
    grid: Any,  # Grid object
    agents: list[Any],  # Agent objects
    recent_turns: list[dict],
    status: str = "running",
) -> None:
    """Update live state with current simulation state."""
    # Build grid pixels representation
    grid_pixels = []
    for y in range(grid.height):
        row = []
        for x in range(grid.width):
            pixel = grid.get_pixel(x, y)
            row.append({
                "color": pixel.color if pixel else "empty",
                "owner_id": pixel.owner_id if pixel else None,
            })
        grid_pixels.append(row)
    
    # Build leaderboard
    leaderboard = []
    for agent in sorted(agents, key=lambda a: grid.get_territory_count(a.id), reverse=True):
        leaderboard.append({
            "agent_id": agent.id,
            "color": agent.preferred_color,
            "territory": grid.get_territory_count(agent.id),
            "pixels_placed": agent.pixels_placed,
            "pixels_lost": agent.pixels_lost,
            "personality": agent.personality.get_short_description(),
            "goal": agent.personality.loose_goal,
        })
    
    # Calculate fill rate
    total_pixels = grid.width * grid.height
    filled = total_pixels - grid.get_empty_count()
    fill_rate = filled / total_pixels if total_pixels > 0 else 0.0
    
    state = LiveState(
        status=status,
        generation=generation,
        turn=turn,
        total_turns=total_turns,
        grid_width=grid.width,
        grid_height=grid.height,
        grid_pixels=grid_pixels,
        leaderboard=leaderboard,
        recent_turns=recent_turns[-20:],  # Keep last 20
        total_pixels_placed=len(grid.history),
        fill_rate=fill_rate,
    )
    
    write_live_state(state)


def mark_evolving(generation: int) -> None:
    """Mark that evolution is in progress."""
    state = read_live_state()
    if state:
        state.status = "evolving"
        write_live_state(state)


def mark_complete() -> None:
    """Mark simulation as complete."""
    state = read_live_state()
    if state:
        state.status = "complete"
        write_live_state(state)
