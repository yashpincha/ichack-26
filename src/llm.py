"""LLM integration for agent decision making."""

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
    NO_HISTORY_TEXT,
    HISTORY_ENTRY_TEMPLATE,
    ROUNDS_PER_MATCH,
)


@dataclass
class LLMResponse:
    """Parsed response from LLM."""
    decision: str  # "COOPERATE" or "DEFECT"
    message: Optional[str]  # Message to opponent
    reasoning: str  # Agent's reasoning
    raw_response: str  # Full response text


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
                {"role": "system", "content": "You are an AI agent competing in a Prisoner's Dilemma tournament. Follow the response format exactly."},
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
            messages=[
                {"role": "user", "content": prompt}
            ],
            system="You are an AI agent competing in a Prisoner's Dilemma tournament. Follow the response format exactly.",
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
    """Parse LLM response into structured format."""
    # Default values
    decision = "COOPERATE"  # Default to cooperation if parsing fails
    message = None
    reasoning = ""
    
    # Try to extract DECISION
    decision_match = re.search(r"DECISION:\s*(COOPERATE|DEFECT)", response, re.IGNORECASE)
    if decision_match:
        decision = decision_match.group(1).upper()
    
    # Try to extract MESSAGE
    message_match = re.search(r"MESSAGE:\s*(.+?)(?:\n|REASONING:|$)", response, re.IGNORECASE | re.DOTALL)
    if message_match:
        msg = message_match.group(1).strip()
        if msg.upper() != "NONE" and msg:
            message = msg[:50]  # Truncate to 50 chars
    
    # Try to extract REASONING
    reasoning_match = re.search(r"REASONING:\s*(.+?)$", response, re.IGNORECASE | re.DOTALL)
    if reasoning_match:
        reasoning = reasoning_match.group(1).strip()
    
    return LLMResponse(
        decision=decision,
        message=message,
        reasoning=reasoning,
        raw_response=response,
    )


def build_decision_prompt(
    agent_id: str,
    agent_genes: dict[str, Any],
    opponent_id: str,
    round_history: list[dict],
    current_round: int,
    opponent_message: Optional[str] = None,
) -> str:
    """Build the decision prompt for an agent."""
    # Format round history
    if round_history:
        history_lines = []
        for entry in round_history:
            history_lines.append(HISTORY_ENTRY_TEMPLATE.format(
                round_num=entry["round"],
                your_move=entry["your_move"],
                their_move=entry["their_move"],
                your_score=entry["your_score"],
            ))
        history_text = "\n".join(history_lines)
    else:
        history_text = NO_HISTORY_TEXT
    
    # Format opponent message section
    if opponent_message:
        message_section = OPPONENT_MESSAGE_SECTION.format(opponent_message=opponent_message)
    else:
        message_section = "OPPONENT'S MESSAGE: None"
    
    # Format strategy keywords
    keywords = agent_genes.get("strategy_keywords", ["neutral"])
    if isinstance(keywords, list):
        keywords_str = ", ".join(keywords)
    else:
        keywords_str = str(keywords)
    
    return DECISION_PROMPT.format(
        agent_id=agent_id,
        cooperation_bias=agent_genes.get("cooperation_bias", 0.5),
        retaliation_sensitivity=agent_genes.get("retaliation_sensitivity", 0.5),
        forgiveness_rate=agent_genes.get("forgiveness_rate", 0.5),
        memory_weight=agent_genes.get("memory_weight", 0.5),
        strategy_keywords=keywords_str,
        reasoning_depth=agent_genes.get("reasoning_depth", "medium"),
        current_round=current_round,
        total_rounds=ROUNDS_PER_MATCH,
        opponent_id=opponent_id,
        round_history=history_text,
        opponent_message_section=message_section,
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
    agent_genes: dict[str, Any],
    opponent_id: str,
    round_history: list[dict],
    current_round: int,
    opponent_message: Optional[str] = None,
    client: Optional[LLMClient] = None,
) -> LLMResponse:
    """Get an agent's decision for a round."""
    if client is None:
        client = get_llm_client()
    
    prompt = build_decision_prompt(
        agent_id=agent_id,
        agent_genes=agent_genes,
        opponent_id=opponent_id,
        round_history=round_history,
        current_round=current_round,
        opponent_message=opponent_message,
    )
    
    response = await client.call(prompt)
    return parse_llm_response(response)
