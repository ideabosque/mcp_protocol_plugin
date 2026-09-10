# MCP Protocol Plugin Development Plan

Status: planning baseline
Last updated: 2026-09-10

## Goal

`mcp_protocol_plugin` owns the Model Context Protocol runtime that is currently
embedded in `mcp_daemon_engine`. It should depend on `silvaengine_daemon` for shared configuration,
gateway dispatch, partitioning, repository contracts, GraphQL execution, and
generic SSE fan-out.

Capability-facing MCP compatibility must move to `capability_mcp_plugin`; this
project should expose daemon-native MCP protocol and catalog APIs only.

## Source Analysis

Source project: `C:\Users\bibo7\gitrepo\silvaengine\mcp_daemon_engine`

Current implementation includes:

- Gateway dispatch functions in `mcp_daemon_engine.main`: GraphQL, MCP JSON-RPC,
  async tool execution, SSE message, cache refresh/clear, and info.
- MCP SDK/runtime handling in `handlers/mcp_server.py` for tools, resources,
  prompts, JSON-RPC processing, and stdio support.
- Dynamic module loading and execution in `handlers/mcp_utility.py`.
- Package registration paths in `handlers/mcp_handlers.py`,
  `handlers/mcp_git.py`, and `handlers/mcp_external.py`.
- External server proxy support in `handlers/external_mcp_proxy.py`.
- MCP catalog entities: functions, modules, settings, and function calls, with
  DynamoDB and PostgreSQL backends plus Alembic migrations.
- Capability compatibility files that should be extracted:
  `types/capability_mcp.py`, `queries/capability_mcp.py`,
  `mutations/capability_mcp.py`, and `handlers/capability_mcp_invoke.py`.

## Target Ownership

Keep in this plugin:

| Area | Target modules |
| --- | --- |
| MCP gateway surface | Native MCP GraphQL, MCP JSON-RPC, async execution, cache management, info dispatch. |
| MCP runtime | Tool/resource/prompt listing, call/read/get prompt handlers, JSON-RPC message processing, stdio runtime. |
| MCP package lifecycle | S3 upload/process, Base64 package loading, Git install/refresh/version check, external MCP sync. |
| MCP catalog | `MCPFunction`, `MCPModule`, `MCPSetting`, `MCPFunctionCall` types, queries, mutations, models, repositories, migrations. |
| Runtime execution | Dynamic import, package extraction, tool execution, audit decoration, S3 result offload. |

Move to or consume from `silvaengine_daemon`:

- Partition defaulting, RLS setup, repository interfaces, GraphQL execution,
  JSON normalization, cache helper conventions, async runner, and generic SSE
  manager.
- Per-plugin module YAML descriptor consumed by `silvaengine_daemon` internal
  plugin routing.
  `silvaengine_gateway` dispatches external requests to `silvaengine_daemon`,
  and `silvaengine_daemon` dispatches matching MCP routes to this plugin.

Move to `capability_mcp_plugin`:

- Capability provider/server/tool/invocation GraphQL projections.
- `registerCapability*`, `invokeCapabilityMcpTool`, `testCapabilityMcpTool`,
  and `unregisterCapabilityMcp` compatibility mutations.
- Built-in module classification as a capability read-view concern, unless it is
  also needed by daemon-native MCP UI.

## Proposed Package Shape

```text
mcp_protocol_plugin/
|-- mcp_protocol_plugin/
|   |-- __init__.py
|   |-- main.py
|   |-- schema.py
|   |-- handlers/
|   |   |-- config.py
|   |   |-- mcp_server.py
|   |   |-- mcp_utility.py
|   |   |-- mcp_handlers.py
|   |   |-- mcp_git.py
|   |   |-- mcp_external.py
|   |   |-- external_mcp_proxy.py
|   |   `-- sse_events.py
|   |-- models/
|   |-- queries/
|   |-- mutations/
|   |-- types/
|   `-- tests/
|-- migration/
|-- docs/
|   `-- DEVELOPMENT_PLAN.md
|-- pyproject.toml
`-- README.md
```

## Migration Phases

### Phase 1: Bootstrap Package

- Create packaging metadata with `mcp>=2.0,<3.0`, `httpx[http2]`, `aiohttp`,
  `graphene`, `python-dotenv`, `SilvaEngine-Utility`,
  `SilvaEngine-DynamoDB-Base`, and optional PostgreSQL extras.
- Copy daemon-native MCP files from `mcp_daemon_engine` and rename imports.
- Do not copy capability compatibility files in this phase.
- Add the native MCP plugin module YAML descriptor required by
  `silvaengine_daemon` internal plugin routing.

### Phase 2: Adopt `silvaengine_daemon`

- Replace local partition/context helpers with `silvaengine_daemon.partitioning`.
- Replace repository base/dispatch scaffolding with the shared contract while
  keeping MCP entity-specific repos here.
- Use shared GraphQL execution and RLS teardown behavior.
- Use shared SSE primitives for connection management and keep MCP event payload
  construction in this plugin.
- Declare and import the shared dependency as `silvaengine_daemon`.

### Phase 3: Catalog and Package Lifecycle

- Port `MCPFunction`, `MCPModule`, `MCPSetting`, and `MCPFunctionCall` GraphQL
  CRUD exactly before adding new behavior.
- Keep migrations for `mcp_functions`, `mcp_modules`, `mcp_settings`, and
  `mcp_function_calls` with `status` and RLS support.
- Preserve S3, Base64, Git, and external sync registration paths.
- Add tests for manifest validation, safe Git URL handling, package extraction
  path safety, and cache invalidation.

### Phase 4: Runtime Protocol Verification

- Port MCP JSON-RPC tests for `tools/list`, `tools/call`, `resources/list`,
  `resources/read`, `prompts/list`, and `prompts/get`.
- Verify gateway dispatch unwraps `statusCode/body` responses consistently.
- Verify async tool execution returns immediate content when complete and a
  function-call reference when still running.

### Phase 5: Capability Split Contract

- Expose a stable Python service API for `capability_mcp_plugin` to call:
  provider registration helpers, tool invocation, catalog queries, and cache
  refresh/clear.
- Avoid GraphQL-to-GraphQL loops between the two plugins inside the same process;
  prefer direct service functions for in-process integration and GraphQL only at
  the gateway boundary.
- Remove capability fields from this plugin's native schema after Banyanos
  cutover is complete.

## Acceptance Criteria

- `mcp_protocol_plugin` installs and imports without `a2a-sdk` or Banyanos
  capability engine dependencies.
- `mcp_protocol_plugin` declares and imports its shared runtime dependency as
  `silvaengine_daemon`.
- Native MCP JSON-RPC and GraphQL catalog routes work through the gateway.
- Native MCP routes are registered through `silvaengine_daemon` internal plugin
  routing YAML and the MCP plugin module YAML.
- Outside traffic flows through `silvaengine_gateway` first, then
  `silvaengine_daemon`, then this plugin.
- Package upload, Base64, Git install/refresh/check, and external sync paths are
  covered by focused tests.
- Existing MCP catalog data remains readable with the same partition keys and
  table schemas.
- Capability compatibility concerns are absent or limited to documented service
  hooks consumed by `capability_mcp_plugin`.

## Risks

| Risk | Mitigation |
| --- | --- |
| Capability compatibility remains tangled in the native MCP schema. | Move compatibility files first and add an import-boundary test. |
| Dynamic package loading writes unsafe paths. | Keep existing safe-path validation and add regression tests. |
| Cache invalidation changes during split. | Centralize cache clear hooks through `silvaengine_daemon` and test config mutations. |
