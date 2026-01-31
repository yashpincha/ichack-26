"""Round-robin tournament orchestration."""

from __future__ import annotations

import asyncio
import itertools
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable

from src.agent import Agent
from src.game import play_match, MatchResult
from src.llm import LLMClient, get_llm_client


@dataclass
class TournamentResult:
    """Result of a complete tournament (all matchups in one generation)."""
    generation: int
    matches: list[MatchResult] = field(default_factory=list)
    agent_rankings: list[dict] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """Get tournament duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "generation": self.generation,
            "num_matches": len(self.matches),
            "duration_seconds": self.duration_seconds,
            "agent_rankings": self.agent_rankings,
            "matches": [m.to_dict() for m in self.matches],
        }


def calculate_rankings(agents: list[Agent]) -> list[dict]:
    """Calculate agent rankings based on fitness."""
    sorted_agents = sorted(agents, key=lambda a: a.fitness, reverse=True)
    rankings = []
    for rank, agent in enumerate(sorted_agents, 1):
        rankings.append({
            "rank": rank,
            "agent_id": agent.id,
            "generation": agent.generation,
            "fitness": agent.fitness,
            "avg_fitness": agent.avg_fitness_per_match,
            "cooperation_rate": agent.cooperation_rate,
            "matches_played": agent.matches_played,
        })
    return rankings


async def run_tournament(
    agents: list[Agent],
    generation: int,
    llm_client: Optional[LLMClient] = None,
    on_match_complete: Optional[Callable[[MatchResult, int, int], None]] = None,
    max_concurrent: int = 4,
) -> TournamentResult:
    """
    Run a round-robin tournament between all agents.
    
    Args:
        agents: List of agents to compete
        generation: Current generation number
        llm_client: LLM client for agent decisions
        on_match_complete: Callback after each match (match_result, completed, total)
        max_concurrent: Maximum concurrent matchups
    
    Returns:
        TournamentResult with all match data
    """
    if llm_client is None:
        llm_client = get_llm_client()
    
    result = TournamentResult(
        generation=generation,
        start_time=datetime.now(),
    )
    
    # Generate all matchups (combinations of 2)
    matchups = list(itertools.combinations(agents, 2))
    total_matchups = len(matchups)
    
    # Use semaphore to limit concurrency
    semaphore = asyncio.Semaphore(max_concurrent)
    completed = 0
    
    async def run_match_with_semaphore(agent1: Agent, agent2: Agent) -> MatchResult:
        nonlocal completed
        async with semaphore:
            match_result = await play_match(agent1, agent2, llm_client=llm_client)
            completed += 1
            if on_match_complete:
                on_match_complete(match_result, completed, total_matchups)
            return match_result
    
    # Run all matches with limited concurrency
    tasks = [run_match_with_semaphore(a1, a2) for a1, a2 in matchups]
    match_results = await asyncio.gather(*tasks)
    
    result.matches = list(match_results)
    result.end_time = datetime.now()
    result.agent_rankings = calculate_rankings(agents)
    
    return result


async def run_tournament_sequential(
    agents: list[Agent],
    generation: int,
    llm_client: Optional[LLMClient] = None,
    on_match_complete: Optional[Callable[[MatchResult, int, int], None]] = None,
) -> TournamentResult:
    """
    Run a round-robin tournament sequentially (for debugging/visualization).
    """
    if llm_client is None:
        llm_client = get_llm_client()
    
    result = TournamentResult(
        generation=generation,
        start_time=datetime.now(),
    )
    
    matchups = list(itertools.combinations(agents, 2))
    total_matchups = len(matchups)
    
    for i, (agent1, agent2) in enumerate(matchups):
        match_result = await play_match(agent1, agent2, llm_client=llm_client)
        result.matches.append(match_result)
        
        if on_match_complete:
            on_match_complete(match_result, i + 1, total_matchups)
    
    result.end_time = datetime.now()
    result.agent_rankings = calculate_rankings(agents)
    
    return result


def get_tournament_statistics(result: TournamentResult) -> dict:
    """Calculate aggregate statistics for a tournament."""
    if not result.matches:
        return {}
    
    total_cooperations = 0
    total_defections = 0
    mutual_cooperations = 0
    mutual_defections = 0
    exploitations = 0  # One cooperates, one defects
    
    for match in result.matches:
        for round_result in match.rounds:
            move1, move2 = round_result.agent1_move, round_result.agent2_move
            
            if move1 == "COOPERATE":
                total_cooperations += 1
            else:
                total_defections += 1
            
            if move2 == "COOPERATE":
                total_cooperations += 1
            else:
                total_defections += 1
            
            if move1 == "COOPERATE" and move2 == "COOPERATE":
                mutual_cooperations += 1
            elif move1 == "DEFECT" and move2 == "DEFECT":
                mutual_defections += 1
            else:
                exploitations += 1
    
    total_moves = total_cooperations + total_defections
    total_rounds = sum(len(m.rounds) for m in result.matches)
    
    return {
        "total_rounds": total_rounds,
        "cooperation_rate": total_cooperations / total_moves if total_moves > 0 else 0,
        "mutual_cooperation_rate": mutual_cooperations / total_rounds if total_rounds > 0 else 0,
        "mutual_defection_rate": mutual_defections / total_rounds if total_rounds > 0 else 0,
        "exploitation_rate": exploitations / total_rounds if total_rounds > 0 else 0,
        "avg_score_per_round": sum(m.agent1_total_score + m.agent2_total_score for m in result.matches) / (2 * total_rounds) if total_rounds > 0 else 0,
    }
