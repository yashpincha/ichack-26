"""Unit tests for game module."""

import pytest
from src.game import (
    calculate_payoffs,
    build_history_for_agent,
    RoundResult,
    MatchResult,
)
from src.config import PAYOFF_MATRIX


class TestPayoffs:
    """Tests for payoff calculation."""
    
    def test_mutual_cooperation(self):
        """Both cooperate: (3, 3)."""
        p1, p2 = calculate_payoffs("COOPERATE", "COOPERATE")
        assert p1 == 3
        assert p2 == 3
    
    def test_mutual_defection(self):
        """Both defect: (1, 1)."""
        p1, p2 = calculate_payoffs("DEFECT", "DEFECT")
        assert p1 == 1
        assert p2 == 1
    
    def test_temptation(self):
        """P1 defects, P2 cooperates: (5, 0)."""
        p1, p2 = calculate_payoffs("DEFECT", "COOPERATE")
        assert p1 == 5
        assert p2 == 0
    
    def test_sucker(self):
        """P1 cooperates, P2 defects: (0, 5)."""
        p1, p2 = calculate_payoffs("COOPERATE", "DEFECT")
        assert p1 == 0
        assert p2 == 5
    
    def test_payoff_matrix_consistency(self):
        """Payoff matrix should be consistent."""
        assert PAYOFF_MATRIX["COOPERATE"]["COOPERATE"] == (3, 3)
        assert PAYOFF_MATRIX["DEFECT"]["DEFECT"] == (1, 1)
        assert PAYOFF_MATRIX["COOPERATE"]["DEFECT"] == (0, 5)
        assert PAYOFF_MATRIX["DEFECT"]["COOPERATE"] == (5, 0)


class TestRoundResult:
    """Tests for RoundResult class."""
    
    def test_round_result_creation(self):
        """Should create round result with all fields."""
        result = RoundResult(
            round_number=1,
            agent1_id="agent_a",
            agent2_id="agent_b",
            agent1_move="COOPERATE",
            agent2_move="DEFECT",
            agent1_score=0,
            agent2_score=5,
        )
        
        assert result.round_number == 1
        assert result.agent1_score == 0
        assert result.agent2_score == 5
    
    def test_round_result_to_dict(self):
        """Should serialize to dict."""
        result = RoundResult(
            round_number=3,
            agent1_id="a1",
            agent2_id="a2",
            agent1_move="DEFECT",
            agent2_move="DEFECT",
            agent1_score=1,
            agent2_score=1,
            agent1_message="I'll cooperate next",
            agent2_message=None,
        )
        
        d = result.to_dict()
        
        assert d["round"] == 3
        assert d["agent1_move"] == "DEFECT"
        assert d["agent1_message"] == "I'll cooperate next"
        assert d["agent2_message"] is None


class TestMatchResult:
    """Tests for MatchResult class."""
    
    def test_add_round(self):
        """Should accumulate scores correctly."""
        match = MatchResult(agent1_id="a1", agent2_id="a2")
        
        match.add_round(RoundResult(
            round_number=1,
            agent1_id="a1", agent2_id="a2",
            agent1_move="COOPERATE", agent2_move="COOPERATE",
            agent1_score=3, agent2_score=3,
        ))
        
        match.add_round(RoundResult(
            round_number=2,
            agent1_id="a1", agent2_id="a2",
            agent1_move="DEFECT", agent2_move="COOPERATE",
            agent1_score=5, agent2_score=0,
        ))
        
        assert match.agent1_total_score == 8
        assert match.agent2_total_score == 3
        assert len(match.rounds) == 2
    
    def test_winner_determination(self):
        """Should correctly determine winner."""
        match = MatchResult(agent1_id="a1", agent2_id="a2")
        match.agent1_total_score = 25
        match.agent2_total_score = 20
        
        assert match.winner_id == "a1"
        
        match.agent2_total_score = 30
        assert match.winner_id == "a2"
        
        match.agent1_total_score = 30
        assert match.winner_id is None  # Tie
    
    def test_to_dict(self):
        """Should serialize match to dict."""
        match = MatchResult(agent1_id="a1", agent2_id="a2")
        match.agent1_total_score = 15
        match.agent2_total_score = 20
        
        d = match.to_dict()
        
        assert d["agent1_id"] == "a1"
        assert d["agent1_total_score"] == 15
        assert d["winner_id"] == "a2"


class TestHistoryBuilding:
    """Tests for history building function."""
    
    def test_build_history_agent1_perspective(self):
        """History should be from agent's perspective."""
        rounds = [
            RoundResult(
                round_number=1,
                agent1_id="alice", agent2_id="bob",
                agent1_move="COOPERATE", agent2_move="DEFECT",
                agent1_score=0, agent2_score=5,
            ),
            RoundResult(
                round_number=2,
                agent1_id="alice", agent2_id="bob",
                agent1_move="DEFECT", agent2_move="DEFECT",
                agent1_score=1, agent2_score=1,
            ),
        ]
        
        history = build_history_for_agent(rounds, "alice", "bob")
        
        assert len(history) == 2
        assert history[0]["your_move"] == "COOPERATE"
        assert history[0]["their_move"] == "DEFECT"
        assert history[0]["your_score"] == 0
    
    def test_build_history_agent2_perspective(self):
        """History from agent2 perspective should flip moves."""
        rounds = [
            RoundResult(
                round_number=1,
                agent1_id="alice", agent2_id="bob",
                agent1_move="COOPERATE", agent2_move="DEFECT",
                agent1_score=0, agent2_score=5,
            ),
        ]
        
        history = build_history_for_agent(rounds, "bob", "alice")
        
        assert history[0]["your_move"] == "DEFECT"
        assert history[0]["their_move"] == "COOPERATE"
        assert history[0]["your_score"] == 5
    
    def test_empty_history(self):
        """Should handle empty rounds list."""
        history = build_history_for_agent([], "a1", "a2")
        assert history == []
