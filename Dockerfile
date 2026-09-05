# Minimal image for the MCP server. No credentials and no state: it proxies
# public AVEVA PI System documentation over stdio.
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY server.py ./

RUN pip install --no-cache-dir .

ENTRYPOINT ["pi-doc-mcp"]
