"""LLM integration for AI agent pixel decisions."""

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
    PIXEL_DECISION_PROMPT,
    NO_HISTORY_TEXT,
    HISTORY_ENTRY_TEMPLATE,
    COLORS,
    GRID_WIDTH,
    GRID_HEIGHT,
    TURNS_PER_GENERATION,
)


@dataclass
class PixelDecision:
    """Parsed response from LLM for pixel placement."""
    x: int
    y: int
    color: str
    thinking: str  # Agent's reasoning
    raw_response: str  # Full response text
    valid: bool = True  # Whether the decision is valid
    
    def to_dict(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "color": self.color,
            "thinking": self.thinking,
            "valid": self.valid,
        }


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
                        "You are an AI agent with a unique personality competing in an r/place-style canvas simulation. "
                        "You must think and act according to your personality traits. "
                        "Follow the response format exactly: THINKING, then PLACE."
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
                "You are an AI agent with a unique personality competing in an r/place-style canvas simulation. "
                "You must think and act according to your personality traits. "
                "Follow the response format exactly: THINKING, then PLACE."
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


def parse_pixel_decision(
    response: str,
    grid_width: int = GRID_WIDTH,
    grid_height: int = GRID_HEIGHT,
    default_color: str = "red",
) -> PixelDecision:
    """Parse LLM response into a pixel placement decision."""
    # Default values
    x, y = 0, 0
    color = default_color
    thinking = ""
    valid = True
    
    # Try to extract THINKING
    thinking_match = re.search(
        r"THINKING:\s*(.+?)(?=\n\s*PLACE:|$)", 
        response, 
        re.IGNORECASE | re.DOTALL
    )
    if thinking_match:
        thinking = thinking_match.group(1).strip()
    
    # Try to extract PLACE: x,y,color
    place_match = re.search(
        r"PLACE:\s*(\d+)\s*,\s*(\d+)\s*,\s*(\w+)", 
        response, 
        re.IGNORECASE
    )
    if place_match:
        try:
            x = int(place_match.group(1))
            y = int(place_match.group(2))
            color = place_match.group(3).lower()
        except (ValueError, IndexError):
            valid = False
    else:
        # Try alternative formats
        # Format: x,y,color or (x,y,color) or x y color
        alt_match = re.search(
            r"(\d+)\s*[,\s]\s*(\d+)\s*[,\s]\s*(\w+)",
            response,
            re.IGNORECASE
        )
        if alt_match:
            try:
                x = int(alt_match.group(1))
                y = int(alt_match.group(2))
                color = alt_match.group(3).lower()
            except (ValueError, IndexError):
                valid = False
        else:
            valid = False
    
    # Validate coordinates
    if x < 0 or x >= grid_width or y < 0 or y >= grid_height:
        # Clamp to valid range
        x = max(0, min(x, grid_width - 1))
        y = max(0, min(y, grid_height - 1))
    
    # Validate color
    if color not in COLORS:
        # Try to match partial color name
        for valid_color in COLORS:
            if color in valid_color or valid_color in color:
                color = valid_color
                break
        else:
            color = default_color
    
    return PixelDecision(
        x=x,
        y=y,
        color=color,
        thinking=thinking,
        raw_response=response,
        valid=valid,
    )


def build_pixel_prompt(
    agent_id: str,
    personality_description: str,
    agent_color: str,
    grid_ascii: str,
    grid_width: int,
    grid_height: int,
    territory_count: int,
    current_turn: int,
    total_turns: int,
    recent_history: list[dict],
    goal: Optional[str] = None,
) -> str:
    """Build the prompt for pixel placement decision."""
    
    # Format recent history
    if recent_history:
        history_lines = []
        for entry in recent_history[-5:]:  # Last 5 placements
            history_lines.append(HISTORY_ENTRY_TEMPLATE.format(
                turn=entry.get("turn", "?"),
                agent_id=entry.get("agent_id", "?")[:8],
                color=entry.get("color", "?"),
                x=entry.get("x", "?"),
                y=entry.get("y", "?"),
            ))
        history_text = "\n".join(history_lines)
    else:
        history_text = NO_HISTORY_TEXT
    
    goal_text = goal if goal else "maximize your territory and express your personality"
    
    return PIXEL_DECISION_PROMPT.format(
        personality_description=personality_description,
        width=grid_width,
        height=grid_height,
        grid_ascii=grid_ascii,
        agent_color=agent_color,
        territory_count=territory_count,
        current_turn=current_turn,
        total_turns=total_turns,
        recent_history=history_text,
        goal_text=goal_text,
        max_x=grid_width - 1,
        max_y=grid_height - 1,
        colors=", ".join(COLORS),
    )


# Global client instance (lazy initialization)
_llm_client: Optional[LLMClient] = None


def get_llm_client(use_cache: bool = True) -> LLMClient:
    """Get or create the global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(use_cache=use_cache)
    return _llm_client


async def get_pixel_decision(
    agent_id: str,
    personality_description: str,
    agent_color: str,
    grid_ascii: str,
    grid_width: int,
    grid_height: int,
    territory_count: int,
    current_turn: int,
    total_turns: int,
    recent_history: list[dict],
    goal: Optional[str] = None,
    client: Optional[LLMClient] = None,
) -> PixelDecision:
    """Get an AI agent's decision for pixel placement."""
    if client is None:
        client = get_llm_client()
    
    prompt = build_pixel_prompt(
        agent_id=agent_id,
        personality_description=personality_description,
        agent_color=agent_color,
        grid_ascii=grid_ascii,
        grid_width=grid_width,
        grid_height=grid_height,
        territory_count=territory_count,
        current_turn=current_turn,
        total_turns=total_turns,
        recent_history=recent_history,
        goal=goal,
    )
    
    response = await client.call(prompt)
    return parse_pixel_decision(
        response,
        grid_width=grid_width,
        grid_height=grid_height,
        default_color=agent_color,
    )
