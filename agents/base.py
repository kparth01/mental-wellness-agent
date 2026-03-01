"""Base agent class with common utilities."""
import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    """Base class for all wellness agents."""
    
    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.7):
        self.llm = ChatOpenAI(
            model_name=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self._validate_setup()
    
    def _validate_setup(self):
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    def create_chain(self, system_prompt: str, template: str):
        """Create a LangChain chain with system prompt."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", template)
        ])
        return prompt | self.llm
    
    def safe_json_parse(self, content: str) -> Dict[str, Any]:
        """Safely parse JSON from LLM output."""
        import json
        import re
        
        # Try to extract JSON if wrapped in markdown
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback: return structured error
            return {
                "error": "Failed to parse JSON",
                "raw_content": content[:200]
            }