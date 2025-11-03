"""PRD (Product Requirements Document) parser using LLM."""

import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from .llm.providers import LLMClient, LLMMessage

logger = logging.getLogger(__name__)


class PRDParser:
    """Parses PRD files and generates structured task lists using LLM."""
    
    def __init__(self, llm_client: LLMClient):
        """
        Initialize PRD Parser.
        
        Args:
            llm_client: LLM client for parsing PRDs
        """
        self.llm_client = llm_client
    
    async def parse_prd(
        self,
        prd_path: str,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse a PRD file and generate structured tasks.
        
        Args:
            prd_path: Path to PRD file (typically prd.txt or prd.md)
            provider: LLM provider to use (uses default if None)
            
        Returns:
            Parsed result with tasks and metadata
        """
        prd_file = Path(prd_path)
        if not prd_file.exists():
            # Try relative to current directory
            prd_file = Path.cwd() / prd_path
            if not prd_file.exists():
                # Try common names
                for name in ["prd.txt", "prd.md", "PRD.txt", "PRD.md"]:
                    potential = Path.cwd() / name
                    if potential.exists():
                        prd_file = potential
                        break
                    potential = Path.cwd() / ".taskmaster" / name
                    if potential.exists():
                        prd_file = potential
                        break
        
        if not prd_file.exists():
            raise FileNotFoundError(f"PRD file not found: {prd_path}")
        
        logger.info(f"Parsing PRD from {prd_file}")
        
        # Read PRD content
        with open(prd_file, 'r') as f:
            prd_content = f.read()
        
        # Generate tasks using LLM
        system_prompt = """You are an expert project manager that breaks down Product Requirements Documents (PRDs) into structured, actionable tasks.

Your job is to analyze the PRD and generate a list of tasks with:
- Clear, concise descriptions
- Logical dependencies (tasks must be done before dependent tasks)
- Appropriate priority levels (0-10, higher = more important)
- Subtasks when a task is complex

Return your response in the following JSON format:
{
  "summary": "Brief summary of the project",
  "tasks": [
    {
      "id": "task-1",
      "description": "Clear task description",
      "priority": 5,
      "dependencies": [],
      "subtasks": []
    },
    {
      "id": "task-2",
      "description": "Another task",
      "priority": 7,
      "dependencies": ["task-1"],
      "subtasks": ["subtask-2-1", "subtask-2-2"]
    }
  ],
  "subtasks": [
    {
      "id": "subtask-2-1",
      "description": "Subtask description",
      "parent_task": "task-2"
    }
  ]
}

Make sure:
- Task IDs are unique and descriptive
- Dependencies reference existing task IDs
- Priorities reflect importance (0 = low, 10 = critical)
- Tasks are broken down into manageable chunks
- Dependencies make logical sense"""
        
        user_prompt = f"""Please analyze the following PRD and generate a structured task breakdown:

{prd_content}

Generate the task list in JSON format as specified."""
        
        try:
            response = await self.llm_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                provider=provider or "anthropic",  # Use Anthropic for better reasoning
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=4000
            )
            
            # Parse JSON from response
            content = response.content.strip()
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
            
            import json
            parsed = json.loads(content)
            
            # Validate structure
            if "tasks" not in parsed:
                raise ValueError("LLM response missing 'tasks' field")
            
            logger.info(f"Parsed PRD into {len(parsed['tasks'])} tasks")
            
            return {
                "success": True,
                "summary": parsed.get("summary", ""),
                "tasks": parsed.get("tasks", []),
                "subtasks": parsed.get("subtasks", []),
                "metadata": {
                    "prd_file": str(prd_file),
                    "model": response.model,
                    "tokens_used": response.tokens_used,
                    "cost": response.cost
                }
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {content[:500]}")
            raise ValueError(f"Failed to parse LLM response: {e}")
        except Exception as e:
            logger.error(f"PRD parsing failed: {e}")
            raise
    
    async def expand_task_with_research(
        self,
        task_description: str,
        research_query: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Expand a task into subtasks using research capabilities.
        Can use external APIs (like Perplexity) for research context.
        
        Args:
            task_description: Description of the task to expand
            research_query: Optional research query for gathering context
            provider: LLM provider (prefer research-capable models)
            
        Returns:
            Expanded task breakdown with subtasks
        """
        system_prompt = """You are an expert task breakdown specialist. Your job is to break complex tasks into smaller, actionable subtasks.

When given a task description, analyze it and break it down into:
- Clear, sequential subtasks
- Logical ordering (dependencies implied by order)
- Specific, actionable items (not vague)
- Appropriate granularity (not too fine, not too coarse)

Return your response as JSON:
{
  "analysis": "Brief analysis of the task complexity",
  "subtasks": [
    "Subtask 1 description",
    "Subtask 2 description",
    "Subtask 3 description"
  ]
}"""
        
        user_prompt = f"""Please break down the following task into actionable subtasks:

Task: {task_description}

{f'Research context: {research_query}' if research_query else ''}

Generate subtasks that are:
- Specific and actionable
- Logically ordered
- Appropriate granularity (typically 3-10 subtasks)
- Clear and unambiguous"""
        
        try:
            response = await self.llm_client.generate(
                prompt=user_prompt,
                system=system_prompt,
                provider=provider,
                temperature=0.4,
                max_tokens=2000
            )
            
            content = response.content.strip()
            
            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
            
            import json
            parsed = json.loads(content)
            
            return {
                "success": True,
                "analysis": parsed.get("analysis", ""),
                "subtasks": parsed.get("subtasks", []),
                "metadata": {
                    "model": response.model,
                    "tokens_used": response.tokens_used,
                    "cost": response.cost
                }
            }
        
        except Exception as e:
            logger.error(f"Task expansion failed: {e}")
            raise