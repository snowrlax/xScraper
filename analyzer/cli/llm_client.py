# llm_client.py
# ─────────────────────────────────────────────────────────────
# OpenAI API wrapper for LLM interactions.
# ─────────────────────────────────────────────────────────────

from typing import Optional, Generator
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analyzer import config as analyzer_config


class LLMClient:
    """OpenAI API client for tweet analysis and generation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the LLM client.

        Args:
            api_key: OpenAI API key (defaults to config/env)
            model: Model to use (defaults to config)
        """
        self.api_key = api_key or analyzer_config.OPENAI_API_KEY
        self.model = model or analyzer_config.LLM_MODEL

        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable."
            )

        # Import OpenAI here to avoid import errors if not installed
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            )

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            system_prompt: System message defining assistant behavior
            user_message: User's message/query
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Returns:
            Assistant's response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature or analyzer_config.LLM_TEMPERATURE,
            max_tokens=max_tokens or analyzer_config.LLM_MAX_TOKENS,
        )

        return response.choices[0].message.content

    def chat_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """
        Send a streaming chat completion request.

        Args:
            system_prompt: System message defining assistant behavior
            user_message: User's message/query
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response

        Yields:
            Chunks of assistant's response text
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature or analyzer_config.LLM_TEMPERATURE,
            max_tokens=max_tokens or analyzer_config.LLM_MAX_TOKENS,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def chat_with_history(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a chat completion with full message history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Assistant's response text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or analyzer_config.LLM_TEMPERATURE,
            max_tokens=max_tokens or analyzer_config.LLM_MAX_TOKENS,
        )

        return response.choices[0].message.content


def get_client() -> LLMClient:
    """
    Get a configured LLM client instance.

    Returns:
        Configured LLMClient

    Raises:
        ValueError: If API key is not configured
    """
    return LLMClient()
