# Challenge Six: Federal Emergency Machine Assistant (ReadyNow)

ReadyNow - the **Federal Emergency Machine Assistant** - is a US emergency-preparedness assistant built with the Google ADK. A root LLM orchestrator calls specialist tools, enforces a FEMA-only scope, validates input with Model Armor, and validates its web-sourced answers through a critique/refine workflow. It also includes Agent Platform deployment code and in-notebook integration checks.

The entire agent solution is **self-contained inside [`emergency_preparedness.ipynb`](emergency_preparedness.ipynb)** - dependencies, configuration, tools, callbacks, agents, deployment helpers, and tests all live in notebook cells.

## Core services

1. **Weather + emergency planning** - current US weather conditions and risk; when weather is dangerous, ReadyNow proactively follows up with preparedness guidance and offers an evacuation route.
2. **Evacuation routes** - driving/route guidance between US locations, composable with the weather flow (e.g., leave town ahead of a hurricane or wildfire).
3. **FEMA / natural-disaster guidance** - validated, web-sourced answers for disasters (weather, earthquakes, etc.), official FEMA guidance, nearby shelters, active alerts/declarations, and emergency supply-kit / family-plan help.

## Goal

Demonstrate the ability to build and validate a complex agent system using the Google Agent Development Kit (ADK), then deploy and test it on Agent Platform.

## Requirements met

- Root LLM orchestrator that describes its own capabilities and calls specialists as tools (so multi-part prompts are handled in one turn).
- Specialist tools for weather forecasting, evacuation routes, and a validated internet-search workflow.
- Validated search path: `search_agent` (draft) -> `search_critique_agent` -> `search_refine_agent`.
- Deterministic FEMA-only scope gate plus Model Armor input validation, with logging callbacks.
- Local notebook tests and deployed-agent tests.
- Agent Platform deployment flow.
- In-notebook integration checks for the deployed runtime.

## Architecture

![ReadyNow - Federal Emergency Machine Assistant architecture](https://raw.githubusercontent.com/olorinhill/agent-dev-skills-workshop-david/main/challenge-6/ReadNow_Architecture.png)

<details>
<summary>Text version (mermaid)</summary>

```mermaid
flowchart TD
    user[User] --> root["ready_now_root_agent (Federal Emergency Machine Assistant)"]
    root -. before_model_callback .-> guard["Model Armor + deterministic FEMA scope gate"]
    root -->|AgentTool| weather["weather_agent (geocode + weather)"]
    root -->|AgentTool| route["route_agent (Routes API)"]
    root -->|transfer_to_agent| sw["search_workflow (SequentialAgent)"]
    route --> routesapi["Routes API (computeRoutes)"]
    sw --> sd["search_agent (google_search draft)"] --> sc["search_critique_agent"] --> sr["search_refine_agent"]
    root --> platform["Agent Platform deployment"]
```

</details>

> **Note on the "Cloud Run Frontend" in the diagram:** the diagram shows a Cloud Run frontend as a possible deployment topology - you could front the deployed Agent Engine with a web UI on Cloud Run. This repo does **not** include that UI code; the diagram depicts it only as an example of how a frontend would connect to the agent.

## Project layout

```text
challenge-6/
|- emergency_preparedness.ipynb   # Self-contained agent solution (code + tests + markdown)
|- README.md
|- ReadNow_Architecture.png       # Architecture diagram
```

## Notebook flow

Open [`emergency_preparedness.ipynb`](emergency_preparedness.ipynb) in Colab Enterprise and run cells in order:

1. Install dependencies (inline; no external requirements file).
2. Configure environment and initialize Vertex AI.
3. Model Armor preflight check.
4. Define tool functions.
5. Define callbacks (logging + Model Armor validation).
6. Build the ReadyNow root agent.
7. Local execution helpers and local test prompts.
8. Deploy to Agent Platform.
9. Test the deployed runtime and run in-notebook integration checks.

## Required Google APIs (instructor / one-time per project)

Enable these on the lab project before running the notebook (the lab `student-*` account typically lacks permission to enable them):

```bash
gcloud services enable \
  geocoding-backend.googleapis.com \
  weather.googleapis.com \
  routes.googleapis.com \
  modelarmor.googleapis.com \
  --project=your-project-id
```

- Geocoding API and Weather API back `weather_agent`.
- Routes API backs `route_agent` (the modern replacement for the deprecated legacy Directions API; the route tool calls `routes.googleapis.com/directions/v2:computeRoutes`).
- Model Armor API backs input validation (see below).

## Model Armor setup

### Enable the API first (instructor / one-time per project)

Model Armor has **no default template**, and the API is not enabled by default. Before running the notebook, enable the API once for the lab project:

```bash
gcloud services enable modelarmor.googleapis.com --project=your-project-id
```

The runtime identity needs `roles/modelarmor.admin` to create a template (notebook Step 2c creates `ma-template` automatically if it is missing), or at least `roles/modelarmor.user` if the template already exists. If the API is not enabled or permissions are missing, Step 2c raises a clear error explaining what to fix.

### Environment variables

Set these before running the notebook configuration cell (Step 2):

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_MAPS_API_KEY="your-maps-key"
export MODEL_ARMOR_TEMPLATE_ID="projects/your-project-id/locations/us-central1/templates/your-template-id"
```

You can also provide only the template ID and let the callback build the full resource name:

```bash
export MODEL_ARMOR_TEMPLATE_ID="your-template-id"
export MODEL_ARMOR_PROJECT_ID="your-project-id"
export MODEL_ARMOR_LOCATION="us-central1"
```

Required permission for the runtime identity:
- `modelarmor.templates.useToSanitizeUserPrompt` on the Model Armor template (for example via `roles/modelarmor.user`).

Important:
- Keep `MODEL_ARMOR_LOCATION` aligned with the template location.
- Validation is configured **fail-closed**: if Model Armor is unavailable, requests are blocked.

## Deploying to Agent Engine (Step 11)

The deployed agent runs in its own container, separate from the notebook process, so it needs two things the local run gets for free:

1. **Runtime environment variables.** `deploy_agent` forwards `GOOGLE_MAPS_API_KEY`, `MODEL_ARMOR_TEMPLATE_ID`, `MODEL_ARMOR_PROJECT_ID`, `MODEL_ARMOR_LOCATION`, and `GOOGLE_GENAI_USE_VERTEXAI` from the current environment into the deployment's `env_vars` (plus telemetry). Without these, the deployed agent fail-closes on every prompt (Model Armor template missing) and the weather/route tools error (no Maps key). So make sure these are set in the notebook before deploying.

2. **Model Armor access for the runtime service account.** The Agent Engine runtime identity (`service-<PROJECT_NUMBER>@gcp-sa-aiplatform-re.iam.gserviceaccount.com`) must be able to call `sanitizeUserPrompt`. Grant it once:

```bash
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/modelarmor.user"
```

(Find `PROJECT_NUMBER` with `gcloud projects describe your-project-id --format='value(projectNumber)'`, or read it from the deployed engine's `effective_identity`.) Without this, the deployed agent returns "Model Armor safety validation is temporarily unavailable" for every request.

The dependency requirements pinned for deployment (`DEFAULT_REQUIREMENTS`) include `requests==2.32.4` (required by `google-adk==1.18.0`) and `google-cloud-modelarmor` (needed by the validation callback at runtime).

## In-notebook integration checks

The former standalone pytest suite is now an in-notebook cell (Step 13). It validates both successful refined-response generation and malicious-input blocking against the deployed agent. Set these before running it:

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export AGENT_ENGINE_RESOURCE_NAME="projects/.../locations/.../reasoningEngines/..."
```

The checks skip automatically when `AGENT_ENGINE_RESOURCE_NAME` is not set.

## Notes

- `weather_agent` and `route_agent` are exposed as `AgentTool`s, so a multi-part prompt (e.g., weather risk plus an evacuation route) triggers multiple tool calls combined into one answer.
- `search_workflow` is reached by **delegation** (`sub_agents` + `transfer_to_agent`), not as a tool, so its `search_agent` -> `search_critique_agent` -> `search_refine_agent` stages stream as top-level events (full visibility, like challenge-4). Trade-off: because it is a handoff, a search question is not combined in the same turn with weather/route.
- Only the search path is wrapped in critique -> refine, because that is where the answer is synthesized; `weather_agent` and `route_agent` return deterministic tool data and are left plain.
- `google_search` stays isolated inside `search_agent` (its own workflow stage), so there is no built-in-tool mixing at the root.
- Scope is enforced two ways: a deterministic FEMA keyword/capability gate in `before_model_callback` (after Model Armor `sanitizeUserPrompt`), plus the root instruction that refuses off-topic requests.
- This workshop code targets ephemeral lab projects; avoid hard-coded keys in long-lived environments.
