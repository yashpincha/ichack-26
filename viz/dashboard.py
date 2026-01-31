"""Streamlit dashboard for AI r/place simulation visualization."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Page config
st.set_page_config(
    page_title="AI r/place",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import LOGS_DIR, COLOR_HEX
from src.live_state import read_live_state, LiveState

# =============================================================================
# CSS Styling
# =============================================================================

st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom card styling */
    .agent-card {
        background: rgba(30, 41, 59, 0.8);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
    }
    
    .status-running { background: #22c55e20; color: #22c55e; }
    .status-evolving { background: #eab30820; color: #eab308; }
    .status-complete { background: #3b82f620; color: #3b82f6; }
    
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.3), transparent);
        margin: 24px 0;
    }
    
    .pixel-grid {
        display: grid;
        gap: 1px;
        background: #1e293b;
        padding: 4px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Data Loading
# =============================================================================

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


# =============================================================================
# Grid Visualization
# =============================================================================

def create_grid_figure(grid_pixels: list[list[dict]], width: int, height: int) -> go.Figure:
    """Create a Plotly heatmap figure for the grid."""
    # Create color matrix
    z = []
    customdata = []
    
    color_to_num = {
        "empty": 0,
        "red": 1,
        "blue": 2,
        "green": 3,
        "yellow": 4,
        "purple": 5,
        "orange": 6,
        "cyan": 7,
        "pink": 8,
    }
    
    colors = [
        COLOR_HEX.get("empty", "#1f2937"),
        COLOR_HEX.get("red", "#ef4444"),
        COLOR_HEX.get("blue", "#3b82f6"),
        COLOR_HEX.get("green", "#22c55e"),
        COLOR_HEX.get("yellow", "#eab308"),
        COLOR_HEX.get("purple", "#a855f7"),
        COLOR_HEX.get("orange", "#f97316"),
        COLOR_HEX.get("cyan", "#06b6d4"),
        COLOR_HEX.get("pink", "#ec4899"),
    ]
    
    for row in grid_pixels:
        z_row = []
        data_row = []
        for pixel in row:
            color = pixel.get("color", "empty")
            owner = pixel.get("owner_id", "")
            z_row.append(color_to_num.get(color, 0))
            data_row.append(f"{color}<br>Owner: {owner[:8] if owner else 'none'}")
        z.append(z_row)
        customdata.append(data_row)
    
    fig = go.Figure(data=go.Heatmap(
        z=z,
        customdata=customdata,
        hovertemplate="%{customdata}<extra></extra>",
        colorscale=[[i/8, c] for i, c in enumerate(colors)],
        showscale=False,
        xgap=1,
        ygap=1,
    ))
    
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#1e293b",
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, autorange="reversed"),
    )
    
    return fig


# =============================================================================
# Main App
# =============================================================================

def main():
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 40px 0;">
        <h1 style="font-size: 3rem; margin: 0; color: white;">
            ⚔️ Shape Battle
        </h1>
        <p style="font-size: 1.2rem; color: #64748b; margin-top: 8px;">
            Watch AI agents compete to draw their shapes on the canvas!
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    live_state = read_live_state()
    all_data = load_generation_data()
    
    # Check if running
    is_running = live_state and live_state.status in ["running", "evolving"]
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🔴 LIVE", "📊 Results", "🧬 Evolution"])
    
    with tab1:
        show_live_view(live_state)
    
    with tab2:
        show_results_view(all_data)
    
    with tab3:
        show_evolution_view(all_data)
    
    # Auto-refresh if running
    if is_running:
        time.sleep(2)
        st.rerun()


# =============================================================================
# LIVE VIEW
# =============================================================================

def show_live_view(live_state: Optional[LiveState]):
    """Live canvas view."""
    if not live_state or live_state.status == "idle":
        show_waiting_state()
        return
    
    # Status header
    status_class = f"status-{live_state.status}"
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <span class="status-badge {status_class}">{live_state.status.upper()}</span>
        <span style="color: #64748b;">Generation {live_state.generation} | Turn {live_state.turn}/{live_state.total_turns}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress
    progress = live_state.progress_percent / 100
    st.progress(progress)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Main content - grid and leaderboard
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🖼️ Canvas")
        if live_state.grid_pixels:
            fig = create_grid_figure(
                live_state.grid_pixels,
                live_state.grid_width,
                live_state.grid_height,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Canvas loading...")
    
    with col2:
        st.markdown("### ⚔️ Shape Battle")
        show_leaderboard(live_state.leaderboard)
        
        st.markdown("### 📊 Battle Stats")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Canvas Fill", f"{live_state.fill_rate:.0%}")
        with col_b:
            st.metric("Total Moves", live_state.total_pixels_placed)
    
    # Recent activity
    if live_state.recent_turns:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("### ⚡ Battle Log")
        for turn in live_state.recent_turns[-5:]:
            agent_id = turn.get("agent_id", "?")[:8]
            color = turn.get("color", "?")
            x, y = turn.get("x", 0), turn.get("y", 0)
            thinking = turn.get("thinking", "")[:60]
            overwrote = turn.get("overwrote")
            
            if overwrote:
                action = "⚔️ ATTACKED"
                action_color = "#ef4444"
                target_text = f"(destroyed {overwrote[:6]}'s pixel)"
            else:
                action = "🔨 BUILD"
                action_color = "#22c55e"
                target_text = ""
            
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.5); padding: 8px 12px; border-radius: 8px; margin: 4px 0; border-left: 3px solid {COLOR_HEX.get(color, '#666')};">
                <span style="color: {action_color}; font-weight: 600;">{action}</span>
                <span style="color: white; margin: 0 8px;">{agent_id}</span>
                <span style="color: #64748b;">→ ({x},{y})</span>
                <span style="color: #ef4444; font-size: 12px; margin-left: 8px;">{target_text}</span>
                <div style="color: #64748b; font-size: 12px; font-style: italic; margin-top: 4px;">{thinking}...</div>
            </div>
            """, unsafe_allow_html=True)


def show_waiting_state():
    """Show when no simulation is running."""
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 20px;">⚔️</div>
        <h2 style="color: white; margin-bottom: 16px;">No Battle Running</h2>
        <p style="color: #64748b; max-width: 400px; margin: 0 auto 24px auto;">
            Start a Shape Battle to watch AI agents compete to draw their shapes!
        </p>
        <code style="background: #1e293b; padding: 12px 20px; border-radius: 8px; color: #22c55e;">
            python main.py simulate --live
        </code>
    </div>
    """, unsafe_allow_html=True)


def show_leaderboard(leaderboard: list[dict]):
    """Display agent leaderboard with shape completion."""
    if not leaderboard:
        st.info("Waiting for data...")
        return
    
    for i, entry in enumerate(leaderboard[:4], 1):
        agent_id = entry.get("agent_id", "?")[:10]
        color = entry.get("color", "red")
        territory = entry.get("territory", 0)
        personality = entry.get("personality", "")
        shape = entry.get("shape", "?")
        shape_completion = entry.get("shape_completion", {})
        completion_pct = shape_completion.get("percentage", 0) if shape_completion else 0
        
        if i == 1:
            rank_icon = "🏆"
            bg = "rgba(34, 197, 94, 0.1)"
            border = "#22c55e"
        elif i == 2:
            rank_icon = "🥈"
            bg = "rgba(148, 163, 184, 0.1)"
            border = "#94a3b8"
        elif i == 3:
            rank_icon = "🥉"
            bg = "rgba(205, 127, 50, 0.1)"
            border = "#cd7f32"
        else:
            rank_icon = str(i)
            bg = "rgba(239, 68, 68, 0.05)"
            border = "#ef4444"
        
        st.markdown(f"""
        <div style="background: {bg}; border-left: 3px solid {border}; padding: 12px 16px; margin: 8px 0; border-radius: 0 8px 8px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 20px; margin-right: 8px;">{rank_icon}</span>
                    <span style="color: white; font-weight: 600;">{shape}</span>
                    <span style="color: {COLOR_HEX.get(color, '#666')}; margin-left: 8px;">●</span>
                </div>
                <div style="text-align: right;">
                    <span style="color: white; font-weight: 700; font-size: 18px;">{completion_pct:.0f}%</span>
                </div>
            </div>
            <div style="margin-top: 6px;">
                <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 6px; overflow: hidden;">
                    <div style="background: {COLOR_HEX.get(color, '#666')}; width: {completion_pct}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# RESULTS VIEW
# =============================================================================

def show_results_view(all_data: list[dict]):
    """Show Shape Battle results."""
    if not all_data:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px; margin-bottom: 20px;">⚔️</div>
            <h2 style="color: white;">No Battle Results Yet</h2>
            <p style="color: #64748b;">Run a Shape Battle simulation to see results here.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Generation selector
    gen_options = [f"Generation {d.get('generation', i)}" for i, d in enumerate(all_data)]
    selected = st.selectbox("Select Generation", gen_options, index=len(gen_options)-1)
    selected_idx = gen_options.index(selected)
    gen_data = all_data[selected_idx]
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Show final grid if available
    if "result" in gen_data and gen_data["result"].get("final_grid"):
        grid_data = gen_data["result"]["final_grid"]
        pixels = grid_data.get("pixels", [])
        
        # Convert to expected format
        grid_pixels = []
        for row in pixels:
            grid_pixels.append([{"color": p.get("color", "empty"), "owner_id": p.get("owner_id")} for p in row])
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Battle Canvas")
            fig = create_grid_figure(grid_pixels, grid_data.get("width", 32), grid_data.get("height", 32))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 🏆 Winner")
            rankings = gen_data.get("statistics", {}).get("agent_rankings", [])
            if rankings:
                winner = rankings[0]
                shape = winner.get("shape", "?")
                shape_comp = winner.get("shape_completion", {})
                completion_pct = shape_comp.get("percentage", 0) if shape_comp else 0
                completed = shape_comp.get("completed", 0) if shape_comp else 0
                total = shape_comp.get("total", 0) if shape_comp else 0
                
                st.markdown(f"""
                <div class="agent-card" style="text-align: center; background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));">
                    <div style="font-size: 48px;">🏆</div>
                    <h2 style="color: #22c55e; margin: 12px 0 4px 0; text-transform: capitalize;">{shape}</h2>
                    <div style="color: {COLOR_HEX.get(winner.get('color', 'red'), '#666')}; font-size: 24px;">●</div>
                    <div style="font-size: 32px; color: white; margin: 12px 0;">{completion_pct:.0f}%</div>
                    <div style="color: #64748b; font-size: 14px;">{completed}/{total} pixels</div>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 8px; margin: 12px 0; overflow: hidden;">
                        <div style="background: #22c55e; width: {completion_pct}%; height: 100%;"></div>
                    </div>
                    <div style="color: #64748b; font-size: 12px;">{winner.get('agent_id', '?')[:12]}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # All agents table
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("### Battle Standings")
    
    rankings = gen_data.get("statistics", {}).get("agent_rankings", [])
    for ranking in rankings:
        color = ranking.get("color", "red")
        shape = ranking.get("shape", "?")
        shape_comp = ranking.get("shape_completion", {})
        completion_pct = shape_comp.get("percentage", 0) if shape_comp else 0
        completed = shape_comp.get("completed", 0) if shape_comp else 0
        total = shape_comp.get("total", 0) if shape_comp else 0
        
        rank = ranking.get("rank", "?")
        rank_icon = "🏆" if rank == 1 else f"#{rank}"
        
        st.markdown(f"""
        <div class="agent-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 20px; margin-right: 8px;">{rank_icon}</span>
                    <span style="color: white; font-size: 18px; font-weight: 600; text-transform: capitalize;">{shape}</span>
                    <span style="color: {COLOR_HEX.get(color, '#666')}; margin-left: 8px; font-size: 20px;">●</span>
                    <div style="color: #64748b; margin-top: 4px; font-size: 12px;">{ranking.get('agent_id', '?')[:12]} - {ranking.get('personality', '')}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: white; font-size: 24px; font-weight: bold;">{completion_pct:.0f}%</div>
                    <div style="color: #64748b; font-size: 12px;">{completed}/{total} pixels</div>
                </div>
            </div>
            <div style="margin-top: 8px;">
                <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 6px; overflow: hidden;">
                    <div style="background: {COLOR_HEX.get(color, '#666')}; width: {completion_pct}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# EVOLUTION VIEW
# =============================================================================

def show_evolution_view(all_data: list[dict]):
    """Show evolution analysis."""
    if len(all_data) < 2:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px; margin-bottom: 20px;">🧬</div>
            <h2 style="color: white;">Need More Generations</h2>
            <p style="color: #64748b;">Run at least 2 generations to see evolution analysis.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    first_gen = all_data[0]
    last_gen = all_data[-1]
    
    first_stats = first_gen.get("gene_statistics", {})
    last_stats = last_gen.get("gene_statistics", {})
    
    st.markdown(f"### Evolution: Generation 0 → {last_gen.get('generation', len(all_data)-1)}")
    
    # Calculate changes
    traits = ["territoriality", "aggression", "creativity", "cooperation", "exploration", "color_loyalty"]
    changes = []
    
    for trait in traits:
        if trait in first_stats and trait in last_stats:
            gen0 = first_stats[trait].get("mean", 0.5)
            final = last_stats[trait].get("mean", 0.5)
            change = final - gen0
            changes.append({
                "trait": trait.replace("_", " ").title(),
                "gen0": gen0,
                "final": final,
                "change": change,
            })
    
    changes.sort(key=lambda x: abs(x["change"]), reverse=True)
    
    # Key insight
    if changes:
        biggest = changes[0]
        direction = "increased" if biggest["change"] > 0 else "decreased"
        
        st.markdown(f"""
        <div class="agent-card" style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));">
            <h3 style="color: #3b82f6; margin-top: 0;">🔬 Key Finding</h3>
            <p style="color: white; font-size: 18px; margin: 12px 0;">
                <strong>{biggest['trait']}</strong> {direction} the most: 
                {biggest['gen0']:.0%} → {biggest['final']:.0%}
            </p>
            <p style="color: #64748b;">
                Evolution selected for agents with {'higher' if biggest['change'] > 0 else 'lower'} {biggest['trait'].lower()}.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Trait evolution chart
    st.markdown("### Trait Evolution")
    
    # Build data for chart
    chart_data = []
    for gen_idx, gen_data in enumerate(all_data):
        gen_stats = gen_data.get("gene_statistics", {})
        for trait in traits:
            if trait in gen_stats:
                chart_data.append({
                    "Generation": gen_idx,
                    "Trait": trait.replace("_", " ").title(),
                    "Value": gen_stats[trait].get("mean", 0.5),
                })
    
    if chart_data:
        import pandas as pd
        df = pd.DataFrame(chart_data)
        fig = px.line(
            df, x="Generation", y="Value", color="Trait",
            title="Trait Evolution Over Generations",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30, 41, 59, 0.5)",
            font=dict(color="white"),
            yaxis=dict(range=[0, 1]),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Color distribution
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("### Color Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Generation 0**")
        gen0_colors = first_stats.get("color_distribution", {})
        for color, count in gen0_colors.items():
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin: 4px 0;">
                <span style="color: {COLOR_HEX.get(color, '#666')}; font-size: 20px; margin-right: 8px;">●</span>
                <span style="color: white;">{color}: {count}</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**Generation {last_gen.get('generation', len(all_data)-1)}**")
        final_colors = last_stats.get("color_distribution", {})
        for color, count in final_colors.items():
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin: 4px 0;">
                <span style="color: {COLOR_HEX.get(color, '#666')}; font-size: 20px; margin-right: 8px;">●</span>
                <span style="color: white;">{color}: {count}</span>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
