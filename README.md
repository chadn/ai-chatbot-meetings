# 💬 AI Chatbot Meetings

A Streamlit-based chatbot application to book meetings on your cal.com calendar.
Uses the Langchain Framework to interact with OpenAI's language models, using tool calling to interact with cal.com's API.

Demo the code in this repo here: https://ai-chatbot-meetings.streamlit.app/

## Features

-   Chat interface with OpenAI models (e.g. GPT-4 Turbo)
-   Uses Langchain Framework which enables easy support for Tool Calling and OpenAI API.
-   Tool calling support for custom functions
-   Chat history management with JSON export/import
-   Debug print option with logging configuration
-   Streamlit-based web interface

Also see [Architecture.md](docs/Architecture.md), [TODO.md](docs/TODO.md), [Bugs.md](docs/Bugs.md) and more in [docs/](docs/).

## Setup

1. Clone the repository
2. Create a virtual environment:
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3. Install dependencies:
    ```bash
    uv pip install -e .
    ```
4. Copy `.env.template` to `.env` and add your OpenAI API key:
    ```bash
    cp .env.template .env
    # Edit .env with your OpenAI API key
    ```

## Running the Application

```bash
streamlit run src/streamlit_app.py
```

You can add timestamps and log to a file when debugging like this:

```bash
streamlit run src/streamlit_app.py 2>&1 |ts |tee -a src/streamlit_app.py.log
```

## Development

Install development dependencies:

```
# uv pip install -e .[dev]
```

Run the app with [httpdbg](https://github.com/cle-b/httpdbg) to capture HTTP requests and responses:

```bash
pyhttpdbg -m streamlit.web.cli run src/streamlit_app.py 2>&1 |ts |tee -a src/streamlit_app.py.log
```

## Running Tests

Run all tests:

```bash
pytest tests/
```

For integration tests:

```bash
pytest tests/ -m integration
```

## Project Structure

```
/
├── .devcontainer/
│   └── devcontainer.json    # Configuration for development container
├── docs/
│   ├── Architecture.md       # System architecture documentation
│   ├── Bugs.md              # Known issues and their status
│   └── TODO.md               # Project tasks and plans
├── src/
│   ├── streamlit_app.py      # Main Streamlit application
│   ├── services/
│   │   ├── chat_history.py   # Chat history management
│   │   ├── chat_model.py     # OpenAI chat model integration
│   │   └── tool_manager.py   # Tool calling functionality
│   └── utils/
├── tests/
│   ├── test_chat_history.py  # Unit tests for chat history management
│   └── test_chat_model.py    # Unit tests for chat model integration
│
├── .env                      # Environment variables configuration
├── .env.template             # Template for environment variables
├── .gitignore                # Git ignore file
├── .python-version           # Python version specification
├── pyproject.toml            # Project configuration and dependencies
├── uv.lock                   # UV package manager dependencies lock file (by uv lock)
├── LICENSE                   # License file (Apache 2.0)
├── README.md                 # Project documentation
```

## Development

The application is structured into several key components:

-   `ChatModelService`: Handles interactions with OpenAI's API
-   `ChatHistoryManager`: Manages chat history and persistence
-   `ToolManager`: Handles tool calling functionality
-   Streamlit UI: Provides the user interface and interaction flow

## Environment Variables

-   `OPENAI_API_KEY`: Your OpenAI API key
-   `DEBUG_PRINT`: Enable/disable debug printing (True/False)
-   `LANGCHAIN_VERBOSE`: Enable/disable Langchain verbose mode
-   `LANGCHAIN_DEBUG`: Enable/disable Langchain debug mode
-   `LOG_PROMPTS`: Enable/disable prompt logging

[Apache License 2.0](LICENSE)
