"""Clean, demo-ready Streamlit dashboard for DarwinLM."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional
import streamlit as st
import plotly.graph_objects as go

# Page config - clean minimal setup
st.set_page_config(
    page_title="DarwinLM",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import LOGS_DIR
from src.live_state import read_live_state, LiveState

# =============================================================================
# Clean CSS Styling
# =============================================================================

st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Hide default streamlit elements */
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
    
    .thinking-bubble {
        background: rgba(59, 130, 246, 0.1);
        border-left: 4px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 0 12px 12px 0;
        margin: 8px 0;
        font-style: italic;
        color: #94a3b8;
        font-size: 14px;
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
    
    .lie-badge {
        background: #ef444430;
        color: #ef4444;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 8px;
    }
    
    .move-cooperate { color: #22c55e; font-weight: bold; }
    .move-defect { color: #ef4444; font-weight: bold; }
    
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.3), transparent);
        margin: 24px 0;
    }
    
    .interaction-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 16px;
        margin: 12px 0;
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
# Main App
# =============================================================================

def main():
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 40px 0;">
        <h1 style="font-size: 3rem; margin: 0; color: white;">
            🧬 DarwinLM
        </h1>
        <p style="font-size: 1.2rem; color: #64748b; margin-top: 8px;">
            Watch AI personalities evolve through the Prisoner's Dilemma
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    live_state = read_live_state()
    all_data = load_generation_data()
    
    # Navigation tabs - 4 tabs now
    tab1, tab2, tab3, tab4 = st.tabs(["🔴 LIVE", "💬 Interactions", "📊 Results", "🧬 Evolution"])
    
    with tab1:
        show_live_view(live_state)
    
    with tab2:
        show_interactions_view(live_state)
    
    with tab3:
        show_results_view(all_data)
    
    with tab4:
        show_evolution_view(all_data)


# =============================================================================
# LIVE VIEW
# =============================================================================

def show_live_view(live_state: Optional[LiveState]):
    """Clean live tournament view."""
    
    if not live_state or live_state.status == "idle":
        show_waiting_state()
        return
    
    # Status header
    status_class = f"status-{live_state.status}"
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <span class="status-badge {status_class}">{live_state.status.upper()}</span>
        <span style="color: #64748b;">Generation {live_state.generation}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress
    progress = live_state.progress_percent / 100
    st.progress(progress)
    st.markdown(f"<p style='text-align: center; color: #64748b;'>Match {live_state.match_number} of {live_state.total_matches}</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Main content - two columns
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 🏆 Leaderboard")
        show_leaderboard(live_state.leaderboard)
    
    with col2:
        st.markdown("### 📊 Stats")
        show_live_stats(live_state)
    
    # Recent match with AI thinking
    if live_state.recent_matches:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("### 🎮 Latest Match")
        show_latest_match(live_state.recent_matches[0])
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()


def show_waiting_state():
    """Show when no tournament is running."""
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 20px;">⏳</div>
        <h2 style="color: white; margin-bottom: 16px;">No Tournament Running</h2>
        <p style="color: #64748b; max-width: 400px; margin: 0 auto 24px auto;">
            Start a tournament to watch AI agents with random personalities 
            compete and evolve over generations.
        </p>
        <code style="background: #1e293b; padding: 12px 20px; border-radius: 8px; color: #22c55e;">
            python main.py evolve --generations 3 --live
        </code>
    </div>
    """, unsafe_allow_html=True)


def show_leaderboard(leaderboard: list[dict]):
    """Clean leaderboard display with lie counts."""
    if not leaderboard:
        st.info("Waiting for first match...")
        return
    
    for i, entry in enumerate(leaderboard[:4], 1):
        agent_id = entry.get("agent_id", "?")[:10]
        fitness = entry.get("fitness", 0)
        personality = entry.get("personality_description", "")
        lies = entry.get("lies_told", 0)
        
        # Rank styling
        if i == 1:
            rank_icon = "🥇"
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
            rank_icon = "4"
            bg = "rgba(239, 68, 68, 0.05)"
            border = "#ef4444"
        
        lie_badge = f'<span class="lie-badge">🤥 {lies} lies</span>' if lies > 0 else ''
        
        st.markdown(f"""
        <div style="
            background: {bg};
            border-left: 3px solid {border};
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 0 8px 8px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div>
                <span style="font-size: 20px; margin-right: 12px;">{rank_icon}</span>
                <span style="color: white; font-weight: 600;">{agent_id}</span>
                <span style="color: #64748b; font-size: 12px; margin-left: 8px;">{personality}</span>
                {lie_badge}
            </div>
            <div style="text-align: right;">
                <span style="color: white; font-weight: 700; font-size: 18px;">{fitness}</span>
                <span style="color: #64748b; font-size: 12px;"> pts</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def show_live_stats(live_state: LiveState):
    """Show live statistics including lies."""
    coop_rate = live_state.cooperation_rate * 100 if live_state.cooperation_rate else 0
    
    # Cooperation gauge
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=coop_rate,
        title={"text": "Cooperation Rate", "font": {"size": 14, "color": "#64748b"}},
        number={"suffix": "%", "font": {"size": 32, "color": "white"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#64748b"},
            "bar": {"color": "#22c55e" if coop_rate >= 50 else "#ef4444"},
            "bgcolor": "#1e293b",
            "bordercolor": "#334155",
            "steps": [
                {"range": [0, 50], "color": "rgba(239, 68, 68, 0.1)"},
                {"range": [50, 100], "color": "rgba(34, 197, 94, 0.1)"},
            ],
        },
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Quick stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Mutual Coop", live_state.mutual_cooperations)
    with col2:
        st.metric("Mutual Defect", live_state.mutual_defections)
    with col3:
        st.metric("🤥 Total Lies", live_state.total_lies)


def show_latest_match(match: dict):
    """Show the latest match with lie info."""
    a1_id = match.get("agent1_id", "?")[:10]
    a2_id = match.get("agent2_id", "?")[:10]
    a1_score = match.get("agent1_score", 0)
    a2_score = match.get("agent2_score", 0)
    a1_desc = match.get("agent1_description", "")
    a2_desc = match.get("agent2_description", "")
    a1_lies = match.get("agent1_lies", 0)
    a2_lies = match.get("agent2_lies", 0)
    winner = match.get("winner_id")
    
    # Determine winner styling
    if winner == match.get("agent1_id"):
        a1_style = "color: #22c55e; font-weight: bold;"
        a2_style = "color: #ef4444;"
        result_text = f"{a1_id} wins!"
    elif winner == match.get("agent2_id"):
        a1_style = "color: #ef4444;"
        a2_style = "color: #22c55e; font-weight: bold;"
        result_text = f"{a2_id} wins!"
    else:
        a1_style = a2_style = "color: #eab308;"
        result_text = "Draw!"
    
    a1_lie_badge = f'<span class="lie-badge">🤥 {a1_lies}</span>' if a1_lies > 0 else ''
    a2_lie_badge = f'<span class="lie-badge">🤥 {a2_lies}</span>' if a2_lies > 0 else ''
    
    st.markdown(f"""
    <div class="agent-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="text-align: center; flex: 1;">
                <div style="{a1_style} font-size: 24px;">{a1_id} {a1_lie_badge}</div>
                <div style="color: #64748b; font-size: 12px;">{a1_desc}</div>
                <div style="font-size: 36px; color: white; margin-top: 8px;">{a1_score}</div>
            </div>
            <div style="color: #64748b; font-size: 24px; padding: 0 20px;">vs</div>
            <div style="text-align: center; flex: 1;">
                <div style="{a2_style} font-size: 24px;">{a2_id} {a2_lie_badge}</div>
                <div style="color: #64748b; font-size: 12px;">{a2_desc}</div>
                <div style="font-size: 36px; color: white; margin-top: 8px;">{a2_score}</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: 16px; color: #94a3b8;">
            {result_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# INTERACTIONS VIEW - NEW!
# =============================================================================

def show_interactions_view(live_state: Optional[LiveState]):
    """Show all AI interactions with thinking and lies."""
    st.markdown("### 💬 Agent Interactions")
    st.markdown("<p style='color: #64748b;'>Watch the AI agents think, negotiate, and deceive each other in real-time.</p>", unsafe_allow_html=True)
    
    if not live_state or not live_state.recent_rounds:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px; margin-bottom: 20px;">💭</div>
            <h2 style="color: white;">No Interactions Yet</h2>
            <p style="color: #64748b;">Start a tournament to see agent interactions here.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-refresh if tournament is running
        if live_state and live_state.status in ["running", "evolving"]:
            time.sleep(2)
            st.rerun()
        return
    
    # Show recent rounds
    for round_data in live_state.recent_rounds[:10]:
        show_interaction_card(round_data)
    
    # Auto-refresh more frequently for interactions
    if live_state.status in ["running", "evolving"]:
        time.sleep(1)
        st.rerun()


def show_interaction_card(round_data: dict):
    """Display a single round interaction with full detail."""
    match_id = round_data.get("match_id", "?")
    round_num = round_data.get("round_num", "?")
    
    a1_id = round_data.get("agent1_id", "?")[:10]
    a2_id = round_data.get("agent2_id", "?")[:10]
    a1_desc = round_data.get("agent1_description", "")
    a2_desc = round_data.get("agent2_description", "")
    
    a1_thinking = round_data.get("agent1_thinking", "")
    a2_thinking = round_data.get("agent2_thinking", "")
    a1_message = round_data.get("agent1_message") or "None"
    a2_message = round_data.get("agent2_message") or "None"
    a1_action = round_data.get("agent1_action", "?")
    a2_action = round_data.get("agent2_action", "?")
    a1_score = round_data.get("agent1_score", 0)
    a2_score = round_data.get("agent2_score", 0)
    a1_lied = round_data.get("agent1_lied", False)
    a2_lied = round_data.get("agent2_lied", False)
    outcome = round_data.get("outcome", "")
    
    # Outcome styling
    if outcome == "mutual_cooperation":
        outcome_text = "🤝 Mutual Cooperation"
        outcome_color = "#22c55e"
    elif outcome == "mutual_defection":
        outcome_text = "💥 Mutual Defection"
        outcome_color = "#ef4444"
    elif outcome == "agent1_exploited":
        outcome_text = f"🗡️ {a1_id} exploited {a2_id}"
        outcome_color = "#eab308"
    else:
        outcome_text = f"🗡️ {a2_id} exploited {a1_id}"
        outcome_color = "#eab308"
    
    # Action colors
    a1_color = "#22c55e" if a1_action == "COOPERATE" else "#ef4444"
    a2_color = "#22c55e" if a2_action == "COOPERATE" else "#ef4444"
    
    # Lie badges
    a1_lie = '<span class="lie-badge">LIE!</span>' if a1_lied else ''
    a2_lie = '<span class="lie-badge">LIE!</span>' if a2_lied else ''
    
    st.markdown(f"""
    <div class="interaction-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: #64748b; font-size: 12px;">Round {round_num}</span>
            <span style="color: {outcome_color}; font-size: 14px;">{outcome_text} ({a1_score} - {a2_score})</span>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
            <!-- Agent 1 -->
            <div>
                <div style="color: white; font-weight: 600; margin-bottom: 4px;">
                    {a1_id} <span style="color: #64748b; font-weight: normal;">({a1_desc})</span>
                </div>
                <div class="thinking-bubble">
                    💭 "{a1_thinking[:150]}{'...' if len(a1_thinking) > 150 else ''}"
                </div>
                <div style="color: #64748b; font-size: 13px; margin: 8px 0;">
                    💬 "{a1_message}" {a1_lie}
                </div>
                <div style="color: {a1_color}; font-weight: bold;">
                    → {a1_action}
                </div>
            </div>
            
            <!-- Agent 2 -->
            <div>
                <div style="color: white; font-weight: 600; margin-bottom: 4px;">
                    {a2_id} <span style="color: #64748b; font-weight: normal;">({a2_desc})</span>
                </div>
                <div class="thinking-bubble">
                    💭 "{a2_thinking[:150]}{'...' if len(a2_thinking) > 150 else ''}"
                </div>
                <div style="color: #64748b; font-size: 13px; margin: 8px 0;">
                    💬 "{a2_message}" {a2_lie}
                </div>
                <div style="color: {a2_color}; font-weight: bold;">
                    → {a2_action}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# RESULTS VIEW
# =============================================================================

def show_results_view(all_data: list[dict]):
    """Show tournament results."""
    live_state = read_live_state()
    
    # Auto-refresh if tournament is running
    if live_state and live_state.status in ["running", "evolving"]:
        # Reload data to get latest
        all_data = load_generation_data()
        time.sleep(3)
        st.rerun()
    
    if not all_data:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 64px; margin-bottom: 20px;">📊</div>
            <h2 style="color: white;">No Results Yet</h2>
            <p style="color: #64748b;">Run a tournament to see results here.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Get final generation
    final_gen = all_data[-1]
    gen_num = final_gen.get("generation", 0)
    
    st.markdown(f"### Generation {gen_num} Results")
    
    # Winner announcement
    rankings = final_gen.get("tournament", {}).get("agent_rankings", [])
    if rankings:
        winner = rankings[0]
        agents = final_gen.get("agents", [])
        winner_agent = next((a for a in agents if a["id"] == winner["agent_id"]), None)
        winner_personality = winner_agent.get("short_description", "") if winner_agent else ""
        
        st.markdown(f"""
        <div class="agent-card" style="text-align: center; background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));">
            <div style="font-size: 48px;">🏆</div>
            <h2 style="color: #22c55e; margin: 12px 0 4px 0;">Champion</h2>
            <div style="font-size: 24px; color: white;">{winner['agent_id'][:12]}</div>
            <div style="color: #64748b; margin: 8px 0;">{winner_personality}</div>
            <div style="font-size: 36px; color: white; font-weight: bold;">{winner['fitness']} pts</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # All agents
    st.markdown("### All Agents")
    
    agents = final_gen.get("agents", [])
    rank_lookup = {r["agent_id"]: r for r in rankings}
    
    for agent in sorted(agents, key=lambda a: rank_lookup.get(a["id"], {}).get("rank", 99)):
        rank_info = rank_lookup.get(agent["id"], {})
        rank = rank_info.get("rank", "?")
        fitness = rank_info.get("fitness", 0)
        coop_rate = rank_info.get("cooperation_rate", 0.5) * 100
        personality = agent.get("short_description", "")
        
        # Get key personality traits
        p = agent.get("personality", agent.get("dna", {}))
        trust = p.get("trust", 0.5) * 100
        honesty = p.get("honesty", 0.5) * 100
        vengefulness = p.get("vengefulness", 0.5) * 100
        
        st.markdown(f"""
        <div class="agent-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span style="font-size: 20px; margin-right: 8px;">#{rank}</span>
                    <span style="color: white; font-size: 18px; font-weight: 600;">{agent['id'][:12]}</span>
                    <div style="color: #64748b; margin-top: 4px;">{personality}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: white; font-size: 24px; font-weight: bold;">{fitness} <span style="font-size: 14px; color: #64748b;">pts</span></div>
                    <div style="color: {'#22c55e' if coop_rate >= 50 else '#ef4444'}; font-size: 14px;">{coop_rate:.0f}% cooperative</div>
                </div>
            </div>
            <div style="display: flex; gap: 24px; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(148, 163, 184, 0.1);">
                <div><span style="color: #64748b;">Trust:</span> <span style="color: white;">{trust:.0f}%</span></div>
                <div><span style="color: #64748b;">Honesty:</span> <span style="color: white;">{honesty:.0f}%</span></div>
                <div><span style="color: #64748b;">Vengefulness:</span> <span style="color: white;">{vengefulness:.0f}%</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# EVOLUTION VIEW
# =============================================================================

def show_evolution_view(all_data: list[dict]):
    """Show how personalities evolved."""
    live_state = read_live_state()
    
    # Auto-refresh if tournament is running
    if live_state and live_state.status in ["running", "evolving"]:
        all_data = load_generation_data()
        time.sleep(3)
        st.rerun()
    
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
    changes = []
    for trait in first_stats:
        if trait in last_stats:
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
    
    # Trait changes
    st.markdown("### Trait Changes")
    
    col1, col2 = st.columns(2)
    
    increased = [c for c in changes if c["change"] > 0.03]
    decreased = [c for c in changes if c["change"] < -0.03]
    
    with col1:
        st.markdown("**📈 Increased (selected FOR)**")
        for c in increased:
            st.markdown(f"""
            <div style="background: rgba(34, 197, 94, 0.1); padding: 8px 12px; border-radius: 8px; margin: 4px 0;">
                <span style="color: white;">{c['trait']}</span>
                <span style="color: #22c55e; float: right;">+{c['change']:.0%}</span>
            </div>
            """, unsafe_allow_html=True)
        if not increased:
            st.markdown("<p style='color: #64748b;'>No significant increases</p>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("**📉 Decreased (selected AGAINST)**")
        for c in decreased:
            st.markdown(f"""
            <div style="background: rgba(239, 68, 68, 0.1); padding: 8px 12px; border-radius: 8px; margin: 4px 0;">
                <span style="color: white;">{c['trait']}</span>
                <span style="color: #ef4444; float: right;">{c['change']:.0%}</span>
            </div>
            """, unsafe_allow_html=True)
        if not decreased:
            st.markdown("<p style='color: #64748b;'>No significant decreases</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Evolved strategy summary
    st.markdown("### 🎯 Evolved Strategy")
    
    high_traits = [c["trait"] for c in changes if c["final"] > 0.6]
    low_traits = [c["trait"] for c in changes if c["final"] < 0.4]
    
    strategy_desc = []
    if "Forgiveness" in high_traits:
        strategy_desc.append("forgiving of mistakes")
    if "Vengefulness" in high_traits:
        strategy_desc.append("retaliates when betrayed")
    if "Trust" in high_traits:
        strategy_desc.append("trusting of others")
    if "Honesty" in high_traits:
        strategy_desc.append("honest in communication")
    if "Honesty" in low_traits:
        strategy_desc.append("willing to deceive")
    if "Trust" in low_traits:
        strategy_desc.append("suspicious of others")
    if "Patience" in high_traits:
        strategy_desc.append("thinks long-term")
    
    if strategy_desc:
        st.markdown(f"""
        <div class="agent-card">
            <p style="color: white; font-size: 16px; margin: 0;">
                The winning strategy is to be <strong>{', '.join(strategy_desc[:3])}</strong>.
            </p>
            <p style="color: #64748b; margin-top: 8px;">
                This resembles the famous "Tit-for-Tat" strategy, but discovered through AI evolution.
            </p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
