"""Emotion Reflection Agent - Empathetic reflection."""
from typing import Dict, Any
from .base import BaseAgent

class EmotionReflectionAgent(BaseAgent):
    """Provides empathetic reflection without advice."""
    
    SYSTEM_PROMPT = """You are the Emotion Reflection Agent.
    Your role is to:
    1. Reflect the user's emotions with empathy and validation
    2. Normalize their feelings (it's okay to feel this way)
    3. Reframe thoughts positively when appropriate
    4. DO NOT give advice, only reflect and validate
    
    Tone: Warm, non-judgmental, supportive
    Constraints: No medical language, no diagnosis, no "you should" statements
    
    Output valid JSON:
    {{
        "reflection": "empathetic reflection text",
        "normalization": "statement normalizing their feelings",
        "reframe": "positive reframe of their situation"
    }}"""
    
    def reflect(self, user_input: str, emotional_state: str) -> Dict[str, Any]:
        """Generate emotional reflection."""
        chain = self.create_chain(
            self.SYSTEM_PROMPT,
            "User said: {input}\nDetected emotion: {emotion}\nProvide reflection."
        )
        
        response = chain.invoke({
            "input": user_input,
            "emotion": emotional_state
        })
        
        result = self.safe_json_parse(response.content)
        result.setdefault("reflection", "I hear that you're going through something difficult.")
        result.setdefault("normalization", "Many people feel this way.")
        result.setdefault("reframe", "This moment is temporary.")
        
        return result