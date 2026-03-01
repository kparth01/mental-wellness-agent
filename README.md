# Mental Wellness Agent (Local LangGraph)

A local-first, multi-agent Mental Wellness AI system built with LangGraph. Implements a **Supervisor → Planner → Executor → Aggregator** architecture for safe, supportive mental wellness conversations.

**Author:** Nisarg Kadam – Agentic AI & Automation Architect

## Architecture
User Input

↓

Supervisor Agent (Safety & Routing)

↓

Planner Agent (Task Decomposition)

↓

Executor Agents (Parallel Execution)

├─ Emotion Reflection Agent

├─ Coping Strategy Agent

└─ Resource Agent

↓

Aggregator Agent (Response Composition)

↓

Final Wellness Response


## Prerequisites

- Python 3.10+
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))
- Windows PowerShell or Git Bash (for commands below)

## Quick Start (Windows)

Copy and run these commands in PowerShell:

```powershell
# 1. Navigate to project folder
cd "C:\Users\nisar\Documents\AI Builder 2\Projects\MentalWellness\mental-wellness-agent"

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Set up environment variables
cp .env.example .env
# Edit .env file and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-key-here

# 6. Run the agent
python main.py

Project Structure
mental-wellness-agent/
├── agents/
│   ├── __init__.py
│   ├── base.py                 # Base agent class with shared utilities
│   ├── supervisor.py           # Entry point & safety guardrails
│   ├── planner.py              # Task decomposition
│   ├── emotion_reflection.py   # Empathetic reflection (no advice)
│   ├── coping_strategy.py      # Wellness techniques
│   ├── resource_agent.py       # External resources
│   └── aggregator.py           # Final response composition
├── graph.py                    # LangGraph workflow definition
├── main.py                     # CLI interface
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file

Configuration
Edit .env file:
env

OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini      # Options: gpt-4o-mini, gpt-4, gpt-3.5-turbo
TEMPERATURE=0.7               # 0.0-1.0 (lower = more focused/deterministic)

Usage

Interactive Mode
python main.py
Then type how you're feeling when prompted.

Single Query Mode --> python main.py "I'm feeling stressed about my presentation tomorrow"

Debug Mode (shows full workflow state) --> python main.py --debug

Example Interaction
Input:
I'm feeling overwhelmed with my workload and can't focus on anything.
Output:
Copy
============================================================
MENTAL WELLNESS AGENT RESPONSE
============================================================

Understanding:
It sounds like you're carrying a heavy mental load right now, and that feeling of everything being too much is completely valid...

Practical Steps:
   1. Box Breathing Technique
      → Inhale for 4 counts, hold for 4, exhale for 4, hold for 4
      → Repeat for 2 minutes
   2. Brain Dump
      → Write down every task on your mind without organizing
      → Helps clear mental RAM
   3. Single-Task Focus
      → Pick ONE small task (5 minutes max)
      → Complete it before looking at the full list

Optional Resources:
   • Headspace Focus Exercises (App - Free tier available)
   • NIH: Managing Workplace Stress (Article)
   • 5-4-3-2-1 Grounding Technique (YouTube)

Closing:
Be gentle with yourself. You don't have to solve everything right now.

------------------------------------------------------------
DISCLAIMER: This is not medical advice. Consult a qualified healthcare professional for clinical support.
------------------------------------------------------------
Safety Features
Medical Guardrails: Blocks requests for diagnosis, medication advice, or clinical treatment
Crisis Detection: Recognizes crisis language and provides immediate resources
Non-Diagnostic: All responses include appropriate disclaimers
Optional Tone: All suggestions presented as optional, not prescriptive


Extending the System
Adding a New Sub-Agent
Create agents/new_agent.py:
Python

from .base import BaseAgent

class NewAgent(BaseAgent):
    def process(self, input_data: dict) -> dict:
        # Your logic here
        return {"result": "output"}
Register in graph.py:

Import the agent
Add node: workflow.add_node("new_agent", node_function)
Update planner logic in agents/planner.py
Add edges connecting to aggregator
Modifying Safety Rules

Disclaimer
This agent is designed for general wellness support only. It does not provide medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.
If you're in crisis:
US: Call or text 988 (Suicide & Crisis Lifeline) - Available 24/7
UK: Call Samaritans at 116 123
Global: Visit findahelpline.com for local resources
License
MIT License - feel free to use, modify, and distribute with attribution.
Created by Nisarg Kadam – Agentic AI & Automation Architect
Building local-first AI systems for human wellbeing.
