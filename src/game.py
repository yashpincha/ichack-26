"""Prisoner's Dilemma game logic for single matchups."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.agent import Agent
from src.config import PAYOFF_MATRIX, ROUNDS_PER_MATCH
from src.llm import get_agent_decision, LLMClient, LLMResponse


@dataclass
class RoundResult:
    """Result of a single round."""
    round_number: int
    agent1_id: str
    agent2_id: str
    agent1_move: str
    agent2_move: str
    agent1_score: int
    agent2_score: int
    agent1_message: Optional[str] = None
    agent2_message: Optional[str] = None
    agent1_reasoning: str = ""
    agent2_reasoning: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "round": self.round_number,
            "agent1_id": self.agent1_id,
            "agent2_id": self.agent2_id,
            "agent1_move": self.agent1_move,
            "agent2_move": self.agent2_move,
            "agent1_score": self.agent1_score,
            "agent2_score": self.agent2_score,
            "agent1_message": self.agent1_message,
            "agent2_message": self.agent2_message,
            "agent1_reasoning": self.agent1_reasoning,
            "agent2_reasoning": self.agent2_reasoning,
        }


@dataclass
class MatchResult:
    """Result of a complete match (10 rounds)."""
    agent1_id: str
    agent2_id: str
    rounds: list[RoundResult] = field(default_factory=list)
    agent1_total_score: int = 0
    agent2_total_score: int = 0
    
    def add_round(self, round_result: RoundResult) -> None:
        """Add a round result and update totals."""
        self.rounds.append(round_result)
        self.agent1_total_score += round_result.agent1_score
        self.agent2_total_score += round_result.agent2_score
    
    @property
    def winner_id(self) -> Optional[str]:
        """Get the ID of the winning agent, or None for a tie."""
        if self.agent1_total_score > self.agent2_total_score:
            return self.agent1_id
        elif self.agent2_total_score > self.agent1_total_score:
            return self.agent2_id
        return None  # Tie
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "agent1_id": self.agent1_id,
            "agent2_id": self.agent2_id,
            "agent1_total_score": self.agent1_total_score,
            "agent2_total_score": self.agent2_total_score,
            "winner_id": self.winner_id,
            "rounds": [r.to_dict() for r in self.rounds],
        }


def calculate_payoffs(move1: str, move2: str) -> tuple[int, int]:
    """Calculate payoffs for both players given their moves."""
    player1_score, _ = PAYOFF_MATRIX[move1][move2]
    _, player2_score = PAYOFF_MATRIX[move2][move1]
    return player1_score, player2_score


def build_history_for_agent(
    rounds: list[RoundResult],
    agent_id: str,
    opponent_id: str,
) -> list[dict]:
    """Build round history from perspective of a specific agent."""
    history = []
    for r in rounds:
        if r.agent1_id == agent_id:
            history.append({
                "round": r.round_number,
                "your_move": r.agent1_move,
                "their_move": r.agent2_move,
                "your_score": r.agent1_score,
            })
        else:
            history.append({
                "round": r.round_number,
                "your_move": r.agent2_move,
                "their_move": r.agent1_move,
                "your_score": r.agent2_score,
            })
    return history


async def play_round(
    agent1: Agent,
    agent2: Agent,
    round_number: int,
    previous_rounds: list[RoundResult],
    agent1_last_message: Optional[str] = None,
    agent2_last_message: Optional[str] = None,
    llm_client: Optional[LLMClient] = None,
) -> RoundResult:
    """Play a single round between two agents."""
    import asyncio
    
    # Build history from each agent's perspective
    history1 = build_history_for_agent(previous_rounds, agent1.id, agent2.id)
    history2 = build_history_for_agent(previous_rounds, agent2.id, agent1.id)
    
    # Get both decisions in parallel
    response1_task = get_agent_decision(
        agent_id=agent1.id,
        agent_genes=agent1.genes,
        opponent_id=agent2.id,
        round_history=history1,
        current_round=round_number,
        opponent_message=agent2_last_message,
        client=llm_client,
    )
    
    response2_task = get_agent_decision(
        agent_id=agent2.id,
        agent_genes=agent2.genes,
        opponent_id=agent1.id,
        round_history=history2,
        current_round=round_number,
        opponent_message=agent1_last_message,
        client=llm_client,
    )
    
    response1, response2 = await asyncio.gather(response1_task, response2_task)
    
    # Calculate payoffs
    score1, score2 = calculate_payoffs(response1.decision, response2.decision)
    
    # Record moves for agent statistics
    agent1.record_move(response1.decision)
    agent2.record_move(response2.decision)
    
    return RoundResult(
        round_number=round_number,
        agent1_id=agent1.id,
        agent2_id=agent2.id,
        agent1_move=response1.decision,
        agent2_move=response2.decision,
        agent1_score=score1,
        agent2_score=score2,
        agent1_message=response1.message,
        agent2_message=response2.message,
        agent1_reasoning=response1.reasoning,
        agent2_reasoning=response2.reasoning,
    )


async def play_match(
    agent1: Agent,
    agent2: Agent,
    num_rounds: int = ROUNDS_PER_MATCH,
    llm_client: Optional[LLMClient] = None,
) -> MatchResult:
    """Play a complete match between two agents."""
    result = MatchResult(agent1_id=agent1.id, agent2_id=agent2.id)
    
    agent1_message: Optional[str] = None
    agent2_message: Optional[str] = None
    
    for round_num in range(1, num_rounds + 1):
        round_result = await play_round(
            agent1=agent1,
            agent2=agent2,
            round_number=round_num,
            previous_rounds=result.rounds,
            agent1_last_message=agent1_message,
            agent2_last_message=agent2_message,
            llm_client=llm_client,
        )
        
        result.add_round(round_result)
        
        # Update messages for next round
        agent1_message = round_result.agent1_message
        agent2_message = round_result.agent2_message
    
    # Update agent fitness and match count
    agent1.add_fitness(result.agent1_total_score)
    agent2.add_fitness(result.agent2_total_score)
    agent1.increment_matches()
    agent2.increment_matches()
    
    return result


async def play_match_with_callback(
    agent1: Agent,
    agent2: Agent,
    num_rounds: int = ROUNDS_PER_MATCH,
    llm_client: Optional[LLMClient] = None,
    on_round_complete: Optional[callable] = None,
) -> MatchResult:
    """Play a match with optional callback after each round (for live visualization)."""
    result = MatchResult(agent1_id=agent1.id, agent2_id=agent2.id)
    
    agent1_message: Optional[str] = None
    agent2_message: Optional[str] = None
    
    for round_num in range(1, num_rounds + 1):
        round_result = await play_round(
            agent1=agent1,
            agent2=agent2,
            round_number=round_num,
            previous_rounds=result.rounds,
            agent1_last_message=agent1_message,
            agent2_last_message=agent2_message,
            llm_client=llm_client,
        )
        
        result.add_round(round_result)
        
        # Call callback if provided
        if on_round_complete:
            on_round_complete(round_result, result)
        
        # Update messages for next round
        agent1_message = round_result.agent1_message
        agent2_message = round_result.agent2_message
    
    # Update agent fitness and match count
    agent1.add_fitness(result.agent1_total_score)
    agent2.add_fitness(result.agent2_total_score)
    agent1.increment_matches()
    agent2.increment_matches()
    
    return result
