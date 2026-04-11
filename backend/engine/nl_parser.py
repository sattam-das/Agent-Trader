"""Natural Language Strategy Parser — converts English to structured strategy specs.

Uses Google Gemini to parse human-readable trading strategy descriptions into
a structured JSON specification that DynamicStrategy can execute.
"""

from __future__ import annotations

import json
import os
from typing import Any

from google import genai
from google.genai import types

from backend.agents.base_agent import _get_client


_SYSTEM_PROMPT = """You are a quantitative trading strategy parser. Your ONLY job is to convert
a trader's English description of a strategy into a precise, structured JSON specification.

## Available Indicators (use EXACTLY these names)

| Token | Description | Example |
|-------|-------------|---------|
| RSI(period) | Relative Strength Index (0-100) | RSI(14) |
| SMA(period) | Simple Moving Average | SMA(20), SMA(50), SMA(200) |
| EMA(period) | Exponential Moving Average | EMA(12), EMA(26) |
| MACD_LINE(fast,slow,signal) | MACD line value | MACD_LINE(12,26,9) |
| MACD_SIGNAL(fast,slow,signal) | MACD signal line | MACD_SIGNAL(12,26,9) |
| MACD_HISTOGRAM(fast,slow,signal) | MACD histogram | MACD_HISTOGRAM(12,26,9) |
| BB_UPPER(period,std) | Upper Bollinger Band | BB_UPPER(20,2) |
| BB_LOWER(period,std) | Lower Bollinger Band | BB_LOWER(20,2) |
| BB_MIDDLE(period,std) | Middle Bollinger Band (SMA) | BB_MIDDLE(20,2) |
| PRICE | Current closing price | PRICE |
| VOLUME | Current volume | VOLUME |
| HIGH | Daily high price | HIGH |
| LOW | Daily low price | LOW |
| ATR(period) | Average True Range | ATR(14) |

## Available Operators
- `>` : greater than
- `<` : less than
- `>=` : greater or equal
- `<=` : less or equal
- `crosses_above` : was below, now above (bullish crossover)
- `crosses_below` : was above, now below (bearish crossunder)

## Rules
1. The "right" value can be a number (like "30") OR another indicator (like "SMA(200)").
2. If the user doesn't specify parameters, use sensible defaults (RSI → 14, SMA → 20, MACD → 12,26,9, BB → 20,2).
3. Every strategy MUST have at least one buy_condition AND at least one sell_condition.
4. If the user describes something vague like "buy the dip", interpret it as a reasonable technical strategy.
5. Use "crosses_above" / "crosses_below" for crossover strategies (like Golden Cross).
6. Use "<" / ">" for threshold strategies (like RSI oversold/overbought).

## Output Format (strict JSON, no markdown)
{
  "strategy_name": "Short descriptive name",
  "description": "One sentence explaining what this strategy does",
  "buy_conditions": [
    {"left": "INDICATOR(params)", "operator": "operator", "right": "value_or_indicator"}
  ],
  "buy_logic": "AND",
  "sell_conditions": [
    {"left": "INDICATOR(params)", "operator": "operator", "right": "value_or_indicator"}
  ],
  "sell_logic": "AND",
  "parameters_used": {"rsi_period": 14, "sma_fast": 50}
}

If the input is completely unparseable or unrelated to trading, return:
{"error": "Cannot parse: brief explanation"}
"""


class NLParser:
    """Parse natural language strategy descriptions into structured specs."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        resolved_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_key:
            raise ValueError("GEMINI_API_KEY required for NL parsing")
        self.client = _get_client(resolved_key)
        self.model_name = model or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"

    async def parse(self, prompt: str) -> dict[str, Any]:
        """Parse an English strategy description into a structured spec.

        Parameters
        ----------
        prompt : str
            Human-readable strategy description.

        Returns
        -------
        dict
            Structured strategy specification, or {"error": "..."} on failure.
        """
        if not prompt or len(prompt.strip()) < 5:
            return {"error": "Strategy description is too short. Please describe when to buy and sell."}

        if len(prompt) > 2000:
            return {"error": "Strategy description is too long (max 2000 characters). Please be concise."}

        try:
            full_prompt = f"{_SYSTEM_PROMPT}\n\nParse this trading strategy:\n\n{prompt}"

            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )

            # Handle safety-blocked or empty responses
            try:
                message = response.text
            except (ValueError, AttributeError):
                return {"error": "LLM response was blocked by safety filters. Try rephrasing your strategy."}

            if not message:
                return {"error": "LLM returned empty response"}

            # Strip markdown fences if present
            text = message.strip()
            if text.startswith("```"):
                lines = text.split("\n", 1)
                text = lines[1] if len(lines) > 1 else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            spec = json.loads(text)

            if not isinstance(spec, dict):
                return {"error": "LLM returned non-object response"}

            # Check for LLM-reported errors
            if "error" in spec:
                return spec

            # Validate minimum structure
            if not spec.get("buy_conditions") or not spec.get("sell_conditions"):
                return {"error": "Strategy must have both buy and sell conditions. Please specify when to buy AND when to sell."}

            # Add defaults
            spec.setdefault("strategy_name", "Custom Strategy")
            spec.setdefault("description", "User-defined strategy")
            spec.setdefault("buy_logic", "AND")
            spec.setdefault("sell_logic", "AND")
            spec.setdefault("parameters_used", {})

            # Store original prompt
            spec["original_prompt"] = prompt

            return spec

        except json.JSONDecodeError:
            return {"error": "Failed to parse LLM output as JSON"}
        except Exception as exc:
            return {"error": f"LLM parsing failed: {str(exc)}"}
