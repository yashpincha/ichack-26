"""Evolutionary algorithms: selection, crossover, and mutation."""

from __future__ import annotations

import random
import uuid
from typing import Optional

from src.agent import Agent, AgentDNA
from src.config import (
    MUTATION_RATE,
    MUTATION_SIGMA,
    SURVIVORS_PER_GENERATION,
    BLENDING_PROBABILITY,
    GENE_MIN,
    GENE_MAX,
    STRATEGY_KEYWORD_POOL,
    REASONING_DEPTH_OPTIONS,
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
    Create a child agent by mixing parent genes.
    
    Uses uniform crossover with occasional gene blending for numeric values.
    
    Args:
        parent1: First parent agent
        parent2: Second parent agent
    
    Returns:
        New child agent
    """
    genes1 = parent1.dna.to_dict()
    genes2 = parent2.dna.to_dict()
    child_genes = {}
    
    for gene in genes1:
        # Randomly choose from either parent
        if random.random() < 0.5:
            value = genes1[gene]
        else:
            value = genes2[gene]
        
        # Occasionally blend numeric genes
        if isinstance(value, float) and random.random() < BLENDING_PROBABILITY:
            avg = (genes1[gene] + genes2[gene]) / 2
            # Add small noise to blended value
            noise = random.gauss(0, 0.05)
            value = max(GENE_MIN, min(GENE_MAX, avg + noise))
        
        # Handle list types (strategy_keywords)
        if isinstance(value, list):
            # Combine keywords from both parents, take a random subset
            combined = list(set(genes1[gene] + genes2[gene]))
            num_keywords = random.randint(1, min(4, len(combined)))
            value = random.sample(combined, num_keywords)
        
        child_genes[gene] = value
    
    return Agent(
        id=f"agent_{uuid.uuid4().hex[:8]}",
        generation=max(parent1.generation, parent2.generation) + 1,
        dna=AgentDNA.from_dict(child_genes),
        parent_ids=[parent1.id, parent2.id],
    )


def mutate(agent: Agent, rate: float = MUTATION_RATE) -> Agent:
    """
    Randomly mutate agent genes.
    
    Args:
        agent: Agent to mutate (modified in place)
        rate: Probability of mutating each gene
    
    Returns:
        The mutated agent (same object)
    """
    genes = agent.dna.to_dict()
    
    for gene, value in genes.items():
        if random.random() >= rate:
            continue
        
        if isinstance(value, float):
            # Gaussian mutation, clamped to [0, 1]
            new_val = value + random.gauss(0, MUTATION_SIGMA)
            genes[gene] = max(GENE_MIN, min(GENE_MAX, new_val))
        
        elif isinstance(value, list):
            # Mutate keyword list
            if random.random() < 0.5 and len(value) > 1:
                # Remove a random keyword
                value = value.copy()
                value.pop(random.randint(0, len(value) - 1))
            else:
                # Add a random keyword
                value = value.copy()
                new_keyword = random.choice(STRATEGY_KEYWORD_POOL)
                if new_keyword not in value:
                    value.append(new_keyword)
            genes[gene] = value
        
        elif gene == "reasoning_depth":
            # Mutate reasoning depth
            genes[gene] = random.choice(REASONING_DEPTH_OPTIONS)
    
    # Update agent's DNA
    agent.dna = AgentDNA.from_dict(genes)
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
        # Select two parents (can be the same in small populations)
        parent1, parent2 = random.sample(survivors, min(2, len(survivors)))
        
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


def calculate_gene_statistics(agents: list[Agent]) -> dict:
    """
    Calculate statistics for each gene across the population.
    
    Returns dict with mean, std, min, max for numeric genes
    and frequency distribution for categorical genes.
    """
    import statistics
    
    stats = {}
    
    # Collect gene values
    gene_values: dict[str, list] = {}
    for agent in agents:
        for gene, value in agent.genes.items():
            if gene not in gene_values:
                gene_values[gene] = []
            gene_values[gene].append(value)
    
    for gene, values in gene_values.items():
        if not values:
            continue
        
        if isinstance(values[0], float):
            stats[gene] = {
                "type": "numeric",
                "mean": statistics.mean(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
            }
        elif isinstance(values[0], str):
            # Categorical (like reasoning_depth)
            from collections import Counter
            counts = Counter(values)
            stats[gene] = {
                "type": "categorical",
                "distribution": dict(counts),
                "mode": counts.most_common(1)[0][0] if counts else None,
            }
        elif isinstance(values[0], list):
            # List type (like strategy_keywords)
            all_keywords = []
            for v in values:
                all_keywords.extend(v)
            from collections import Counter
            counts = Counter(all_keywords)
            stats[gene] = {
                "type": "keywords",
                "frequency": dict(counts),
                "most_common": counts.most_common(5),
            }
    
    return stats


def analyze_lineage(agents: list[Agent]) -> dict:
    """
    Analyze the lineage/ancestry of agents.
    
    Returns information about parent-child relationships
    and how many agents descend from each original agent.
    """
    # Build family tree
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
