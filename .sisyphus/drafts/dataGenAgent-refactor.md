# Draft: dataGenAgent Comprehensive Refactoring Plan

## Project Overview

**dataGenAgent** is a multi-agent data generation pipeline for computer vision that:
1. Ingests images (load, deduplicate, quality check)
2. Annotates them using SAM3 (Segment Anything Model 3)
3. Refines the masks (morphology, area filtering)
4. Validates using VLM (quality assessment)
5. Distills results into tar shards + JSONL output

## User Requirements

1. **LLM Agents**: Use MiniMax API (minimax-cn-coding-plan/MiniMax-M2.7-highspeed)
2. **VLM Agent**: Use locally deployed Qwen3-VL-32B at localhost:1285
3. **Goal**: Debug until successful data conversion for first batch + multi-agent review for quality
4. **API Docs**: `/data/lch/SAM/dataGenAgent/ApiDoc/`

## API Configuration

### MiniMax API (LLM tasks)
- Base URL: `https://api.minimaxi.com/v1`
- API Key: `sk-cp-QEDYNmZwYBXSaQApoH2q6xo4rR6oXBhO5M1MG6fEhads9VgGQk1X3nI4f1qAwp8F18KGdeY-tBxFlqekywYgk0-Q10Axq3vRuDCY8Gqr0fa0VRAGULvsTmA`
- Model: `MiniMax-M2.7` or `MiniMax-M2.7-highspeed`
- Special param: `reasoning_split=True` for thinking separation

### Qwen3-VL-32B (VLM tasks)
- Base URL: `http://localhost:1285/v1`
- Model: `Qwen/Qwen3-VL-32B-Instruct`
- API Key: `EMPTY` (no auth for local deployment)

## Issues Identified

### Critical Issues

1. **ValidationAgent uses wrong API** - `agents/validation.py` calls Kimi API (`api.moonshot.cn`) instead of Qwen3-VL-32B
2. **MiniMax not integrated** - TextGenAgent is rule-based only, doesn't use MiniMax LLM
3. **Duplicate agent definitions** - `orchestrator.py` has its own ValidationAgent and DistillationAgent that differ from `agents/validation.py` and `agents/distillation.py`
4. **LangGraph pipeline incomplete** - `graph/nodes.py` references agents that may not be properly integrated

### Minor Issues

1. **Checkpointer not integrated in main.py** - Checkpointing exists but isn't called during pipeline execution
2. **No proper error handling** - Pipeline may fail silently on errors
3. **State type mismatches** - Various TypedDict schemas may not match

## Scope of Work

### INCLUDE:
- Fix ValidationAgent to use Qwen3-VL-32B (localhost:1285)
- Integrate MiniMax API into TextGenAgent for intelligent prompt generation
- Remove duplicate agents from orchestrator.py (use agents/ module versions)
- Add proper MiniMax API client configuration
- Debug and fix pipeline until first successful data conversion
- Add multi-agent quality review using LLM

### EXCLUDE:
- SAM3 model changes (model path already correct)
- Changes to refinement logic (working correctly)
- Changes to ingestion logic (working correctly)

## Technical Decisions

1. **MiniMax Client**: Use OpenAI SDK with MiniMax base URL
2. **VLM Client**: Use OpenAI SDK with Qwen3-VL-32B endpoint
3. **Agent Architecture**: Use LangGraph workflow (graph/pipeline.py) as primary
4. **Orchestrator**: Consider removing duplicate agents, using only graph-based workflow

## Research Findings

### MiniMax API Pattern
```python
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[...],
    extra_body={"reasoning_split": True}
)
```

### Qwen3-VL-32B Pattern
```python
from openai import OpenAI
client = OpenAI(api_key="EMPTY", base_url="http://localhost:1285/v1")
response = client.chat.completions.create(
    model="Qwen/Qwen3-VL-32B-Instruct",
    messages=[{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": "file:///path/to/image.jpg"}},
        {"type": "text", "text": "Describe this image"}
    ]}],
    max_tokens=512
)
```

## Open Questions

1. Should we keep the orchestrator.py-based pipeline or only use LangGraph pipeline?
2. What specific quality criteria should the multi-agent review check?
3. How many images should constitute "first batch" for successful conversion?
4. Should we use TDD approach or fix-and-run approach for debugging?

## Test Strategy

- Infrastructure: pytest already configured
- Decision: Tests-after (debug first, then add tests once working)
- Agent-Executed QA: Run actual pipeline on small image set to verify