"""Unit tests for evolution module."""

import pytest
from src.agent import Agent, AgentPersonality, create_initial_population
from src.evolution import (
    select,
    tournament_select,
    crossover,
    mutate,
    reproduce,
    evolve_generation,
    calculate_trait_statistics,
)


class TestSelection:
    """Tests for selection functions."""
    
    def test_select_returns_top_k(self):
        """Select should return top k agents by fitness."""
        agents = create_initial_population(8)
        
        # Assign different fitness values
        for i, agent in enumerate(agents):
            agent.fitness = i * 10
        
        survivors = select(agents, k=4)
        
        assert len(survivors) == 4
        # Should be sorted by fitness descending
        fitnesses = [a.fitness for a in survivors]
        assert fitnesses == sorted(fitnesses, reverse=True)
        assert survivors[0].fitness == 70  # Highest
    
    def test_select_with_ties(self):
        """Select should handle ties gracefully."""
        agents = create_initial_population(4)
        for agent in agents:
            agent.fitness = 50
        
        survivors = select(agents, k=2)
        assert len(survivors) == 2
    
    def test_tournament_select(self):
        """Tournament selection should favor higher fitness."""
        agents = create_initial_population(8)
        for i, agent in enumerate(agents):
            agent.fitness = i * 10
        
        # Run multiple times to check statistical tendency
        high_fitness_wins = 0
        for _ in range(100):
            winners = tournament_select(agents, k=4, tournament_size=3)
            avg_fitness = sum(w.fitness for w in winners) / len(winners)
            if avg_fitness > 35:  # Above median
                high_fitness_wins += 1
        
        # Should favor higher fitness most of the time
        assert high_fitness_wins > 50


class TestCrossover:
    """Tests for crossover function."""
    
    def test_crossover_creates_child(self):
        """Crossover should create a new agent."""
        parent1 = Agent.create_random(generation=1)
        parent2 = Agent.create_random(generation=2)
        
        child = crossover(parent1, parent2)
        
        assert child.id != parent1.id
        assert child.id != parent2.id
        assert child.generation == 3  # max(1, 2) + 1
        assert parent1.id in child.parent_ids
        assert parent2.id in child.parent_ids
    
    def test_crossover_inherits_traits(self):
        """Child traits should come from parents."""
        parent1 = Agent.create_random(generation=0)
        parent2 = Agent.create_random(generation=0)
        
        # Set distinct values
        parent1.personality.trust = 0.0
        parent2.personality.trust = 1.0
        
        children = [crossover(parent1, parent2) for _ in range(50)]
        
        # Child values should be between parent values (with some noise)
        for child in children:
            assert 0.0 <= child.personality.trust <= 1.0


class TestMutation:
    """Tests for mutation function."""
    
    def test_mutate_modifies_traits(self):
        """Mutation should modify some traits."""
        agent = Agent.create_random(generation=0)
        original_traits = agent.personality.to_dict()
        
        # High mutation rate to ensure changes
        mutate(agent, rate=1.0)
        
        mutated_traits = agent.personality.to_dict()
        
        # At least some traits should change
        changes = 0
        for trait in ["trust", "forgiveness", "vengefulness"]:
            if abs(original_traits[trait] - mutated_traits[trait]) > 0.01:
                changes += 1
        
        assert changes > 0
    
    def test_mutate_respects_bounds(self):
        """Mutated values should stay in [0, 1]."""
        for _ in range(50):
            agent = Agent.create_random(generation=0)
            mutate(agent, rate=1.0)
            
            assert 0.0 <= agent.personality.trust <= 1.0
            assert 0.0 <= agent.personality.forgiveness <= 1.0
            assert 0.0 <= agent.personality.vengefulness <= 1.0
    
    def test_low_mutation_rate(self):
        """Low mutation rate should preserve most traits."""
        agent = Agent.create_random(generation=0)
        original = agent.personality.to_dict()
        
        mutate(agent, rate=0.0)  # No mutation
        mutated = agent.personality.to_dict()
        
        # All traits should be unchanged
        for trait in ["trust", "forgiveness"]:
            assert original[trait] == mutated[trait]


class TestReproduce:
    """Tests for reproduction function."""
    
    def test_reproduce_creates_correct_number(self):
        """Reproduce should create correct number of offspring."""
        survivors = create_initial_population(4)
        offspring = reproduce(survivors, target_population=8)
        
        assert len(offspring) == 4
    
    def test_reproduce_offspring_have_parents(self):
        """All offspring should have parent references."""
        survivors = create_initial_population(4)
        offspring = reproduce(survivors, target_population=8)
        
        survivor_ids = {a.id for a in survivors}
        
        for child in offspring:
            assert len(child.parent_ids) == 2
            for parent_id in child.parent_ids:
                assert parent_id in survivor_ids


class TestEvolveGeneration:
    """Tests for full generation evolution."""
    
    def test_evolve_maintains_population_size(self):
        """Evolution should maintain population size."""
        agents = create_initial_population(8)
        for i, agent in enumerate(agents):
            agent.fitness = i * 10
        
        new_pop, survivors, offspring = evolve_generation(agents, num_survivors=4)
        
        assert len(new_pop) == 8
        assert len(survivors) == 4
        assert len(offspring) == 4
    
    def test_evolve_resets_survivor_fitness(self):
        """Surviving agents should have fitness reset."""
        agents = create_initial_population(8)
        for agent in agents:
            agent.fitness = 100
        
        _, survivors, _ = evolve_generation(agents)
        
        for survivor in survivors:
            assert survivor.fitness == 0
    
    def test_evolve_preserves_best(self):
        """Best agents should survive."""
        agents = create_initial_population(8)
        for i, agent in enumerate(agents):
            agent.fitness = i * 10
        
        best_agent = agents[-1]  # Highest fitness
        
        _, survivors, _ = evolve_generation(agents, num_survivors=4)
        
        survivor_ids = {a.id for a in survivors}
        assert best_agent.id in survivor_ids


class TestTraitStatistics:
    """Tests for trait statistics calculation."""
    
    def test_calculate_trait_statistics(self):
        """Should calculate correct statistics."""
        agents = create_initial_population(4)
        
        # Set known values
        for i, agent in enumerate(agents):
            agent.personality.trust = 0.25 * i  # 0.0, 0.25, 0.5, 0.75
        
        stats = calculate_trait_statistics(agents)
        
        assert "trust" in stats
        assert abs(stats["trust"]["mean"] - 0.375) < 0.01
        assert stats["trust"]["min"] == 0.0
        assert stats["trust"]["max"] == 0.75


class TestAgentPersonality:
    """Tests for AgentPersonality class."""
    
    def test_personality_to_dict(self):
        """Personality should serialize to dict."""
        personality = AgentPersonality.random()
        d = personality.to_dict()
        
        assert "trust" in d
        assert "forgiveness" in d
        assert isinstance(d["trust"], float)
    
    def test_personality_from_dict(self):
        """Personality should deserialize from dict."""
        original = AgentPersonality.random()
        d = original.to_dict()
        restored = AgentPersonality.from_dict(d)
        
        assert restored.trust == original.trust
        assert restored.forgiveness == original.forgiveness
    
    def test_random_personality_is_valid(self):
        """Random personality should have valid values."""
        for _ in range(20):
            personality = AgentPersonality.random()
            
            assert 0.0 <= personality.trust <= 1.0
            assert 0.0 <= personality.forgiveness <= 1.0
            assert 0.0 <= personality.vengefulness <= 1.0
    
    def test_short_description(self):
        """Should generate short description."""
        personality = AgentPersonality(trust=0.9, honesty=0.1)
        desc = personality.get_short_description()
        
        assert isinstance(desc, str)
        assert len(desc) > 0


class TestAgent:
    """Tests for Agent class."""
    
    def test_create_random(self):
        """Should create random agent."""
        agent = Agent.create_random(generation=5)
        
        assert agent.id.startswith("agent_")
        assert agent.generation == 5
        assert agent.fitness == 0
    
    def test_create_baseline(self):
        """Should create baseline agent."""
        baseline = Agent.create_baseline()
        
        assert baseline.id == "baseline_agent"
        assert baseline.generation == -1
        assert baseline.personality.trust == 0.5
    
    def test_record_move(self):
        """Should track moves correctly."""
        agent = Agent.create_random()
        
        agent.record_move("COOPERATE")
        agent.record_move("COOPERATE")
        agent.record_move("DEFECT")
        
        assert agent.total_cooperations == 2
        assert agent.total_defections == 1
        assert agent.cooperation_rate == 2/3
    
    def test_clone(self):
        """Clone should create deep copy."""
        original = Agent.create_random()
        original.fitness = 100
        original.record_move("COOPERATE")
        
        clone = original.clone()
        
        assert clone.id == original.id
        assert clone.fitness == original.fitness
        
        # Modify clone, original unchanged
        clone.fitness = 0
        assert original.fitness == 100
    
    def test_serialization(self):
        """Agent should serialize and deserialize."""
        original = Agent.create_random(generation=3)
        original.fitness = 42
        original.record_move("DEFECT")
        
        d = original.to_dict()
        restored = Agent.from_dict(d)
        
        assert restored.id == original.id
        assert restored.fitness == original.fitness
        assert restored.total_defections == original.total_defections
