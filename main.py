import json
import sys
from typing import Dict, Any
from dotenv import load_dotenv

from graph import app
from langchain_core.messages import HumanMessage

load_dotenv()

def format_output(output: Dict[str, Any]) -> str:
    """Pretty print the final wellness response."""
    final = output.get("final_output", {})
    
    lines = []
    lines.append("=" * 60)
    lines.append("MENTAL WELLNESS AGENT RESPONSE")
    lines.append("=" * 60)
    
    # Empathy section
    if "empathy" in final:
        lines.append(f"\nUnderstanding:\n{final['empathy']}")
    
    # Practical steps
    if "practical_steps" in final and final["practical_steps"]:
        lines.append("\nPractical Steps:")
        for i, step in enumerate(final["practical_steps"], 1):
            if isinstance(step, dict):
                lines.append(f"   {i}. {step.get('technique', step)}")
                if "instructions" in step:
                    lines.append(f"      → {step['instructions']}")
            else:
                lines.append(f"   {i}. {step}")
    
    # Resources
    if "optional_resources" in final and final["optional_resources"]:
        lines.append("\nOptional Resources:")
        for res in final["optional_resources"]:
            if isinstance(res, dict):
                lines.append(f"   • {res.get('title', 'Resource')}")
                if "source" in res:
                    lines.append(f"     Source: {res['source']}")
            else:
                lines.append(f"   • {res}")
    
    # Closing
    if "closing" in final:
        lines.append(f"\n{final['closing']}")
    
    # Disclaimer
    lines.append("\n" + "-" * 60)
    lines.append("DISCLAIMER: " + final.get("disclaimer", "Not medical advice."))
    lines.append("-" * 60)
    
    return "\n".join(lines)

def run_agent(user_input: str) -> Dict[str, Any]:
    """Run the wellness agent with user input."""
    try:
        result = app.invoke({
            "user_input": user_input,
            "messages": [HumanMessage(content=user_input)]
        })
        return result
    except Exception as e:
        return {
            "error": str(e),
            "final_output": {
                "empathy": "I apologize, but I encountered a technical issue.",
                "practical_steps": ["Please try again later"],
                "disclaimer": "System error occurred."
            }
        }

def interactive_mode():
    """Run interactive CLI session."""
    print("=" * 60)
    print("Mental Wellness Agent (Local Mode)")
    print("Type 'exit', 'quit', or press Ctrl+C to exit")
    print("=" * 60)
    
    while True:
        try:
            print("\n")
            user_input = input("How are you feeling today? > ").strip()
            
            if user_input.lower() in ["exit", "quit"]:
                print("\nTake care!")
                break
            
            if not user_input:
                continue
            
            print("\nProcessing... (this may take a moment)")
            result = run_agent(user_input)
            
            print(format_output(result))
            
            # Debug: Show workflow state (optional)
            if "--debug" in sys.argv:
                print("\n[DEBUG] Full state:")
                print(json.dumps(result, indent=2, default=str))
                
        except KeyboardInterrupt:
            print("\n\nTake care!")
            break
        except Exception as e:
            print(f"\nError: {e}")

def single_mode(user_input: str):
    """Run single query and output JSON."""
    result = run_agent(user_input)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] not in ["--debug", "-d"]:
        # Single query mode: python main.py "I feel stressed"
        single_mode(" ".join(sys.argv[1:]))
    else:
        # Interactive mode
        interactive_mode()