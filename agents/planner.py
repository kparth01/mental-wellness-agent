"""Planner Agent - Task decomposition."""
from typing import Dict, Any, List
from .base import BaseAgent

class PlannerAgent(BaseAgent):
    """Decomposes user intent into executable tasks."""
    
    SYSTEM_PROMPT = """You are the Planner Agent for a Mental Wellness system.
    Based on the user's intent and emotional state, create a plan of which sub-agents to invoke.
    
    Available agents:
    - emotion_reflection: Reflects and normalizes feelings (use for emotional support)
    - coping_strategy: Suggests light wellness techniques (use for stress/burnout/focus)
    - resource_agent: Fetches external wellness resources (use when user wants exercises/articles)
    
    Rules:
    - Always include emotion_reflection for emotional inputs
    - Include coping_strategy for stress/burnout/focus issues
    - Include resource_agent if user asks for techniques, exercises, or articles
    - Order matters: reflection → coping → resources
    
    Output valid JSON:
    {{
        "plan": ["agent_name_1", "agent_name_2"],
        "reasoning": "brief explanation of choices"
    }}"""
    
    def create_plan(self, intent: str, emotional_state: str) -> Dict[str, Any]:
        """Create execution plan based on supervisor output."""
        chain = self.create_chain(
            self.SYSTEM_PROMPT,
            "Intent: {intent}\nEmotional State: {state}\nCreate execution plan."
        )
        
        response = chain.invoke({
            "intent": intent,
            "state": emotional_state
        })
        
        result = self.safe_json_parse(response.content)
        result.setdefault("plan", ["emotion_reflection"])
        result.setdefault("reasoning", "Default reflection plan")
        
        return result