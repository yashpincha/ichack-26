"""Reusable UI components for the Streamlit dashboard."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Optional
import streamlit as st

from src.config import COOPERATE_COLOR, DEFECT_COLOR, NEUTRAL_COLOR, BACKGROUND_COLOR


def create_fitness_chart(generation_data: list[dict]) -> go.Figure:
    """
    Create a line chart showing fitness evolution over generations.
    
    Args:
        generation_data: List of dicts with generation stats
    
    Returns:
        Plotly figure
    """
    generations = [d["generation"] for d in generation_data]
    
    # Extract fitness metrics
    max_fitness = []
    avg_fitness = []
    min_fitness = []
    
    for data in generation_data:
        rankings = data.get("tournament", {}).get("agent_rankings", [])
        if rankings:
            fitnesses = [r["fitness"] for r in rankings]
            max_fitness.append(max(fitnesses))
            avg_fitness.append(sum(fitnesses) / len(fitnesses))
            min_fitness.append(min(fitnesses))
        else:
            max_fitness.append(0)
            avg_fitness.append(0)
            min_fitness.append(0)
    
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=generations, y=max_fitness,
        mode="lines+markers",
        name="Max Fitness",
        line=dict(color=COOPERATE_COLOR, width=2),
        marker=dict(size=8),
    ))
    
    fig.add_trace(go.Scatter(
        x=generations, y=avg_fitness,
        mode="lines+markers",
        name="Avg Fitness",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=6),
    ))
    
    fig.add_trace(go.Scatter(
        x=generations, y=min_fitness,
        mode="lines+markers",
        name="Min Fitness",
        line=dict(color=DEFECT_COLOR, width=2),
        marker=dict(size=6),
    ))
    
    fig.update_layout(
        title="Fitness Evolution Over Generations",
        xaxis_title="Generation",
        yaxis_title="Fitness",
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    
    return fig


def create_cooperation_rate_chart(generation_data: list[dict]) -> go.Figure:
    """Create a chart showing cooperation rate over generations."""
    generations = [d["generation"] for d in generation_data]
    
    coop_rates = []
    mutual_coop_rates = []
    mutual_defect_rates = []
    
    for data in generation_data:
        stats = data.get("statistics", {})
        coop_rates.append(stats.get("cooperation_rate", 0) * 100)
        mutual_coop_rates.append(stats.get("mutual_cooperation_rate", 0) * 100)
        mutual_defect_rates.append(stats.get("mutual_defection_rate", 0) * 100)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=generations, y=coop_rates,
        mode="lines+markers",
        name="Overall Cooperation",
        line=dict(color=COOPERATE_COLOR, width=2),
    ))
    
    fig.add_trace(go.Scatter(
        x=generations, y=mutual_coop_rates,
        mode="lines+markers",
        name="Mutual Cooperation",
        line=dict(color="#22d3ee", width=2, dash="dash"),
    ))
    
    fig.add_trace(go.Scatter(
        x=generations, y=mutual_defect_rates,
        mode="lines+markers",
        name="Mutual Defection",
        line=dict(color=DEFECT_COLOR, width=2, dash="dash"),
    ))
    
    fig.update_layout(
        title="Cooperation Patterns Over Generations",
        xaxis_title="Generation",
        yaxis_title="Rate (%)",
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        yaxis=dict(range=[0, 100]),
    )
    
    return fig


def create_gene_heatmap(generation_data: list[dict]) -> go.Figure:
    """Create a heatmap showing gene evolution over generations."""
    numeric_genes = [
        "cooperation_bias",
        "retaliation_sensitivity", 
        "forgiveness_rate",
        "memory_weight",
        "message_honesty",
        "threat_frequency",
    ]
    
    generations = [d["generation"] for d in generation_data]
    
    # Build matrix
    z_values = []
    for gene in numeric_genes:
        gene_values = []
        for data in generation_data:
            gene_stats = data.get("gene_statistics", {}).get(gene, {})
            mean_val = gene_stats.get("mean", 0.5)
            gene_values.append(mean_val)
        z_values.append(gene_values)
    
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=[f"Gen {g}" for g in generations],
        y=[g.replace("_", " ").title() for g in numeric_genes],
        colorscale="RdYlGn",
        zmin=0,
        zmax=1,
    ))
    
    fig.update_layout(
        title="Gene Evolution Heatmap (Population Means)",
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
    )
    
    return fig


def create_agent_card(agent_data: dict, rank: Optional[int] = None) -> None:
    """Render an agent card in Streamlit."""
    dna = agent_data.get("dna", {})
    
    # Determine card color based on rank
    if rank == 1:
        border_color = "#fbbf24"  # Gold
    elif rank == 2:
        border_color = "#94a3b8"  # Silver
    elif rank == 3:
        border_color = "#cd7f32"  # Bronze
    else:
        border_color = NEUTRAL_COLOR
    
    # Card header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 🤖 {agent_data['id'][:12]}")
    with col2:
        if rank:
            st.metric("Rank", f"#{rank}")
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fitness", agent_data.get("fitness", 0))
    with col2:
        coop_rate = agent_data.get("total_cooperations", 0)
        total = coop_rate + agent_data.get("total_defections", 0)
        rate = coop_rate / total * 100 if total > 0 else 50
        st.metric("Coop Rate", f"{rate:.0f}%")
    with col3:
        st.metric("Generation", agent_data.get("generation", 0))
    
    # DNA traits
    with st.expander("DNA Traits"):
        col1, col2 = st.columns(2)
        with col1:
            st.progress(dna.get("cooperation_bias", 0.5), text=f"Cooperation: {dna.get('cooperation_bias', 0.5):.0%}")
            st.progress(dna.get("retaliation_sensitivity", 0.5), text=f"Retaliation: {dna.get('retaliation_sensitivity', 0.5):.0%}")
            st.progress(dna.get("forgiveness_rate", 0.5), text=f"Forgiveness: {dna.get('forgiveness_rate', 0.5):.0%}")
        with col2:
            st.progress(dna.get("memory_weight", 0.5), text=f"Memory: {dna.get('memory_weight', 0.5):.0%}")
            st.progress(dna.get("message_honesty", 0.5), text=f"Honesty: {dna.get('message_honesty', 0.5):.0%}")
            st.progress(dna.get("threat_frequency", 0.0), text=f"Threats: {dna.get('threat_frequency', 0.0):.0%}")
        
        keywords = dna.get("strategy_keywords", [])
        st.write(f"**Strategy:** {', '.join(keywords)}")
        st.write(f"**Reasoning:** {dna.get('reasoning_depth', 'medium')}")
    
    # Parent lineage
    parents = agent_data.get("parent_ids", [])
    if parents:
        st.caption(f"Parents: {', '.join(p[:8] for p in parents)}")
    
    st.divider()


def create_match_viewer(match_data: dict) -> None:
    """Render a match viewer in Streamlit."""
    st.subheader(f"Match: {match_data['agent1_id'][:8]} vs {match_data['agent2_id'][:8]}")
    
    # Score summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Agent 1 Score", match_data["agent1_total_score"])
    with col2:
        winner = match_data.get("winner_id")
        if winner:
            st.metric("Winner", winner[:8])
        else:
            st.metric("Result", "Tie")
    with col3:
        st.metric("Agent 2 Score", match_data["agent2_total_score"])
    
    # Round-by-round breakdown
    st.write("**Round History:**")
    
    for round_data in match_data.get("rounds", []):
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 2])
        
        with col1:
            st.write(f"R{round_data['round']}")
        
        with col2:
            move1 = round_data["agent1_move"]
            color1 = COOPERATE_COLOR if move1 == "COOPERATE" else DEFECT_COLOR
            st.markdown(f"<span style='color:{color1}'>{move1[0]}</span>", unsafe_allow_html=True)
        
        with col3:
            st.write(f"+{round_data['agent1_score']}")
        
        with col4:
            move2 = round_data["agent2_move"]
            color2 = COOPERATE_COLOR if move2 == "COOPERATE" else DEFECT_COLOR
            st.markdown(f"<span style='color:{color2}'>{move2[0]}</span>", unsafe_allow_html=True)
        
        with col5:
            st.write(f"+{round_data['agent2_score']}")


def create_strategy_radar(agent_data: dict) -> go.Figure:
    """Create a radar chart of agent traits."""
    dna = agent_data.get("dna", {})
    
    categories = [
        "Cooperation",
        "Retaliation",
        "Forgiveness",
        "Memory",
        "Honesty",
        "Aggression"
    ]
    
    values = [
        dna.get("cooperation_bias", 0.5),
        dna.get("retaliation_sensitivity", 0.5),
        dna.get("forgiveness_rate", 0.5),
        dna.get("memory_weight", 0.5),
        dna.get("message_honesty", 0.5),
        dna.get("threat_frequency", 0.0),
    ]
    
    # Close the radar
    values.append(values[0])
    categories.append(categories[0])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        fillcolor=f"rgba(34, 197, 94, 0.3)",
        line=dict(color=COOPERATE_COLOR),
        name=agent_data["id"][:8],
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
            ),
            bgcolor=BACKGROUND_COLOR,
        ),
        showlegend=False,
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        title=f"Strategy Profile: {agent_data['id'][:12]}",
    )
    
    return fig


def create_lineage_tree(generation_data: list[dict]) -> go.Figure:
    """Create a simple lineage visualization."""
    # Collect all agents and their relationships
    all_agents = {}
    edges = []
    
    for gen_data in generation_data:
        for agent in gen_data.get("agents", []):
            agent_id = agent["id"]
            gen = agent["generation"]
            all_agents[agent_id] = {"gen": gen, "fitness": agent.get("fitness", 0)}
            
            for parent_id in agent.get("parent_ids", []):
                if parent_id in all_agents:
                    edges.append((parent_id, agent_id))
    
    # Create node positions
    gen_counts = {}
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    
    for agent_id, info in all_agents.items():
        gen = info["gen"]
        if gen not in gen_counts:
            gen_counts[gen] = 0
        
        node_x.append(gen)
        node_y.append(gen_counts[gen])
        node_text.append(f"{agent_id[:8]}<br>Fitness: {info['fitness']}")
        node_color.append(info["fitness"])
        
        gen_counts[gen] += 1
    
    # Create edge traces
    edge_x = []
    edge_y = []
    
    for parent_id, child_id in edges:
        if parent_id in all_agents and child_id in all_agents:
            parent_idx = list(all_agents.keys()).index(parent_id)
            child_idx = list(all_agents.keys()).index(child_id)
            
            edge_x.extend([node_x[parent_idx], node_x[child_idx], None])
            edge_y.extend([node_y[parent_idx], node_y[child_idx], None])
    
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode="lines",
        line=dict(width=1, color=NEUTRAL_COLOR),
        hoverinfo="none",
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(
            size=20,
            color=node_color,
            colorscale="Viridis",
            showscale=True,
            colorbar=dict(title="Fitness"),
        ),
        text=[t.split("<br>")[0] for t in node_text],
        textposition="top center",
        hovertext=node_text,
        hoverinfo="text",
    ))
    
    fig.update_layout(
        title="Agent Lineage Tree",
        xaxis_title="Generation",
        yaxis_title="",
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
        showlegend=False,
        yaxis=dict(showticklabels=False),
    )
    
    return fig


# =============================================================================
# Live Tournament Components
# =============================================================================

def create_live_leaderboard(leaderboard: list[dict]) -> None:
    """Render a live updating leaderboard with personality info."""
    if not leaderboard:
        st.info("No agents yet...")
        return
    
    # Create a styled table
    for i, entry in enumerate(leaderboard[:8], 1):
        agent_id = entry.get("agent_id", "unknown")[:12]
        fitness = entry.get("fitness", 0)
        matches = entry.get("matches_played", 0)
        coop_rate = entry.get("cooperation_rate", 0.5)
        personality = entry.get("personality_description", "")
        
        # Determine style based on rank
        if i == 1:
            rank_emoji = "🥇"
        elif i == 2:
            rank_emoji = "🥈"
        elif i == 3:
            rank_emoji = "🥉"
        elif i <= 4:
            rank_emoji = "✅"
        else:
            rank_emoji = "❌"
        
        col1, col2, col3 = st.columns([1, 4, 2])
        
        with col1:
            st.write(f"{rank_emoji} **{i}**")
        with col2:
            st.write(f"`{agent_id}`")
            if personality:
                st.caption(f"_{personality}_")
        with col3:
            st.write(f"**{fitness}** pts")
            coop_pct = coop_rate * 100
            color = COOPERATE_COLOR if coop_pct >= 50 else DEFECT_COLOR
            st.markdown(f"<span style='color:{color};font-size:0.8em'>{coop_pct:.0f}% coop</span>", unsafe_allow_html=True)


def create_live_match_card(match: dict) -> None:
    """Render a compact match result card for live view."""
    agent1_id = match.get("agent1_id", "?")[:8]
    agent2_id = match.get("agent2_id", "?")[:8]
    score1 = match.get("agent1_score", 0)
    score2 = match.get("agent2_score", 0)
    winner_id = match.get("winner_id")
    a1_coop = match.get("agent1_cooperations", 0)
    a1_def = match.get("agent1_defections", 0)
    a2_coop = match.get("agent2_cooperations", 0)
    a2_def = match.get("agent2_defections", 0)
    
    # Determine winner styling
    if winner_id:
        if winner_id == match.get("agent1_id"):
            a1_style = f"color: {COOPERATE_COLOR}; font-weight: bold;"
            a2_style = f"color: {DEFECT_COLOR};"
            result = "🏆"
        else:
            a1_style = f"color: {DEFECT_COLOR};"
            a2_style = f"color: {COOPERATE_COLOR}; font-weight: bold;"
            result = "🏆"
    else:
        a1_style = "color: #fbbf24;"
        a2_style = "color: #fbbf24;"
        result = "🤝"
    
    st.markdown(f"""
    <div style="background: #374151; padding: 8px; border-radius: 6px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="{a1_style}">{agent1_id}</span>
            <span style="color: #9ca3af;">{score1} - {score2}</span>
            <span style="{a2_style}">{agent2_id}</span>
        </div>
        <div style="font-size: 0.75em; color: #6b7280; margin-top: 4px;">
            {a1_coop}C/{a1_def}D vs {a2_coop}C/{a2_def}D
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_cooperation_gauge(cooperation_rate: float) -> None:
    """Create a gauge showing cooperation rate."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cooperation_rate * 100,
        title={"text": "Cooperation Rate"},
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": COOPERATE_COLOR if cooperation_rate >= 0.5 else DEFECT_COLOR},
            "bgcolor": BACKGROUND_COLOR,
            "steps": [
                {"range": [0, 30], "color": "rgba(239, 68, 68, 0.3)"},
                {"range": [30, 70], "color": "rgba(251, 191, 36, 0.3)"},
                {"range": [70, 100], "color": "rgba(34, 197, 94, 0.3)"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 2},
                "thickness": 0.75,
                "value": 50,
            },
        },
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor=BACKGROUND_COLOR,
        font=dict(color="white"),
    )
    
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# AI Thinking Display Components
# =============================================================================

def create_thinking_display(round_data: dict, agent_num: int = 1) -> None:
    """Display an agent's thinking process for a round."""
    prefix = f"agent{agent_num}_"
    
    agent_id = round_data.get(f"{prefix}id", "?")[:8]
    move = round_data.get(f"{prefix}move", "?")
    thinking = round_data.get(f"{prefix}thinking", "No thinking recorded")
    message = round_data.get(f"{prefix}message", "none")
    score = round_data.get(f"{prefix}score", 0)
    
    move_color = COOPERATE_COLOR if move == "COOPERATE" else DEFECT_COLOR
    move_emoji = "🤝" if move == "COOPERATE" else "🗡️"
    
    st.markdown(f"""
    <div style="background: #374151; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid {move_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: bold; color: white;">{agent_id}</span>
            <span style="color: {move_color}; font-weight: bold;">{move_emoji} {move} (+{score})</span>
        </div>
        <div style="color: #9ca3af; font-size: 0.9em; font-style: italic; margin-bottom: 6px;">
            💭 "{thinking[:200]}{"..." if len(thinking) > 200 else ""}"
        </div>
        <div style="color: #6b7280; font-size: 0.8em;">
            💬 Message: "{message if message else 'none'}"
        </div>
    </div>
    """, unsafe_allow_html=True)


def create_round_display(round_data: dict) -> None:
    """Display a complete round with both agents' thinking."""
    round_num = round_data.get("round", "?")
    
    st.markdown(f"### Round {round_num}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        create_thinking_display(round_data, agent_num=1)
    
    with col2:
        create_thinking_display(round_data, agent_num=2)
    
    # Show outcome
    move1 = round_data.get("agent1_move", "?")
    move2 = round_data.get("agent2_move", "?")
    score1 = round_data.get("agent1_score", 0)
    score2 = round_data.get("agent2_score", 0)
    
    if move1 == "COOPERATE" and move2 == "COOPERATE":
        outcome = "🤝 Mutual Cooperation"
        outcome_color = COOPERATE_COLOR
    elif move1 == "DEFECT" and move2 == "DEFECT":
        outcome = "💥 Mutual Defection"
        outcome_color = DEFECT_COLOR
    elif move1 == "DEFECT":
        outcome = f"🗡️ Agent 1 exploited Agent 2"
        outcome_color = "#fbbf24"
    else:
        outcome = f"🗡️ Agent 2 exploited Agent 1"
        outcome_color = "#fbbf24"
    
    st.markdown(f"<div style='text-align: center; color: {outcome_color}; padding: 8px;'>{outcome} ({score1} - {score2})</div>", unsafe_allow_html=True)


def create_personality_radar_multi(agents_data: list[dict], title: str = "Personality Comparison") -> go.Figure:
    """Create a radar chart comparing multiple agent personalities."""
    traits = [
        "trust", "forgiveness", "vengefulness", "risk_tolerance",
        "patience", "empathy", "honesty", "aggression"
    ]
    
    fig = go.Figure()
    
    colors = [COOPERATE_COLOR, DEFECT_COLOR, "#3b82f6", "#fbbf24", "#8b5cf6"]
    
    for i, agent in enumerate(agents_data[:5]):
        personality = agent.get("personality", agent.get("dna", {}))
        
        values = [personality.get(t, 0.5) for t in traits]
        values.append(values[0])  # Close the radar
        
        agent_id = agent.get("id", f"Agent {i+1}")[:12]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[t.replace("_", " ").title() for t in traits] + [traits[0].replace("_", " ").title()],
            fill="toself",
            name=agent_id,
            line=dict(color=colors[i % len(colors)]),
            fillcolor=f"rgba{tuple(list(int(colors[i % len(colors)].lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.2])}",
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
            ),
            bgcolor=BACKGROUND_COLOR,
        ),
        showlegend=True,
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        title=title,
    )
    
    return fig


def create_trait_evolution_chart(generation_data: list[dict], trait: str) -> go.Figure:
    """Create a chart showing how a specific trait evolved over generations."""
    generations = []
    means = []
    mins = []
    maxs = []
    
    for data in generation_data:
        gen = data.get("generation", 0)
        trait_stats = data.get("gene_statistics", {}).get(trait, {})
        
        if trait_stats:
            generations.append(gen)
            means.append(trait_stats.get("mean", 0.5))
            mins.append(trait_stats.get("min", 0))
            maxs.append(trait_stats.get("max", 1))
    
    fig = go.Figure()
    
    # Add range band
    fig.add_trace(go.Scatter(
        x=generations + generations[::-1],
        y=maxs + mins[::-1],
        fill="toself",
        fillcolor="rgba(59, 130, 246, 0.2)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Range",
        showlegend=False,
    ))
    
    # Add mean line
    fig.add_trace(go.Scatter(
        x=generations,
        y=means,
        mode="lines+markers",
        name=f"{trait.replace('_', ' ').title()} (mean)",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=8),
    ))
    
    # Add neutral line
    fig.add_hline(y=0.5, line_dash="dash", line_color=NEUTRAL_COLOR, annotation_text="Neutral")
    
    fig.update_layout(
        title=f"{trait.replace('_', ' ').title()} Evolution",
        xaxis_title="Generation",
        yaxis_title="Value",
        yaxis=dict(range=[0, 1]),
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
    )
    
    return fig


def create_evolution_summary_card(gen0_stats: dict, final_stats: dict) -> None:
    """Display a summary of how evolution changed the population."""
    st.subheader("🧬 Evolution Summary")
    
    # Calculate biggest changes
    changes = []
    for trait in gen0_stats:
        if trait in final_stats:
            gen0_mean = gen0_stats[trait].get("mean", 0.5)
            final_mean = final_stats[trait].get("mean", 0.5)
            change = final_mean - gen0_mean
            changes.append({
                "trait": trait,
                "gen0": gen0_mean,
                "final": final_mean,
                "change": change,
            })
    
    # Sort by absolute change
    changes.sort(key=lambda x: abs(x["change"]), reverse=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Traits that INCREASED:**")
        for c in changes:
            if c["change"] > 0.05:
                st.markdown(f"- {c['trait'].replace('_', ' ').title()}: {c['gen0']:.0%} → {c['final']:.0%} (+{c['change']:.0%})")
    
    with col2:
        st.markdown("**Traits that DECREASED:**")
        for c in changes:
            if c["change"] < -0.05:
                st.markdown(f"- {c['trait'].replace('_', ' ').title()}: {c['gen0']:.0%} → {c['final']:.0%} ({c['change']:.0%})")
