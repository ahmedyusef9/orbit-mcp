"""Cost management and token optimization for LLM usage."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class CostManager:
    """Manages LLM API costs and budget limits."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cost manager.
        
        Args:
            config: Cost control configuration
        """
        self.config = config
        self.daily_limit = config.get('daily_budget', 10.0)
        self.monthly_limit = config.get('monthly_budget', 200.0)
        self.alert_threshold = config.get('alert_at', 0.8)
        
        # Track usage
        self.usage_file = Path.home() / '.orbit' / 'usage.json'
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.usage = self._load_usage()
    
    def _load_usage(self) -> Dict[str, Any]:
        """Load usage tracking data."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load usage data: {e}")
        
        return {
            'daily': {'date': datetime.now().date().isoformat(), 'cost': 0.0, 'tokens': 0},
            'monthly': {'month': datetime.now().strftime('%Y-%m'), 'cost': 0.0, 'tokens': 0},
            'total': {'cost': 0.0, 'tokens': 0}
        }
    
    def _save_usage(self):
        """Save usage tracking data."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def _reset_if_needed(self):
        """Reset counters if day/month changed."""
        today = datetime.now().date().isoformat()
        this_month = datetime.now().strftime('%Y-%m')
        
        # Reset daily if new day
        if self.usage['daily']['date'] != today:
            logger.info(f"New day - resetting daily usage (was ${self.usage['daily']['cost']:.2f})")
            self.usage['daily'] = {'date': today, 'cost': 0.0, 'tokens': 0}
        
        # Reset monthly if new month
        if self.usage['monthly']['month'] != this_month:
            logger.info(f"New month - resetting monthly usage (was ${self.usage['monthly']['cost']:.2f})")
            self.usage['monthly'] = {'month': this_month, 'cost': 0.0, 'tokens': 0}
        
        self._save_usage()
    
    def can_make_request(self, estimated_cost: float) -> bool:
        """
        Check if request would exceed budget.
        
        Args:
            estimated_cost: Estimated cost of request
            
        Returns:
            True if within budget
        """
        self._reset_if_needed()
        
        daily_remaining = self.daily_limit - self.usage['daily']['cost']
        monthly_remaining = self.monthly_limit - self.usage['monthly']['cost']
        
        if estimated_cost > daily_remaining:
            logger.warning(f"Request would exceed daily budget: ${estimated_cost:.4f} > ${daily_remaining:.2f}")
            return False
        
        if estimated_cost > monthly_remaining:
            logger.warning(f"Request would exceed monthly budget: ${estimated_cost:.4f} > ${monthly_remaining:.2f}")
            return False
        
        # Alert if approaching limits
        daily_usage_pct = self.usage['daily']['cost'] / self.daily_limit
        if daily_usage_pct >= self.alert_threshold:
            logger.warning(f"??  {daily_usage_pct*100:.0f}% of daily budget used")
        
        monthly_usage_pct = self.usage['monthly']['cost'] / self.monthly_limit
        if monthly_usage_pct >= self.alert_threshold:
            logger.warning(f"??  {monthly_usage_pct*100:.0f}% of monthly budget used")
        
        return True
    
    def record_usage(self, provider: str, tokens: int, cost: float):
        """
        Record LLM usage.
        
        Args:
            provider: Provider name
            tokens: Tokens used
            cost: Cost incurred
        """
        self._reset_if_needed()
        
        self.usage['daily']['cost'] += cost
        self.usage['daily']['tokens'] += tokens
        self.usage['monthly']['cost'] += cost
        self.usage['monthly']['tokens'] += tokens
        self.usage['total']['cost'] += cost
        self.usage['total']['tokens'] += tokens
        
        self._save_usage()
        
        logger.info(f"Usage recorded: {provider} - {tokens} tokens, ${cost:.4f}")
        logger.debug(f"Daily: ${self.usage['daily']['cost']:.2f} / ${self.daily_limit:.2f}")
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        self._reset_if_needed()
        
        return {
            'daily': {
                **self.usage['daily'],
                'limit': self.daily_limit,
                'remaining': self.daily_limit - self.usage['daily']['cost']
            },
            'monthly': {
                **self.usage['monthly'],
                'limit': self.monthly_limit,
                'remaining': self.monthly_limit - self.usage['monthly']['cost']
            },
            'total': self.usage['total']
        }
    
    def select_provider(
        self,
        task_complexity: int,
        context_size: int,
        prefer_local: bool = True
    ) -> str:
        """
        Select most cost-effective provider for task.
        
        Args:
            task_complexity: Task complexity (1-10)
            context_size: Estimated context tokens
            prefer_local: Prefer local models when possible
            
        Returns:
            Provider name
        """
        budget_remaining = self.daily_limit - self.usage['daily']['cost']
        
        # If very low budget, force local
        if budget_remaining < 0.10:
            if 'ollama' in self.providers:
                logger.info("Low budget - using local model")
                return 'ollama'
        
        # Prefer local for simple tasks
        if prefer_local and task_complexity <= 7 and 'ollama' in self.providers:
            logger.info("Using local model for routine task")
            return 'ollama'
        
        # Use Claude for large context
        if context_size > 30000 and 'anthropic' in self.providers:
            logger.info("Using Claude for large context")
            return 'anthropic'
        
        # Use cheap cloud model for moderate complexity
        if task_complexity <= 8 and budget_remaining > 1.0:
            if 'openai' in self.providers:
                logger.info("Using GPT-3.5 for moderate task")
                return 'openai'
        
        # Premium model for complex tasks
        if task_complexity >= 9 and budget_remaining > 5.0:
            logger.info("Using premium model for complex task")
            return 'anthropic' if 'anthropic' in self.providers else 'openai'
        
        # Fallback to default
        return self.default_provider


class TokenOptimizer:
    """Optimizes prompts and context to reduce token usage."""
    
    def __init__(self, max_context_tokens: int = 4000):
        """
        Initialize token optimizer.
        
        Args:
            max_context_tokens: Maximum context size
        """
        self.max_context_tokens = max_context_tokens
    
    def optimize_log_content(self, log_content: str, max_lines: int = 500) -> str:
        """
        Optimize log content to reduce tokens.
        
        Args:
            log_content: Raw log content
            max_lines: Maximum lines to keep
            
        Returns:
            Optimized log content
        """
        lines = log_content.split('\n')
        
        if len(lines) <= max_lines:
            return log_content
        
        # Extract relevant lines (errors, warnings)
        error_lines = [l for l in lines if any(
            keyword in l.lower() 
            for keyword in ['error', 'exception', 'fail', 'critical']
        )]
        
        warning_lines = [l for l in lines if 'warning' in l.lower() or 'warn' in l.lower()]
        
        # Take recent lines
        recent_lines = lines[-100:]
        
        # Combine
        relevant = error_lines + warning_lines + recent_lines
        
        # Deduplicate while preserving order
        seen = set()
        optimized = []
        for line in relevant:
            if line not in seen:
                seen.add(line)
                optimized.append(line)
            if len(optimized) >= max_lines:
                break
        
        result = '\n'.join(optimized)
        
        logger.info(f"Optimized log: {len(lines)} ? {len(optimized)} lines "
                   f"({len(log_content)} ? {len(result)} chars)")
        
        return result
    
    def optimize_context(self, context: str) -> str:
        """
        Optimize context to fit within token limits.
        
        Args:
            context: Raw context text
            
        Returns:
            Optimized context
        """
        # Rough estimate: 1 token ? 4 characters
        estimated_tokens = len(context) // 4
        
        if estimated_tokens <= self.max_context_tokens:
            return context
        
        # Need to truncate
        target_chars = self.max_context_tokens * 4
        
        # Keep first and last parts
        keep_start = target_chars // 2
        keep_end = target_chars // 2
        
        truncated = (
            context[:keep_start] +
            f"\n\n... [TRUNCATED {estimated_tokens - self.max_context_tokens} tokens] ...\n\n" +
            context[-keep_end:]
        )
        
        logger.warning(f"Context truncated: {estimated_tokens} ? {self.max_context_tokens} tokens")
        
        return truncated
    
    def create_log_summary_prompt(self, log_content: str) -> str:
        """
        Create optimized prompt for log summarization.
        
        Args:
            log_content: Log content to summarize
            
        Returns:
            Optimized prompt
        """
        # Optimize log content first
        optimized_logs = self.optimize_log_content(log_content)
        
        prompt = f"""Analyze the following log excerpt and provide a concise summary focusing on:
1. Critical errors or failures
2. Root cause if identifiable
3. Relevant warnings or anomalies

Log excerpt:
```
{optimized_logs}
```

Provide a brief summary (max 200 words) of the key issues."""
        
        return prompt
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ? 4 characters
        # More accurate would use tiktoken for OpenAI
        return len(text) // 4
    
    def should_use_streaming(self, estimated_response_tokens: int) -> bool:
        """
        Determine if streaming should be used.
        
        Args:
            estimated_response_tokens: Expected response size
            
        Returns:
            True if streaming recommended
        """
        # Stream for responses > 500 tokens (better UX)
        return estimated_response_tokens > 500
