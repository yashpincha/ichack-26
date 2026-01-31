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
class RoundInteraction:
    """A single round interaction for the interactions feed."""
    match_id: str
    round_num: int
    agent1_id: str
    agent2_id: str
    agent1_description: str
    agent2_description: str
    agent1_thinking: str
    agent2_thinking: str
    agent1_message: Optional[str]
    agent2_message: Optional[str]
    agent1_action: str
    agent2_action: str
    agent1_score: int
    agent2_score: int
    agent1_lied: bool
    agent2_lied: bool
    outcome: str  # "mutual_cooperation", "mutual_defection", "agent1_exploited", "agent2_exploited"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_round_result(cls, round_result, match_id: str, a1_desc: str, a2_desc: str) -> "RoundInteraction":
        """Create from a RoundResult object."""
        return cls(
            match_id=match_id,
            round_num=round_result.round_number,
            agent1_id=round_result.agent1_id,
            agent2_id=round_result.agent2_id,
            agent1_description=a1_desc,
            agent2_description=a2_desc,
            agent1_thinking=round_result.agent1_thinking[:300] if round_result.agent1_thinking else "",
            agent2_thinking=round_result.agent2_thinking[:300] if round_result.agent2_thinking else "",
            agent1_message=round_result.agent1_message,
            agent2_message=round_result.agent2_message,
            agent1_action=round_result.agent1_move,
            agent2_action=round_result.agent2_move,
            agent1_score=round_result.agent1_score,
            agent2_score=round_result.agent2_score,
            agent1_lied=round_result.agent1_lied,
            agent2_lied=round_result.agent2_lied,
            outcome=round_result.outcome,
        )


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
    agent1_description: str = ""
    agent2_description: str = ""
    agent1_lies: int = 0
    agent2_lies: int = 0
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
        a1_lies = sum(1 for r in match_result.rounds if r.agent1_lied)
        a2_lies = sum(1 for r in match_result.rounds if r.agent2_lied)
        
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
            agent1_lies=a1_lies,
            agent2_lies=a2_lies,
        )


@dataclass
class LeaderboardEntry:
    """Entry in the live leaderboard."""
    agent_id: str
    fitness: int
    matches_played: int
    cooperation_rate: float
    generation: int
    personality_description: str = ""
    lies_told: int = 0
    
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
            lies_told=agent.lies_told,
        )


@dataclass
class LiveState:
    """Complete live state for tournament visualization."""
    generation: int = 0
    match_number: int = 0
    total_matches: int = 3  # 3 agents = 3 matches per generation
    status: str = "idle"
    leaderboard: list[dict] = field(default_factory=list)
    recent_matches: list[dict] = field(default_factory=list)
    recent_rounds: list[dict] = field(default_factory=list)  # NEW: Full round interactions
    current_match: Optional[dict] = None
    
    # Aggregate stats
    total_cooperations: int = 0
    total_defections: int = 0
    mutual_cooperations: int = 0
    mutual_defections: int = 0
    total_lies: int = 0
    
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "generation": self.generation,
            "match_number": self.match_number,
            "total_matches": self.total_matches,
            "status": self.status,
            "leaderboard": self.leaderboard,
            "recent_matches": self.recent_matches,
            "recent_rounds": self.recent_rounds,
            "current_match": self.current_match,
            "total_cooperations": self.total_cooperations,
            "total_defections": self.total_defections,
            "mutual_cooperations": self.mutual_cooperations,
            "mutual_defections": self.mutual_defections,
            "total_lies": self.total_lies,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LiveState":
        return cls(
            generation=data.get("generation", 0),
            match_number=data.get("match_number", 0),
            total_matches=data.get("total_matches", 3),
            status=data.get("status", "idle"),
            leaderboard=data.get("leaderboard", []),
            recent_matches=data.get("recent_matches", []),
            recent_rounds=data.get("recent_rounds", []),
            current_match=data.get("current_match"),
            total_cooperations=data.get("total_cooperations", 0),
            total_defections=data.get("total_defections", 0),
            mutual_cooperations=data.get("mutual_cooperations", 0),
            mutual_defections=data.get("mutual_defections", 0),
            total_lies=data.get("total_lies", 0),
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


def add_round_interaction(round_result, match_id: str, a1_desc: str, a2_desc: str) -> None:
    """Add a round interaction to the live state."""
    state = read_live_state() or LiveState()
    
    interaction = RoundInteraction.from_round_result(round_result, match_id, a1_desc, a2_desc)
    state.recent_rounds.insert(0, interaction.to_dict())
    state.recent_rounds = state.recent_rounds[:20]  # Keep last 20 rounds
    
    # Update lie counter
    if round_result.agent1_lied:
        state.total_lies += 1
    if round_result.agent2_lied:
        state.total_lies += 1
    
    state.last_updated = datetime.now().isoformat()
    write_live_state(state)


def update_live_state(
    generation: int,
    match_number: int,
    total_matches: int,
    agents: list,
    match_result: Optional[Any] = None,
    status: str = "running",
    current_match_agents: Optional[tuple] = None,
) -> LiveState:
    """Update the live state file with current tournament progress."""
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
            "agent1_description": current_match_agents[0].personality.get_short_description(),
            "agent2_description": current_match_agents[1].personality.get_short_description(),
        }
    else:
        state.current_match = None
    
    # Add completed match to recent matches
    if match_result:
        summary = MatchSummary.from_match_result(match_result)
        state.recent_matches.insert(0, summary.to_dict())
        state.recent_matches = state.recent_matches[:5]
        
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
    
    write_live_state(state)
    return state


def reset_live_state(generation: int = 0, num_agents: int = 3) -> LiveState:
    """Reset live state for a new generation."""
    # Calculate total matches for n agents (round-robin)
    total_matches = (num_agents * (num_agents - 1)) // 2
    
    state = LiveState(
        generation=generation,
        match_number=0,
        total_matches=total_matches,
        status="running",
        total_cooperations=0,
        total_defections=0,
        mutual_cooperations=0,
        mutual_defections=0,
        total_lies=0,
        recent_rounds=[],
    )
    write_live_state(state)
    return state


def write_live_state(state: LiveState) -> None:
    """Write live state to JSON file."""
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
