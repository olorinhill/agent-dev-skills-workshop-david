"""ReadyNow multi-agent definition for Challenge 6."""

from __future__ import annotations

from datetime import datetime, timezone

from google.adk.agents import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools import google_search

from .callbacks import chained_before_callback, log_model_response
from .tools import get_evacuation_route, get_lat_lon, get_weather_forecast


def _search_instruction() -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return (
        "You are the ReadyNow internet search specialist.\n"
        f"Today's UTC date is {today}.\n"
        "Use google_search for current, factual disaster updates and official guidance.\n"
        "Cite sources in plain language and call out uncertainty when information changes quickly."
    )


def build_ready_now_root_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Build the root multi-agent system for FEMA ReadyNow."""
    weather_agent = Agent(
        name="weather_agent",
        model=model,
        description="Provides US weather forecasts and alert signals for emergency preparedness.",
        instruction=(
            "You are the ReadyNow weather specialist.\n"
            "1. Resolve location using get_lat_lon.\n"
            "2. Fetch current conditions with get_weather_forecast.\n"
            "3. Summarize risks and practical safety actions in concise bullet points.\n"
            "4. If location is non-US, ask for a US location."
        ),
        tools=[get_lat_lon, get_weather_forecast],
        before_model_callback=chained_before_callback,
        after_model_callback=log_model_response,
    )

    search_agent = Agent(
        name="search_agent",
        model=model,
        description="Finds up-to-date emergency information from the public web.",
        instruction=_search_instruction(),
        tools=[google_search],
        # Keep google_search as the only tool in request payloads (Gemini constraint).
        disallow_transfer_to_parent=True,
        disallow_transfer_to_peers=True,
        before_model_callback=chained_before_callback,
        after_model_callback=log_model_response,
    )

    route_agent = Agent(
        name="route_agent",
        model=model,
        description="Provides route options to safer locations using Google Maps directions.",
        instruction=(
            "You are the ReadyNow evacuation route specialist.\n"
            "Use get_evacuation_route when the user provides an origin and destination.\n"
            "Explain route duration, distance, and first key steps.\n"
            "If destination is missing, ask clarifying questions."
        ),
        tools=[get_evacuation_route],
        before_model_callback=chained_before_callback,
        after_model_callback=log_model_response,
    )

    qa_agent = Agent(
        name="qa_agent",
        model=model,
        description="Drafts a mission-focused emergency response.",
        instruction=(
            "You draft the initial emergency response.\n"
            "Use the user question and any available context from earlier specialist calls.\n"
            "Create a clear response with immediate actions, a short rationale, and follow-up steps."
        ),
        output_key="initial_answer",
        before_model_callback=chained_before_callback,
        after_model_callback=log_model_response,
    )

    critique_agent = Agent(
        name="critique_agent",
        model=model,
        description="Validates completeness, clarity, and safety before final response.",
        instruction=(
            "Review the drafted response in {initial_answer}.\n"
            "Return a short critique covering:\n"
            "1. Accuracy and caution level\n"
            "2. Missing details or assumptions\n"
            "3. Improvements for readability and next actions"
        ),
        output_key="critique",
        before_model_callback=chained_before_callback,
        after_model_callback=log_model_response,
    )

    refine_agent = Agent(
        name="refine_agent",
        model=model,
        description="Produces the final polished emergency guidance.",
        instruction=(
            "Rewrite the final response using:\n"
            "- Initial answer: {initial_answer}\n"
            "- Critique: {critique}\n"
            "Return practical, easy-to-understand safety guidance."
        ),
        output_key="final_answer",
        before_model_callback=chained_before_callback,
        after_model_callback=log_model_response,
    )

    response_workflow = SequentialAgent(
        name="response_workflow_sequential",
        description="Runs answer, critique, and refine in sequence.",
        sub_agents=[qa_agent, critique_agent, refine_agent],
    )

    root_agent = Agent(
        name="ready_now_root_agent",
        model=model,
        description=(
            "FEMA ReadyNow assistant for US emergency preparedness, weather updates, "
            "evacuation routes, and safety Q&A."
        ),
        instruction=(
            "You are ReadyNow, FEMA's emergency preparedness assistant.\n"
            "Capabilities:\n"
            "- Weather forecasting and risk alerts for US locations.\n"
            "- Real-time disaster and safety updates via web search.\n"
            "- Suggested evacuation routes using Google Maps directions.\n"
            "- Refined question answering through a validate/refine workflow.\n"
            "Routing rules:\n"
            "1. Delegate weather requests to weather_agent.\n"
            "2. Delegate route requests to route_agent.\n"
            "3. Delegate current-events/news requests to search_agent.\n"
            "4. Delegate broad safety questions and final composition to response_workflow_sequential.\n"
            "Never fabricate tool results. Keep guidance concise, actionable, and mission-focused."
        ),
        sub_agents=[weather_agent, search_agent, route_agent, response_workflow],
        before_model_callback=chained_before_callback,
        after_model_callback=log_model_response,
    )
    return root_agent
