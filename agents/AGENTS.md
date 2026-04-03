# AGENTS.md - /data/lch/SAM/dataGenAgent/agents/

**Parent**: `/data/lch/SAM/dataGenAgent/AGENTS.md` — see parent for generic patterns (BaseAgent, BaseTool, state management, logging conventions).

## OVERVIEW

9 agent implementations:

| Agent | File | Purpose |
|-------|------|---------|
| IngestionAgent | ingestion.py | Load, dedupe, quality-check images |
| AnnotationAgent | annotation.py | SAM3 mask generation |
| PromptGenAgent | prompt_gen.py | Text prompt generation for VLM |
| RefinementAgent | refinement.py | Mask boundary refinement |
| ValidationAgent | validation.py | VLM-based quality evaluation |
| DistillationAgent | distillation.py | Package to training format |
| TextGenAgent | text_generation.py | LLM text description generation |
| QualityReviewAgent | quality_review.py | LLM quality review |
| DataOrchestrator | orchestrator.py | Multi-agent coordination |

## STRUCTURE

```
agents/
├── base.py              # BaseAgent abstract class
├── ingestion.py         # IngestionAgent + LoadImagesTool, DeduplicateImagesTool, QualityCheckTool
├── annotation.py        # AnnotationAgent (SAM3)
├── prompt_gen.py       # PromptGenAgent
├── refinement.py        # RefinementAgent
├── validation.py        # ValidationAgent (VLM)
├── distillation.py      # DistillationAgent
├── text_generation.py   # TextGenAgent
├── quality_review.py    # QualityReviewAgent
└── orchestrator.py     # DataOrchestrator
```

## WHERE TO LOOK

- **IngestionAgent**: `agents/ingestion.py` line 208 — image loading/dedupe logic
- **AnnotationAgent**: `agents/annotation.py` line 26 — SAM3 predictor setup
- **ValidationAgent**: `agents/validation.py` — VLM evaluation with 5-dimension scoring
- **QualityCheckTool**: `agents/ingestion.py` line 150 — image quality thresholds
- **Singleton getters**: `graph/nodes.py` lines 24-58 — `_get_*_agent()` pattern

## CONVENTIONS

**Agent initialization** (in nodes.py):
```python
_agent: AgentType | None = None

def _get_agent() -> AgentType:
    global _agent
    if _agent is None:
        _agent = AgentType(name="agent_name")
    return _agent
```

**Tool pattern**: Input schema (TypedDict subclass), Tool class with `name`, `description`, `_run()` method.

**Agent pattern**: Subclass `BaseAgent[T]`, implement `async process(state: T) -> T`, use `get_logger(f"agents.{name}")`.

## ANTI-PATTERNS

- **Do not** create agents inline in node functions — use singleton `_get_agent()`
- **Do not** skip the singleton pattern — graph nodes call agents repeatedly
- **Do not** use bare `except:` — catch specific exceptions

## NOTES

- Max 3 regeneration rounds per image with progressively relaxed thresholds (see `config/prompts.yaml` `regeneration_template`)
- QualityCheckTool thresholds: min_width=256, min_height=256, min_quality=30, brightness range 10-245, contrast min 10
- ValidationAgent scores: >=7.0 pass, 5.0-6.9 regenerate, <5.0 discard
