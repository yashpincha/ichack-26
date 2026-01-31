"""Live state management for real-time tournament visualization."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from src.config import LOGS_DIR


LIVE_STATE_FILE = os.path.join(LOGS_DIR, "live_state.json")


@dataclass
class MatchSummary:
    """Summary of a completed match for live display."""
    agent1_id: str
    agent2_id: str
    agent1_score: int
    agent2_score: int
    agent1_cooperations: int
    agent1_defections: int
    agent2_cooperations: int
    agent2_defections: int
    winner_id: Optional[str]
    agent1_description: str = ""  # Personality description
    agent2_description: str = ""
    last_round_thinking: str = ""  # Last round's AI thinking (for display)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_match_result(cls, match_result) -> "MatchSummary":
        """Create summary from a MatchResult object."""
        a1_coop = sum(1 for r in match_result.rounds if r.agent1_move == "COOPERATE")
        a1_defect = sum(1 for r in match_result.rounds if r.agent1_move == "DEFECT")
        a2_coop = sum(1 for r in match_result.rounds if r.agent2_move == "COOPERATE")
        a2_defect = sum(1 for r in match_result.rounds if r.agent2_move == "DEFECT")
        
        # Get last round thinking if available
        last_thinking = ""
        if match_result.rounds:
            last_round = match_result.rounds[-1]
            if last_round.agent1_thinking:
                last_thinking = last_round.agent1_thinking[:200]
        
        return cls(
            agent1_id=match_result.agent1_id,
            agent2_id=match_result.agent2_id,
            agent1_score=match_result.agent1_total_score,
            agent2_score=match_result.agent2_total_score,
            agent1_cooperations=a1_coop,
            agent1_defections=a1_defect,
            agent2_cooperations=a2_coop,
            agent2_defections=a2_defect,
            winner_id=match_result.winner_id,
            agent1_description=getattr(match_result, 'agent1_description', ''),
            agent2_description=getattr(match_result, 'agent2_description', ''),
            last_round_thinking=last_thinking,
        )


@dataclass
class LeaderboardEntry:
    """Entry in the live leaderboard."""
    agent_id: str
    fitness: int
    matches_played: int
    cooperation_rate: float
    generation: int
    personality_description: str = ""  # Short personality summary
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_agent(cls, agent) -> "LeaderboardEntry":
        """Create entry from an Agent object."""
        return cls(
            agent_id=agent.id,
            fitness=agent.fitness,
            matches_played=agent.matches_played,
            cooperation_rate=agent.cooperation_rate,
            generation=agent.generation,
            personality_description=agent.personality.get_short_description(),
        )


@dataclass
class LiveState:
    """Complete live state for tournament visualization."""
    generation: int = 0
    match_number: int = 0
    total_matches: int = 28
    status: str = "idle"  # "idle", "running", "evolving", "complete"
    leaderboard: list[dict] = field(default_factory=list)
    recent_matches: list[dict] = field(default_factory=list)
    current_match: Optional[dict] = None
    
    # Aggregate stats
    total_cooperations: int = 0
    total_defections: int = 0
    mutual_cooperations: int = 0
    mutual_defections: int = 0
    
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "match_number": self.match_number,
            "total_matches": self.total_matches,
            "status": self.status,
            "leaderboard": self.leaderboard,
            "recent_matches": self.recent_matches,
            "current_match": self.current_match,
            "total_cooperations": self.total_cooperations,
            "total_defections": self.total_defections,
            "mutual_cooperations": self.mutual_cooperations,
            "mutual_defections": self.mutual_defections,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LiveState":
        return cls(
            generation=data.get("generation", 0),
            match_number=data.get("match_number", 0),
            total_matches=data.get("total_matches", 28),
            status=data.get("status", "idle"),
            leaderboard=data.get("leaderboard", []),
            recent_matches=data.get("recent_matches", []),
            current_match=data.get("current_match"),
            total_cooperations=data.get("total_cooperations", 0),
            total_defections=data.get("total_defections", 0),
            mutual_cooperations=data.get("mutual_cooperations", 0),
            mutual_defections=data.get("mutual_defections", 0),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
        )
    
    @property
    def cooperation_rate(self) -> float:
        """Calculate overall cooperation rate."""
        total = self.total_cooperations + self.total_defections
        if total == 0:
            return 0.0
        return self.total_cooperations / total
    
    @property
    def progress_percent(self) -> float:
        """Calculate tournament progress percentage."""
        if self.total_matches == 0:
            return 0.0
        return (self.match_number / self.total_matches) * 100


def update_live_state(
    generation: int,
    match_number: int,
    total_matches: int,
    agents: list,
    match_result: Optional[Any] = None,
    status: str = "running",
    current_match_agents: Optional[tuple] = None,
) -> LiveState:
    """
    Update the live state file with current tournament progress.
    
    Args:
        generation: Current generation number
        match_number: Current match number (1-indexed)
        total_matches: Total matches in tournament
        agents: List of Agent objects
        match_result: Optional MatchResult from just-completed match
        status: Current status ("running", "evolving", "complete")
        current_match_agents: Optional tuple of (agent1, agent2) currently playing
    
    Returns:
        Updated LiveState object
    """
    # Read existing state or create new
    state = read_live_state() or LiveState()
    
    # Update basic info
    state.generation = generation
    state.match_number = match_number
    state.total_matches = total_matches
    state.status = status
    state.last_updated = datetime.now().isoformat()
    
    # Update leaderboard from agents
    state.leaderboard = sorted(
        [LeaderboardEntry.from_agent(a).to_dict() for a in agents],
        key=lambda x: x["fitness"],
        reverse=True
    )
    
    # Update current match info
    if current_match_agents:
        state.current_match = {
            "agent1_id": current_match_agents[0].id,
            "agent2_id": current_match_agents[1].id,
        }
    else:
        state.current_match = None
    
    # Add completed match to recent matches
    if match_result:
        summary = MatchSummary.from_match_result(match_result)
        state.recent_matches.insert(0, summary.to_dict())
        state.recent_matches = state.recent_matches[:5]  # Keep last 5
        
        # Update aggregate stats
        for r in match_result.rounds:
            if r.agent1_move == "COOPERATE":
                state.total_cooperations += 1
            else:
                state.total_defections += 1
            if r.agent2_move == "COOPERATE":
                state.total_cooperations += 1
            else:
                state.total_defections += 1
            
            if r.agent1_move == "COOPERATE" and r.agent2_move == "COOPERATE":
                state.mutual_cooperations += 1
            elif r.agent1_move == "DEFECT" and r.agent2_move == "DEFECT":
                state.mutual_defections += 1
    
    # Write state to file
    write_live_state(state)
    
    return state


def reset_live_state(generation: int = 0) -> LiveState:
    """Reset live state for a new generation."""
    state = LiveState(
        generation=generation,
        match_number=0,
        total_matches=28,
        status="running",
        total_cooperations=0,
        total_defections=0,
        mutual_cooperations=0,
        mutual_defections=0,
    )
    write_live_state(state)
    return state


def write_live_state(state: LiveState) -> None:
    """Write live state to JSON file."""
    # Ensure logs directory exists
    Path(LOGS_DIR).mkdir(exist_ok=True)
    
    with open(LIVE_STATE_FILE, "w") as f:
        json.dump(state.to_dict(), f, indent=2)


def read_live_state() -> Optional[LiveState]:
    """Read live state from JSON file."""
    try:
        if not os.path.exists(LIVE_STATE_FILE):
            return None
        
        with open(LIVE_STATE_FILE, "r") as f:
            data = json.load(f)
        
        return LiveState.from_dict(data)
    except (json.JSONDecodeError, IOError):
        return None


def mark_complete() -> None:
    """Mark the evolution as complete."""
    state = read_live_state() or LiveState()
    state.status = "complete"
    state.last_updated = datetime.now().isoformat()
    write_live_state(state)


def mark_evolving(generation: int) -> None:
    """Mark that evolution is happening between generations."""
    state = read_live_state() or LiveState()
    state.generation = generation
    state.status = "evolving"
    state.last_updated = datetime.now().isoformat()
    write_live_state(state)
