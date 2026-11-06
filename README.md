# Connoisseur Companion

A portfolio-quality restaurant recommendation application built with Python, Gradio, MCP tools, and a locally runnable language model.

It searches a synthetic set of California restaurants, recommends restaurants by atmosphere, and retrieves reviews. Everything runs locally; no API keys are needed.

## How it works

```
Gradio chat UI -> RestaurantAgent -> Ollama (qwen3:4b-instruct)
                        |
                        v  tool calls over stdio
                  MCP server -> RestaurantService -> data/raw/*.json
```

The agent gives the model the tools exposed by the MCP server, runs up to 4 tool rounds per question, and returns the model's final answer.

### MCP tools

| Tool | Purpose |
|---|---|
| `search_restaurants(query, limit=5)` | Find restaurants by name (case-insensitive substring) |
| `get_restaurant_info(item_id)` | Full details for one restaurant |
| `recommend_by_vibe(vibe, limit=5)` | Restaurants whose vibe or environment contains the phrase |
| `get_review(item_id)` | Reviews for a restaurant, newest first |

## Prerequisites

- Python 3.11 or newer
- [Ollama](https://ollama.com/download) installed and running

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install the project (add the dev extra to run tests)
pip install -e ".[dev]"

# 3. Pull the local model (one-time download)
ollama pull qwen3:4b-instruct
```

Make sure the Ollama server is running (`ollama serve`, or the desktop app) at `localhost:11434`.

## Run

Start the chat interface:

```bash
connoisseur-app
```

Then open the local URL Gradio prints (usually http://127.0.0.1:7860). Try:

- "Find restaurants with a bohemian vibe"
- "Tell me about restaurant 1000001"
- "Search for Iron and show me its reviews"

To run the MCP server on its own (stdio transport), for example with an MCP inspector or another client:

```bash
connoisseur-mcp
```

## Test

```bash
pytest
```

## Data

Source data lives in `data/raw/` (210 restaurants, 10 reviews). See `data/README.md` for field notes and known quirks.

## Known limitations

- Vibe search matches the whole phrase as a substring, not word by word.
- Results are capped at 5 by default.
- The Ollama host and model are fixed in `ollama_client.py`.
- A new MCP server process starts for every chat message.
