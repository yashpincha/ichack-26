"""Main entry point for AI r/place Simulation."""

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
from src.grid import Grid, create_grid, COLOR_ASCII
from src.simulation import run_generation, GenerationResult, get_generation_statistics, TurnResult
from src.evolution import evolve_generation, calculate_trait_statistics
from src.llm import LLMClient
from src.config import (
    NUM_AGENTS,
    NUM_GENERATIONS,
    TURNS_PER_GENERATION,
    GRID_WIDTH,
    GRID_HEIGHT,
    LOGS_DIR,
    COLOR_HEX,
)

console = Console()


def save_generation_log(
    generation: int,
    agents: list[Agent],
    result: GenerationResult,
    survivors: list[Agent],
    offspring: list[Agent],
    log_dir: str = LOGS_DIR,
) -> str:
    """Save generation data to JSON log file."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    filename = f"generation_{generation:03d}.json"
    filepath = log_path / filename
    
    data = {
        "generation": generation,
        "timestamp": timestamp,
        "agents": [a.to_dict() for a in agents],
        "result": result.to_dict(),
        "statistics": get_generation_statistics(result, agents),
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
    result: GenerationResult,
) -> None:
    """Display a rich summary of the generation results."""
    stats = get_generation_statistics(result, agents)
    
    # Create rankings table
    table = Table(title=f"Generation {generation} Results", show_header=True)
    table.add_column("Rank", style="cyan", justify="right")
    table.add_column("Agent ID", style="magenta")
    table.add_column("Color", justify="center")
    table.add_column("Fitness", style="green", justify="right")
    table.add_column("Territory", style="yellow", justify="right")
    table.add_column("Survival", style="blue", justify="right")
    table.add_column("Personality", style="dim")
    
    for ranking in stats.get("agent_rankings", []):
        # Color indicator
        color = ranking.get("color", "red")
        color_char = COLOR_ASCII.get(color, "?")
        
        table.add_row(
            str(ranking["rank"]),
            ranking["agent_id"][:12],
            f"[{color}]{color_char}[/{color}]",
            str(ranking["fitness"]),
            str(ranking["territory"]),
            f"{ranking['survival_rate']:.0%}",
            ranking["personality"],
        )
    
    console.print(table)
    
    # Show grid state
    if result.final_grid:
        console.print(Panel(
            result.final_grid.to_ascii(use_color=True),
            title="Final Canvas",
            border_style="blue",
        ))


def display_evolution_summary(survivors: list[Agent], offspring: list[Agent]) -> None:
    """Display evolution (selection and reproduction) summary."""
    survivor_info = [f"{a.id[:8]} ({a.preferred_color})" for a in survivors]
    offspring_info = [f"{a.id[:8]} ({a.preferred_color})" for a in offspring]
    
    console.print(Panel(
        f"[bold green]Survivors:[/bold green] {', '.join(survivor_info)}\n"
        f"[bold yellow]Offspring:[/bold yellow] {', '.join(offspring_info)}",
        title="Evolution",
        border_style="cyan"
    ))


def build_live_display(
    generation: int,
    turn: int,
    total_turns: int,
    grid: Grid,
    agents: list[Agent],
    recent_turns: list[TurnResult],
) -> Panel:
    """Build the live display panel for simulation progress."""
    # Header with progress
    progress_pct = (turn / total_turns * 100) if total_turns > 0 else 0
    progress_bar = "█" * int(progress_pct / 5) + "░" * (20 - int(progress_pct / 5))
    header = Text()
    header.append(f"Generation {generation}", style="bold cyan")
    header.append(f" | Turn {turn}/{total_turns} ")
    header.append(f"[{progress_bar}] {progress_pct:.0f}%", style="green")
    
    # Grid section (compact)
    grid_text = Text()
    grid_text.append("\n\nCanvas:\n", style="bold")
    grid_text.append(grid.to_compact_ascii())
    
    # Leaderboard section
    leaderboard = Text()
    leaderboard.append("\n\nLeaderboard:\n", style="bold")
    sorted_agents = sorted(agents, key=lambda a: grid.get_territory_count(a.id), reverse=True)
    for i, agent in enumerate(sorted_agents[:4], 1):
        territory = grid.get_territory_count(agent.id)
        color = agent.preferred_color
        desc = agent.personality.get_short_description()
        
        if i == 1:
            style = "bold green"
        elif i <= 2:
            style = "green"
        else:
            style = "dim"
        
        leaderboard.append(f"  {i}. ", style="cyan")
        leaderboard.append(f"{agent.id[:10]:<10}", style=style)
        leaderboard.append(f" [{color}] ", style=color)
        leaderboard.append(f"{territory:>3} px ", style=style)
        leaderboard.append(f"[{desc[:12]}]\n", style="dim italic")
    
    # Recent activity
    activity = Text()
    if recent_turns:
        activity.append("\n\nRecent Activity:\n", style="bold")
        for turn_result in recent_turns[-3:]:
            overwrote_text = ""
            if turn_result.overwrote:
                overwrote_text = f" (overwrote {turn_result.overwrote[:6]})"
            activity.append(
                f"  {turn_result.agent_id[:8]} → ({turn_result.x},{turn_result.y}) {turn_result.color}{overwrote_text}\n",
                style="dim"
            )
    
    # Combine all sections
    content = Group(header, grid_text, leaderboard, activity)
    
    return Panel(
        content,
        title="[bold]AI r/place Simulation[/bold]",
        border_style="blue",
        padding=(0, 1),
    )


async def run_simulation(
    num_generations: int = NUM_GENERATIONS,
    num_agents: int = NUM_AGENTS,
    grid_width: int = GRID_WIDTH,
    grid_height: int = GRID_HEIGHT,
    turns_per_gen: int = TURNS_PER_GENERATION,
    use_cache: bool = True,
    verbose: bool = True,
    live: bool = False,
) -> tuple[list[Agent], list[GenerationResult]]:
    """
    Run the complete evolutionary simulation.
    
    Args:
        num_generations: Number of generations to simulate
        num_agents: Number of agents in population
        grid_width: Width of the canvas
        grid_height: Height of the canvas
        turns_per_gen: Turns per generation
        use_cache: Whether to cache LLM responses
        verbose: Whether to print progress
        live: Whether to show live display
    
    Returns:
        Tuple of (final_population, generation_results)
    """
    # Initialize
    agents = create_initial_population(num_agents)
    llm_client = LLMClient(use_cache=use_cache)
    all_results: list[GenerationResult] = []
    
    if verbose:
        console.print(Panel(
            f"[bold]AI r/place Simulation[/bold]\n"
            f"Agents: {num_agents} | Generations: {num_generations}\n"
            f"Grid: {grid_width}x{grid_height} | Turns/Gen: {turns_per_gen}" +
            ("\n[cyan]Live mode enabled[/cyan]" if live else ""),
            title="Starting Simulation",
            border_style="blue"
        ))
        
        # Show initial agents
        for agent in agents:
            console.print(f"  • {agent.id[:12]} - {agent.preferred_color} - {agent.personality.get_short_description()}")
    
    for gen in range(num_generations):
        # Create fresh grid for each generation
        grid = create_grid(width=grid_width, height=grid_height)
        recent_turns: list[TurnResult] = []
        
        if verbose and not live:
            console.print(f"\n[bold cyan]═══ Generation {gen} ═══[/bold cyan]")
        
        if live:
            # Live mode with Rich Live display
            total_agent_turns = turns_per_gen * num_agents
            
            def on_turn_complete(turn_result: TurnResult, completed: int, total: int):
                recent_turns.append(turn_result)
                if len(recent_turns) > 10:
                    recent_turns.pop(0)
            
            with Live(
                build_live_display(gen, 0, turns_per_gen, grid, agents, []),
                console=console,
                refresh_per_second=4,
            ) as live_display:
                # Custom callback to update live display
                turn_count = [0]
                
                def live_callback(turn_result: TurnResult, completed: int, total: int):
                    on_turn_complete(turn_result, completed, total)
                    current_turn = (completed - 1) // num_agents + 1
                    if current_turn != turn_count[0]:
                        turn_count[0] = current_turn
                        live_display.update(build_live_display(
                            gen, current_turn, turns_per_gen, grid, agents, recent_turns
                        ))
                
                result = await run_generation(
                    agents=agents,
                    grid=grid,
                    generation=gen,
                    turns_per_gen=turns_per_gen,
                    llm_client=llm_client,
                    on_turn_complete=live_callback,
                )
                
                # Final update
                live_display.update(build_live_display(
                    gen, turns_per_gen, turns_per_gen, grid, agents, recent_turns
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
                total_agent_turns = turns_per_gen * num_agents
                task = progress.add_task(f"Running generation {gen}...", total=total_agent_turns)
                
                def on_turn_complete(turn_result: TurnResult, completed: int, total: int):
                    progress.update(task, completed=completed)
                    recent_turns.append(turn_result)
                
                result = await run_generation(
                    agents=agents,
                    grid=grid,
                    generation=gen,
                    turns_per_gen=turns_per_gen,
                    llm_client=llm_client,
                    on_turn_complete=on_turn_complete,
                )
        
        all_results.append(result)
        
        if verbose:
            display_generation_summary(gen, agents, result)
        
        # Evolve (except for last generation)
        if gen < num_generations - 1:
            agents, survivors, offspring = evolve_generation(agents)
            
            if verbose:
                display_evolution_summary(survivors, offspring)
            
            # Save log
            log_file = save_generation_log(gen, agents, result, survivors, offspring)
            if verbose:
                console.print(f"[dim]Saved: {log_file}[/dim]")
        else:
            # Save final generation
            log_file = save_generation_log(gen, agents, result, [], [])
            if verbose:
                console.print(f"[dim]Saved: {log_file}[/dim]")
    
    if verbose:
        console.print(Panel(
            "[bold green]Simulation Complete![/bold green]",
            border_style="green"
        ))
    
    return agents, all_results


def main():
    """CLI entry point."""
    import typer
    
    app = typer.Typer(help="AI r/place Simulation - Watch AI agents compete on a shared canvas")
    
    @app.command()
    def simulate(
        generations: int = typer.Option(NUM_GENERATIONS, "--generations", "-g", help="Number of generations"),
        agents: int = typer.Option(NUM_AGENTS, "--agents", "-a", help="Number of agents"),
        grid_size: int = typer.Option(GRID_WIDTH, "--grid-size", "-s", help="Grid width and height"),
        turns: int = typer.Option(TURNS_PER_GENERATION, "--turns", "-t", help="Turns per generation"),
        no_cache: bool = typer.Option(False, "--no-cache", help="Disable LLM response caching"),
        quiet: bool = typer.Option(False, "--quiet", "-q", help="Reduce output verbosity"),
        live: bool = typer.Option(False, "--live", "-l", help="Show live canvas updates"),
    ):
        """Run the AI r/place simulation."""
        asyncio.run(run_simulation(
            num_generations=generations,
            num_agents=agents,
            grid_width=grid_size,
            grid_height=grid_size,
            turns_per_gen=turns,
            use_cache=not no_cache,
            verbose=not quiet,
            live=live,
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
        table.add_column("Color")
        table.add_column("Fitness")
        table.add_column("Territory")
        table.add_column("Territoriality")
        table.add_column("Aggression")
        table.add_column("Goal")
        
        for agent_data in data["agents"][:8]:
            personality = agent_data.get("personality", {})
            table.add_row(
                agent_data["id"][:12],
                personality.get("preferred_color", "?"),
                str(agent_data["fitness"]),
                str(data["statistics"]["territory_by_agent"].get(agent_data["id"], 0)),
                f"{personality.get('territoriality', 0.5):.2f}",
                f"{personality.get('aggression', 0.5):.2f}",
                personality.get("loose_goal", "None")[:20] if personality.get("loose_goal") else "None",
            )
        
        console.print(table)
        
        # Display grid if available
        if "result" in data and data["result"].get("final_grid"):
            from src.grid import Grid
            grid = Grid.from_dict(data["result"]["final_grid"])
            console.print(Panel(
                grid.to_ascii(),
                title="Final Canvas",
                border_style="blue",
            ))
        
        # Display statistics
        if "statistics" in data:
            stats = data["statistics"]
            console.print(Panel(
                f"Total Turns: {stats.get('total_turns', 0)}\n"
                f"Fill Rate: {stats.get('fill_rate', 0):.1%}\n"
                f"Filled Pixels: {stats.get('filled_pixels', 0)}/{stats.get('total_pixels', 0)}",
                title="Statistics"
            ))
    
    @app.command()
    def replay(
        generation: int = typer.Argument(..., help="Generation number to replay"),
        speed: float = typer.Option(0.1, "--speed", "-s", help="Seconds between turns"),
    ):
        """Replay a generation turn by turn."""
        import time
        
        log_file = Path(LOGS_DIR) / f"generation_{generation:03d}.json"
        if not log_file.exists():
            console.print(f"[red]Generation log not found: {log_file}[/red]")
            raise typer.Exit(1)
        
        with open(log_file) as f:
            data = json.load(f)
        
        if "result" not in data or "final_grid" not in data["result"]:
            console.print("[red]No grid data found in log[/red]")
            raise typer.Exit(1)
        
        # Reconstruct grid from turns
        grid_data = data["result"]["final_grid"]
        grid = create_grid(width=grid_data["width"], height=grid_data["height"])
        
        turns = data["result"].get("turns", [])
        
        console.print(f"[bold]Replaying Generation {generation}[/bold] ({len(turns)} turns)")
        
        with Live(
            Panel(grid.to_ascii(), title="Canvas"),
            console=console,
            refresh_per_second=10,
        ) as live:
            for turn_data in turns:
                grid.place_pixel(
                    x=turn_data["x"],
                    y=turn_data["y"],
                    color=turn_data["color"],
                    agent_id=turn_data["agent_id"],
                    turn=turn_data["turn"],
                )
                live.update(Panel(
                    grid.to_ascii() + f"\n\nTurn {turn_data['turn']}: {turn_data['agent_id'][:8]} placed {turn_data['color']} at ({turn_data['x']},{turn_data['y']})",
                    title=f"Canvas - Turn {turn_data['turn']}",
                    border_style="blue",
                ))
                time.sleep(speed)
        
        console.print("[green]Replay complete![/green]")
    
    app()


if __name__ == "__main__":
    main()
