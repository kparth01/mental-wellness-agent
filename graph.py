"""
LangGraph workflow definition for Mental Wellness Agent.
Implements Supervisor → Planner → Executor → Aggregator pattern.
"""
import os
from typing import Dict, Any, TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
import operator

from agents.supervisor import SupervisorAgent
from agents.planner import PlannerAgent
from agents.emotion_reflection import EmotionReflectionAgent
from agents.coping_strategy import CopingStrategyAgent
from agents.resource_agent import ResourceAgent
from agents.aggregator import AggregatorAgent

# Initialize agents
supervisor = SupervisorAgent()
planner = PlannerAgent()
emotion_agent = EmotionReflectionAgent()
coping_agent = CopingStrategyAgent()
resource_agent = ResourceAgent()
aggregator = AggregatorAgent()

# State definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_input: str
    supervisor_output: Dict[str, Any]
    plan: Dict[str, Any]
    emotion_result: Dict[str, Any]
    coping_result: Dict[str, Any]
    resource_result: Dict[str, Any]
    final_output: Dict[str, Any]
    next_step: str

# Node functions
def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Supervisor validates input and determines routing."""
    user_input = state["user_input"]
    result = supervisor.process(user_input)
    
    if not result.get("allowed", True):
        return {
            "supervisor_output": result,
            "next_step": "end_blocked"
        }
    
    return {
        "supervisor_output": result,
        "next_step": "planner"
    }

def planner_node(state: AgentState) -> Dict[str, Any]:
    """Planner creates execution strategy."""
    sup = state["supervisor_output"]
    plan = planner.create_plan(
        intent=sup.get("intent", "general wellness"),
        emotional_state=sup.get("emotional_state", "neutral")
    )
    
    return {
        "plan": plan,
        "next_step": "executor"
    }

def emotion_node(state: AgentState) -> Dict[str, Any]:
    """Execute emotion reflection."""
    result = emotion_agent.reflect(
        user_input=state["user_input"],
        emotional_state=state["supervisor_output"].get("emotional_state", "neutral")
    )
    return {"emotion_result": result}

def coping_node(state: AgentState) -> Dict[str, Any]:
    """Execute coping strategies."""
    result = coping_agent.suggest(
        emotional_state=state["supervisor_output"].get("emotional_state", "neutral"),
        intent=state["supervisor_output"].get("intent", "general wellness")
    )
    return {"coping_result": result}

def resource_node(state: AgentState) -> Dict[str, Any]:
    """Execute resource fetching."""
    result = resource_agent.fetch_resources(
        topic=state["supervisor_output"].get("intent", "wellness"),
        emotional_state=state["supervisor_output"].get("emotional_state", "neutral")
    )
    return {"resource_result": result}

def aggregator_node(state: AgentState) -> Dict[str, Any]:
    """Combine all results."""
    final = aggregator.aggregate(
        reflection=state.get("emotion_result", {}),
        strategies=state.get("coping_result", {}),
        resources=state.get("resource_result", {}),
        original_input=state["user_input"]
    )
    return {
        "final_output": final,
        "next_step": "end"
    }

def blocked_node(state: AgentState) -> Dict[str, Any]:
    """Handle blocked requests."""
    sup = state["supervisor_output"]
    final = {
        "empathy": "I notice you may be going through something serious.",
        "practical_steps": [
            "Please reach out to a mental health professional",
            "Contact crisis resources if needed"
        ],
        "optional_resources": [
            "National Suicide Prevention Lifeline: 988",
            "Crisis Text Line: Text HOME to 741741"
        ],
        "closing": "You don't have to go through this alone.",
        "disclaimer": "This system cannot provide crisis support.",
        "blocked_reason": sup.get("reason_if_blocked", "Safety guardrail triggered")
    }
    return {"final_output": final, "next_step": "end"}

# Conditional routing logic
def route_from_supervisor(state: AgentState) -> str:
    """Determine next step after supervisor."""
    if state["next_step"] == "end_blocked":
        return "blocked"
    return "planner"

def route_from_planner(state: AgentState) -> list:
    """Determine which agents to run based on plan."""
    plan = state["plan"].get("plan", ["emotion_reflection"])
    nodes = []
    
    # Always run these in parallel if included
    if "emotion_reflection" in plan:
        nodes.append("emotion_reflection")
    if "coping_strategy" in plan:
        nodes.append("coping_strategy")
    if "resource_agent" in plan:
        nodes.append("resource_agent")
    
    # If plan is empty, default to emotion
    if not nodes:
        nodes.append("emotion_reflection")
    
    return nodes

def route_from_executor(state: AgentState) -> str:
    """After executors, go to aggregator."""
    return "aggregator"

# Build graph
def create_workflow():
    """Create and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("emotion_reflection", emotion_node)
    workflow.add_node("coping_strategy", coping_node)
    workflow.add_node("resource_agent", resource_node)
    workflow.add_node("aggregator", aggregator_node)
    workflow.add_node("blocked", blocked_node)
    
    # Add edges
    workflow.set_entry_point("supervisor")
    
    # Conditional from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "planner": "planner",
            "blocked": "blocked"
        }
    )
    
    # Planner to executors (parallel)
    workflow.add_conditional_edges(
        "planner",
        route_from_planner,
        {
            "emotion_reflection": "emotion_reflection",
            "coping_strategy": "coping_strategy",
            "resource_agent": "resource_agent"
        }
    )
    
    # All executors go to aggregator
    workflow.add_edge("emotion_reflection", "aggregator")
    workflow.add_edge("coping_strategy", "aggregator")
    workflow.add_edge("resource_agent", "aggregator")
    
    # Aggregator and blocked end
    workflow.add_edge("aggregator", END)
    workflow.add_edge("blocked", END)
    
    return workflow.compile()

# Create compiled app
app = create_workflow()