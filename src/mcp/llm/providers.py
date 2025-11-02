"""LLM provider integrations for orbit-mcp."""

import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
from abc import ABC, abstractmethod
from dataclasses import dataclass
import os

logger = logging.getLogger(__name__)


@dataclass
class LLMMessage:
    """LLM message structure."""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """LLM response structure."""
    content: str
    model: str
    tokens_used: int
    cost: float = 0.0
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        self.model = model
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Generate LLM response."""
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Generate streaming LLM response."""
        pass
    
    @abstractmethod
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost for token count."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI (ChatGPT) provider."""
    
    PRICING = {
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},  # per 1K tokens
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
    }
    
    def __init__(self, model: str = 'gpt-3.5-turbo', api_key: Optional[str] = None):
        super().__init__(model, api_key or os.getenv('OPENAI_API_KEY'))
        
        if not self.api_key:
            raise ValueError("OpenAI API key required (OPENAI_API_KEY)")
    
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Generate response using OpenAI API."""
        try:
            import openai
            openai.api_key = self.api_key
            
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            cost = self.estimate_cost(tokens_used)
            
            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                cost=cost,
                finish_reason=response.choices[0].finish_reason
            )
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Stream response from OpenAI."""
        try:
            import openai
            openai.api_key = self.api_key
            
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.get('content'):
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on token usage."""
        pricing = self.PRICING.get(self.model, {'input': 0.01, 'output': 0.03})
        # Approximate: assume 75% input, 25% output
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        cost = (input_tokens / 1000 * pricing['input'] + 
                output_tokens / 1000 * pricing['output'])
        return cost


class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) provider."""
    
    PRICING = {
        'claude-3-opus': {'input': 0.015, 'output': 0.075},
        'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        'claude-2.1': {'input': 0.008, 'output': 0.024},
    }
    
    def __init__(self, model: str = 'claude-3-sonnet', api_key: Optional[str] = None):
        super().__init__(model, api_key or os.getenv('ANTHROPIC_API_KEY'))
        
        if not self.api_key:
            raise ValueError("Anthropic API key required (ANTHROPIC_API_KEY)")
    
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Generate response using Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            # Extract system message if present
            system_msg = None
            user_messages = []
            for msg in messages:
                if msg.role == 'system':
                    system_msg = msg.content
                else:
                    user_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            response = await asyncio.to_thread(
                client.messages.create,
                model=self.model,
                max_tokens=max_tokens or 4096,
                system=system_msg,
                messages=user_messages,
                temperature=temperature
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            cost = self.estimate_cost(tokens_used)
            
            return LLMResponse(
                content=content,
                model=self.model,
                tokens_used=tokens_used,
                cost=cost,
                finish_reason=response.stop_reason
            )
        
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Stream response from Anthropic."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            system_msg = None
            user_messages = []
            for msg in messages:
                if msg.role == 'system':
                    system_msg = msg.content
                else:
                    user_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            async with client.messages.stream(
                model=self.model,
                max_tokens=max_tokens or 4096,
                system=system_msg,
                messages=user_messages,
                temperature=temperature
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on token usage."""
        pricing = self.PRICING.get(self.model, {'input': 0.003, 'output': 0.015})
        input_tokens = int(tokens * 0.75)
        output_tokens = int(tokens * 0.25)
        
        cost = (input_tokens / 1000 * pricing['input'] + 
                output_tokens / 1000 * pricing['output'])
        return cost


class OllamaProvider(LLMProvider):
    """Ollama (local models) provider."""
    
    def __init__(
        self,
        model: str = 'llama2',
        base_url: str = 'http://localhost:11434'
    ):
        super().__init__(model, None)
        self.base_url = base_url
    
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """Generate response using Ollama."""
        try:
            import aiohttp
            
            # Convert messages to Ollama format
            prompt = self._format_messages(messages)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "temperature": temperature,
                        "stream": False
                    }
                ) as response:
                    result = await response.json()
                    
                    content = result.get('response', '')
                    
                    # Ollama doesn't track tokens precisely, estimate
                    tokens_used = len(prompt.split()) + len(content.split())
                    
                    return LLMResponse(
                        content=content,
                        model=self.model,
                        tokens_used=tokens_used,
                        cost=0.0,  # Local model, no API cost
                        finish_reason='stop'
                    )
        
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    async def generate_stream(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Stream response from Ollama."""
        try:
            import aiohttp
            
            prompt = self._format_messages(messages)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "temperature": temperature,
                        "stream": True
                    }
                ) as response:
                    async for line in response.content:
                        if line:
                            import json
                            try:
                                data = json.loads(line)
                                if data.get('response'):
                                    yield data['response']
                            except json.JSONDecodeError:
                                continue
        
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")
            raise
    
    def _format_messages(self, messages: List[LLMMessage]) -> str:
        """Format messages for Ollama."""
        formatted = []
        for msg in messages:
            if msg.role == 'system':
                formatted.append(f"System: {msg.content}")
            elif msg.role == 'user':
                formatted.append(f"Human: {msg.content}")
            elif msg.role == 'assistant':
                formatted.append(f"Assistant: {msg.content}")
        
        formatted.append("Assistant:")
        return "\n\n".join(formatted)
    
    def estimate_cost(self, tokens: int) -> float:
        """Local model - no API cost."""
        return 0.0


class LLMClient:
    """Unified LLM client supporting multiple providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = config.get('default_provider', 'ollama')
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize configured providers."""
        providers_config = self.config.get('providers', {})
        
        # OpenAI
        if 'openai' in providers_config:
            cfg = providers_config['openai']
            try:
                self.providers['openai'] = OpenAIProvider(
                    model=cfg.get('model', 'gpt-3.5-turbo'),
                    api_key=cfg.get('api_key')
                )
                logger.info(f"Initialized OpenAI provider: {cfg.get('model')}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        # Anthropic
        if 'anthropic' in providers_config:
            cfg = providers_config['anthropic']
            try:
                self.providers['anthropic'] = AnthropicProvider(
                    model=cfg.get('model', 'claude-3-sonnet'),
                    api_key=cfg.get('api_key')
                )
                logger.info(f"Initialized Anthropic provider: {cfg.get('model')}")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
        
        # Ollama
        if 'ollama' in providers_config:
            cfg = providers_config['ollama']
            if cfg.get('enabled', True):
                try:
                    self.providers['ollama'] = OllamaProvider(
                        model=cfg.get('model', 'llama2'),
                        base_url=cfg.get('base_url', 'http://localhost:11434')
                    )
                    logger.info(f"Initialized Ollama provider: {cfg.get('model')}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Ollama: {e}")
    
    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """Get LLM provider."""
        provider_name = provider_name or self.default_provider
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider not configured: {provider_name}")
        
        return self.providers[provider_name]
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> LLMResponse:
        """
        Generate LLM response.
        
        Args:
            prompt: User prompt
            system: System prompt
            provider: Provider name (uses default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            LLM response
        """
        messages = []
        
        if system:
            messages.append(LLMMessage(role='system', content=system))
        
        messages.append(LLMMessage(role='user', content=prompt))
        
        provider_obj = self.get_provider(provider)
        
        return await provider_obj.generate(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )
    
    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Generate streaming LLM response."""
        messages = []
        
        if system:
            messages.append(LLMMessage(role='system', content=system))
        
        messages.append(LLMMessage(role='user', content=prompt))
        
        provider_obj = self.get_provider(provider)
        
        async for chunk in provider_obj.generate_stream(
            messages,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            yield chunk
    
    def list_providers(self) -> List[str]:
        """List available providers."""
        return list(self.providers.keys())
    
    def get_default_provider(self) -> str:
        """Get default provider name."""
        return self.default_provider
    
    def set_default_provider(self, provider: str):
        """Set default provider."""
        if provider not in self.providers:
            raise ValueError(f"Provider not available: {provider}")
        self.default_provider = provider
        logger.info(f"Default provider set to: {provider}")
