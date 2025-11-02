"""AI Agent with plan-execute-reflect loop for autonomous DevOps operations."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from ..llm.providers import LLMClient, LLMMessage

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """Task complexity levels."""
    SIMPLE = 1      # Simple query, single step
    MODERATE = 5    # Multiple steps, straightforward
    COMPLEX = 8     # Multiple steps with dependencies
    ADVANCED = 10   # Requires deep reasoning, many steps


@dataclass
class AgentStep:
    """Single step in agent execution."""
    step_num: int
    description: str
    tool: str
    args: Dict[str, Any]
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class AgentPlan:
    """Agent execution plan."""
    goal: str
    steps: List[Dict[str, Any]]
    complexity: TaskComplexity
    estimated_time: int  # seconds


class AIAgent:
    """Autonomous AI agent with plan-execute-reflect capabilities."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: Dict[str, Any],
        max_iterations: int = 10
    ):
        """
        Initialize AI agent.
        
        Args:
            llm_client: LLM client for AI operations
            tool_registry: Available tools
            max_iterations: Maximum plan-execute iterations
        """
        self.llm = llm_client
        self.tools = tool_registry
        self.max_iterations = max_iterations
        
        self.conversation_history: List[LLMMessage] = []
    
    async def process_prompt(
        self,
        user_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process user prompt through plan-execute-reflect loop.
        
        Args:
            user_prompt: User's natural language request
            context: Additional context (profile, environment, etc.)
            
        Returns:
            Final response
        """
        logger.info(f"Processing prompt: {user_prompt[:100]}...")
        
        try:
            # Phase 1: Parse & Understand
            intent = await self._parse_intent(user_prompt, context)
            logger.info(f"Intent: {intent['intent_type']}")
            
            # Phase 2: Plan
            plan = await self._create_plan(user_prompt, intent, context)
            logger.info(f"Plan created with {len(plan.steps)} steps")
            
            # Phase 3: Execute
            execution_results = await self._execute_plan(plan)
            logger.info(f"Plan executed: {len(execution_results)} steps completed")
            
            # Phase 4: Reflect & Synthesize
            final_response = await self._reflect_and_synthesize(
                user_prompt,
                plan,
                execution_results
            )
            
            return final_response
        
        except Exception as e:
            logger.error(f"Agent error: {e}", exc_info=True)
            return f"I encountered an error processing your request: {str(e)}"
    
    async def _parse_intent(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Parse user intent from natural language.
        
        Args:
            prompt: User prompt
            context: Context information
            
        Returns:
            Intent structure
        """
        system_prompt = """You are an intent parser for a DevOps AI assistant.
Analyze the user's request and extract:
1. Intent type (check_status, diagnose_failure, get_logs, execute_command, etc.)
2. Target entities (servers, services, clusters)
3. Key parameters
4. Urgency level

Respond in JSON format."""
        
        parse_prompt = f"""User request: {prompt}
        
Context: {context or 'None'}

Parse this request and respond with JSON containing:
- intent_type: main intent
- entities: list of target systems/services
- parameters: relevant parameters
- urgency: low/medium/high
- requires_confirmation: boolean (true if action could be destructive)"""
        
        response = await self.llm.generate(
            parse_prompt,
            system=system_prompt,
            temperature=0.3
        )
        
        # Parse JSON response
        import json
        try:
            intent = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback to basic parsing
            intent = {
                'intent_type': 'unknown',
                'entities': [],
                'parameters': {},
                'urgency': 'medium',
                'requires_confirmation': False
            }
        
        return intent
    
    async def _create_plan(
        self,
        prompt: str,
        intent: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> AgentPlan:
        """
        Create execution plan using LLM.
        
        Args:
            prompt: Original user prompt
            intent: Parsed intent
            context: Context information
            
        Returns:
            Execution plan
        """
        # Build tool descriptions
        tool_descriptions = self._format_available_tools()
        
        system_prompt = f"""You are a DevOps planning AI. Create a step-by-step plan to fulfill user requests.

Available tools:
{tool_descriptions}

Create a plan as a JSON array of steps. Each step should have:
- description: what to do
- tool: which tool to use
- args: arguments for the tool
- depends_on: list of previous step numbers this depends on (optional)

Make the plan efficient and safe. For diagnostic tasks, gather data before analysis."""
        
        plan_prompt = f"""User request: {prompt}

Intent: {intent['intent_type']}
Entities: {intent.get('entities', [])}

Create a detailed plan to fulfill this request. Consider:
1. What information do we need to gather?
2. In what order should we execute?
3. What safety checks are needed?

Respond with JSON plan."""
        
        response = await self.llm.generate(
            plan_prompt,
            system=system_prompt,
            temperature=0.5
        )
        
        # Parse plan
        import json
        try:
            plan_data = json.loads(response.content)
            steps = plan_data if isinstance(plan_data, list) else plan_data.get('steps', [])
        except json.JSONDecodeError:
            logger.warning("Failed to parse plan JSON, using fallback")
            steps = self._create_fallback_plan(intent)
        
        # Assess complexity
        complexity = self._assess_complexity(steps, intent)
        
        return AgentPlan(
            goal=prompt,
            steps=steps,
            complexity=complexity,
            estimated_time=len(steps) * 10  # rough estimate
        )
    
    def _format_available_tools(self) -> str:
        """Format tool registry for LLM."""
        descriptions = []
        for name, tool in self.tools.items():
            desc = tool.get('description', 'No description')
            descriptions.append(f"- {name}: {desc}")
        
        return '\n'.join(descriptions[:20])  # Limit to top 20 tools
    
    def _assess_complexity(
        self,
        steps: List[Dict[str, Any]],
        intent: Dict[str, Any]
    ) -> TaskComplexity:
        """Assess task complexity."""
        num_steps = len(steps)
        
        if num_steps <= 2:
            return TaskComplexity.SIMPLE
        elif num_steps <= 5:
            return TaskComplexity.MODERATE
        elif num_steps <= 8:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ADVANCED
    
    def _create_fallback_plan(self, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create simple fallback plan if LLM planning fails."""
        intent_type = intent.get('intent_type', 'unknown')
        
        if intent_type == 'check_status':
            return [
                {
                    'description': 'Check system status',
                    'tool': 'ssh.execute',
                    'args': {'command': 'systemctl status'}
                }
            ]
        elif intent_type == 'get_logs':
            return [
                {
                    'description': 'Retrieve logs',
                    'tool': 'logs.tail',
                    'args': {'lines': 100}
                }
            ]
        else:
            return [
                {
                    'description': 'Execute user request',
                    'tool': 'generic',
                    'args': {}
                }
            ]
    
    async def _execute_plan(self, plan: AgentPlan) -> List[AgentStep]:
        """
        Execute plan steps.
        
        Args:
            plan: Execution plan
            
        Returns:
            Execution results
        """
        results = []
        
        for idx, step_def in enumerate(plan.steps, 1):
            if idx > self.max_iterations:
                logger.warning(f"Max iterations ({self.max_iterations}) reached")
                break
            
            step = AgentStep(
                step_num=idx,
                description=step_def.get('description', ''),
                tool=step_def.get('tool', ''),
                args=step_def.get('args', {})
            )
            
            logger.info(f"Step {idx}/{len(plan.steps)}: {step.description}")
            
            try:
                # Execute tool
                result = await self._execute_tool(step.tool, step.args)
                step.result = result
                logger.info(f"Step {idx} completed successfully")
            
            except Exception as e:
                step.error = str(e)
                logger.error(f"Step {idx} failed: {e}")
                
                # Decide whether to continue or abort
                if self._is_critical_failure(step, e):
                    logger.error("Critical failure - aborting plan")
                    break
            
            results.append(step)
            
            # Small delay between steps
            await asyncio.sleep(0.5)
        
        return results
    
    async def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """
        Execute a tool.
        
        Args:
            tool_name: Tool to execute
            args: Tool arguments
            
        Returns:
            Tool result
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        handler = tool.get('handler')
        
        if not handler:
            raise ValueError(f"No handler for tool: {tool_name}")
        
        # Execute tool handler
        if asyncio.iscoroutinefunction(handler):
            result = await handler(**args)
        else:
            result = await asyncio.to_thread(handler, **args)
        
        return result
    
    def _is_critical_failure(self, step: AgentStep, error: Exception) -> bool:
        """Determine if failure is critical (should abort)."""
        # Connection errors, auth errors are critical
        error_str = str(error).lower()
        critical_keywords = ['connection', 'authentication', 'permission', 'not found']
        
        return any(keyword in error_str for keyword in critical_keywords)
    
    async def _reflect_and_synthesize(
        self,
        original_prompt: str,
        plan: AgentPlan,
        execution_results: List[AgentStep]
    ) -> str:
        """
        Reflect on execution and synthesize final response.
        
        Args:
            original_prompt: Original user request
            plan: Execution plan
            execution_results: Results from execution
            
        Returns:
            Final response to user
        """
        # Format execution summary
        execution_summary = self._format_execution_summary(execution_results)
        
        system_prompt = """You are a DevOps AI assistant. Synthesize the execution results into a clear, helpful response for the user.

Focus on:
1. Directly answering their question
2. Highlighting key findings
3. Suggesting next steps if relevant
4. Being concise but informative

Use markdown formatting for readability."""
        
        synthesis_prompt = f"""Original request: {original_prompt}

Execution results:
{execution_summary}

Synthesize these results into a clear response. If there were failures, explain them. If successful, provide the key information."""
        
        response = await self.llm.generate(
            synthesis_prompt,
            system=system_prompt,
            temperature=0.7
        )
        
        return response.content
    
    def _format_execution_summary(self, results: List[AgentStep]) -> str:
        """Format execution results for LLM."""
        lines = []
        
        for step in results:
            status = "?" if not step.error else "?"
            lines.append(f"{status} Step {step.step_num}: {step.description}")
            
            if step.error:
                lines.append(f"   Error: {step.error}")
            elif step.result:
                # Truncate long results
                result_str = str(step.result)[:500]
                lines.append(f"   Result: {result_str}")
        
        return '\n'.join(lines)
    
    async def chat_turn(self, user_message: str) -> str:
        """
        Handle a single conversational turn (for REPL mode).
        
        Args:
            user_message: User's message
            
        Returns:
            Assistant's response
        """
        # Add to conversation history
        self.conversation_history.append(
            LLMMessage(role='user', content=user_message)
        )
        
        # Check if this is a simple conversational query or requires tools
        if self._is_simple_query(user_message):
            # Direct LLM response
            response = await self.llm.generate(
                user_message,
                system="You are a helpful DevOps assistant.",
                temperature=0.7
            )
            answer = response.content
        else:
            # Full agent loop
            answer = await self.process_prompt(user_message)
        
        # Add to history
        self.conversation_history.append(
            LLMMessage(role='assistant', content=answer)
        )
        
        # Keep history manageable
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        
        return answer
    
    def _is_simple_query(self, message: str) -> bool:
        """Check if query is simple conversation (no tools needed)."""
        message_lower = message.lower()
        
        # Simple queries
        simple_patterns = [
            'what is', 'who is', 'how do you', 'can you explain',
            'tell me about', 'what does', 'define', 'help'
        ]
        
        # Tool-requiring patterns
        action_patterns = [
            'check', 'show me', 'get', 'fetch', 'restart', 'deploy',
            'status of', 'logs from', 'running on'
        ]
        
        has_simple = any(p in message_lower for p in simple_patterns)
        has_action = any(p in message_lower for p in action_patterns)
        
        # Simple if it's a knowledge question and not an action
        return has_simple and not has_action
    
    def reset_conversation(self):
        """Reset conversation history."""
        self.conversation_history = []
        logger.info("Conversation history reset")
