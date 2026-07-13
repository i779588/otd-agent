# Agent Guidelines

Technical constraints and patterns for building Pro-Code AI Agents. Follow these throughout specification execution.

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Key Constraints](#key-constraints)
4. [LLM Integration Patterns](#llm-integration-patterns)
5. [Code Quality](#code-quality)
6. [Agent Decorators](#agent-decorators)
7. [Agent Instrumentation](#agent-instrumentation)
8. [MCP Tool Integration](#mcp-tool-integration)
9. [Agent Card & A2A Protocol](#agent-card--a2a-protocol)
10. [Common Utility Methods](#common-utility-methods)
11. [Security & Authentication](#security--authentication)
    - [Credential Management](#credential-management)
    - [Principal Propagation](#principal-propagation)
    - [SAP Destination Service](#sap-destination-service)
    - [Security Best Practices](#security-best-practices)
12. [Testing](#testing)
13. [Validation Checklist](#validation-checklist)
14. [MCP Translation Files & Mock Tools](#mcp-translation-files-mcp-servers--mock-tools-post-implementation)
15. [Agent Evaluation](#agent-evaluation-post-implementation)

## Tech Stack

- Python 3.13
- Agent framework defined in the `sap-agent-bootstrap` skill
- Agent2Agent (A2A) protocol
- Local execution only (in-memory storage, no deployment)

## Project Structure

- Asset root: `assets/<asset-name>/`
- Required structure: `asset.yaml`, `app/`
- Full layout from project root: `solution.yaml`, `assets/<asset-name>/asset.yaml`, `assets/<asset-name>/app/`
- `asset.yaml` must use `buildPath: .` and `/.well-known/agent.json` for all health probes
- Follow the `sap-agent-bootstrap` skill for project scaffolding — invoke directly from `assets/<asset-name>/`, use copy commands

## Key Constraints

- When working with LangChain or LangGraph, you MUST NEVER use the `create_react_agent` function (`from langgraph.prebuilt import create_react_agent`) as it has been deprecated in LangChain 1.0. Instead, you should use the `from langchain.agents import create_agent` function.
- **NEVER call SAP APIs directly** (no `requests`, `httpx`, or hand-rolled OData clients). All SAP API consumption MUST go through MCP servers. The agent consumes them as tools, never as raw HTTP calls (regardless of whether it's an existing MCP Server or a new MCP Server created by the `mcp-translation-file` skill).
- Only use public APIs; mock any private systems (like S/4HANA) with minimal mock data
- AI Core is available at **runtime** via LiteLLM (environment variables provided at deployment) but is **NOT available during tests** — all LLM calls must be mocked
- No Git operations, no authentication, no documentation/READMEs
- Update `requirements.txt` for any new dependencies
- Never modify `sys.path`
- Map SAP Joule Studio/Skills concepts to standard agent tools
- No `.env` files (environment variables supplied at runtime)

## LLM Integration Patterns

### AI Core Integration

```python
def _summarize_with_llm(
    self,
    user_input: str,
    tool_result: Dict[str, Any],
    action_result: Optional[Dict[str, Any]] = None
) -> str:
    """Summarize results using SAP AI Core deployed model."""
    access_token = self._get_access_token()
    responses_url = f"{self.deployment_url}/v1/responses"
    
    # System instruction for the LLM
    system_instruction = """
You are a SAP Joule agent assistant.
You receive a user query, API results, and optionally action results.

Return a concise business-friendly answer.

Rules:
- Clearly state the detected intent and API endpoint used
- Summarize key results using available JSON fields
- If an action was created, state action ID, type, priority, and next steps
- If no action was requested, do not mention actions
- If no data found, explain why and mention the filters used
- Do NOT invent data not present in the API result
- Keep responses chat-appropriate (concise, scannable)
- Use markdown for formatting when appropriate
"""
    
    # Prepare context from tool results
    context = {
        "user_query": user_input,
        "api_endpoint": tool_result.get("endpoint"),
        "intent": tool_result.get("intent"),
        "filters": tool_result.get("filters"),
        "result_count": tool_result.get("count"),
        "results": tool_result.get("results", [])
    }
    
    if action_result:
        context["action"] = action_result
    
    # Build LLM request
    payload = {
        "instructions": system_instruction,
        "context": json.dumps(context, indent=2),
        "temperature": 0.3,
        "max_tokens": 500
    }
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "AI-Resource-Group": self.resource_group
    }
    
    try:
        response = httpx.post(
            responses_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        return self._extract_response_text(result)
    except Exception as e:
        # Fallback to structured response if LLM fails
        return self._fallback_response(user_input, tool_result, action_result)

def _fallback_response(
    self,
    user_input: str,
    tool_result: Dict[str, Any],
    action_result: Optional[Dict[str, Any]] = None
) -> str:
    """Generate fallback response without LLM."""
    endpoint = tool_result.get("endpoint", "unknown")
    count = tool_result.get("count", 0)
    
    response = f"Found {count} results from {endpoint}."
    
    if count > 0 and tool_result.get("results"):
        # Show first result as example
        first = tool_result["results"][0]
        response += f"\n\nExample: {json.dumps(first, indent=2)}"
    
    if action_result:
        action_id = action_result.get("action_id")
        action_type = action_result.get("action_type")
        response += f"\n\n✅ Action {action_id} ({action_type}) created successfully."
    
    return response
```

### System Prompt Best Practices

When crafting system instructions for LLMs:

1. **Be explicit about data constraints**: Instruct the model not to hallucate or invent data
2. **Set pagination limits**: Always instruct to use `top` parameter (max 100) to prevent context overflow
3. **Define output format**: Specify markdown, structure, tone, and length expectations
4. **Clarify context**: Explain what data sources are available and how to interpret them
5. **Error handling**: Define behavior when data is missing or incomplete
6. **Business domain**: Include domain-specific terminology and conventions

```python
# Example: System prompt with guardrails
system_prompt = """
You are an SAP inventory management assistant.

Available Tools:
- get_stock_levels: Query material stock by plant
- get_gr_ir_mismatch: Query goods receipt / invoice receipt discrepancies
- create_replenishment: Create replenishment request

CRITICAL RULES:
- NEVER invent material numbers, plant codes, or quantities
- When calling tools that accept 'top' parameter, ALWAYS set it to maximum 100
- If user requests more than 100 items, inform them only first 100 will be shown
- Only use data returned by tools in your response
- If a tool returns empty results, explain why based on filters used
- Format numbers according to SAP conventions (e.g., material numbers with leading zeros)
- Always confirm action parameters before creating requests

Response Format:
- Use markdown for structure (headers, lists, tables)
- Keep responses concise (under 200 words)
- Use bullet points for multiple items
- Include action IDs when operations complete
"""
```

### LLM Call Mocking (for Tests)

```python
# conftest.py
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_llm():
    """Mock LLM calls for testing."""
    with patch('app.agent.MyAgent._summarize_with_llm') as mock:
        mock.return_value = "Mocked LLM response"
        yield mock

# test_agent.py
def test_agent_with_mocked_llm(mock_llm):
    """Test agent without making real LLM calls."""
    agent = MyAgent()
    result = agent.invoke("Show stock out materials", context_id="test-123")
    
    assert "response" in result
    mock_llm.assert_called_once()
```

## Code Quality

- All Python code must compile with valid imports
- No `src.` import patterns
- All function parameters must be used in function body

## Agent Decorators

- The bootstrap template already includes decorator scaffolding — no separate skill invocation needed
- **NEVER add new decorated functions to `app/agent.py`** — the three from the bootstrap template (`@agent_model`, `@agent_config` for temperature, `@prompt_section`) are the complete and final set. `@agent_config` is not a general-purpose decorator; it exposes parameters to the SAP platform UI and is intentionally limited to temperature. All other values (thresholds, limits, counts, etc.) must be plain Python constants.
- Never mark decorator tasks complete until `sap_cloud_sdk.agent_decorators` imports exist in `app/agent.py`

## Agent Instrumentation

- ALL business logic steps MUST be instrumented with proper logging and OpenTelemetry spans
- Use milestones from the PRD's "Milestones" section (if available) or derive from the project input for business step instrumentation
- Each milestone must emit structured log statements on achievement and miss
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`
- Add OpenTelemetry custom spans for each business step using `tracer.start_as_current_span` — use the **decorator form** (`@tracer.start_as_current_span("name")`) on regular async methods, or the **context manager form** (`with tracer.start_as_current_span("name"):`) inside non-generator async functions
- **NEVER use `with tracer.start_as_current_span(...)` as a context manager inside an async generator** (i.e. any method containing `yield`). Doing so causes `ValueError: Token was created in a different Context` when the generator is closed via `GeneratorExit`. For `stream()`, extract all business logic into a plain async helper method (e.g. `_run_agent()`) and instrument that method instead, then call it from `stream()` and yield the result outside any span context.
- Ensure `auto_instrument()` is called at top of `main.py` before any AI framework imports

## MCP Tool Integration

All SAP API integrations MUST use this pattern. If the PRD or specification references any SAP API (OData, REST, events), MCP wiring is mandatory, not optional.

MCP tool names are prefixed with an MCP server identifier at runtime (e.g. `mcp_myserver__get_items`). **Never hard-code tool names in code.** Retrieve tools dynamically via `get_mcp_tools()` and let the agent resolve them by capability, not by name.

When writing system instructions for the agent, explicitly instruct the agent not to hallucinate data. The system prompt MUST always instruct the agent to set `top` (or equivalent page-size parameter) to a maximum of 100 on every tool call that accepts it — regardless of whether the user requested a limit — to prevent context overflow. The agent must inform the user when this limit is applied.

### Canonical Pattern

```python
from mcp_tools import get_mcp_tools

async def _load_tools() -> list:
    return await get_mcp_tools()
```

`mcp_tools.py` is the owned indirection layer produced by the bootstrap — import from there, never directly from `sap_cloud_sdk.agentgateway`. This is the target the test fixture patches.

Call `_load_tools()` lazily (not in `__init__`) — it makes network calls. Wire the result into the agent graph:

```python
class MyAgent:
    def __init__(self):
        self._tools = None

    async def _get_tools(self) -> list:
        if self._tools is None:
            self._tools = await _load_tools()
        return self._tools

    async def stream(self, query, context_id, ext_impl=None):
        tools = await self._get_tools()
        graph = self._build_graph(tools, system_prompt=get_system_prompt())
        ...
```

### Local Testing (IBD_TESTING)

**Do NOT branch on `IBD_TESTING` in application code.** The `conftest.py` monkey-patches `mcp_tools.get_mcp_tools` before any agent code runs. Agent code stays identical in production and tests.

The patch returns `StructuredTool` instances built from `mcp-mock.json`. Generate `mcp-mock.json` with the `mcp-mock-config` skill before running tests.

## Testing

Working directory for all test operations: `assets/<asset-name>/` (asset root).

### Setup

1. Install test dependencies: `pip install -r requirements-test.txt`

### Environment Configuration

```python
import socket

def is_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result != 0
    except Exception:
        return False

def find_available_port(start_port: int = 8080, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    for offset in range(max_attempts):
        port = start_port + offset
        if is_port_available(port):
            return port
    raise RuntimeError(f"Could not find an available port starting from {start_port}")

def get_app_url(host: str, port: int) -> str:
    """Get application URL for local or Cloud Foundry environment."""
    vcap = json.loads(os.getenv("VCAP_APPLICATION", "{}"))
    uris = vcap.get("application_uris", [])
    if uris:
        return f"https://{uris[0]}"
    # Use localhost instead of 0.0.0.0 for URLs
    display_host = "localhost" if host == "0.0.0.0" else host
    return f"http://{display_host}:{port}"
```

### Action Execution Patterns

Agents can handle actions in two modes: **Human-in-the-Loop** (requires confirmation) or **Auto-Action** (executes autonomously).

#### Pattern 1: Human-in-the-Loop (Confirmation Required)

For high-risk operations that require explicit user approval:

```python
class MyAgent:
    def __init__(self):
        # In-memory action state (use database/cache for production)
        self.pending_actions: Dict[str, Dict[str, Any]] = {}
    
    def invoke(self, user_input: str, context_id: Optional[str] = None) -> dict:
        """Agent invocation with confirmation workflow."""
        action_key = context_id or "default"
        
        # Handle pending action confirmation/rejection
        if action_key in self.pending_actions:
            pending = self.pending_actions[action_key]
            
            if self._is_confirmation(user_input):
                # User approved - execute action
                result = self._execute_action(pending)
                del self.pending_actions[action_key]
                return {
                    "content": f"✅ Action completed: {result['action_id']}",
                    "artifact_name": "action_result"
                }
            
            elif self._is_rejection(user_input):
                # User rejected - cancel action
                del self.pending_actions[action_key]
                return {
                    "content": "Action cancelled. How else can I help?",
                    "artifact_name": "response"
                }
        
        # Analyze query and determine if action is needed
        analysis = self._analyze_query(user_input)
        
        if analysis.get("requires_action") and analysis.get("risk_level") == "high":
            # High-risk action - require confirmation
            action_proposal = self._prepare_action_proposal(analysis)
            self.pending_actions[action_key] = action_proposal
            
            return {
                "content": (
                    f"{analysis['summary']}\n\n"
                    f"⚠️ This will {action_proposal['description']}.\n\n"
                    f"Reply 'yes' to proceed or 'no' to cancel."
                ),
                "artifact_name": "confirmation"
            }
        
        # No action or low-risk action (see Auto-Action pattern)
        return self._generate_response(analysis)
```

#### Pattern 2: Auto-Action (Autonomous Execution)

For low-risk, routine operations that agents can execute autonomously:

```python
class MyAgent:
    def __init__(self):
        # Define auto-executable action types with risk assessment
        self.auto_action_whitelist = {
            "search": {"max_risk": "low"},
            "read_data": {"max_risk": "low"},
            "create_notification": {"max_risk": "medium"},
            "update_status": {"max_risk": "medium", "conditions": ["non_critical"]}
        }
    
    def _assess_action_risk(self, action: Dict[str, Any]) -> str:
        """Assess risk level: low, medium, high."""
        action_type = action.get("type")
        
        # High-risk criteria
        if action_type in ["delete", "purchase", "financial_transaction"]:
            return "high"
        if action.get("amount", 0) > 10000:
            return "high"
        if action.get("irreversible", False):
            return "high"
        
        # Medium-risk criteria
        if action_type in ["create", "update", "send"]:
            return "medium"
        
        # Low-risk (read-only, queries, searches)
        return "low"
    
    def _can_auto_execute(self, action: Dict[str, Any]) -> bool:
        """Determine if action can be auto-executed."""
        action_type = action.get("type")
        risk_level = self._assess_action_risk(action)
        
        # Check whitelist
        if action_type not in self.auto_action_whitelist:
            return False
        
        whitelist_config = self.auto_action_whitelist[action_type]
        
        # Verify risk level is within allowed threshold
        risk_hierarchy = {"low": 0, "medium": 1, "high": 2}
        if risk_hierarchy[risk_level] > risk_hierarchy[whitelist_config["max_risk"]]:
            return False
        
        # Check additional conditions
        conditions = whitelist_config.get("conditions", [])
        for condition in conditions:
            if not self._check_condition(action, condition):
                return False
        
        return True
    
    def invoke(self, user_input: str, context_id: Optional[str] = None) -> dict:
        """Agent invocation with auto-action capability."""
        # Analyze query
        analysis = self._analyze_query(user_input)
        
        if analysis.get("requires_action"):
            action = self._prepare_action(analysis)
            
            if self._can_auto_execute(action):
                # Auto-execute low/medium-risk actions
                result = self._execute_action(action)
                
                return {
                    "content": (
                        f"{analysis['summary']}\n\n"
                        f"✅ I've automatically {action['description']}.\n"
                        f"Action ID: {result['action_id']}"
                    ),
                    "artifact_name": "action_result"
                }
            else:
                # High-risk - require confirmation (Pattern 1)
                self.pending_actions[context_id or "default"] = action
                
                return {
                    "content": (
                        f"{analysis['summary']}\n\n"
                        f"⚠️ This requires confirmation: {action['description']}\n\n"
                        f"Reply 'yes' to proceed or 'no' to cancel."
                    ),
                    "artifact_name": "confirmation"
                }
        
        # Information-only response
        return self._generate_response(analysis)
```

#### Pattern 3: Hybrid Mode (Configurable)

Allow users to configure auto-action behavior:

```python
class MyAgent:
    def __init__(self, auto_action_mode: str = "conservative"):
        """
        auto_action_mode:
        - 'conservative': Only auto-execute read operations
        - 'balanced': Auto-execute low/medium-risk operations
        - 'aggressive': Auto-execute most operations except destructive ones
        - 'manual': Always require confirmation
        """
        self.auto_action_mode = auto_action_mode
        self.pending_actions: Dict[str, Dict[str, Any]] = {}
    
    def _can_auto_execute(self, action: Dict[str, Any]) -> bool:
        """Check if action can be auto-executed based on mode."""
        if self.auto_action_mode == "manual":
            return False
        
        risk_level = self._assess_action_risk(action)
        
        if self.auto_action_mode == "conservative":
            return risk_level == "low" and action["type"] in ["search", "read"]
        
        if self.auto_action_mode == "balanced":
            return risk_level in ["low", "medium"]
        
        if self.auto_action_mode == "aggressive":
            return risk_level != "high"
        
        return False
```

#### Best Practices

1. **Risk Assessment**: Always evaluate action risk before execution
2. **Audit Logging**: Log all auto-executed actions with timestamps and context
3. **Rollback Support**: Provide undo/rollback for reversible auto-actions
4. **User Notification**: Inform users of auto-executed actions even without confirmation
5. **Configurable Thresholds**: Allow customization of auto-action risk thresholds
6. **Circuit Breaker**: Implement failure limits to prevent cascading auto-actions
7. **Dry-Run Mode**: Support simulation mode to preview actions without execution

### Boilerplate Files

- `conftest.py` — shared fixtures, custom markers, writes `test_report.json` on full runs
- `pytest.ini` — configures test discovery (`prebuilt_tests/`, `tests/`), default flags, markers
- `requirements-test.txt` — test dependencies
- `prebuilt_tests/` — pre-built structure and server tests; NEVER modify these

### Writing Tests

- All generated tests go in `assets/<asset-name>/tests/` (NOT inside `app/`)
- Unit tests: exactly one per tool; run each immediately after writing
- Integration test: one end-to-end test exercising the full agent graph
- **AI Core / LLM calls MUST be mocked in all tests.** AI Core credentials are NOT available in the test environment. Patch the LLM (e.g. `ChatLiteLLM`) to return canned responses. Never make real network calls to AI Core during tests.
- Mock all external systems (S/4HANA, MCP servers, AI Core) — tests must run offline

### Running Tests

- ALWAYS invoke as just `pytest` from asset root — no paths, no `--cov`, no `--json-report`, no extra flags
- `pytest.ini` configures everything; extra CLI flags conflict with ini settings
- Only exception: targeting a single test: `pytest path/to/test_file.py::test_name`
- Coverage must be ≥ 70%; if below, add targeted tests until threshold met
- Final `pytest` run (no args) MUST produce `test_report.json` — this only happens on full runs without arguments

## Agent Card & A2A Protocol

### Agent Card Configuration

The agent card defines the agent's capabilities, skills, and interfaces. It must be exposed via the `/.well-known/agent.json` endpoint.

```python
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

def get_agent_card(base_url: str) -> AgentCard:
    """Define agent capabilities and skills."""
    capabilities = AgentCapabilities(
        streaming=False,
        push_notifications=False
    )
    
    # Define skills with examples
    main_skill = AgentSkill(
        id="inventory_insights",
        name="Inventory Insights",
        description=(
            "Routes queries to APIs for inventory analysis and "
            "provides AI-generated summaries"
        ),
        tags=["inventory", "procurement", "analytics"],
        examples=[
            "Show me stock out materials for Plant 1004",
            "List GR/IR mismatches for supplier 1020217",
            "Find slow-moving items in plant 1028"
        ]
    )
    
    return AgentCard(
        name="my-agent",
        description="Agent description for discovery and routing",
        documentation_url=f"{base_url}/docs",
        version="1.0.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=capabilities,
        skills=[main_skill],
        supported_interfaces=[]
    )
```

### A2A Request/Response Patterns

#### Executing Agent Logic

```python
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Artifact, Part,
    TaskArtifactUpdateEvent,
    TaskStatusUpdateEvent
)

class MyAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = MyAgent()
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Execute agent logic and emit A2A events."""
        user_input = context.get_user_input()
        task_id = get_task_id(context)
        context_id = get_context_id(context)
        
        try:
            # Execute agent logic
            response = self.agent.invoke(user_input, context_id)
            content = response.get("content", "No response")
            
            # Create artifact with response
            parts = [Part(text=content)]
            artifact = build_event(
                Artifact,
                artifact_id=str(uuid4()),
                name="response",
                parts=parts
            )
            
            # Emit artifact update event
            await event_queue.enqueue_event(
                build_event(
                    TaskArtifactUpdateEvent,
                    task_id=task_id,
                    context_id=context_id,
                    artifact=artifact,
                    append=False,
                    last_chunk=True
                )
            )
            
            # Update task status to completed
            task = context.current_task
            if task:
                task.status.state = 3  # COMPLETED
                task.status.timestamp = datetime.now()
                
                await event_queue.enqueue_event(
                    build_event(
                        TaskStatusUpdateEvent,
                        task_id=task_id,
                        context_id=context_id,
                        status=task.status,
                        final=True
                    )
                )
        
        except Exception as e:
            # Handle errors and emit failure events
            error_content = f"Error: {str(e)}"
            # ... emit error artifact and status update
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handle cancellation requests."""
        raise Exception("cancel not supported")
```

#### Server Setup with Routes

```python
from starlette.applications import Starlette
from starlette.routing import Route
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.routes.rest_routes import create_rest_routes

def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    agent_card = get_agent_card(f"http://{host}:{port}")
    handler = DefaultRequestHandler(
        agent_executor=MyAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card
    )
    
    # Create routes with A2A v0.3 compatibility
    jsonrpc_routes = create_jsonrpc_routes(
        handler,
        rpc_url="/",
        enable_v0_3_compat=True
    )
    rest_routes_list = create_rest_routes(
        handler,
        enable_v0_3_compat=True
    )
    
    # Custom agent card endpoint
    async def card_endpoint(request):
        card_dict = MessageToDict(
            agent_card,
            preserving_proto_field_name=False
        )
        card_dict['url'] = f"http://{host}:{port}"
        return JSONResponse(card_dict, status_code=200)
    
    routes = [
        Route("/.well-known/agent.json", card_endpoint, methods=["GET"]),
        *rest_routes_list,
    ]
    
    app = Starlette(routes=routes + jsonrpc_routes)
    uvicorn.run(app, host=host, port=port)
```

### Calling Remote Agents (Agent-to-Agent)

From Joule capabilities, call remote agents using the `agent-request` action:

```yaml
# functions/call_agent.yaml
parameters:
  - name: user_query
    optional: false

action_groups:
  - actions:
      - type: agent-request
        agent_type: remote
        system_alias: MyAgentSystem  # References capability_context.yaml
        body: <? user_query ?>
        result_variable: agent_response
  
  - condition: agent_response.body != null && agent_response.body.artifacts != null && agent_response.body.artifacts.size() > 0
    actions:
      - type: message
        message:
          type: text
          markdown: true
          content: <? agent_response.body.artifacts[0].parts[0].text ?>
  
  - condition: agent_response.body == null || agent_response.body.artifacts == null || agent_response.body.artifacts.size() == 0
    actions:
      - type: message
        message:
          type: text
          content: "Could not retrieve response from agent."
```

**capability_context.yaml** - Define system alias for agent:

```yaml
systems:
  - name: MyAgentSystem
    base_url: ${dest:MyAgentDestination}
    auth:
      type: destination
      destination_name: MyAgentDestination
```

## Common Utility Methods

Agents commonly require helper methods for data processing and validation. Include these patterns in your agent implementation:

### Data Extraction & Validation

```python
@staticmethod
def _extract_number_after_keywords(text: str, keywords: list[str]) -> Optional[str]:
    """Extract numeric values following specific keywords in user input."""
    for keyword in keywords:
        match = re.search(rf"\b{re.escape(keyword)}\b\s*[:#-]?\s*(\d+)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None

@staticmethod
def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert any value to integer with fallback."""
    try:
        return int(value)
    except Exception:
        return default

@staticmethod
def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float with fallback."""
    try:
        return float(str(value).strip())
    except Exception:
        return default

@staticmethod
def _to_bool(value: Any) -> bool:
    """Convert various representations to boolean."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "x", "1", "yes", "y"}

@staticmethod
def _clean_material(material: Any) -> str:
    """Clean material numbers by removing leading zeros."""
    return str(material or "").strip().lstrip("0")
```

### Intent Classification

```python
@staticmethod
def _is_greeting(text: str) -> bool:
    """Detect greeting or help requests."""
    normalized = text.lower().strip()
    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", 
                 "good evening", "what can you do", "help"}
    return normalized in greetings

@staticmethod
def _is_action_request(text: str) -> bool:
    """Detect if user is requesting an action."""
    normalized = text.lower()
    action_keywords = ["take action", "create action", "create replenishment",
                       "raise request", "create pr", "recommend action", 
                       "create task", "resolve", "initiate", "trigger"]
    return any(keyword in normalized for keyword in action_keywords)

@staticmethod
def _is_confirmation(text: str) -> bool:
    """Detect user confirmation."""
    normalized = text.lower().strip()
    confirmation_keywords = ["yes", "y", "proceed", "confirm", "go ahead",
                             "do it", "execute", "create it", "approve"]
    return normalized in confirmation_keywords or \
           any(keyword in normalized for keyword in confirmation_keywords)
```

### Response Processing

```python
@staticmethod
def _extract_response_text(data: dict) -> str:
    """Extract text from OpenAI Responses API response."""
    if data.get("output_text"):
        return data["output_text"]
    
    texts = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in ("output_text", "text"):
                text = content.get("text")
                if text:
                    texts.append(text)
    if texts:
        return "\n".join(texts)
    return json.dumps(data, indent=2)
```

### Context & Task Management

```python
def get_task_id(context: RequestContext) -> str:
    """Extract task ID from context with fallback."""
    task = context.current_task
    return (
        getattr(context, "task_id", None) or
        getattr(context, "taskId", None) or
        getattr(task, "id", None) or
        str(uuid4())
    )

def get_context_id(context: RequestContext) -> str:
    """Extract context ID from context with fallback."""
    task = context.current_task
    return (
        getattr(context, "context_id", None) or
        getattr(context, "contextId", None) or
        getattr(task, "context_id", None) or
        getattr(task, "contextId", None) or
        str(uuid4())
    )

def build_event(cls, **kwargs):
    """Compatibility helper for A2A SDK versions (snake_case vs camelCase)."""
    try:
        return cls(**kwargs)
    except Exception:
        converted = {}
        for key, value in kwargs.items():
            if key == "task_id":
                converted["taskId"] = value
            elif key == "context_id":
                converted["contextId"] = value
            elif key == "artifact_id":
                converted["artifactId"] = value
            elif key == "last_chunk":
                converted["lastChunk"] = value
            else:
                converted[key] = value
        return cls(**converted)
```

## Security & Authentication

### Credential Management

**NEVER hardcode credentials.** All sensitive configuration must be loaded from environment variables or Cloud Foundry service bindings.

```python
def _get_aicore_credentials(self) -> dict:
    """Read AI Core credentials from local .env or CF VCAP_SERVICES."""
    # Local development: environment variable
    service_key = os.getenv("AICORE_SERVICE_KEY")
    if service_key:
        return json.loads(service_key)
    
    # Cloud Foundry: bound service
    vcap_services = json.loads(os.getenv("VCAP_SERVICES", "{}"))
    if "aicore" in vcap_services:
        return vcap_services["aicore"][0]["credentials"]
    
    # Generic service detection
    for service_instances in vcap_services.values():
        for service in service_instances:
            credentials = service.get("credentials", {})
            if "serviceurls" in credentials and \
               "AI_API_URL" in credentials.get("serviceurls", {}):
                return credentials
    
    raise RuntimeError(
        "No AI Core credentials found. Set AICORE_SERVICE_KEY locally or "
        "bind an AI Core service instance in Cloud Foundry."
    )

def _get_access_token(self) -> str:
    """Obtain OAuth2 access token using client credentials."""
    token_url = self.credentials["url"].rstrip("/") + "/oauth/token"
    response = httpx.post(
        token_url,
        data={"grant_type": "client_credentials"},
        auth=(self.credentials["clientid"], self.credentials["clientsecret"]),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]
```

### Principal Propagation

Principal propagation enables the agent to act on behalf of the authenticated user, preserving user identity across service calls.

#### Pattern: User Token Forwarding

```python
async def _call_backend_with_user_context(
    self,
    user_token: str,
    endpoint: str,
    method: str = "GET",
    data: Optional[dict] = None
) -> dict:
    """Call backend service with user's identity via principal propagation."""
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=endpoint,
            headers=headers,
            json=data,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
```

#### Pattern: Token Exchange (JWT Bearer Flow)

For services requiring token exchange:

```python
def _exchange_user_token(self, user_token: str, target_service: str) -> str:
    """Exchange user token for target service token (JWT Bearer grant)."""
    token_url = self.credentials["url"].rstrip("/") + "/oauth/token"
    
    response = httpx.post(
        token_url,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": user_token,
            "scope": f"{target_service}.read {target_service}.write"
        },
        auth=(self.credentials["clientid"], self.credentials["clientsecret"]),
        timeout=30
    )
    response.raise_for_status()
    return response.json()["access_token"]
```

### SAP Destination Service

The Destination Service provides centralized configuration for external system connectivity with built-in authentication support.

#### Pattern: Destination Lookup

```python
async def _get_destination_config(self, destination_name: str) -> dict:
    """Retrieve destination configuration from SAP Destination Service."""
    # Get Destination Service credentials from VCAP_SERVICES
    vcap = json.loads(os.getenv("VCAP_SERVICES", "{}"))
    dest_service = vcap.get("destination", [{}])[0]
    dest_creds = dest_service.get("credentials", {})
    
    # Obtain access token for Destination Service
    token = self._get_destination_service_token(dest_creds)
    
    # Fetch destination configuration
    dest_url = dest_creds["uri"].rstrip("/")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{dest_url}/destination-configuration/v1/destinations/{destination_name}",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

def _get_destination_service_token(self, dest_creds: dict) -> str:
    """Obtain token for Destination Service API."""
    token_url = dest_creds["url"].rstrip("/") + "/oauth/token"
    response = httpx.post(
        token_url,
        data={"grant_type": "client_credentials"},
        auth=(dest_creds["clientid"], dest_creds["clientsecret"]),
        timeout=30
    )
    response.raise_for_status()
    return response.json()["access_token"]
```

#### Pattern: Using Destinations with Principal Propagation

```python
async def _call_via_destination(
    self,
    destination_name: str,
    path: str,
    user_token: Optional[str] = None,
    method: str = "GET",
    data: Optional[dict] = None
) -> dict:
    """
    Call external system via Destination Service.
    Supports Principal Propagation when user_token is provided.
    """
    dest_config = await self._get_destination_config(destination_name)
    
    # Extract destination details
    url = dest_config["destinationConfiguration"]["URL"].rstrip("/") + path
    auth_type = dest_config["destinationConfiguration"].get("Authentication")
    
    headers = {"Content-Type": "application/json"}
    
    # Handle authentication based on destination configuration
    if auth_type == "PrincipalPropagation" and user_token:
        # Forward user token for principal propagation
        headers["Authorization"] = f"Bearer {user_token}"
    elif auth_type == "OAuth2ClientCredentials":
        # Use destination's OAuth credentials
        token = self._get_destination_oauth_token(dest_config)
        headers["Authorization"] = f"Bearer {token}"
    elif auth_type == "BasicAuthentication":
        # Use basic auth from destination
        user = dest_config["destinationConfiguration"]["User"]
        password = dest_config["destinationConfiguration"]["Password"]
        auth = (user, password)
    else:
        auth = None
    
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            auth=auth if auth_type == "BasicAuthentication" else None,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
```

#### Destination Configuration Example

**manifest.yml** - Binding Destination Service:

```yaml
applications:
  - name: my-agent
    services:
      - my-aicore-service
      - my-destination-service  # Bind Destination Service
```

**destination.json** - Destination Configuration:

```json
{
  "Name": "S4HANA_BACKEND",
  "Type": "HTTP",
  "ProxyType": "Internet",
  "Authentication": "PrincipalPropagation",
  "URL": "https://s4hana-backend.example.com",
  "Description": "S/4HANA backend with user propagation"
}
```

### Security Best Practices

1. **Never log sensitive data**: Credentials, tokens, PII must never appear in logs
2. **Token expiry handling**: Implement token refresh logic for long-running processes
3. **Secure token storage**: Use in-memory storage only; never persist tokens to disk
4. **Minimum privilege**: Request only the OAuth scopes required for the operation
5. **Validate tokens**: Always validate JWT signatures when accepting user tokens
6. **HTTPS only**: Never make API calls over HTTP in production
7. **Timeout configuration**: Always set request timeouts to prevent hanging connections
8. **Error message sanitization**: Don't expose internal system details in error messages

```python
# ❌ BAD - Logs sensitive data
logging.info(f"Using token: {access_token}")

# ✅ GOOD - Logs safely
logging.info("Successfully obtained access token")

# ❌ BAD - No timeout
response = httpx.get(url, headers=headers)

# ✅ GOOD - With timeout
response = httpx.get(url, headers=headers, timeout=30)
```

## Validation Checklist

Run these verifications before marking implementation complete:

```bash
# Instrumentation
grep -r "M[0-9]\.achieved" assets/<asset-name>/app/     # must return results

# Decorators
grep -r "sap_cloud_sdk.agent_decorators" assets/<asset-name>/app/  # must return results
grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/<asset-name>/app/agent.py  # must return 3 (one @agent_model, one @agent_config for temperature, one @prompt_section)

# Test report
ls assets/<asset-name>/test_report.json                  # must exist

# Security checks
grep -r "password\|token\|secret\|key" assets/<asset-name>/app/ | grep -i "print\|log"  # should return no sensitive logging
```

## MCP Translation Files, MCP Servers & Mock Tools (Post-Implementation)

After all asset spec TODO items are complete, run the applicable path(s):

### Skill Availability — Graceful Degradation

The `mcp-translation-file` skill depends on the `generate_mcp_translation` tool which is only available in the Joule studio runtime. **Before invoking Path A**, check whether the skill is available:

- If `mcp-translation-file` **is available** (i.e. the skill exists) → proceed with Path A normally.
- If `mcp-translation-file` **is available but doesn't pass the Gate 0** (i.e. the `generate_mcp_translation` tool is not available) **OR** if `mcp-translation-file` **is NOT available** (i.e. the skill does not exist) → skip Path A entirely (no translation files, no MCP server assets). Log: `[MCP-SKILL] mcp-translation-file unavailable — skipping MCP server asset generation. Agent will use existing MCP servers only.` Continue the process normally with Path B (if applicable) or proceed directly to testing. The solution will not include MCP server assets for APIs that lack pre-existing MCP servers.

This does NOT affect Path B (existing MCP servers with known ORD IDs) — those always work regardless of skill availability.

### Path A — API spec files (OData/REST, no existing MCP server)

Run when `specification/<asset-name>/api-specs/` contains API spec files (e.g. `supplier-invoices.json`).

1. **MCP Translation Files:** Invoke the `mcp-translation-file` skill. Do NOT manually create translation files.
2. **MCP Server Assets:** Invoke the `setup-solution` skill to create MCP server assets for any translation files generated in step 1. Do NOT manually create any MCP server assets.

Remember the names and ORD IDs of the generated MCP servers for later reference in the agent's `asset.yaml` required dependencies.

### Path B — MCP spec files (existing MCP server with known ORD ID)

Run when `specification/<asset-name>/mcp-specs/` contains `mcp-spec-*.json` files captured during API discovery (step 2a).

No translation or MCP server asset creation needed — the MCP server already exists externally.

Remember the names and ORD IDs of the existing MCP servers for later reference in the agent's `asset.yaml` required dependencies.

### MCP Server Dependencies in asset.yaml

For **every** MCP server the agent uses, add a corresponding entry to the agent's `asset.yaml` under `requires`:

```yaml
requires:
  - name: <mcp-server-name>
    kind: mcp-server
    ordId: <ord-id>
```

This applies to both internally created MCP server assets (Path A) and externally existing MCP servers (Path B).

### Mock MCP Configuration

After **both** `mcp-translation-file` and `setup-solution` have completed (Path A), or after confirming existing MCP specs (Path B), invoke the `mcp-mock-config` skill to generate `mcp-mock.json`. This must be the **last** MCP-related skill invoked — never before `mcp-translation-file` or `setup-solution`.

The required chain is: `mcp-translation-file` → `setup-solution` → `mcp-mock-config`.

## Agent Evaluation (Post-Implementation)

Run after all tests pass and the agent is working locally.

### Step 1: Generate tool schema

Invoke the `sap-aeval-generate-tool-schema` skill from the asset root (`assets/<asset-name>/`). It scans the `app/` directory, extracts all tool function signatures and docstrings, and writes `tools.json` to the current working directory.

### Step 2: Generate eval test cases

Invoke the `sap-aeval-generate-testcase` skill from the same asset root, passing:

- The PRD file path (e.g. `specification/<asset-name>/specification.md`)
- `tools.json` generated in Step 1

The skill writes eval criteria to `aeval/eval.yaml` and YAML test cases to `aeval/testcases/`. Review the generated test cases and replace any placeholder values (e.g. `<param_name:example>`) with realistic data before running evaluations.

---

## Quick Reference

### Common Import Patterns

```python
# A2A Protocol
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    AgentCard, AgentCapabilities, AgentSkill,
    Artifact, Part,
    TaskArtifactUpdateEvent, TaskStatusUpdateEvent
)

# HTTP & Authentication
import httpx
import os
import json
from typing import Any, Dict, List, Optional

# Utilities
from uuid import uuid4
from datetime import datetime
import re

# MCP Tools
from mcp_tools import get_mcp_tools

# SAP Cloud SDK (decorators)
from sap_cloud_sdk.agent_decorators import agent_model, agent_config, prompt_section
```

### Essential Environment Variables

```bash
# AI Core Configuration
AICORE_SERVICE_KEY="<json_service_key>"
AICORE_DEPLOYMENT_ID="<deployment_id>"
AICORE_DEPLOYMENT_URL="<full_deployment_url>"
AICORE_RESOURCE_GROUP="default"
MODEL_NAME="gpt-5.5"

# Server Configuration
HOST="0.0.0.0"
PORT="8080"

# Testing
IBD_TESTING="true"  # Set automatically by test fixtures
```

### Key File Locations

```
assets/<asset-name>/
├── asset.yaml                    # Asset metadata
├── app/
│   ├── __init__.py
│   ├── __main__.py              # Server entry point
│   ├── agent.py                 # Core agent logic
│   ├── agent_card.py            # Agent card definition
│   ├── agent_executor.py        # A2A executor
│   ├── mcp_tools.py             # MCP tool loader
│   └── tools.py                 # Custom tools
├── tests/                       # Generated tests
├── prebuilt_tests/              # Framework tests (don't modify)
├── conftest.py                  # Test fixtures
├── pytest.ini                   # Test configuration
├── requirements.txt             # Runtime dependencies
├── requirements-test.txt        # Test dependencies
├── mcp-mock.json               # MCP mock configuration
└── test_report.json            # Generated by pytest
```

### Common Command Sequences

```bash
# Development workflow (from asset root)
cd assets/<asset-name>

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run agent locally
python -m app

# Run all tests
pytest

# Run specific test
pytest tests/test_my_feature.py::test_specific_function

# Check coverage (configured in pytest.ini)
# Coverage report generated automatically with pytest
```

### Debugging Checklist

When agent behavior is unexpected:

- [ ] Check logs for milestone achievements/misses
- [ ] Verify MCP tools are loaded: `print(await get_mcp_tools())`
- [ ] Confirm environment variables are set: `echo $AICORE_DEPLOYMENT_ID`
- [ ] Test credential loading: Verify `_get_aicore_credentials()` succeeds
- [ ] Check token generation: Verify `_get_access_token()` returns valid token
- [ ] Validate system prompt: Ensure no hallucination instructions present
- [ ] Review agent card: Confirm skills and examples are accurate
- [ ] Test with mocked LLM: Isolate logic from model responses
- [ ] Check A2A event emission: Verify TaskArtifactUpdateEvent is emitted
- [ ] Validate JSON responses: Ensure proper structure and no null artifacts

### Security Checklist

Before deployment:

- [ ] No hardcoded credentials in code
- [ ] All secrets loaded from environment or VCAP_SERVICES
- [ ] No sensitive data in logs (tokens, passwords, PII)
- [ ] All HTTP calls use HTTPS in production
- [ ] Request timeouts configured (30s recommended)
- [ ] Token refresh logic implemented for long operations
- [ ] Destination Service used for external system connectivity
- [ ] Principal propagation implemented for user context
- [ ] Error messages don't expose internal system details
- [ ] OAuth scopes follow minimum privilege principle
