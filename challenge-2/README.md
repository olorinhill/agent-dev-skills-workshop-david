# Challenge Two: Enhancing Agents with Callbacks

This notebook builds upon Challenge One by adding **callback functions** to the ADK agent to add logging and validation. The full solution lives in [`callbacks_agent.ipynb`](callbacks_agent.ipynb).

## Goal

Demonstrate the ability to use callback functions to add logging and validation to ADK agents.

## Requirements Met

- **Log user prompts**: Implemented `log_user_prompt` using the `before_model_callback` signature.
- **Log model responses**: Implemented `log_model_response` using the `after_model_callback` signature.
- **Validate user input**: Implemented `validate_user_input` to check for malicious input and non-US locations before sending requests to the model.
- **Chained callbacks**: Implemented `chained_before_callback` to run validation first, and if successful, run the logging callback.

## How to run

1. Open [`callbacks_agent.ipynb`](callbacks_agent.ipynb) in **Agent Platform Colab Enterprise** (or a Vertex AI-authenticated Jupyter environment).
2. Run the cells top to bottom.
3. Observe the output of the test cell, which demonstrates the agent successfully answering valid requests, blocking non-US locations, and blocking malicious prompts. The Python `logging` module output will also show the intercepted prompts and responses.
