"""Main entry point for DarwinLM - Evolutionary Prisoner's Dilemma Tournament."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import print as rprint

from src.agent import Agent, create_initial_population
from src.tournament import run_tournament, TournamentResult, get_tournament_statistics
from src.evolution import evolve_generation, calculate_trait_statistics
from src.llm import LLMClient
from src.config import NUM_AGENTS, NUM_GENERATIONS, LOGS_DIR
from src.live_state import (
    update_live_state, reset_live_state, mark_complete, mark_evolving,
    MatchSummary
)

console = Console()


def save_generation_log(
    generation: int,
    agents: list[Agent],
    tournament_result: TournamentResult,
    survivors: list[Agent],
    offspring: list[Agent],
    log_dir: str = LOGS_DIR,
) -> str:
    """Save generation data to JSON log file."""
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    filename = f"generation_{generation:03d}.json"
    filepath = log_path / filename
    
    data = {
        "generation": generation,
        "timestamp": timestamp,
        "agents": [a.to_dict() for a in agents],
        "tournament": tournament_result.to_dict(),
        "statistics": get_tournament_statistics(tournament_result),
        "gene_statistics": calculate_trait_statistics(agents),
        "survivors": [a.id for a in survivors],
        "offspring": [a.id for a in offspring],
    }
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    return str(filepath)


def display_generation_summary(
    generation: int,
    agents: list[Agent],
    tournament_result: TournamentResult,
) -> None:
    """Display a rich summary of the generation results."""
    # Create rankings table
    table = Table(title=f"Generation {generation} Results", show_header=True)
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Agent ID", style="magenta")
    table.add_column("Fitness", style="green", justify="right")
    table.add_column("Avg/Match", style="yellow", justify="right")
    table.add_column("Coop Rate", style="blue", justify="right")
    table.add_column("Gen", justify="right")
    
    for ranking in tournament_result.agent_rankings:
        table.add_row(
            str(ranking["rank"]),
            ranking["agent_id"][:12],
            str(ranking["fitness"]),
            f"{ranking['avg_fitness']:.1f}",
            f"{ranking['cooperation_rate']:.0%}",
            str(ranking["generation"]),
        )
    
    console.print(table)
    
    # Show statistics
    stats = get_tournament_statistics(tournament_result)
    if stats:
        console.print(Panel(
            f"[bold]Tournament Statistics[/bold]\n"
            f"Cooperation Rate: {stats['cooperation_rate']:.1%}\n"
            f"Mutual Cooperation: {stats['mutual_cooperation_rate']:.1%}\n"
            f"Mutual Defection: {stats['mutual_defection_rate']:.1%}\n"
            f"Avg Score/Round: {stats['avg_score_per_round']:.2f}",
            title="Stats",
            border_style="green"
        ))


def display_evolution_summary(survivors: list[Agent], offspring: list[Agent]) -> None:
    """Display evolution (selection and reproduction) summary."""
    survivor_ids = [a.id[:12] for a in survivors]
    offspring_ids = [a.id[:12] for a in offspring]
    
    console.print(Panel(
        f"[bold green]Survivors:[/bold green] {', '.join(survivor_ids)}\n"
        f"[bold yellow]Offspring:[/bold yellow] {', '.join(offspring_ids)}",
        title="Evolution",
        border_style="cyan"
    ))


def build_live_display(
    generation: int,
    match_number: int,
    total_matches: int,
    agents: list[Agent],
    recent_matches: list[dict],
    current_match: Optional[tuple[Agent, Agent]] = None,
) -> Panel:
    """Build the live display panel for tournament progress."""
    # Header with progress
    progress_pct = (match_number / total_matches * 100) if total_matches > 0 else 0
    progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
    header = Text()
    header.append(f"Generation {generation}", style="bold cyan")
    header.append(f" | Match {match_number}/{total_matches} ")
    header.append(f"[{progress_bar}] {progress_pct:.0f}%", style="green")
    
    # Current match section
    current_section = Text()
    if current_match:
        current_section.append("\n\nCurrent Match: ", style="bold yellow")
        current_section.append(f"{current_match[0].id[:12]}", style="magenta")
        current_section.append(" vs ", style="dim")
        current_section.append(f"{current_match[1].id[:12]}", style="magenta")
    
    # Recent matches section
    recent_section = Text()
    if recent_matches:
        recent_section.append("\n\nRecent Matches:\n", style="bold")
        for match in recent_matches[:3]:
            winner = match.get("winner_id")
            a1_id = match["agent1_id"][:8]
            a2_id = match["agent2_id"][:8]
            a1_score = match["agent1_score"]
            a2_score = match["agent2_score"]
            a1_coop = match["agent1_cooperations"]
            a1_def = match["agent1_defections"]
            a2_coop = match["agent2_cooperations"]
            a2_def = match["agent2_defections"]
            
            if winner:
                winner_name = a1_id if winner == match["agent1_id"] else a2_id
                recent_section.append(f"  {winner_name}", style="green")
                recent_section.append(" beat ")
                loser_name = a2_id if winner == match["agent1_id"] else a1_id
                recent_section.append(f"{loser_name}", style="red")
            else:
                recent_section.append(f"  {a1_id} tied {a2_id}", style="yellow")
            
            recent_section.append(f" ({a1_score}-{a2_score})")
            recent_section.append(f" | {a1_coop}C/{a1_def}D vs {a2_coop}C/{a2_def}D\n", style="dim")
    
    # Leaderboard section with personalities
    leaderboard_section = Text()
    leaderboard_section.append("\n\nLeaderboard:\n", style="bold")
    sorted_agents = sorted(agents, key=lambda a: a.fitness, reverse=True)
    for i, agent in enumerate(sorted_agents[:8], 1):
        coop_rate = agent.cooperation_rate
        fitness_bar = "▓" * min(10, agent.fitness // 5) if agent.fitness > 0 else ""
        personality_desc = agent.personality.get_short_description()
        
        if i == 1:
            style = "bold green"
        elif i <= 4:
            style = "green"
        else:
            style = "dim"
        
        leaderboard_section.append(f"  {i}. ", style="cyan")
        leaderboard_section.append(f"{agent.id[:12]:<12}", style=style)
        leaderboard_section.append(f" {agent.fitness:>3} pts ", style=style)
        leaderboard_section.append(f"[{personality_desc[:15]:<15}]", style="italic dim")
        leaderboard_section.append(f" {coop_rate:.0%}\n", style="dim")
    
    # Combine all sections
    content = Group(header, current_section, recent_section, leaderboard_section)
    
    return Panel(
        content,
        title="[bold]Live Tournament[/bold]",
        border_style="blue",
        padding=(0, 1),
    )


async def run_evolution(
    num_generations: int = NUM_GENERATIONS,
    num_agents: int = NUM_AGENTS,
    use_cache: bool = True,
    verbose: bool = True,
    live: bool = False,
) -> tuple[list[Agent], list[TournamentResult]]:
    """
    Run the complete evolutionary tournament.
    
    Args:
        num_generations: Number of generations to evolve
        num_agents: Number of agents in population
        use_cache: Whether to cache LLM responses
        verbose: Whether to print progress
        live: Whether to show live tournament display
    
    Returns:
        Tuple of (final_population, tournament_results)
    """
    # Initialize
    agents = create_initial_population(num_agents)
    llm_client = LLMClient(use_cache=use_cache)
    all_results: list[TournamentResult] = []
    
    # Track recent matches for live display
    recent_matches: list[dict] = []
    current_match_agents: Optional[tuple[Agent, Agent]] = None
    
    if verbose:
        console.print(Panel(
            f"[bold]DarwinLM - Evolutionary Prisoner's Dilemma[/bold]\n"
            f"Agents: {num_agents} | Generations: {num_generations}" +
            ("\n[cyan]Live mode enabled[/cyan]" if live else ""),
            title="Starting Evolution",
            border_style="blue"
        ))
    
    for gen in range(num_generations):
        # Reset live state for new generation
        if live:
            reset_live_state(gen)
            recent_matches = []
        
        if verbose and not live:
            console.print(f"\n[bold cyan]═══ Generation {gen} ═══[/bold cyan]")
        
        if live:
            # Live mode with Rich Live display
            live_display = None
            match_count = 0
            total_matches = (num_agents * (num_agents - 1)) // 2
            
            def on_match_complete_live(result, completed, total):
                nonlocal match_count, recent_matches, live_display
                match_count = completed
                
                # Create match summary
                summary = MatchSummary.from_match_result(result)
                recent_matches.insert(0, summary.to_dict())
                recent_matches = recent_matches[:5]
                
                # Update live state file for Streamlit
                update_live_state(
                    generation=gen,
                    match_number=completed,
                    total_matches=total,
                    agents=agents,
                    match_result=result,
                    status="running",
                )
                
                # Update live display
                if live_display:
                    live_display.update(build_live_display(
                        generation=gen,
                        match_number=completed,
                        total_matches=total,
                        agents=agents,
                        recent_matches=recent_matches,
                    ))
            
            with Live(
                build_live_display(gen, 0, total_matches, agents, []),
                console=console,
                refresh_per_second=4,
            ) as live_display:
                tournament_result = await run_tournament(
                    agents=agents,
                    generation=gen,
                    llm_client=llm_client,
                    on_match_complete=on_match_complete_live,
                )
                
                # Final update
                live_display.update(build_live_display(
                    generation=gen,
                    match_number=total_matches,
                    total_matches=total_matches,
                    agents=agents,
                    recent_matches=recent_matches,
                ))
        else:
            # Standard progress bar mode
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console,
                disable=not verbose,
            ) as progress:
                task = progress.add_task(f"Running tournament...", total=100)
                
                def on_match_complete(result, completed, total):
                    progress.update(task, completed=int((completed / total) * 100))
                
                tournament_result = await run_tournament(
                    agents=agents,
                    generation=gen,
                    llm_client=llm_client,
                    on_match_complete=on_match_complete,
                )
        
        all_results.append(tournament_result)
        
        if verbose and not live:
            display_generation_summary(gen, agents, tournament_result)
        elif live:
            # Brief summary after live display
            console.print(f"\n[bold cyan]Generation {gen} Complete[/bold cyan]")
            stats = get_tournament_statistics(tournament_result)
            console.print(f"  Top Agent: {agents[0].id[:12]} ({agents[0].fitness} pts)")
            console.print(f"  Cooperation Rate: {stats.get('cooperation_rate', 0):.1%}")
        
        # Evolve (except for last generation)
        if gen < num_generations - 1:
            if live:
                mark_evolving(gen)
            
            agents, survivors, offspring = evolve_generation(agents)
            
            if verbose:
                display_evolution_summary(survivors, offspring)
            
            # Save log
            log_file = save_generation_log(
                gen, agents, tournament_result, survivors, offspring
            )
            if verbose:
                console.print(f"[dim]Saved: {log_file}[/dim]")
        else:
            # Save final generation
            log_file = save_generation_log(
                gen, agents, tournament_result, [], []
            )
            if verbose:
                console.print(f"[dim]Saved: {log_file}[/dim]")
    
    if live:
        mark_complete()
    
    if verbose:
        console.print(Panel(
            "[bold green]Evolution Complete![/bold green]",
            border_style="green"
        ))
    
    return agents, all_results


async def run_baseline_comparison(
    evolved_agent: Agent,
    num_matches: int = 5,
    use_cache: bool = True,
) -> dict:
    """
    Compare an evolved agent against baseline.
    
    Returns statistics about win/loss/tie.
    """
    from src.agent import Agent
    from src.game import play_match
    
    baseline = Agent.create_baseline()
    llm_client = LLMClient(use_cache=use_cache)
    
    results = {
        "evolved_wins": 0,
        "baseline_wins": 0,
        "ties": 0,
        "evolved_total_score": 0,
        "baseline_total_score": 0,
    }
    
    for _ in range(num_matches):
        # Reset fitness for fair comparison
        evolved_clone = evolved_agent.clone()
        evolved_clone.fitness = 0
        baseline_clone = Agent.create_baseline()
        
        match_result = await play_match(evolved_clone, baseline_clone, llm_client=llm_client)
        
        results["evolved_total_score"] += match_result.agent1_total_score
        results["baseline_total_score"] += match_result.agent2_total_score
        
        if match_result.agent1_total_score > match_result.agent2_total_score:
            results["evolved_wins"] += 1
        elif match_result.agent2_total_score > match_result.agent1_total_score:
            results["baseline_wins"] += 1
        else:
            results["ties"] += 1
    
    return results


def main():
    """CLI entry point."""
    import typer
    
    app = typer.Typer(help="DarwinLM - Evolutionary Prisoner's Dilemma Tournament")
    
    @app.command()
    def evolve(
        generations: int = typer.Option(NUM_GENERATIONS, "--generations", "-g", help="Number of generations"),
        agents: int = typer.Option(NUM_AGENTS, "--agents", "-a", help="Number of agents"),
        no_cache: bool = typer.Option(False, "--no-cache", help="Disable LLM response caching"),
        quiet: bool = typer.Option(False, "--quiet", "-q", help="Reduce output verbosity"),
        live: bool = typer.Option(False, "--live", "-l", help="Show live tournament display with running leaderboard"),
    ):
        """Run the evolutionary tournament."""
        asyncio.run(run_evolution(
            num_generations=generations,
            num_agents=agents,
            use_cache=not no_cache,
            verbose=not quiet,
            live=live,
        ))
    
    @app.command()
    def compare(
        generation: int = typer.Argument(..., help="Generation number to load"),
        matches: int = typer.Option(5, "--matches", "-m", help="Number of comparison matches"),
    ):
        """Compare evolved agent from a generation against baseline."""
        # Load generation data
        log_file = Path(LOGS_DIR) / f"generation_{generation:03d}.json"
        if not log_file.exists():
            console.print(f"[red]Generation log not found: {log_file}[/red]")
            raise typer.Exit(1)
        
        with open(log_file) as f:
            data = json.load(f)
        
        # Get best agent
        best_agent_data = data["agents"][0]  # Already sorted by fitness
        evolved_agent = Agent.from_dict(best_agent_data)
        
        console.print(f"Comparing {evolved_agent.id} (Gen {generation}) against baseline...")
        
        results = asyncio.run(run_baseline_comparison(evolved_agent, matches))
        
        console.print(Panel(
            f"[bold]Comparison Results ({matches} matches)[/bold]\n"
            f"Evolved Wins: {results['evolved_wins']}\n"
            f"Baseline Wins: {results['baseline_wins']}\n"
            f"Ties: {results['ties']}\n"
            f"Evolved Total Score: {results['evolved_total_score']}\n"
            f"Baseline Total Score: {results['baseline_total_score']}",
            border_style="cyan"
        ))
    
    @app.command()
    def show(
        generation: int = typer.Argument(..., help="Generation number to display"),
    ):
        """Display details of a specific generation."""
        log_file = Path(LOGS_DIR) / f"generation_{generation:03d}.json"
        if not log_file.exists():
            console.print(f"[red]Generation log not found: {log_file}[/red]")
            raise typer.Exit(1)
        
        with open(log_file) as f:
            data = json.load(f)
        
        # Display agents
        table = Table(title=f"Generation {generation} Agents")
        table.add_column("ID")
        table.add_column("Fitness")
        table.add_column("Coop Bias")
        table.add_column("Retaliation")
        table.add_column("Forgiveness")
        table.add_column("Keywords")
        
        for agent_data in data["agents"][:8]:
            dna = agent_data["dna"]
            table.add_row(
                agent_data["id"][:12],
                str(agent_data["fitness"]),
                f"{dna['cooperation_bias']:.2f}",
                f"{dna['retaliation_sensitivity']:.2f}",
                f"{dna['forgiveness_rate']:.2f}",
                ", ".join(dna["strategy_keywords"][:2]),
            )
        
        console.print(table)
        
        # Display statistics
        if "statistics" in data:
            stats = data["statistics"]
            console.print(Panel(
                f"Cooperation Rate: {stats.get('cooperation_rate', 0):.1%}\n"
                f"Mutual Cooperation: {stats.get('mutual_cooperation_rate', 0):.1%}\n"
                f"Mutual Defection: {stats.get('mutual_defection_rate', 0):.1%}",
                title="Statistics"
            ))
    
    app()


if __name__ == "__main__":
    main()
