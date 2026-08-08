# Aveva PI Doc MCP

**Ground your AI answers in live AVEVA PI System documentation.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![MCP](https://img.shields.io/badge/MCP-compatible-green)
![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)

---

## What it does

PI Doc MCP is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI assistants like Claude direct access to the official AVEVA PI System documentation. Instead of relying on training data that may be outdated or incorrect, the AI fetches real answers from live docs — eliminating hallucination on PI-specific topics.

Results are scoped strictly to [`docs.aveva.com/category/pi-system`](https://docs.aveva.com/category/pi-system). Other AVEVA product families (System Platform, CONNECT, etc.) are excluded by design.

---

## How it works

The server proxies the publicly accessible `docs-be.aveva.com` API in real time. No API key, no local doc files, no indexing step — every search and page fetch goes directly to AVEVA's documentation backend and returns content that is always up to date.

---

## Prerequisites

- **Python 3.11 or later** — [python.org/downloads](https://www.python.org/downloads/)
- **uv** — fast Python package manager

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **Claude Code** CLI — [installation guide](https://docs.anthropic.com/en/docs/claude-code/getting-started)

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/naufal-halal/pi-doc-mcp.git
cd pi-doc-mcp
```

**2. Install dependencies**

```bash
uv sync
```

**3. Register with Claude Code**

```bash
claude mcp add pi-docs --scope user -- uv run --directory /path/to/pi-doc-mcp python server.py
```

Replace `/path/to/pi-doc-mcp` with the absolute path to the cloned folder.

**4. Restart Claude Code** to pick up the new MCP server. You should see `pi-docs` listed when you run:

```bash
claude mcp list
```

---

## Available Tools

Once registered, Claude has access to three tools:

| Tool | Description |
|---|---|
| `search_pi_docs` | Search PI System docs by keyword. Optional: `bundle` to scope to a specific product, `n_results` (default 5, max 20). |
| `get_page` | Fetch the full text of a documentation page by URL. Optional: `max_chars` (default 4000, max 12000). |
| `list_pi_bundles` | List all 90+ PI System documentation bundles grouped by product area (PI Server, PI Web API, Interfaces, Connectors, etc.). |

---

## Usage Examples

Ask Claude questions like:

- *"What authentication methods does PI Web API support?"*
- *"What are the required tag attributes for the PI RDBMS Interface?"*
- *"How do I configure buffering for a PI Interface on an interface node?"*
- *"Show me the AF SDK getting started guide."*
- *"List all available PI System documentation bundles."*

Claude will search the live docs and cite the exact page it used.

---

## Scope

This server covers documentation bundles under `docs.aveva.com/category/pi-system`, including:

- PI Server (Windows and Linux)
- PI Web API and AF SDK
- PI Vision, PI DataLink, PI Manual Logger
- PI Interfaces (OPC DA/HDA, RDBMS, UFL, Modbus, DNP3, Batch, and more)
- PI Connectors (OPC UA, MQTT, BACnet, IEC 61850, and more)
- Adapters for Edge Data Store
- PI Integrators, PI SQL / OLEDB, PI OPC UA Server

Use `list_pi_bundles` inside Claude to see the full list.

---

## References

- [AVEVA PI System Documentation](https://docs.aveva.com/category/pi-system)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [uv — Python package manager](https://docs.astral.sh/uv/)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)

---

## Disclaimer

This project is not affiliated with, endorsed by, or supported by AVEVA. It proxies AVEVA's publicly accessible documentation API for personal and developer use. Users are responsible for complying with [AVEVA's terms of use](https://www.aveva.com/en/legal/terms-and-conditions/).

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for detils.
