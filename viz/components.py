"""Reusable UI components for the AI r/place Streamlit dashboard."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
from typing import Any, Optional
import streamlit as st

from src.config import COLOR_HEX, BACKGROUND_COLOR


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
        rankings = data.get("statistics", {}).get("agent_rankings", [])
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
        line=dict(color="#22c55e", width=2),
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
        line=dict(color="#ef4444", width=2),
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


def create_territory_chart(generation_data: list[dict]) -> go.Figure:
    """Create a chart showing territory distribution over generations."""
    generations = [d["generation"] for d in generation_data]
    
    # Get all agent colors across generations
    all_colors = set()
    for data in generation_data:
        rankings = data.get("statistics", {}).get("agent_rankings", [])
        for r in rankings:
            all_colors.add(r.get("color", "red"))
    
    fig = go.Figure()
    
    for color in all_colors:
        territories = []
        for data in generation_data:
            rankings = data.get("statistics", {}).get("agent_rankings", [])
            color_territory = sum(r.get("territory", 0) for r in rankings if r.get("color") == color)
            territories.append(color_territory)
        
        fig.add_trace(go.Scatter(
            x=generations,
            y=territories,
            mode="lines+markers",
            name=color.title(),
            line=dict(color=COLOR_HEX.get(color, "#666"), width=2),
            marker=dict(size=6),
        ))
    
    fig.update_layout(
        title="Territory by Color Over Generations",
        xaxis_title="Generation",
        yaxis_title="Pixels Owned",
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
    )
    
    return fig


def create_trait_heatmap(generation_data: list[dict]) -> go.Figure:
    """Create a heatmap showing trait evolution over generations."""
    traits = [
        "territoriality",
        "aggression", 
        "creativity",
        "cooperation",
        "exploration",
        "color_loyalty",
    ]
    
    generations = [d["generation"] for d in generation_data]
    
    # Build matrix
    z_values = []
    for trait in traits:
        trait_values = []
        for data in generation_data:
            trait_stats = data.get("gene_statistics", {}).get(trait, {})
            mean_val = trait_stats.get("mean", 0.5)
            trait_values.append(mean_val)
        z_values.append(trait_values)
    
    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=[f"Gen {g}" for g in generations],
        y=[t.replace("_", " ").title() for t in traits],
        colorscale="RdYlGn",
        zmin=0,
        zmax=1,
    ))
    
    fig.update_layout(
        title="Trait Evolution Heatmap (Population Means)",
        template="plotly_dark",
        paper_bgcolor=BACKGROUND_COLOR,
        plot_bgcolor=BACKGROUND_COLOR,
    )
    
    return fig


def create_agent_card(agent_data: dict, rank: Optional[int] = None) -> None:
    """Render an agent card in Streamlit."""
    personality = agent_data.get("personality", {})
    color = personality.get("preferred_color", "red")
    
    # Determine card color based on rank
    if rank == 1:
        border_color = "#fbbf24"  # Gold
    elif rank == 2:
        border_color = "#94a3b8"  # Silver
    elif rank == 3:
        border_color = "#cd7f32"  # Bronze
    else:
        border_color = "#6b7280"
    
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
        st.metric("Pixels Placed", agent_data.get("pixels_placed", 0))
    with col3:
        st.metric("Generation", agent_data.get("generation", 0))
    
    # Color indicator
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin: 8px 0;">
        <span style="color: {COLOR_HEX.get(color, '#666')}; font-size: 24px; margin-right: 8px;">●</span>
        <span style="color: white;">{color.title()}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Personality traits
    with st.expander("Personality Traits"):
        col1, col2 = st.columns(2)
        with col1:
            st.progress(personality.get("territoriality", 0.5), text=f"Territoriality: {personality.get('territoriality', 0.5):.0%}")
            st.progress(personality.get("aggression", 0.5), text=f"Aggression: {personality.get('aggression', 0.5):.0%}")
            st.progress(personality.get("creativity", 0.5), text=f"Creativity: {personality.get('creativity', 0.5):.0%}")
        with col2:
            st.progress(personality.get("cooperation", 0.5), text=f"Cooperation: {personality.get('cooperation', 0.5):.0%}")
            st.progress(personality.get("exploration", 0.5), text=f"Exploration: {personality.get('exploration', 0.5):.0%}")
            st.progress(personality.get("color_loyalty", 0.5), text=f"Color Loyalty: {personality.get('color_loyalty', 0.5):.0%}")
        
        goal = personality.get("loose_goal")
        if goal:
            st.write(f"**Goal:** {goal}")
    
    # Parent lineage
    parents = agent_data.get("parent_ids", [])
    if parents:
        st.caption(f"Parents: {', '.join(p[:8] for p in parents)}")
    
    st.divider()


def create_strategy_radar(agent_data: dict) -> go.Figure:
    """Create a radar chart of agent traits."""
    personality = agent_data.get("personality", {})
    
    categories = [
        "Territoriality",
        "Aggression",
        "Creativity",
        "Cooperation",
        "Exploration",
        "Color Loyalty"
    ]
    
    values = [
        personality.get("territoriality", 0.5),
        personality.get("aggression", 0.5),
        personality.get("creativity", 0.5),
        personality.get("cooperation", 0.5),
        personality.get("exploration", 0.5),
        personality.get("color_loyalty", 0.5),
    ]
    
    # Close the radar
    values.append(values[0])
    categories.append(categories[0])
    
    color = personality.get("preferred_color", "blue")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill="toself",
        fillcolor=f"rgba{tuple(list(int(COLOR_HEX.get(color, '#3b82f6').lstrip('#')[j:j+2], 16) for j in (0, 2, 4)) + [0.3])}",
        line=dict(color=COLOR_HEX.get(color, "#3b82f6")),
        name=agent_data.get("id", "Agent")[:8],
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
        title=f"Strategy Profile: {agent_data.get('id', 'Agent')[:12]}",
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
            color = agent.get("personality", {}).get("preferred_color", "blue")
            all_agents[agent_id] = {
                "gen": gen,
                "fitness": agent.get("fitness", 0),
                "color": color,
            }
            
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
        node_text.append(f"{agent_id[:8]}<br>Fitness: {info['fitness']}<br>Color: {info['color']}")
        node_color.append(COLOR_HEX.get(info["color"], "#666"))
        
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
        line=dict(width=1, color="#6b7280"),
        hoverinfo="none",
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        marker=dict(
            size=20,
            color=node_color,
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


def create_fill_rate_gauge(fill_rate: float) -> go.Figure:
    """Create a gauge showing canvas fill rate."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fill_rate * 100,
        title={"text": "Canvas Fill Rate", "font": {"size": 14, "color": "#94a3b8"}},
        number={"suffix": "%", "font": {"size": 32, "color": "white"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#64748b"},
            "bar": {"color": "#22c55e" if fill_rate >= 0.5 else "#eab308"},
            "bgcolor": "#1e293b",
            "bordercolor": "#334155",
            "steps": [
                {"range": [0, 33], "color": "rgba(239, 68, 68, 0.1)"},
                {"range": [33, 66], "color": "rgba(234, 179, 8, 0.1)"},
                {"range": [66, 100], "color": "rgba(34, 197, 94, 0.1)"},
            ],
        },
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
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
    fig.add_hline(y=0.5, line_dash="dash", line_color="#6b7280", annotation_text="Neutral")
    
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


def create_personality_radar_multi(agents_data: list[dict], title: str = "Personality Comparison") -> go.Figure:
    """Create a radar chart comparing multiple agent personalities."""
    traits = [
        "territoriality", "aggression", "creativity",
        "cooperation", "exploration", "color_loyalty"
    ]
    
    fig = go.Figure()
    
    for i, agent in enumerate(agents_data[:5]):
        personality = agent.get("personality", {})
        color = personality.get("preferred_color", "blue")
        
        values = [personality.get(t, 0.5) for t in traits]
        values.append(values[0])  # Close the radar
        
        agent_id = agent.get("id", f"Agent {i+1}")[:12]
        hex_color = COLOR_HEX.get(color, "#3b82f6")
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[t.replace("_", " ").title() for t in traits] + [traits[0].replace("_", " ").title()],
            fill="toself",
            name=agent_id,
            line=dict(color=hex_color),
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
