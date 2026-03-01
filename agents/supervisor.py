"""Supervisor Agent - Entry point and safety gate."""
import json
from typing import Dict, Any
from .base import BaseAgent

class SupervisorAgent(BaseAgent):
    """Orchestrates input validation and routing."""
    
    SYSTEM_PROMPT = """You are the Supervisor Agent for a Mental Wellness AI system.
    Your role is to:
    1. Analyze user input for intent and emotional state
    2. Validate that requests are NON-CLINICAL (no medical advice, diagnosis, or crisis intervention)
    3. Detect emotional tone (stress, anxiety, burnout, focus issues, general wellness)
    4. Enforce guardrails strictly
    
    CRITICAL GUARDRAILS:
    - If user mentions self-harm, suicide, or crisis: Set "allowed" to false and provide crisis resources
    - If user asks for medical diagnosis or medication advice: Set "allowed" to false
    - Only allow general wellness, stress management, focus, and emotional support topics
    
    Output MUST be valid JSON:
    {{
        "intent": "",
        "emotional_state": "",
        "allowed": true/false,
        "reason_if_blocked": "explanation if blocked, null if allowed",
        "safety_note": "include disclaimer about non-medical nature"
    }}"""
    
    def process(self, user_input: str) -> Dict[str, Any]:
        """Process user input and return routing decision."""
        chain = self.create_chain(
            self.SYSTEM_PROMPT,
            "Analyze this user input: {input}"
        )
        
        response = chain.invoke({"input": user_input})
        result = self.safe_json_parse(response.content)
        
        # Ensure required fields
        result.setdefault("intent", "general wellness")
        result.setdefault("emotional_state", "neutral")
        result.setdefault("allowed", True)
        result.setdefault("safety_note", "This is not medical advice.")
        
        return result