"""Aggregator Agent - Final response composer."""
from typing import Dict, Any, List
from .base import BaseAgent

class AggregatorAgent(BaseAgent):
    """Combines all sub-agent outputs into final response."""
    
    SYSTEM_PROMPT = """You are the Aggregator Agent for a Mental Wellness system.
    Combine outputs from multiple sub-agents into a cohesive, supportive final response.
    
    Input sections:
    - Reflection: Empathetic validation from Emotion Agent
    - Strategies: Practical techniques from Coping Agent  
    - Resources: External links from Resource Agent
    
    Rules:
    1. Maintain calm, warm, supportive tone throughout
    2. Remove any duplicate suggestions
    3. Ensure NO medical or diagnostic language
    4. Add gentle disclaimer at end
    5. Format for readability
    
    Structure:
    - Opening validation (from reflection)
    - Practical steps (from strategies)
    - Optional resources (if provided)
    - Disclaimer
    
    Output valid JSON:
    {{
        "empathy": "opening empathetic statement",
        "practical_steps": ["step 1", "step 2"],
        "optional_resources": ["resource 1"],
        "closing": "supportive closing",
        "disclaimer": "medical disclaimer"
    }}"""
    
    def aggregate(
        self,
        reflection: Dict[str, Any],
        strategies: Dict[str, Any],
        resources: Dict[str, Any],
        original_input: str
    ) -> Dict[str, Any]:
        """Combine all outputs into final response."""
        
        # Prepare context for LLM
        context = f"""
        Original user input: {original_input}
        
        Reflection output: {reflection}
        
        Strategies output: {strategies}
        
        Resources output: {resources}
        """
        
        chain = self.create_chain(
            self.SYSTEM_PROMPT,
            "Combine these outputs into final response:\n{context}"
        )
        
        response = chain.invoke({"context": context})
        result = self.safe_json_parse(response.content)
        
        # Ensure structure
        result.setdefault("empathy", "Thank you for sharing how you're feeling.")
        result.setdefault("practical_steps", [])
        result.setdefault("optional_resources", [])
        result.setdefault("closing", "Take care of yourself.")
        result.setdefault("disclaimer", "This is not medical advice. Consult a professional for clinical support.")
        
        return result