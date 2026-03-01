# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

nanobot is an ultra-lightweight personal AI assistant framework (~4,000 lines of core agent code). It's designed to be research-friendly, easy to understand, and highly extensible. The project supports multiple LLM providers, chat channels (Telegram, Discord, Slack, WhatsApp, etc.), and uses MCP (Model Context Protocol) for tool integration.

### Key Architecture Concepts

**Agent Loop** (`nanobot/agent/loop.py`): The core processing engine that:
1. Receives messages from the message bus
2. Builds context with history, memory, and skills
3. Calls the LLM with tool definitions
4. Executes tool calls
5. Sends responses back

**Orchestration Environment** (`nanobot/application/orchestration/environment.py`): Composes runtime dependencies:
- Skill-aware context building
- Runtime tool registry (dynamic tool registration)
- MCP lifecycle management (lazy connect/close)
- Separates application orchestration from conversation control flow

**Tool Registry** (`nanobot/agent/tools/registry.py`): Dynamic tool management system where tools can be registered at runtime. Built-in tools include:
- `shell`: Execute shell commands
- `read_file/write_file/edit_file/list_dir`: Filesystem operations
- `web_fetch/web_search`: Web operations
- `spawn`: Create background subagents
- `cron`: Schedule tasks

**Skills System** (`nanobot/agent/skills.py`): Loads markdown-based skill definitions from:
- Built-in skills: `nanobot/skills/*/SKILL.md`
- Workspace skills: `~/.nanobot/workspace/skills/*/SKILL.md`

**Provider Registry** (`nanobot/providers/registry.py`): Single source of truth for LLM providers. Adding new providers requires only 2 steps:
1. Add `ProviderSpec` to `PROVIDERS` tuple
2. Add field to `ProvidersConfig` in `config/schema.py`

**Message Bus** (`nanobot/bus/`): Decoupled message routing between channels and the agent loop using asyncio queues.

## Development Commands

### Installation & Setup
```bash
# Install from source (recommended for development)
pip install -e .

# Or using uv (faster)
uv pip install -e .

# Initialize config and workspace
nanobot onboard

# Edit config manually
vim ~/.nanobot/config.json
```

### Running the Agent
```bash
# Interactive CLI chat
nanobot agent

# Single message
nanobot agent -m "Hello!"

# Gateway mode (connects to configured channels like Telegram/Discord)
nanobot gateway

# Check status
nanobot status
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_commands.py

# Run with coverage
pytest --cov=nanobot

# Run Docker integration test
bash tests/test_docker.sh
```

### Code Quality
```bash
# Lint
ruff check nanobot/

# Format
ruff format nanobot/

# Type checking (if mypy is added)
mypy nanobot/
```

### Docker Development
```bash
# Build image
docker build -t nanobot .

# Run with Docker Compose (recommended)
docker compose up -d nanobot-gateway
docker compose logs -f nanobot-gateway

# Run CLI in container
docker compose run --rm nanobot-cli status
```

## Configuration

Config location: `~/.nanobot/config.json`

### Minimal Config (Required Fields)
```json
{
  "providers": {
    "ollama": {
      "apiBase": "http://127.0.0.1:11434",
      "apiKey": "ollama"
    }
  },
  "agents": {
    "defaults": {
      "model": "ollama/qwen2.5:14b"
    }
  }
}
```

### Key Configuration Sections

**Providers**: LLM provider configurations. This intranet-ready build supports:
- `ollama`: Local Ollama instance
- `vllm`: Local vLLM or OpenAI-compatible server

**Agents**: Agent behavior settings
- `model`: LLM model to use
- `temperature`: Response randomness (0.0-1.0)
- `maxTokens`: Response length limit
- `maxToolIterations`: Max tool calls per message (default: 40)
- `memoryWindow`: Conversation history size (default: 100)

**Channels**: Chat platform integrations (Telegram, Discord, Slack, WhatsApp, Feishu, etc.)

**Tools**:
- `mcpServers`: MCP server configurations (stdio or HTTP transport)
- `restrictToWorkspace`: Sandboxes tools to workspace directory when `true`

**Cron**: Scheduled tasks configuration

## Code Patterns & Conventions

### Adding a New Tool
1. Create a new file in `nanobot/agent/tools/` extending `Tool` base class
2. Implement `name`, `description`, `parameters` properties
3. Implement `execute()` async method
4. Register in `AgentOrchestrationEnvironment.__init__()`

### Adding a New Channel
1. Create file in `nanobot/channels/` extending `Channel` base class
2. Implement `start()`, `stop()`, `send()` methods
3. Add config schema in `nanobot/config/schema.py`
4. Register in `nanobot/channels/manager.py`

### Adding a New Skill
1. Create directory in `nanobot/skills/` or workspace `skills/`
2. Add `SKILL.md` with tool instructions
3. (Optional) Add supporting Python scripts in the skill directory

### Testing Patterns
- Use `pytest` for unit tests
- Mock config/workspace paths with `patch` for isolation
- Use `CliRunner` from typer for CLI testing
- Create fixtures in `conftest.py` for common test setup
- Test files are named `test_*.py` and placed in `tests/`

### Error Handling
- Use `loguru.logger` for logging (already configured)
- Tool errors should return error messages as strings, not raise exceptions
- Channel connection errors should log and retry gracefully
- MCP errors are handled at the orchestration layer

## Important Architecture Notes

### MCP Integration
- MCP servers are configured in `config.json` under `tools.mcpServers`
- Two transport modes: stdio (local processes) and HTTP (remote servers)
- MCP tools are automatically discovered and merged with built-in tools
- MCP lifecycle is managed by `AgentOrchestrationEnvironment`

### Memory System
- Conversation memory is stored in `~/.nanobot/workspace/memory/`
- Uses append-only text files for simplicity
- Memory window controls how many messages are included in context

### Subagents
- The `spawn` tool can create background subagents for parallel tasks
- Subagents run independently and report back results
- Managed by `SubagentManager` in `nanobot/agent/subagent.py`

### Security Considerations
- Always set `tools.restrictToWorkspace: true` for production deployments
- Use `channels.*.allowFrom` to whitelist authorized users
- Never commit API keys or config files with credentials
- Shell command execution is gated behind the `exec` tool

### Internal Orchestrator (Intranet Mode)
- Entry point: `nanobot-internal` command
- Provides FastAPI + Web UI + tool trace dashboard
- Located in `nanobot/internal_orchestrator/`
- Supports weak model tool-call repair with `json-repair`
- Designed for air-gapped enterprise deployments

## Project Structure

```
nanobot/
├── agent/              # Core agent logic (loop, context, memory, tools)
├── channels/           # Chat platform integrations
├── providers/          # LLM provider implementations
├── config/             # Configuration schema and loading
├── bus/                # Message routing (events, queue)
├── application/        # Application-layer orchestration
├── skills/             # Built-in skills
├── internal_orchestrator/  # Intranet deployment mode
├── cli/                # Command-line interface
├── session/            # Session management
├── cron/               # Scheduled tasks
├── heartbeat/          # Proactive task execution
├── observability/      # Tool trace logging
└── utils/              # Helper functions
```

## Workspace Directory

Located at `~/.nanobot/workspace/`:
- `memory/`: Conversation memory
- `skills/`: User-defined skills
- `HEARTBEAT.md`: Periodic tasks
- `USER.md`: User preferences and context
- `TOOLS.md`: Tool documentation
- `AGENTS.md`: Agent behavior instructions

## Debugging Tips

- Run `nanobot agent --logs` to see runtime logs during chat
- Tool traces are logged to `~/.nanobot/logs/tool_trace.jsonl`
- Use `nanobot trace -n 100` to view recent tool calls
- Check `nanobot status` for configuration validation
- Gateway logs show channel connection status and errors

## Common Issues

**Provider not found**: Check model name matches provider prefix (e.g., `ollama/qwen2.5:14b`)

**Tool execution fails**: Check `restrictToWorkspace` setting and file permissions

**Channel not connecting**: Verify credentials in config and check firewall/proxy settings

**MCP server timeout**: Increase `toolTimeout` in MCP server config (default: 30s)
