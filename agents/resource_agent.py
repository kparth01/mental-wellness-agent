"""Resource Agent - Web search for wellness resources."""
from typing import Dict, Any, List
import requests
from .base import BaseAgent

class ResourceAgent(BaseAgent):
    """Fetches external wellness resources using web search."""
    
    SYSTEM_PROMPT = """You are the Resource Agent.
    Based on user needs, suggest relevant public wellness resources.
    Since you cannot browse live, use your knowledge to suggest:
    - Well-known wellness exercises (e.g., Headspace, Calm apps have free content)
    - Public domain mental health articles (NIH, APA, Mind.org)
    - YouTube meditation channels
    - Free PDF workbooks
    
    CRITICAL: Only suggest reputable, non-medical-advice resources.
    No diagnostic tools. Only wellness and educational content.
    
    Output valid JSON:
    {{
        "resources": [
            {{
                "title": "Resource name",
                "type": "article/video/exercise/app",
                "source": "Organization name",
                "description": "what it offers",
                "free": true/false,
                "url": "general URL if known"
            }}
        ],
        "disclaimer": "These are suggestions, not endorsements"
    }}"""
    
    def fetch_resources(self, topic: str, emotional_state: str) -> Dict[str, Any]:
        """Generate resource recommendations."""
        chain = self.create_chain(
            self.SYSTEM_PROMPT,
            "Topic: {topic}\nEmotional state: {state}\nSuggest resources."
        )
        
        response = chain.invoke({
            "topic": topic,
            "state": emotional_state
        })
        
        result = self.safe_json_parse(response.content)
        result.setdefault("resources", [])
        result.setdefault("disclaimer", "Not medical advice. Verify suitability for yourself.")
        
        return result