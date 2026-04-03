# graph/ — LangGraph Workflow Orchestration

## OVERVIEW

LangGraph StateGraph workflow coordinating multi-agent pipeline:
```
ingestion → next_image → prompt_generation → annotation → refinement → distillation
```

Validation is embedded in the pipeline flow but not explicitly wired as a separate node in the compiled graph (quality decisions happen inside agents).

## STRUCTURE

| File | Purpose |
|------|---------|
| `state.py` | `PipelineState` TypedDict — unified state schema for all nodes |
| `nodes.py` | Node functions: `node_*()` — one per pipeline stage |
| `edges.py` | Routing logic: `should_regenerate()`, `has_more_images()`, route_* functions |
| `pipeline.py` | `create_workflow()` — assembles StateGraph with nodes and edges |

## WHERE TO LOOK

### Node functions (nodes.py)

- `node_ingestion()` (line 143) — loads images, skips if pre-populated
- `node_next_image()` (line 356) — selects next unprocessed/undiscarded image
- `node_prompt_generation()` (line 212) — creates text prompts via VLM
- `node_annotation()` (line 182) — SAM3 mask generation
- `node_refinement()` (line 245) — improves mask boundaries
- `node_distillation()` (line 290) — packages approved annotations
- `node_discard()` (line 336) — handles failed images
- `node_increment_iteration()` (line 390) — bumps `iteration_round`

### Edge routing (edges.py)

- `should_regenerate()` (line 11) — pass/regenerate/discard based on `evaluation_result` + `iteration_round`
- `MAX_REGENERATION_ROUNDS = 3` (line 8) — regeneration cap
- `has_more_images()` (line 42) — checks for unprocessed images
- `route_after_*()` functions — direct flow to next_image or END

### Singleton pattern (nodes.py)

Each agent uses module-level singleton:
```python
_ingestion_agent: IngestionAgent | None = None
def _get_ingestion_agent() -> IngestionAgent:
    global _ingestion_agent
    if _ingestion_agent is None:
        _ingestion_agent = IngestionAgent(...)
    return _ingestion_agent
```

Agents: `_get_ingestion_agent()`, `_get_annotation_agent()`, `_get_promptgen_agent()`, `_get_refinement_agent()`, `_get_distillation_agent()`

### State converters (nodes.py)

`_convert_to_*_state()` functions bridge `PipelineState` to agent-specific state:
- `_convert_to_ingestion_state()` (line 61)
- `_convert_to_annotation_state()` (line 72)
- `_convert_to_prompt_gen_state()` (line 82)
- `_convert_to_refinement_state()` (line 90)
- `_convert_to_validation_state()` (line 101)
- `_convert_to_distillation_state()` (line 112)

## CONVENTIONS

- All node functions are `async def`
- Nodes call agent via singleton getter, then `await agent.process(state)`
- `PipelineState` is the single source of truth for pipeline-wide data
- `checkpoint` field updated after each node with step number and timestamp
- Edge functions receive `PipelineState` and return node name strings

## ANTI-PATTERNS

- **Do not call agents directly** — always use `_get_*_agent()` singleton
- **Do not skip singleton** — creates new agent instance on every call, loses state
- **Do not mutate state directly** in edge functions — read-only decision logic
- **Do not use `iteration_round` inconsistently** — tracked by `node_increment_iteration()`

## NOTES

- Validation happens inside `ValidationAgent.process()` — not a separate node
- `should_regenerate()` thresholds: pass (>=7), regenerate (5-6.9), discard (<5)
- Images that fail quality check in `node_prompt_generation()` skip to distillation with empty prompts
- `node_discard()` increments `failed_count` and appends to `discarded_samples`
