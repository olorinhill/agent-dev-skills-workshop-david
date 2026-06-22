# agent-dev-skills-workshop-david

Submission repository for the **Agentic AI with the Google Agent Development Kit (ADK): Skills Validation Workshop**.

This repo contains the challenge solutions, implemented as Colab Enterprise Jupyter notebooks that build, test, and (later) deploy generative AI agents on Google Cloud using the ADK, Gemini, and third-party models.

## Workshop challenges

| # | Challenge | Points | Status |
|---|-----------|--------|--------|
| 1 | Real-Time Weather Alerts Agent | 15 | Complete |
| 2 | Enhancing Agents with Callbacks | 15 | Complete |
| 3 | Developing Multi-Agent Systems | 15 | Complete |
| 4 | Programming an Agent Workflow | 15 | Complete |
| 5 | Deploying Agents (bonus) | 10 | Complete |
| 6 | Emergency Preparedness Assistant (case study) | 40 | Not started |

Passing the workshop requires 80 of 110 possible points.

## Repository structure

```
.
|- README.md                  # This file
|- challenge-one/
|  |- weather_alerts_agent.ipynb   # Challenge 1 notebook
|  |- README.md                    # Challenge 1 details
|- challenge-two/
|  |- callbacks_agent.ipynb        # Challenge 2 notebook
|  |- README.md                    # Challenge 2 details
|- challenge-3/
|  |- multi_agent_system.ipynb     # Challenge 3 notebook
|  |- README.md                    # Challenge 3 details
|- challenge-4/
|  |- agent_workflow.ipynb         # Challenge 4 notebook
|  |- README.md                    # Challenge 4 details
|- challenge-5/
|  |- deploy_agent.ipynb           # Challenge 5 notebook
|  |- README.md                    # Challenge 5 details
|- Agentic AI with the Google Agent Development Kit (ADK)_ ...pdf  # Workshop slides
```

## Challenge One: Real-Time Weather Alerts Agent

[`challenge-one/weather_alerts_agent.ipynb`](challenge-one/weather_alerts_agent.ipynb) is a self-contained notebook that:

- Defines two custom ADK **tools** (plain Python functions with PEP 8 type hints and docstrings):
  - `get_lat_lon` - converts a place name to latitude/longitude via the **Google Maps Geocoding API**.
  - `get_weather_forecast` - retrieves current conditions, a short forecast, and deterministic **alert flags** via the **Google Weather API**.
- Builds a weather agent and runs it on the **Gemini** (`gemini-2.5-flash`) model via Vertex AI.
- Includes a **preflight** cell that verifies API and model access with clear PASS/FAIL diagnostics, and **test code** that exercises the agent across multiple US cities.

### Running it

1. Open the notebook in **Agent Platform Colab Enterprise** (or any Vertex AI-authenticated Jupyter environment).
2. Run the cells in order. On first run you may need to restart the runtime after the install cell.
3. The **preflight** cell reports which dependencies are ready. Before grading, ensure these are enabled on the GCP project:
   - Geocoding API, Weather API, and Vertex AI API (the Maps key must be authorized for Geocoding and Weather).

## Dependencies

Python dependencies are embedded directly within the notebook using the `%%writefile requirements.txt` magic command so it is fully self-contained in Colab.

## Challenge Two: Enhancing Agents with Callbacks

[`challenge-two/callbacks_agent.ipynb`](challenge-two/callbacks_agent.ipynb) builds upon the first challenge by adding ADK callback functions:

- **Logging**: Intercepts and logs user prompts (`before_model_callback`) and model responses (`after_model_callback`).
- **Validation**: Inspects user input before it reaches the model to block non-US locations and malicious prompts.
- **Chaining**: Combines the validation and logging callbacks into a single `chained_before_callback` flow.

## Challenge Three: Developing Multi-Agent Systems

[`challenge-3/multi_agent_system.ipynb`](challenge-3/multi_agent_system.ipynb) extends the workshop with a three-agent ADK architecture:

- **Root coordinator agent** that receives user requests and routes work.
- **Weather agent** (from Challenge Two patterns) for US weather and alert responses.
- **Search agent** using ADK built-in `google_search` for general/current-events lookup.
- **Delegation evidence** through streamed event output in the test cell, showing transfer and tool-call activity.

## Challenge Four: Programming an Agent Workflow

[`challenge-4/agent_workflow.ipynb`](challenge-4/agent_workflow.ipynb) builds **Cloud Security Advisor**, a `SequentialAgent` workflow that answers, verifies, and refines a response:

- **Greeter agent** acknowledges the question and hands off to the workflow.
- **Search agent** drafts an initial answer using ADK built-in `google_search`.
- **Critique agent** reviews the draft for accuracy, completeness, clarity, and missing security considerations.
- **Refine agent** rewrites the answer based on the critique into the final response.
- **Workflow evidence** through streamed, per-agent event output that shows the answer evolving across stages.

## Challenge Five: Deploying an Agent to Agent Platform

[`challenge-5/deploy_agent.ipynb`](challenge-5/deploy_agent.ipynb) deploys the Challenge Four **Cloud Security Advisor** workflow to **Vertex AI Agent Engine** and tests it:

- **Rebuilds the agent** (the `SequentialAgent` from Challenge Four) as `root_agent`.
- **Deploys to Agent Platform** by wrapping it in `agent_engines.AdkApp` and calling `client.agent_engines.create` with a Cloud Storage staging bucket.
- **Tests the deployed agent** by creating a remote session and streaming a query, printing per-sub-agent events.

## Notes

- The notebooks are written to run sequentially with no hidden state, so they can be copied and pasted into a fresh Colab Enterprise notebook.
- API keys are hard-coded for copy-paste convenience because the lab GCP project is ephemeral and destroyed at the end of the workshop. Do not reuse this pattern for long-lived projects.
