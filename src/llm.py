"""LLM integration for AI agent decision making with full reasoning."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass

from src.config import (
    LLM_PROVIDER,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    DECISION_PROMPT,
    OPPONENT_MESSAGE_SECTION,
    NO_MESSAGE_SECTION,
    NO_HISTORY_TEXT,
    HISTORY_ENTRY_TEMPLATE,
    OPPONENT_ANALYSIS_TEMPLATE,
    NO_ANALYSIS_TEXT,
    ROUNDS_PER_MATCH,
)


@dataclass
class LLMResponse:
    """Parsed response from LLM with full reasoning."""
    decision: str  # "COOPERATE" or "DEFECT"
    message: Optional[str]  # Message to opponent
    thinking: str  # Agent's internal reasoning (new!)
    raw_response: str  # Full response text
    
    # Legacy alias
    @property
    def reasoning(self) -> str:
        return self.thinking


class LLMCache:
    """Simple file-based cache for LLM responses."""
    
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._memory_cache: dict[str, str] = {}
    
    def _get_key(self, prompt: str) -> str:
        """Generate cache key from prompt."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
    
    def get(self, prompt: str) -> Optional[str]:
        """Get cached response."""
        key = self._get_key(prompt)
        
        # Check memory cache first
        if key in self._memory_cache:
            return self._memory_cache[key]
        
        # Check file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                self._memory_cache[key] = data["response"]
                return data["response"]
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None
    
    def set(self, prompt: str, response: str) -> None:
        """Cache a response."""
        key = self._get_key(prompt)
        self._memory_cache[key] = response
        
        cache_file = self.cache_dir / f"{key}.json"
        cache_file.write_text(json.dumps({
            "prompt_hash": key,
            "response": response,
        }))


class LLMClient:
    """Async client for LLM API calls."""
    
    def __init__(
        self,
        provider: str = LLM_PROVIDER,
        model: str = LLM_MODEL,
        use_cache: bool = True,
    ):
        self.provider = provider
        self.model = model
        self.cache = LLMCache() if use_cache else None
        self._client = None
        self._semaphore = asyncio.Semaphore(10)  # Rate limiting
    
    def _get_openai_client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        return self._client
    
    def _get_anthropic_client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        return self._client
    
    async def _call_openai(self, prompt: str) -> str:
        """Make async call to OpenAI API."""
        client = self._get_openai_client()
        
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are an AI agent with a unique personality competing in a Prisoner's Dilemma tournament. "
                        "You must think and act according to your personality traits. "
                        "Show your reasoning process, then make your decision. "
                        "Follow the response format exactly: THINKING, MESSAGE, DECISION."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        
        return response.choices[0].message.content or ""
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Make async call to Anthropic API."""
        client = self._get_anthropic_client()
        
        response = await client.messages.create(
            model=self.model,
            max_tokens=LLM_MAX_TOKENS,
            temperature=LLM_TEMPERATURE,
            messages=[
                {"role": "user", "content": prompt}
            ],
            system=(
                "You are an AI agent with a unique personality competing in a Prisoner's Dilemma tournament. "
                "You must think and act according to your personality traits. "
                "Show your reasoning process, then make your decision. "
                "Follow the response format exactly: THINKING, MESSAGE, DECISION."
            ),
        )
        
        return response.content[0].text if response.content else ""
    
    async def call(self, prompt: str) -> str:
        """Make async call to configured LLM provider."""
        # Check cache first
        if self.cache:
            cached = self.cache.get(prompt)
            if cached:
                return cached
        
        # Rate limiting
        async with self._semaphore:
            if self.provider == "openai":
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt)
            else:
                raise ValueError(f"Unknown provider: {self.provider}")
        
        # Cache the response
        if self.cache:
            self.cache.set(prompt, response)
        
        return response


def parse_llm_response(response: str) -> LLMResponse:
    """Parse LLM response with THINKING/MESSAGE/DECISION format."""
    # Default values
    decision = "COOPERATE"  # Default to cooperation if parsing fails
    message = None
    thinking = ""
    
    # Try to extract THINKING (new!)
    thinking_match = re.search(
        r"THINKING:\s*(.+?)(?=\n\s*MESSAGE:|$)", 
        response, 
        re.IGNORECASE | re.DOTALL
    )
    if thinking_match:
        thinking = thinking_match.group(1).strip()
    
    # Try to extract MESSAGE
    message_match = re.search(
        r"MESSAGE:\s*(.+?)(?=\n\s*DECISION:|$)", 
        response, 
        re.IGNORECASE | re.DOTALL
    )
    if message_match:
        msg = message_match.group(1).strip()
        # Clean up the message
        msg = msg.strip('"\'')
        if msg.upper() not in ("NONE", "N/A", ""):
            message = msg[:100]  # Truncate to 100 chars
    
    # Try to extract DECISION
    decision_match = re.search(
        r"DECISION:\s*(COOPERATE|DEFECT)", 
        response, 
        re.IGNORECASE
    )
    if decision_match:
        decision = decision_match.group(1).upper()
    
    return LLMResponse(
        decision=decision,
        message=message,
        thinking=thinking,
        raw_response=response,
    )


def analyze_opponent(round_history: list[dict]) -> dict:
    """Analyze opponent's behavior from history."""
    if not round_history:
        return {
            "coop_rate": "unknown",
            "broken_promises": 0,
            "retaliations": 0,
            "apparent_strategy": "unknown - no history yet",
        }
    
    # Count their moves
    their_coops = sum(1 for r in round_history if r.get("their_move") == "COOPERATE")
    their_defects = sum(1 for r in round_history if r.get("their_move") == "DEFECT")
    total = their_coops + their_defects
    
    coop_rate = f"{their_coops}/{total} ({their_coops/total*100:.0f}%)" if total > 0 else "unknown"
    
    # Detect broken promises (said cooperate but defected)
    broken_promises = 0
    for i, r in enumerate(round_history):
        if i > 0:
            prev_their_msg = round_history[i-1].get("their_message", "")
            if prev_their_msg and "cooperat" in prev_their_msg.lower():
                if r.get("their_move") == "DEFECT":
                    broken_promises += 1
    
    # Detect retaliations (defected after we defected)
    retaliations = 0
    for i, r in enumerate(round_history):
        if i > 0:
            prev_our_move = round_history[i-1].get("your_move")
            if prev_our_move == "DEFECT" and r.get("their_move") == "DEFECT":
                retaliations += 1
    
    # Guess apparent strategy
    if total < 2:
        apparent_strategy = "too early to tell"
    elif their_coops == total:
        apparent_strategy = "Always Cooperate (naive or testing)"
    elif their_defects == total:
        apparent_strategy = "Always Defect (hostile)"
    elif retaliations >= total // 2:
        apparent_strategy = "Tit-for-Tat style (retaliates)"
    elif broken_promises > 0:
        apparent_strategy = "Deceptive (breaks promises)"
    else:
        apparent_strategy = "Mixed/Adaptive"
    
    return {
        "coop_rate": coop_rate,
        "broken_promises": broken_promises,
        "retaliations": retaliations,
        "apparent_strategy": apparent_strategy,
    }


def build_decision_prompt(
    agent_id: str,
    personality_description: str,
    opponent_id: str,
    round_history: list[dict],
    current_round: int,
    your_score: int,
    their_score: int,
    honesty_level: float = 0.5,
    opponent_message: Optional[str] = None,
) -> str:
    """Build the full decision prompt for an AI agent."""
    
    # Format round history with messages
    if round_history:
        history_lines = []
        for entry in round_history:
            history_lines.append(HISTORY_ENTRY_TEMPLATE.format(
                round_num=entry["round"],
                your_move=entry["your_move"],
                their_move=entry["their_move"],
                your_score=entry["your_score"],
                their_score=entry.get("their_score", "?"),
                your_message=entry.get("your_message", "none"),
                their_message=entry.get("their_message", "none"),
            ))
        history_text = "\n".join(history_lines)
    else:
        history_text = NO_HISTORY_TEXT
    
    # Format opponent message section
    if opponent_message:
        message_section = OPPONENT_MESSAGE_SECTION.format(opponent_message=opponent_message)
    else:
        message_section = NO_MESSAGE_SECTION
    
    # Analyze opponent behavior
    analysis = analyze_opponent(round_history)
    if round_history:
        opponent_analysis = OPPONENT_ANALYSIS_TEMPLATE.format(
            coop_rate=analysis["coop_rate"],
            broken_promises=analysis["broken_promises"],
            retaliations=analysis["retaliations"],
            apparent_strategy=analysis["apparent_strategy"],
        )
    else:
        opponent_analysis = NO_ANALYSIS_TEXT
    
    # Determine honesty level description
    if honesty_level < 0.33:
        honesty_desc = "LOW (you are comfortable lying to get ahead)"
    elif honesty_level < 0.67:
        honesty_desc = "MEDIUM (you lie when necessary)"
    else:
        honesty_desc = "HIGH (you prefer honesty)"
    
    return DECISION_PROMPT.format(
        personality_description=personality_description,
        current_round=current_round,
        total_rounds=ROUNDS_PER_MATCH,
        opponent_id=opponent_id,
        your_score=your_score,
        their_score=their_score,
        round_history=history_text,
        opponent_message_section=message_section,
        opponent_analysis=opponent_analysis,
        honesty_level=honesty_desc,
    )


# Global client instance (lazy initialization)
_llm_client: Optional[LLMClient] = None


def get_llm_client(use_cache: bool = True) -> LLMClient:
    """Get or create the global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(use_cache=use_cache)
    return _llm_client


async def get_agent_decision(
    agent_id: str,
    personality_description: str,
    opponent_id: str,
    round_history: list[dict],
    current_round: int,
    your_score: int = 0,
    their_score: int = 0,
    honesty_level: float = 0.5,
    opponent_message: Optional[str] = None,
    client: Optional[LLMClient] = None,
) -> LLMResponse:
    """Get an AI agent's decision for a round with full reasoning."""
    if client is None:
        client = get_llm_client()
    
    prompt = build_decision_prompt(
        agent_id=agent_id,
        personality_description=personality_description,
        opponent_id=opponent_id,
        round_history=round_history,
        current_round=current_round,
        your_score=your_score,
        their_score=their_score,
        honesty_level=honesty_level,
        opponent_message=opponent_message,
    )
    
    response = await client.call(prompt)
    return parse_llm_response(response)
