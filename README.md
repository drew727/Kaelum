# Kaelum

[![CI](https://github.com/drew727/Kaelum/actions/workflows/ci.yml/badge.svg)](https://github.com/drew727/Kaelum/actions/workflows/ci.yml)

Kaelum is an adaptive Discord bot built around short, conversational group-chat replies, mimicking human conversation. It listens in selected channels, decides whether it should jump in, and generates responses through external LLM providers while keeping a small running summary of chat context.

## Features

- Listens in configured Discord text channels and responds in a casual chat style
- Supports multiple personalities, including a normal mode and an intentionally annoying mode
- Exposes slash commands for bot info, health checks, and channel-level listening controls
- Includes a small unit test suite and GitHub Actions CI for compile and test checks

## Requirements

- Python 3.11 or newer
- A Discord bot token
- API keys for the configured LLM providers

## Environment Variables

Set the following environment variables before running the bot:

- `DISCORD_TOKEN`: Discord bot token
- `LLMKEY`: Groq API key used through the OpenAI-compatible client
- `GEMINI_API_KEY`: Google Gemini API key
- `PORT`: Optional HTTP server port for the debug summary endpoint. Defaults to `5000`

## Setup

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the bot:

```bash
python3 main.py
```

## Commands

Kaelum currently exposes these slash commands:

- `/about`: Show a short description of the bot
- `/check`: Confirm that the bot is running
- `/listen`: Start listening in the current channel
- `/purge`: Stop listening in the current channel
- `/switch`: Toggle the configured personality for a selected channel

`/listen` and `/purge` require the `Manage Channels` permission.

## Testing

Run the test suite locally:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Run the compile check used in CI:

```bash
python3 -m compileall main.py ai cogs tests
```

## CI

GitHub Actions runs the compile check and unit tests on every push and pull request through [`ci.yml`](.github/workflows/ci.yml).

## Project Structure

- [`main.py`](main.py): bot startup, cog loading, and debug HTTP endpoint
- [`cogs/`](cogs): Discord commands and message listener logic
- [`ai/`](ai): response generation and system instructions
- [`tests/`](tests): unit tests covering bot behavior and startup flow

## Notes

- The bot currently uses `discord.Intents.all()`
- Listening channels and some privileged user IDs are still configured directly in code
- The debug HTTP endpoint returns the current stored chat summary from [`ai/kaelum_memory.json`](ai/kaelum_memory.json)
