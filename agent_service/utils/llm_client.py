import os
import logging
from typing import Any, List, Dict, Union
from langchain_core.prompts import ChatPromptTemplate
from openai import OpenAI, AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Unified LLM Client.
    Primary: OpenRouter (Grok)
    """

    def __init__(self, settings: Any):
        self.settings = settings
        
        # OpenRouter (Primary)
        self.openrouter_keys = [
            k for k in [
                settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY"),
                settings.openrouter_api_key0 or os.getenv("OPENROUTER_API_KEY0"),
            ] if k
        ]
        self.current_key_index = 0
        self.openrouter_base_url = settings.openrouter_base_url
        self.openrouter_model = settings.openrouter_model or "x-ai/grok-4-fast"
        
        if not self.openrouter_keys:
            logger.warning("No OpenRouter API keys configured for LLMClient.")

    def invoke(self, prompt_or_messages: Union[ChatPromptTemplate, List[Dict[str, str]]], input_data: Dict[str, Any] = None, **kwargs) -> str:
        """
        Invokes LLM via OpenRouter (Sync).
        """
        if self.openrouter_keys:
            return self._invoke_openrouter(prompt_or_messages, input_data or {}, **kwargs)
            
        raise RuntimeError("No available LLM provider configured (OpenRouter API keys missing).")

    async def ainvoke(self, prompt_or_messages: Union[ChatPromptTemplate, List[Dict[str, str]]], input_data: Dict[str, Any] = None, **kwargs) -> str:
        """
        Invokes LLM via OpenRouter (Async).
        """
        if self.openrouter_keys:
            return await self._ainvoke_openrouter(prompt_or_messages, input_data or {}, **kwargs)
            
        raise RuntimeError("No available LLM provider configured (OpenRouter API keys missing).")

    def _get_next_key(self) -> str:
        """Rotates to the next available API key."""
        if not self.openrouter_keys:
            raise RuntimeError("No OpenRouter API keys available.")
        
        key = self.openrouter_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.openrouter_keys)
        return key

    def _invoke_openrouter(self, prompt_or_messages: Union[ChatPromptTemplate, List[Dict[str, str]]], input_data: Dict[str, Any], **kwargs) -> str:
        """Invoke via OpenRouter with fallback (Sync)"""
        import openai
        
        messages = self._format_messages(prompt_or_messages, input_data)
        extra_body = kwargs.pop("extra_body", None)
        max_retries = len(self.openrouter_keys) * 2
        last_error = None
        
        for attempt in range(max_retries):
            current_key = self._get_next_key()
            try:
                client = OpenAI(base_url=self.openrouter_base_url, api_key=current_key)
                logger.info(f"Invoking OpenRouter ({self.openrouter_model}) with key ending in ...{current_key[-4:]} (Attempt {attempt+1})")
                
                completion = client.chat.completions.create(
                    model=self.openrouter_model,
                    messages=messages,
                    temperature=0.6,
                    max_tokens=8192,
                    extra_headers={"HTTP-Referer": "https://ivreetmeet.com", "X-Title": "IvreetMeet"},
                    extra_body=extra_body,
                    **kwargs
                )
                return completion.choices[0].message.content
            except Exception as e:
                logger.warning(f"Error with key ...{current_key[-4:]}: {e}. Rotating...")
                last_error = e
                continue
                
        raise RuntimeError(f"All OpenRouter keys failed. Last error: {last_error}")

    async def _ainvoke_openrouter(self, prompt_or_messages: Union[ChatPromptTemplate, List[Dict[str, str]]], input_data: Dict[str, Any], **kwargs) -> str:
        """Invoke via OpenRouter with fallback (Async)"""
        import openai
        
        messages = self._format_messages(prompt_or_messages, input_data)
        extra_body = kwargs.pop("extra_body", None)
        max_retries = len(self.openrouter_keys) * 2
        last_error = None
        
        for attempt in range(max_retries):
            current_key = self._get_next_key()
            try:
                client = AsyncOpenAI(base_url=self.openrouter_base_url, api_key=current_key)
                logger.info(f"Invoking OpenRouter Async ({self.openrouter_model}) with key ending in ...{current_key[-4:]} (Attempt {attempt+1})")
                
                completion = await client.chat.completions.create(
                    model=self.openrouter_model,
                    messages=messages,
                    temperature=0.6,
                    max_tokens=8192,
                    extra_headers={"HTTP-Referer": "https://ivreetmeet.com", "X-Title": "IvreetMeet"},
                    extra_body=extra_body,
                    **kwargs
                )
                return completion.choices[0].message.content
            except Exception as e:
                logger.warning(f"Async Error with key ...{current_key[-4:]}: {e}. Rotating...")
                last_error = e
                continue
                
        raise RuntimeError(f"All OpenRouter keys failed. Last error: {last_error}")

    def _format_messages(self, prompt_or_messages: Union[ChatPromptTemplate, List[Dict[str, str]]], input_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Helper to format messages for OpenAI API"""
        if isinstance(prompt_or_messages, list):
            return prompt_or_messages
            
        messages = prompt_or_messages.format_messages(**input_data)
        formatted_messages = [{"role": m.type, "content": m.content} for m in messages]
        
        for m in formatted_messages:
            if m["role"] == "human": m["role"] = "user"
            elif m["role"] == "ai": m["role"] = "assistant"
            elif m["role"] == "system": m["role"] = "system"
            else: m["role"] = "user"
            
        return formatted_messages
