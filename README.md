# agent-dev-skills-workshop-david

Submission repository for the **Agentic AI with the Google Agent Development Kit (ADK): Skills Validation Workshop**.

This repo contains the challenge solutions, implemented as Colab Enterprise Jupyter notebooks that build, test, and (later) deploy generative AI agents on Google Cloud using the ADK, Gemini, and third-party models.

## Workshop challenges

| # | Challenge | Points | Status |
|---|-----------|--------|--------|
| 1 | Real-Time Weather Alerts Agent | 15 | Complete |
| 2 | Enhancing Agents with Callbacks | 15 | Not started |
| 3 | Developing Multi-Agent Systems | 15 | Not started |
| 4 | Programming an Agent Workflow | 15 | Not started |
| 5 | Deploying Agents (bonus) | 10 | Not started |
| 6 | Emergency Preparedness Assistant (case study) | 40 | Not started |

Passing the workshop requires 80 of 110 possible points.

## Repository structure

```
.
|- README.md                  # This file
|- challenge-one/
|  |- weather_alerts_agent.ipynb   # Challenge 1 notebook
|  |- README.md                    # Google Maps Platform API key for the lab
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

## Notes

- The notebooks are written to run sequentially with no hidden state, so they can be copied and pasted into a fresh Colab Enterprise notebook.
- API keys are hard-coded for copy-paste convenience because the lab GCP project is ephemeral and destroyed at the end of the workshop. Do not reuse this pattern for long-lived projects.
