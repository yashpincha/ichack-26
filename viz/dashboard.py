"""Streamlit dashboard for DarwinLM visualization."""

from __future__ import annotations

import json
import asyncio
from pathlib import Path
from typing import Optional
import streamlit as st

# Page config must be first Streamlit command
st.set_page_config(
    page_title="DarwinLM - Evolutionary PD Tournament",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

import sys
import time
sys.path.insert(0, str(Path(__file__).parent.parent))

from viz.components import (
    create_fitness_chart,
    create_cooperation_rate_chart,
    create_gene_heatmap,
    create_agent_card,
    create_match_viewer,
    create_strategy_radar,
    create_lineage_tree,
    create_live_leaderboard,
    create_live_match_card,
    create_cooperation_gauge,
    create_thinking_display,
    create_round_display,
    create_personality_radar_multi,
    create_trait_evolution_chart,
    create_evolution_summary_card,
)
from src.config import LOGS_DIR, COOPERATE_COLOR, DEFECT_COLOR, PERSONALITY_TRAITS
from src.live_state import read_live_state, LiveState


# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #1f2937;
    }
    .stMetric {
        background-color: #374151;
        padding: 10px;
        border-radius: 8px;
    }
    .stExpander {
        background-color: #374151;
        border-radius: 8px;
    }
    div[data-testid="stSidebarContent"] {
        background-color: #111827;
    }
    .cooperate {
        color: #22c55e;
        font-weight: bold;
    }
    .defect {
        color: #ef4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def load_generation_data(log_dir: str = LOGS_DIR) -> list[dict]:
    """Load all generation log files."""
    log_path = Path(log_dir)
    if not log_path.exists():
        return []
    
    data = []
    for log_file in sorted(log_path.glob("generation_*.json")):
        try:
            with open(log_file) as f:
                data.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue
    
    return data


def load_single_generation(generation: int, log_dir: str = LOGS_DIR) -> Optional[dict]:
    """Load a specific generation's data."""
    log_file = Path(log_dir) / f"generation_{generation:03d}.json"
    if not log_file.exists():
        return None
    
    with open(log_file) as f:
        return json.load(f)


def main():
    """Main dashboard application."""
    # Header
    st.title("🧬 DarwinLM")
    st.markdown("### Evolutionary Prisoner's Dilemma Tournament")
    
    # Load data
    all_generation_data = load_generation_data()
    live_state = read_live_state()
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # View mode - include Live option
        view_mode = st.radio(
            "View Mode",
            ["🔴 Live", "📊 Overview", "🧬 Evolution", "🤖 Agents", "🎮 Matches", "🌳 Lineage"],
            key="view_mode",
        )
        
        st.divider()
        
        # Show generation selector only for non-live modes
        if view_mode != "🔴 Live":
            if all_generation_data:
                max_gen = max(d["generation"] for d in all_generation_data)
                selected_gen = st.slider(
                    "Select Generation",
                    min_value=0,
                    max_value=max_gen,
                    value=max_gen,
                    key="gen_slider",
                )
                
                st.divider()
                
                # Quick stats
                current_data = load_single_generation(selected_gen)
                if current_data:
                    stats = current_data.get("statistics", {})
                    st.metric("Cooperation Rate", f"{stats.get('cooperation_rate', 0):.1%}")
                    st.metric("Mutual Cooperation", f"{stats.get('mutual_cooperation_rate', 0):.1%}")
                    st.metric("Avg Score/Round", f"{stats.get('avg_score_per_round', 0):.1f}")
            else:
                selected_gen = 0
        else:
            selected_gen = live_state.generation if live_state else 0
            
            # Live mode controls
            if live_state:
                st.metric("Status", live_state.status.upper())
                st.metric("Generation", live_state.generation)
                st.metric("Progress", f"{live_state.match_number}/{live_state.total_matches}")
            
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto-refresh (2s)", value=True, key="auto_refresh")
            if auto_refresh:
                time.sleep(0.1)  # Small delay to prevent tight loop
                st.rerun()
    
    # Handle no data case for non-live modes
    if not all_generation_data and view_mode != "🔴 Live":
        st.warning("No generation data found. Run the evolution first!")
        st.code("python main.py evolve --generations 10 --live", language="bash")
        
        # Show option to run evolution
        if st.button("🚀 Run Evolution (Demo Mode)"):
            with st.spinner("Running evolution... This may take a few minutes."):
                try:
                    from main import run_evolution
                    asyncio.run(run_evolution(num_generations=3, num_agents=4, verbose=False))
                    st.success("Evolution complete! Refresh the page to see results.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error running evolution: {e}")
        return
    
    # Main content based on view mode
    if view_mode == "🔴 Live":
        show_live(live_state)
    elif view_mode == "📊 Overview":
        show_overview(all_generation_data, selected_gen)
    elif view_mode == "🧬 Evolution":
        show_evolution(all_generation_data)
    elif view_mode == "🤖 Agents":
        show_agents(selected_gen)
    elif view_mode == "🎮 Matches":
        show_matches(selected_gen)
    elif view_mode == "🌳 Lineage":
        show_lineage(all_generation_data)


def show_live(live_state: Optional[LiveState]):
    """Show live tournament progress."""
    st.header("🔴 Live Tournament")
    
    if not live_state:
        st.info("No live tournament running. Start one with:")
        st.code("python main.py evolve --generations 10 --live", language="bash")
        return
    
    # Status indicator
    status_colors = {
        "idle": "gray",
        "running": "green", 
        "evolving": "yellow",
        "complete": "blue",
    }
    status_color = status_colors.get(live_state.status, "gray")
    
    # Progress section
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Generation", live_state.generation)
    with col2:
        st.metric("Match", f"{live_state.match_number}/{live_state.total_matches}")
    with col3:
        st.metric("Status", live_state.status.upper())
    with col4:
        coop_rate = live_state.cooperation_rate * 100 if live_state.cooperation_rate else 0
        st.metric("Cooperation", f"{coop_rate:.1f}%")
    
    # Progress bar
    progress_pct = live_state.progress_percent / 100
    st.progress(progress_pct, text=f"Tournament Progress: {live_state.progress_percent:.0f}%")
    
    # Two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Leaderboard
        st.subheader("📊 Live Leaderboard")
        if live_state.leaderboard:
            create_live_leaderboard(live_state.leaderboard)
        else:
            st.info("Waiting for matches to complete...")
    
    with col2:
        # Recent matches
        st.subheader("🎮 Recent Matches")
        if live_state.recent_matches:
            for match in live_state.recent_matches[:5]:
                create_live_match_card(match)
        else:
            st.info("No matches completed yet...")
    
    # Live statistics
    st.subheader("📈 Live Statistics")
    col1, col2, col3 = st.columns(3)
    
    total_moves = live_state.total_cooperations + live_state.total_defections
    total_rounds = live_state.mutual_cooperations + live_state.mutual_defections + (total_moves // 2 - live_state.mutual_cooperations - live_state.mutual_defections) if total_moves > 0 else 0
    
    with col1:
        if total_moves > 0:
            create_cooperation_gauge(live_state.cooperation_rate)
        else:
            st.metric("Overall Cooperation", "N/A")
    
    with col2:
        if total_rounds > 0:
            mutual_coop_rate = live_state.mutual_cooperations / (live_state.match_number * 10) if live_state.match_number > 0 else 0
            st.metric("Mutual Cooperations", live_state.mutual_cooperations)
            st.caption(f"Both players cooperated")
        else:
            st.metric("Mutual Cooperations", "0")
    
    with col3:
        if total_rounds > 0:
            mutual_def_rate = live_state.mutual_defections / (live_state.match_number * 10) if live_state.match_number > 0 else 0
            st.metric("Mutual Defections", live_state.mutual_defections)
            st.caption(f"Both players defected")
        else:
            st.metric("Mutual Defections", "0")
    
    # Last updated
    st.caption(f"Last updated: {live_state.last_updated}")


def show_overview(all_data: list[dict], selected_gen: int):
    """Show overview dashboard."""
    st.header("📊 Evolution Overview")
    
    # Main charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            create_fitness_chart(all_data),
            use_container_width=True,
        )
    
    with col2:
        st.plotly_chart(
            create_cooperation_rate_chart(all_data),
            use_container_width=True,
        )
    
    # Gene heatmap
    st.plotly_chart(
        create_gene_heatmap(all_data),
        use_container_width=True,
    )
    
    # Summary stats
    st.subheader("📈 Evolution Summary")
    
    if len(all_data) >= 2:
        first_gen = all_data[0]
        last_gen = all_data[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        
        first_fitnesses = [r["fitness"] for r in first_gen.get("tournament", {}).get("agent_rankings", [])]
        last_fitnesses = [r["fitness"] for r in last_gen.get("tournament", {}).get("agent_rankings", [])]
        
        with col1:
            first_max = max(first_fitnesses) if first_fitnesses else 0
            last_max = max(last_fitnesses) if last_fitnesses else 0
            st.metric(
                "Max Fitness",
                last_max,
                delta=last_max - first_max,
            )
        
        with col2:
            first_avg = sum(first_fitnesses) / len(first_fitnesses) if first_fitnesses else 0
            last_avg = sum(last_fitnesses) / len(last_fitnesses) if last_fitnesses else 0
            st.metric(
                "Avg Fitness",
                f"{last_avg:.1f}",
                delta=f"{last_avg - first_avg:.1f}",
            )
        
        with col3:
            first_coop = first_gen.get("statistics", {}).get("cooperation_rate", 0)
            last_coop = last_gen.get("statistics", {}).get("cooperation_rate", 0)
            st.metric(
                "Cooperation Rate",
                f"{last_coop:.1%}",
                delta=f"{(last_coop - first_coop) * 100:.1f}%",
            )
        
        with col4:
            st.metric(
                "Generations",
                len(all_data),
            )


def show_evolution(all_data: list[dict]):
    """Show personality evolution analysis."""
    st.header("🧬 Personality Evolution")
    
    if len(all_data) < 2:
        st.info("Need at least 2 generations to show evolution analysis.")
        return
    
    # Get first and last generation stats
    first_gen = all_data[0]
    last_gen = all_data[-1]
    
    first_stats = first_gen.get("gene_statistics", {})
    last_stats = last_gen.get("gene_statistics", {})
    
    # Evolution Summary Card
    if first_stats and last_stats:
        create_evolution_summary_card(first_stats, last_stats)
    
    st.divider()
    
    # Trait selector for detailed view
    st.subheader("📈 Trait Evolution Over Time")
    
    available_traits = list(first_stats.keys()) if first_stats else PERSONALITY_TRAITS
    selected_trait = st.selectbox(
        "Select trait to analyze",
        available_traits,
        format_func=lambda x: x.replace("_", " ").title()
    )
    
    if selected_trait:
        fig = create_trait_evolution_chart(all_data, selected_trait)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Compare first vs last generation personalities
    st.subheader("🎭 Personality Comparison: Gen 0 vs Final")
    
    # Get agents from first and last generation
    first_agents = first_gen.get("agents", [])[:4]
    last_agents = last_gen.get("agents", [])[:4]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Generation 0 (Random Start)**")
        if first_agents:
            fig = create_personality_radar_multi(first_agents, "Gen 0 Personalities")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f"**Generation {last_gen.get('generation', 'Final')} (Evolved)**")
        if last_agents:
            fig = create_personality_radar_multi(last_agents, "Final Personalities")
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Key findings
    st.subheader("🔍 Key Findings")
    
    if first_stats and last_stats:
        # Calculate biggest changes
        changes = []
        for trait in first_stats:
            if trait in last_stats:
                gen0_mean = first_stats[trait].get("mean", 0.5)
                final_mean = last_stats[trait].get("mean", 0.5)
                change = final_mean - gen0_mean
                changes.append({
                    "trait": trait,
                    "gen0": gen0_mean,
                    "final": final_mean,
                    "change": change,
                })
        
        changes.sort(key=lambda x: abs(x["change"]), reverse=True)
        
        if changes:
            biggest = changes[0]
            direction = "increased" if biggest["change"] > 0 else "decreased"
            
            st.markdown(f"""
            **Biggest Change:** {biggest['trait'].replace('_', ' ').title()} {direction} 
            from {biggest['gen0']:.0%} to {biggest['final']:.0%}
            
            **What this means:** Evolution selected for agents with {'higher' if biggest['change'] > 0 else 'lower'} 
            {biggest['trait'].replace('_', ' ')}, suggesting this trait conferred a survival advantage.
            """)
            
            # Interpret the evolved strategy
            st.markdown("### 🎯 Evolved Strategy Profile")
            
            high_traits = [c["trait"] for c in changes if c["final"] > 0.6]
            low_traits = [c["trait"] for c in changes if c["final"] < 0.4]
            
            if high_traits or low_traits:
                st.markdown("The evolved population tends to have:")
                if high_traits:
                    st.markdown("- **High:** " + ", ".join(t.replace("_", " ").title() for t in high_traits))
                if low_traits:
                    st.markdown("- **Low:** " + ", ".join(t.replace("_", " ").title() for t in low_traits))


def show_agents(selected_gen: int):
    """Show agent details for selected generation."""
    st.header(f"🤖 Generation {selected_gen} Agents")
    
    data = load_single_generation(selected_gen)
    if not data:
        st.error("Could not load generation data.")
        return
    
    agents = data.get("agents", [])
    rankings = data.get("tournament", {}).get("agent_rankings", [])
    
    # Create rank lookup
    rank_lookup = {r["agent_id"]: r["rank"] for r in rankings}
    
    # Sort agents by rank
    agents_sorted = sorted(agents, key=lambda a: rank_lookup.get(a["id"], 999))
    
    # Display agents in grid
    cols = st.columns(2)
    
    for i, agent in enumerate(agents_sorted):
        with cols[i % 2]:
            rank = rank_lookup.get(agent["id"])
            create_agent_card(agent, rank)
    
    # Show radar comparison
    st.subheader("🎯 Strategy Comparison")
    
    if len(agents_sorted) >= 2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(
                create_strategy_radar(agents_sorted[0]),
                use_container_width=True,
            )
        
        with col2:
            # Compare with worst performer
            st.plotly_chart(
                create_strategy_radar(agents_sorted[-1]),
                use_container_width=True,
            )


def show_matches(selected_gen: int):
    """Show match details for selected generation."""
    st.header(f"🎮 Generation {selected_gen} Matches")
    
    data = load_single_generation(selected_gen)
    if not data:
        st.error("Could not load generation data.")
        return
    
    matches = data.get("tournament", {}).get("matches", [])
    
    if not matches:
        st.info("No match data available.")
        return
    
    # Match selector
    agents_in_matches = set()
    for m in matches:
        agents_in_matches.add(m["agent1_id"])
        agents_in_matches.add(m["agent2_id"])
    
    col1, col2 = st.columns(2)
    with col1:
        agent1_filter = st.selectbox(
            "Filter by Agent 1",
            ["All"] + sorted(list(agents_in_matches)),
            key="agent1_filter",
        )
    with col2:
        agent2_filter = st.selectbox(
            "Filter by Agent 2",
            ["All"] + sorted(list(agents_in_matches)),
            key="agent2_filter",
        )
    
    # Filter matches
    filtered_matches = matches
    if agent1_filter != "All":
        filtered_matches = [m for m in filtered_matches 
                          if m["agent1_id"] == agent1_filter or m["agent2_id"] == agent1_filter]
    if agent2_filter != "All":
        filtered_matches = [m for m in filtered_matches 
                          if m["agent1_id"] == agent2_filter or m["agent2_id"] == agent2_filter]
    
    st.write(f"Showing {len(filtered_matches)} of {len(matches)} matches")
    
    # Display matches
    for match in filtered_matches[:10]:  # Limit to 10
        with st.expander(f"{match['agent1_id'][:8]} vs {match['agent2_id'][:8]} "
                        f"({match['agent1_total_score']} - {match['agent2_total_score']})"):
            create_match_viewer(match)


def show_lineage(all_data: list[dict]):
    """Show agent lineage tree."""
    st.header("🌳 Agent Lineage")
    
    if len(all_data) < 2:
        st.info("Need at least 2 generations to show lineage.")
        return
    
    st.plotly_chart(
        create_lineage_tree(all_data),
        use_container_width=True,
    )
    
    # Show survivor history
    st.subheader("🏆 Survivor History")
    
    survivor_data = []
    for gen_data in all_data:
        survivors = gen_data.get("survivors", [])
        if survivors:
            survivor_data.append({
                "Generation": gen_data["generation"],
                "Survivors": ", ".join(s[:8] for s in survivors),
            })
    
    if survivor_data:
        st.dataframe(survivor_data, use_container_width=True)


if __name__ == "__main__":
    main()
