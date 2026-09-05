"""AVEVA PI System Documentation MCP Server.

Proxies the live docs-be.aveva.com API so LLMs can search and read
PI System documentation without hallucinating. Scoped strictly to
https://docs.aveva.com/category/pi-system.
"""

import re
from typing import Annotated
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from mcp.server.mcpserver.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

BASE_API = "https://docs-be.aveva.com"

# Pattern that matches ANY bundle under docs.aveva.com/category/pi-system.
_PI_BUNDLE_PATTERN = re.compile(
    r"^("
    r"pi-server|pi-web-api|pi-vision|pi-datalink|pi-sql|pi-oledb"
    r"|pi-connector|pi-interface|pi-integrator|pi-opc-ua|pi-manual-logger"
    r"|pi-cloud-connect|pi-autopointsync|pi-event-frames|pi-processbook"
    r"|pi-system-connector|pi-powershell|pi-to-connect|pi-to-pi"
    r"|pi-universal-interface|pi-connector-administration"
    r"|af-sdk|adapter-for|omf-with-pi|rtreports"
    r"|overview-of-pi|pi-opc-ua-server|pi-oledb-enterprise"
    r")"
)

_PI_BUNDLE_EXCLUDE: frozenset[str] = frozenset({
    "connect-to-pi-agent",
    "edna-to-pi-migration-utility",
})


def is_pi_system_bundle(bundle_id: str) -> bool:
    return (
        bool(_PI_BUNDLE_PATTERN.match(bundle_id))
        and bundle_id not in _PI_BUNDLE_EXCLUDE
    )


PI_SYSTEM_BUNDLES: frozenset[str] = frozenset({
    # PI Server (2024 R2 / Windows)
    "pi-server-f", "pi-server-f-install", "pi-server-f-da-smt",
    "pi-server-f-af-install", "pi-server-f-af-pse", "pi-server-f-af-analytics",
    "pi-server-f-builder", "pi-server-f-topologies",
    "pi-server-s-buf-ha", "pi-server-s-da-admin", "pi-server-s-da-reference",
    # PI Server (2018 / Linux)
    "pi-server-l", "pi-server-l-install", "pi-server-l-da-smt",
    "pi-server-l-af-install", "pi-server-l-af-pse", "pi-server-l-af-analytics",
    "pi-server-l-builder", "pi-server-l-topologies",
    # PI Server related products
    "pi-cloud-connect", "pi-autopointsync", "pi-event-frames-generator",
    # Data visualization
    "pi-vision", "pi-vision-api-reference",
    "pi-datalink", "pi-manual-logger", "rtreports",
    "pi-processbook-to-pi-vision-migration-utility",
    # Data ingress — Adapters
    "adapter-for-bacnet", "adapter-for-dnp3", "adapter-for-modbus-tcp",
    "adapter-for-mqtt", "adapter-for-opc-ua", "adapter-for-rdbms",
    "adapter-for-structured-data-files",
    # Data ingress — PI Interfaces
    "overview-of-pi-interfaces",
    "pi-universal-interface-uniint-framework",
    "pi-interface-configuration-utility-icu",
    "pi-interface-for-abb-800xa-batch",
    "pi-interface-for-abb-800xa-production-response-batch",
    "pi-interface-for-aveva-batch-management",
    "pi-interface-for-dnp3",
    "pi-interface-for-emerson-deltav-batch",
    "pi-interface-for-emerson-syncade-batch",
    "pi-interface-for-modbus-ethernet-plc",
    "pi-interface-for-opc-da", "pi-interface-for-opc-hda",
    "pi-interface-for-performance-monitor",
    "pi-interface-for-ping",
    "pi-interface-for-ramp-soak-simulator-data",
    "pi-interface-for-random-simulator-data",
    "pi-interface-for-relational-database-rdbms-via-odbc",
    "pi-interface-for-rockwell-factory-talk-batch",
    "pi-interface-for-rockwell-pharmasuite",
    "pi-interface-for-siemens-simatic-batch",
    "pi-interface-for-snmp",
    "pi-interface-for-tcp-response",
    "pi-interface-for-universal-file-and-stream-loading-ufl",
    "pi-interface-for-werum-pas-x-batch",
    "pi-to-pi-interface",
    # Data ingress — PI Connectors
    "overview-of-pi-connectors", "pi-connector-administration",
    "pi-connector-for-bacnet", "pi-connector-for-cygnet",
    "pi-connector-for-ethernet-ip", "pi-connector-for-fanuc-focas",
    "pi-connector-for-hart-ip", "pi-connector-for-iec-60870-5-104",
    "pi-connector-for-iec-61850", "pi-connector-for-mqtt-sparkplug",
    "pi-connector-for-opc-ua-gen-1", "pi-connector-for-opc-ua-gen-2",
    "pi-connector-for-ping", "pi-connector-for-siemens-simatic-pcs-7",
    "pi-connector-for-ufl", "pi-connector-for-wonderware-historian",
    # Data ingress — PI Integrators
    "pi-integrator-for-business-analytics", "pi-integrator-for-esri-arcgis",
    # Data ingress — PI OPC UA Server
    "pi-opc-ua-server",
    # Data ingress — PI to CONNECT
    "pi-to-connect-agent", "pi-to-connect-agent-event-frames-preview",
    # Developer tools — AF SDK
    "af-sdk", "af-sdk-getting-started",
    # Developer tools — PI Web API
    "pi-web-api", "pi-web-api-reference", "omf-with-pi-web-api",
    # Developer tools — PI SQL
    "pi-sql-client-jdbc", "pi-sql-client-odbc", "pi-sql-client-oledb",
    "pi-sql-commander-lite", "pi-oledb-enterprise",
    # Developer tools — PowerShell
    "pi-system-connector", "pi-system-connector-3",
})

_BUNDLE_GROUPS: list[tuple[str, list[str]]] = [
    ("PI Server", sorted(b for b in PI_SYSTEM_BUNDLES if "pi-server" in b)),
    ("PI Web API", sorted(b for b in PI_SYSTEM_BUNDLES if "pi-web-api" in b or "omf-with-pi" in b)),
    ("AF SDK", sorted(b for b in PI_SYSTEM_BUNDLES if "af-sdk" in b)),
    ("PI Vision / DataLink", sorted(b for b in PI_SYSTEM_BUNDLES if "pi-vision" in b or "pi-datalink" in b or b in ("pi-manual-logger", "rtreports", "pi-processbook-to-pi-vision-migration-utility"))),
    ("PI SQL / OLEDB", sorted(b for b in PI_SYSTEM_BUNDLES if "pi-sql" in b or "pi-oledb" in b)),
    ("Adapters", sorted(b for b in PI_SYSTEM_BUNDLES if b.startswith("adapter-for-"))),
    ("PI Connectors", sorted(b for b in PI_SYSTEM_BUNDLES if "pi-connector" in b or b == "overview-of-pi-connectors")),
    ("PI Interfaces", sorted(b for b in PI_SYSTEM_BUNDLES if "pi-interface" in b or "uniint" in b or b in ("overview-of-pi-interfaces", "pi-to-pi-interface", "pi-interface-configuration-utility-icu"))),
    ("PI Integrators", sorted(b for b in PI_SYSTEM_BUNDLES if "pi-integrator" in b)),
    ("PowerShell / Other", sorted(b for b in PI_SYSTEM_BUNDLES if b in ("pi-system-connector", "pi-system-connector-3", "pi-opc-ua-server", "pi-cloud-connect", "pi-autopointsync", "pi-event-frames-generator", "pi-to-connect-agent", "pi-to-connect-agent-event-frames-preview"))),
]

# ── App ────────────────────────────────────────────────────────────────────────

# Every tool here reads public documentation over the network: no side effects,
# and results depend on what AVEVA currently publishes.
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=True)

mcp = MCPServer(
    "pi-doc-mcp",
    instructions=(
        "Answers questions about the AVEVA PI System from the official product "
        "documentation at docs.aveva.com. Use search_pi_docs to find pages, then "
        "get_page to read one in full — search excerpts are short and usually omit "
        "the actual procedure. list_pi_bundles gives the bundle IDs that scope a "
        "search to one product. Prefer these tools over recalled knowledge: PI "
        "System details are version-specific and easy to misremember. Everything "
        "is scoped to docs.aveva.com/category/pi-system, so other AVEVA product "
        "families are deliberately excluded. All tools are read-only and need no "
        "credentials."
    ),
)
_client: httpx.AsyncClient | None = None
_bundle_list_cache: str | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
    return _client


# ── Helpers ────────────────────────────────────────────────────────────────────

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def bundle_url_to_api(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    m = re.match(r"^/bundle/([^/]+)/page/(.+)$", parsed.path)
    if not m:
        return None
    bundle_id, nav_path = m.group(1), m.group(2)
    return f"{BASE_API}/api/bundle/{bundle_id}/page/{nav_path}", bundle_id


# ── Tools ──────────────────────────────────────────────────────────────────────

@mcp.tool(
    description=(
        "Search the official AVEVA PI System documentation and return page "
        "titles, bundle IDs, URLs and matching excerpts.\n\n"
        "Use this for how the PI System works and how to configure it: PI Data "
        "Archive, Asset Framework, PI Vision, interfaces and connectors, PI Web "
        "API, AF SDK, PI SQL and DataLink. Reach for it before answering from "
        "memory — PI behaviour, defaults and menu paths differ between versions. "
        "For a specific error message or a known issue, a support knowledge base "
        "is a better source than product manuals, if one is available.\n\n"
        "Read-only; no side effects; no credentials needed. Results are restricted "
        "to docs.aveva.com/category/pi-system, so System Platform, CONNECT and "
        "other AVEVA families never appear. Excerpts are a couple of lines and "
        "routinely omit the procedure itself — follow up with get_page on the URL "
        "that looks right."
    ),
    annotations=READ_ONLY,
)
async def search_pi_docs(
    query: Annotated[str, Field(description=(
        "Search terms describing the task or setting, e.g. 'Kerberos "
        "authentication' or 'configure PI Interface buffering'. Plain keywords "
        "work better than a full question."
    ))],
    n_results: Annotated[int, Field(
        default=5, ge=1, le=20,
        description="Number of results to return, 1-20.",
    )] = 5,
    bundle: Annotated[str, Field(
        default="",
        description=(
            "Optional bundle ID restricting the search to one product, e.g. "
            "'pi-web-api', 'af-sdk' or 'pi-server-f'. Call list_pi_bundles for "
            "valid IDs. Leave empty to search all PI System documentation."
        ),
    )] = "",
) -> str:
    n = min(n_results, 20)
    bundle = bundle.strip()

    fetch_n = 50 if not bundle else n
    params: dict = {"q": query, "results_per_page": fetch_n}
    if bundle:
        params["bundle"] = bundle

    client = get_client()
    resp = await client.get(f"{BASE_API}/api/search", params=params)
    resp.raise_for_status()
    data = resp.json()

    raw_results = data.get("Results", [])
    if bundle:
        results = raw_results[:n]
    else:
        results = [
            r for r in raw_results
            if is_pi_system_bundle((r.get("leading_result") or {}).get("bundle_id", ""))
        ][:n]

    if not results:
        return f"No PI System results for: {query}"

    lines: list[str] = []
    for i, item in enumerate(results, 1):
        lead = item.get("leading_result") or {}
        title = lead.get("title", "Untitled")
        bundle_id = lead.get("bundle_id", "")
        url = lead.get("url", "").replace("https://docs-be.aveva.com/bundle/", "https://docs.aveva.com/bundle/")
        snippet_html = item.get("highlighted_snippet", "")
        snippet = html_to_text(snippet_html)[:250] if snippet_html else ""

        lines.append(f"{i}. {title} [{bundle_id}]")
        lines.append(f"   {url}")
        if snippet:
            lines.append(f"   {snippet}")

    return "\n".join(lines)


@mcp.tool(
    description=(
        "Fetch one AVEVA PI System documentation page and return its text.\n\n"
        "Use this after search_pi_docs on any result whose excerpt looks relevant "
        "— excerpts rarely contain the actual steps, so do not answer from a "
        "search result alone. Also accepts a docs.aveva.com bundle URL the user "
        "pastes.\n\n"
        "Read-only; no side effects; no credentials needed. Only accepts URLs of "
        "the form docs.aveva.com/bundle/<id>/page/<path>; anything else returns a "
        "message saying so rather than failing. Output is a header with the page "
        "title, bundle and last-updated date, then the page text truncated at "
        "max_chars with a marker when cut."
    ),
    annotations=READ_ONLY,
)
async def get_page(
    url: Annotated[str, Field(description=(
        "Full documentation URL, normally copied from a search result, e.g. "
        "'https://docs.aveva.com/bundle/pi-web-api/page/help/getting-started.html'."
    ))],
    max_chars: Annotated[int, Field(
        default=4000, ge=500, le=12000,
        description=(
            "Maximum characters of page text to return, 500-12000. Raise it if "
            "the output ends in a truncation marker."
        ),
    )] = 4000,
) -> str:
    max_chars = min(max_chars, 12000)

    parsed = bundle_url_to_api(url)
    if not parsed:
        return f"Invalid URL: {url}\nExpected: https://docs.aveva.com/bundle/<id>/page/<path>"

    api_url, _ = parsed
    client = get_client()
    try:
        resp = await client.get(api_url)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        return f"Page not found (HTTP {e.response.status_code}): {url}"

    data = resp.json()
    topic_html = data.get("topic_html", "")
    if not topic_html:
        return "Page content not available."

    title = data.get("title", "")
    bundle_title = data.get("bundle_title", "")
    updated = (data.get("dates") or {}).get("Updated on", "")[:10]

    content = html_to_text(topic_html)
    truncated = len(content) > max_chars
    content = content[:max_chars]

    header = f"# {title} — {bundle_title} (updated {updated})\n{url}\n\n"
    suffix = "\n\n[truncated — increase max_chars for more]" if truncated else ""
    return header + content + suffix


@mcp.tool(
    description=(
        "List the PI System documentation bundle IDs, grouped by product area.\n\n"
        "Use this when a search returns results spanning unrelated products and "
        "you need the exact bundle ID to narrow it, or when the user names a "
        "product informally ('PI AF', 'the web API') and you need the ID that "
        "search_pi_docs expects. Not needed for a first, unscoped search.\n\n"
        "Read-only; no side effects; no network call — the list is static and "
        "cached. Returns bundle IDs grouped under headings such as PI Server, PI "
        "Web API, AF SDK and Adapters."
    ),
    annotations=READ_ONLY,
)
def list_pi_bundles() -> str:
    global _bundle_list_cache
    if _bundle_list_cache is not None:
        return _bundle_list_cache

    lines = [f"PI System bundles ({len(PI_SYSTEM_BUNDLES)} total) — docs.aveva.com/category/pi-system\n"]
    lines.append("Pass a bundle ID as the `bundle` param in search_pi_docs to scope results.\n")
    for group_name, ids in _BUNDLE_GROUPS:
        if ids:
            lines.append(f"{group_name}: {', '.join(ids)}")

    _bundle_list_cache = "\n".join(lines)
    return _bundle_list_cache


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
