"""Coping Strategy Agent - Light wellness techniques."""
from typing import Dict, Any, List
from .base import BaseAgent

class CopingStrategyAgent(BaseAgent):
    """Suggests light, non-clinical wellness techniques."""
    
    SYSTEM_PROMPT = """You are the Coping Strategy Agent.
    Suggest 2-3 light, non-clinical wellness techniques based on the user's state.
    
    Allowed techniques:
    - Breathing exercises (box breathing, 4-7-8)
    - Grounding techniques (5-4-3-2-1 method)
    - Light physical movement (stretching, walking)
    - Journaling prompts
    - Time-boxing or Pomodoro for focus
    - Mindfulness observation
    
    Rules:
    - Keep suggestions optional ("You might try..." or "Consider...")
    - No medical claims (don't say "this cures anxiety")
    - Keep it simple (2-5 minutes max per technique)
    - Include brief instructions
    
    Output valid JSON:
    {{
        "suggestions": [
            {{
                "technique": "name of technique",
                "duration": "time required",
                "instructions": "brief steps",
                "context": "why this might help"
            }}
        ]
    }}"""
    
    def suggest(self, emotional_state: str, intent: str) -> Dict[str, Any]:
        """Generate coping strategies."""
        chain = self.create_chain(
            self.SYSTEM_PROMPT,
            "Emotional state: {state}\nIntent: {intent}\nSuggest techniques."
        )
        
        response = chain.invoke({
            "state": emotional_state,
            "intent": intent
        })
        
        result = self.safe_json_parse(response.content)
        result.setdefault("suggestions", [
            {
                "technique": "Box Breathing",
                "duration": "2 minutes",
                "instructions": "Inhale 4 counts, hold, exhale, hold",
                "context": "Helps regulate nervous system"
            }
        ])
        
        return result