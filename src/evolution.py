"""Evolutionary algorithms for AI agent personalities in r/place simulation."""

from __future__ import annotations

import random
import uuid
import statistics
from typing import Optional
from collections import Counter

from src.agent import Agent, AgentPersonality
from src.grid import Grid, COLORS
from src.config import (
    MUTATION_RATE,
    MUTATION_SIGMA,
    SURVIVORS_PER_GENERATION,
    BLENDING_PROBABILITY,
    GENE_MIN,
    GENE_MAX,
    PERSONALITY_TRAITS,
)


def select(agents: list[Agent], k: int = SURVIVORS_PER_GENERATION) -> list[Agent]:
    """
    Select top k agents based on fitness (elitist selection).
    
    Args:
        agents: List of agents to select from
        k: Number of agents to select
    
    Returns:
        List of k fittest agents
    """
    return sorted(agents, key=lambda a: a.fitness, reverse=True)[:k]


def tournament_select(
    agents: list[Agent],
    k: int = SURVIVORS_PER_GENERATION,
    tournament_size: int = 3,
) -> list[Agent]:
    """
    Tournament selection: randomly pick tournament_size agents, keep the best.
    Repeat k times with replacement from winners.
    
    This adds randomness while still favoring fitness.
    """
    winners = []
    for _ in range(k):
        tournament = random.sample(agents, min(tournament_size, len(agents)))
        winner = max(tournament, key=lambda a: a.fitness)
        winners.append(winner)
    return winners


def crossover(parent1: Agent, parent2: Agent) -> Agent:
    """
    Create a child agent by mixing parent personalities.
    
    Uses uniform crossover with occasional trait blending.
    Also handles color preference inheritance.
    Shape assignment is inherited from a random parent (shapes are assigned at start).
    
    Args:
        parent1: First parent agent
        parent2: Second parent agent
    
    Returns:
        New child agent with mixed personality
    """
    traits1 = parent1.personality.to_dict()
    traits2 = parent2.personality.to_dict()
    child_traits = {}
    
    # Crossover numeric traits
    for trait in PERSONALITY_TRAITS:
        # Randomly choose from either parent
        if random.random() < 0.5:
            value = traits1[trait]
        else:
            value = traits2[trait]
        
        # Occasionally blend traits (average with noise)
        if random.random() < BLENDING_PROBABILITY:
            avg = (traits1[trait] + traits2[trait]) / 2
            # Add small noise to blended value
            noise = random.gauss(0, 0.05)
            value = max(GENE_MIN, min(GENE_MAX, avg + noise))
        
        child_traits[trait] = value
    
    # Inherit preferred color from one parent (with small chance of mutation)
    if random.random() < 0.9:
        # 90% inherit from a parent
        child_traits["preferred_color"] = random.choice([
            traits1["preferred_color"],
            traits2["preferred_color"],
        ])
    else:
        # 10% random new color
        child_traits["preferred_color"] = random.choice(COLORS)
    
    # Inherit shape from one parent (shapes are assigned positions, so inherit together)
    chosen_parent = random.choice([traits1, traits2])
    child_traits["assigned_shape"] = chosen_parent.get("assigned_shape", "heart")
    child_traits["shape_position"] = chosen_parent.get("shape_position", [0, 0])
    
    # No longer using loose_goal in shape battle mode
    child_traits["loose_goal"] = None
    
    return Agent(
        id=f"agent_{uuid.uuid4().hex[:8]}",
        generation=max(parent1.generation, parent2.generation) + 1,
        personality=AgentPersonality.from_dict(child_traits),
        parent_ids=[parent1.id, parent2.id],
    )


def mutate(agent: Agent, rate: float = MUTATION_RATE) -> Agent:
    """
    Randomly mutate agent personality traits.
    
    Note: Shape assignment (assigned_shape, shape_position) is NOT mutated
    since shapes are assigned at the start and define the agent's goal.
    
    Args:
        agent: Agent to mutate (modified in place)
        rate: Probability of mutating each trait
    
    Returns:
        The mutated agent (same object)
    """
    traits = agent.personality.to_dict()
    
    for trait in PERSONALITY_TRAITS:
        if random.random() >= rate:
            continue
        
        # Gaussian mutation, clamped to [0, 1]
        old_val = traits[trait]
        new_val = old_val + random.gauss(0, MUTATION_SIGMA)
        traits[trait] = max(GENE_MIN, min(GENE_MAX, new_val))
    
    # Small chance to mutate color
    if random.random() < rate * 0.5:  # Half rate for color
        traits["preferred_color"] = random.choice(COLORS)
    
    # Shape assignment (assigned_shape, shape_position) is NOT mutated
    # These define the agent's objective and should remain constant
    
    # Update agent's personality
    agent.personality = AgentPersonality.from_dict(traits)
    return agent


def reproduce(survivors: list[Agent], target_population: int) -> list[Agent]:
    """
    Create offspring from surviving agents.
    
    Args:
        survivors: List of surviving agents (parents)
        target_population: Total population size to achieve
    
    Returns:
        List of new offspring agents
    """
    num_offspring = target_population - len(survivors)
    offspring = []
    
    for _ in range(num_offspring):
        # Select two different parents if possible
        if len(survivors) >= 2:
            parent1, parent2 = random.sample(survivors, 2)
        else:
            parent1 = parent2 = survivors[0]
        
        # Create child through crossover
        child = crossover(parent1, parent2)
        
        # Apply mutation
        child = mutate(child)
        
        offspring.append(child)
    
    return offspring


def evolve_generation(
    agents: list[Agent],
    num_survivors: int = SURVIVORS_PER_GENERATION,
    use_tournament_selection: bool = False,
) -> tuple[list[Agent], list[Agent], list[Agent]]:
    """
    Perform one generation of evolution.
    
    Args:
        agents: Current population
        num_survivors: Number of agents to keep
        use_tournament_selection: Use tournament selection instead of elitist
    
    Returns:
        Tuple of (new_population, survivors, offspring)
    """
    # Selection
    if use_tournament_selection:
        survivors = tournament_select(agents, num_survivors)
    else:
        survivors = select(agents, num_survivors)
    
    # Reproduction
    target_population = len(agents)
    offspring = reproduce(survivors, target_population)
    
    # Reset fitness for surviving agents
    for agent in survivors:
        agent.reset_fitness()
    
    # New population is survivors + offspring
    new_population = survivors + offspring
    
    return new_population, survivors, offspring


def calculate_trait_statistics(agents: list[Agent]) -> dict:
    """
    Calculate statistics for each personality trait across the population.
    
    Returns dict with mean, std, min, max for each trait, plus color and shape distributions.
    """
    stats = {}
    
    # Collect trait values
    trait_values: dict[str, list[float]] = {trait: [] for trait in PERSONALITY_TRAITS}
    
    for agent in agents:
        traits = agent.personality.to_dict()
        for trait in PERSONALITY_TRAITS:
            trait_values[trait].append(traits[trait])
    
    for trait, values in trait_values.items():
        if not values:
            continue
        
        stats[trait] = {
            "mean": statistics.mean(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values),
        }
    
    # Track color distribution
    color_counts = Counter(a.preferred_color for a in agents)
    stats["color_distribution"] = dict(color_counts)
    
    # Track shape distribution
    shape_counts = Counter(a.assigned_shape for a in agents)
    stats["shape_distribution"] = dict(shape_counts)
    
    return stats


# Legacy alias
calculate_gene_statistics = calculate_trait_statistics


def get_trait_evolution_summary(agents: list[Agent]) -> dict:
    """
    Get a summary of how traits evolved (for display).
    
    Returns traits sorted by how much they changed from neutral (0.5).
    """
    stats = calculate_trait_statistics(agents)
    
    # Sort by distance from neutral (0.5)
    trait_distances = []
    for trait in PERSONALITY_TRAITS:
        if trait not in stats:
            continue
        data = stats[trait]
        mean = data["mean"]
        distance = abs(mean - 0.5)
        direction = "high" if mean > 0.5 else "low"
        trait_distances.append({
            "trait": trait,
            "mean": mean,
            "distance_from_neutral": distance,
            "direction": direction,
            "std": data["std"],
        })
    
    # Sort by distance (most evolved traits first)
    trait_distances.sort(key=lambda x: x["distance_from_neutral"], reverse=True)
    
    return {
        "traits": trait_distances,
        "most_evolved": trait_distances[0]["trait"] if trait_distances else None,
        "least_evolved": trait_distances[-1]["trait"] if trait_distances else None,
        "color_distribution": stats.get("color_distribution", {}),
    }


def analyze_survival(
    gen0_agents: list[Agent],
    final_agents: list[Agent],
) -> dict:
    """
    Analyze which traits survived evolution.
    
    Compare generation 0 traits to final generation traits.
    """
    gen0_stats = calculate_trait_statistics(gen0_agents)
    final_stats = calculate_trait_statistics(final_agents)
    
    changes = {}
    for trait in PERSONALITY_TRAITS:
        gen0_mean = gen0_stats.get(trait, {}).get("mean", 0.5)
        final_mean = final_stats.get(trait, {}).get("mean", 0.5)
        change = final_mean - gen0_mean
        
        changes[trait] = {
            "gen0_mean": gen0_mean,
            "final_mean": final_mean,
            "change": change,
            "direction": "increased" if change > 0.05 else "decreased" if change < -0.05 else "stable",
        }
    
    return changes


def analyze_lineage(agents: list[Agent]) -> dict:
    """
    Analyze the lineage/ancestry of agents.
    
    Returns information about parent-child relationships.
    """
    lineage = {
        "agents_by_generation": {},
        "parent_child_edges": [],
    }
    
    for agent in agents:
        gen = agent.generation
        if gen not in lineage["agents_by_generation"]:
            lineage["agents_by_generation"][gen] = []
        lineage["agents_by_generation"][gen].append(agent.id)
        
        for parent_id in agent.parent_ids:
            lineage["parent_child_edges"].append({
                "parent": parent_id,
                "child": agent.id,
            })
    
    return lineage
