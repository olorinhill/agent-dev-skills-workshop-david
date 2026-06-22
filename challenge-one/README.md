# Challenge One: Real-Time Weather Alerts Agent

A weather-alerts agent built with the **Google Agent Development Kit (ADK)** that retrieves real-time weather for US locations and produces a summary or alert. The full solution lives in [`weather_alerts_agent.ipynb`](weather_alerts_agent.ipynb).

## Goal

Demonstrate the ability to create and test an agent using the ADK that:

- uses custom tools to retrieve real-time weather data for user locations,
- provides a weather summary or alert based on current conditions, and
- works for multiple US cities.

## What the notebook contains

- **`get_lat_lon`** - converts a place name to latitude/longitude using the **Google Maps Geocoding API** (PEP 8 type hints + docstring).
- **`get_weather_forecast`** - retrieves current conditions, a short forecast, and deterministic **alert flags** using the **Google Weather API**.
- **Model** - the agent runs on **Gemini** (`gemini-2.5-flash`) via Vertex AI.
- **Embedded Dependencies** - `requirements.txt` is embedded directly within the notebook using the `%%writefile` magic command.
- **Preflight checks** - verify API and model access with clear PASS/FAIL diagnostics before the demo runs.
- **Tests** - run the Gemini agent across multiple US cities (New York, Chicago, Denver, Miami, Seattle) with assertions.

## How to run

1. Open [`weather_alerts_agent.ipynb`](weather_alerts_agent.ipynb) in **Agent Platform Colab Enterprise** (or a Vertex AI-authenticated Jupyter environment).
2. Run the cells top to bottom. After the install cell you may need to restart the runtime, then continue.
3. Check the **preflight** output. Before grading, confirm these are enabled on the GCP project:
   - Geocoding API, Weather API, and Vertex AI API (the Maps key must be authorized for Geocoding and Weather).

## Configuration

Key settings are defined in the notebook's configuration cell:

- `PROJECT_ID` - the GCP project.
- `GOOGLE_MAPS_API_KEY` - Google Maps Platform key, used for both the Geocoding and Weather APIs.
- `GEMINI_MODEL` - the Gemini model identifier.

Google Maps Platform API key (ephemeral lab project): `AIzaSyCG-ZPd1r5ieh7stUWDl0m6a3it1IVXDT8`

## TODO

- [ ] Add support for both Gemini and some other third-party model (Claude, GPT, etc.).

## Notes

- The notebook runs sequentially with no hidden state and is safe to copy-paste into a fresh Colab Enterprise notebook.
- The API key is hard-coded for copy-paste convenience because the lab project is ephemeral. Do not reuse this pattern for long-lived projects.
