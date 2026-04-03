# dataGenAgent Comprehensive Refactoring Plan

## TL;DR

> **Objective**: Debug and refactor the multi-agent data generation pipeline until first batch successfully converts with multi-agent LLM-driven quality review.
>
> **Key Changes**:
> 1. Replace rule-based TextGenAgent with MiniMax LLM-powered prompt generation
> 2. Fix ValidationAgent to use local Qwen3-VL-32B (not Kimi API)
> 3. Fix state schema mismatches and distillation wiring
> 4. Add LLM-driven quality review agent
>
> **Deliverables**:
> - Working pipeline that converts images to pseudo-labels
> - Qwen3-VL-32B integration for VLM validation
> - MiniMax integration for intelligent text generation
> - Multi-agent quality review system
>
> **Estimated Effort**: Large (20+ discrete tasks)
> **Parallel Execution**: YES - multiple waves
> **Critical Path**: Fix ValidationAgent → Fix MiniMax client → Test pipeline

---

## Context

### Original Request
全面重构项目，持续debug直到成功转化第一批数据、同时经过多Agent审查确保数据质量合格为止. Each agent driven by LLM (MiniMax API), VLM uses local Qwen3-VL-32B.

### Project Purpose
Multi-agent pipeline for generating pseudo-labels (segmentation masks + text descriptions) from infrared/synthetic images:
1. **Ingestion** → Load images, deduplicate, quality filter
2. **Annotation** → SAM3 multi-scale segmentation
3. **Text Generation** → Generate prompts for segmentation descriptions
4. **Refinement** → Morphology, area filtering, RLE encoding
5. **Validation** → VLM-based quality evaluation (5 dimensions)
6. **Distillation** → Tar shard packaging + JSONL output
7. **Quality Review** → LLM-driven quality assessment

### Research Findings

**API Configuration**:
- **MiniMax** (LLM): Base URL `https://api.minimaxi.com/v1`, Key in `ApiDoc/minimax_apikey.txt`
- **Qwen3-VL-32B** (VLM): Base URL `http://localhost:1285/v1`, no auth needed

**Current Issues**:
| Severity | Issue |
|----------|-------|
| CRITICAL | ValidationAgent calls Kimi API (`api.moonshot.cn`) instead of Qwen3-VL-32B |
| CRITICAL | TextGenAgent is rule-based only - no MiniMax integration |
| HIGH | State schema mismatch: `ValidationState` defined differently in `agents/validation.py` vs `agents/orchestrator.py` |
| HIGH | `node_distillation` doesn't set `image_paths`/`output_dir` before calling DistillationAgent |
| MEDIUM | Duplicate ValidationAgent and DistillationAgent classes in `orchestrator.py` |
| MEDIUM | Missing `ultralytics`, `httpx`, `Pillow` in requirements.txt |
| LOW | Orphaned lock files in project root |

---

## Work Objectives

### Core Objective
Refactor dataGenAgent pipeline to use MiniMax LLM for text generation and Qwen3-VL-32B for validation, then debug until first batch successfully converts with multi-agent quality review.

### Concrete Deliverables
- [ ] MiniMax API client utility (`utils/minimax_client.py`)
- [ ] Qwen3-VL-32B API client utility (`utils/vlm_client.py`)
- [ ] Fixed ValidationAgent using Qwen3-VL-32B
- [ ] LLM-powered TextGenAgent using MiniMax
- [ ] Unified state schemas (remove duplicates)
- [ ] Fixed distillation wiring
- [ ] QualityReviewAgent using MiniMax for multi-agent review
- [ ] First batch of images successfully converted (tar shards + JSONL)
- [ ] Quality review reports for converted data

### Definition of Done
- [ ] `conda run -n langchain_lch python main.py --input /path/to/images --output /path/to/output` completes without error
- [ ] Output contains valid `shard_*.tar` files
- [ ] Output contains valid `annotations.jsonl` with mask data
- [ ] Multi-agent quality review passes on converted data

### Must Have
- MiniMax API integration for TextGenAgent
- Qwen3-VL-32B integration for ValidationAgent
- Working pipeline end-to-end
- Proper error handling

### Must NOT Have (Guardrails)
- No Kimi/Moonshot API calls (must use Qwen3-VL-32B)
- No hardcoded API keys (use environment variables)
- No duplicate agent definitions
- No state schema mismatches causing runtime errors

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest configured)
- **Automated tests**: Tests-after (debug first, add tests after verification)
- **Framework**: pytest

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/`.

**QA for this project**:
- Run actual pipeline with 5-10 test images
- Verify tar shards created
- Verify JSONL output valid
- Verify quality review runs and produces report

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - API clients + schema fixes):
├── Task 1: Create utils/minimax_client.py
├── Task 2: Create utils/vlm_client.py  
├── Task 3: Fix ValidationAgent to use Qwen3-VL-32B
├── Task 4: Add missing dependencies to requirements.txt
└── Task 5: Fix ValidationState schema (unify definitions)

Wave 2 (LLM Integration):
├── Task 6: Refactor TextGenAgent with MiniMax integration
├── Task 7: Create QualityReviewAgent using MiniMax
└── Task 8: Remove duplicate agents from orchestrator.py

Wave 3 (Wiring fixes):
├── Task 9: Fix distillation agent wiring (image_paths/output_dir)
├── Task 10: Fix node_distillation to populate required fields
└── Task 11: Add checkpoint integration to main.py

Wave 4 (Testing & Debugging):
├── Task 12: Run integration test with small image set
├── Task 13: Debug and fix any pipeline errors
└── Task 14: Verify tar shards + JSONL output

Wave 5 (Quality Review):
├── Task 15: Run quality review on converted batch
├── Task 16: Fix any quality issues identified
└── Task 17: Final verification of data quality
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 1 (minimax_client) | - | 6 |
| 2 (vlm_client) | - | 3, 7 |
| 3 (fix validation) | 2 | 12 |
| 4 (deps) | - | 12 |
| 5 (schema) | - | 12 |
| 6 (textgen w/ minimax) | 1 | 12 |
| 7 (quality review) | 1, 2 | 15, 16 |
| 8 (remove duplicates) | 5 | 12 |
| 9 (distillation wiring) | - | 12 |
| 10 (node_distillation) | 9 | 12 |
| 11 (checkpoint in main) | - | 12 |
| 12 (integration test) | 1-6, 8-11 | 13, 14 |
| 13 (debug) | 12 | 14 |
| 14 (verify output) | 13 | 15 |
| 15 (quality review) | 7, 14 | 16, 17 |
| 16 (fix quality issues) | 15 | 17 |
| 17 (final verification) | 16 | - |

### Agent Dispatch Summary

- **Wave 1**: 5 agents → `quick` tasks (utility creation, dependency fixes)
- **Wave 2**: 3 agents → `deep` (LLM integration, agent creation)
- **Wave 3**: 3 agents → `unspecified-high` (wiring fixes)
- **Wave 4**: 3 agents → `unspecified-high` (testing, debugging)
- **Wave 5**: 3 agents → `unspecified-high` (quality review)

---

## TODOs

- [ ] 1. **Create MiniMax API Client Utility**

  **What to do**:
  - Create `utils/minimax_client.py`
  - Implement `MiniMaxClient` class with OpenAI SDK
  - Support `reasoning_split=True` for thinking separation
  - Handle multi-turn conversations with tool calls
  - Set `OPENAI_BASE_URL` and `OPENAI_API_KEY` from env/config
  - Include proper error handling and retries

  **Must NOT do**:
  - No hardcoded API keys (read from env or config file)
  - No blocking synchronous calls in async context

  **Recommended Agent Profile**:
  - **Category**: `quick` - utility creation, well-defined pattern
  - **Skills**: None required - follows existing API doc pattern

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2)
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Task 6 (TextGenAgent refactor)

  **References**:
  - `ApiDoc/minimax_api_doc.txt` - API usage pattern
  - `config/settings.py` - Configuration pattern to follow
  - `utils/logger.py:6` - Logger pattern

  **Acceptance Criteria**:
  - [ ] File created: `utils/minimax_client.py`
  - [ ] `python -c "from utils.minimax_client import MiniMaxClient; print('OK')"` passes
  - [ ] Can make a test chat completion call

  **QA Scenarios**:

  Scenario: MiniMax client initialization and chat completion
    Tool: Bash
    Preconditions: Environment variables set
    Steps:
      1. `cd /data/lch/SAM/dataGenAgent && python -c "from utils.minimax_client import MiniMaxClient; client = MiniMaxClient(); print('Client created')"`
      2. `python -c "from utils.minimax_client import MiniMaxClient; client = MiniMaxClient(); response = client.chat('Hello'); print(response)"`
    Expected Result: Client initializes without error, chat returns response
    Failure Indicators: ImportError, APIError, timeout
    Evidence: .sisyphus/evidence/task-1-minimax-client.{ext}

  **Commit**: YES
  - Message: `feat(api): add MiniMax API client utility`
  - Files: `utils/minimax_client.py`

---

- [ ] 2. **Create Qwen3-VL-32B API Client Utility**

  **What to do**:
  - Create `utils/vlm_client.py`
  - Implement `VLMClient` class with OpenAI SDK
  - Support base64 image encoding
  - Support local file URLs (`file:///path`)
  - Set base_url to `http://localhost:1285/v1`, api_key to `"EMPTY"`

  **Must NOT do**:
  - No API key validation (local deployment accepts empty)
  - No timeout less than 60 seconds for large images

  **Recommended Agent Profile**:
  - **Category**: `quick` - utility creation, follows existing pattern
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 1)
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Task 3 (Validation fix), Task 7 (QualityReview)

  **References**:
  - `ApiDoc/vlm_api_doc` - API usage pattern
  - `agents/validation.py:208-277` - Existing VLM call pattern (needs fixing)
  - `test_integration.py:404-465` - VLM test pattern

  **Acceptance Criteria**:
  - [ ] File created: `utils/vlm_client.py`
  - [ ] `python -c "from utils.vlm_client import VLMClient; print('OK')"` passes
  - [ ] Can send image to Qwen3-VL-32B and get response

  **QA Scenarios**:

  Scenario: VLM client initialization with image
    Tool: Bash
    Preconditions: Qwen3-VL-32B server running on localhost:1285
    Steps:
      1. `cd /data/lch/SAM/dataGenAgent && python -c "from utils.vlm_client import VLMClient; client = VLMClient(); print('Client created')"`
      2. Test with synthetic image: create 10x10 white image, send for description
    Expected Result: Client initializes, returns text description of image
    Failure Indicators: ConnectionError, timeout, invalid response
    Evidence: .sisyphus/evidence/task-2-vlm-client.{ext}

  **Commit**: YES
  - Message: `feat(api): add Qwen3-VL-32B client utility`
  - Files: `utils/vlm_client.py`

---

- [ ] 3. **Fix ValidationAgent to Use Qwen3-VL-32B**

  **What to do**:
  - Modify `agents/validation.py`
  - Replace `_call_kimi_vlm` method with `_call_qwen_vlm`
  - Use `VLMClient` from `utils/vlm_client.py`
  - Keep the same 5-dimension evaluation logic
  - Keep heuristic fallback when VLM unavailable
  - Remove Kimi API imports and references

  **Must NOT do**:
  - No changes to evaluation dimensions or weights
  - No changes to scoring thresholds
  - Don't break the heuristic fallback

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - modifying existing complex agent
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Task 2)
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 12 (integration test)

  **References**:
  - `agents/validation.py:208-277` - Current Kimi implementation to replace
  - `utils/vlm_client.py` - New VLM client to use (Task 2)
  - `config/settings.py:2-3` - VLM config already defined

  **Acceptance Criteria**:
  - [ ] `grep -n "moonshot\|kimi" agents/validation.py` returns no results
  - [ ] VLM calls use `VLMClient` with Qwen3-VL-32B endpoint
  - [ ] Heuristic fallback still works when VLM unavailable

  **QA Scenarios**:

  Scenario: ValidationAgent calls Qwen3-VL-32B instead of Kimi
    Tool: Bash
    Preconditions: Qwen3-VL-32B running, test images available
    Steps:
      1. `cd /data/lch/SAM/dataGenAgent && python -c "from agents.validation import ValidationAgent; agent = ValidationAgent(); print('Agent created')"`
      2. Check logs to verify Qwen endpoint is called (not Kimi)
    Expected Result: Agent uses Qwen3-VL-32B endpoint
    Failure Indicators: Still calling api.moonshot.cn
    Evidence: .sisyphus/evidence/task-3-validation-fix.{ext}

  Scenario: ValidationAgent falls back to heuristic when VLM down
    Tool: Bash
    Preconditions: VLM server stopped
    Steps:
      1. Stop VLM server: `pkill -f "Qwen3-VL-32B"`
      2. Run validation with sample image
      3. Verify heuristic fallback is used
    Expected Result: Validation completes using heuristic, no crash
    Failure Indicators: Exception when VLM unavailable
    Evidence: .sisyphus/evidence/task-3-validation-fallback.{ext}

  **Commit**: YES
  - Message: `fix(validation): use Qwen3-VL-32B instead of Kimi API`
  - Files: `agents/validation.py`

---

- [ ] 4. **Add Missing Dependencies to requirements.txt**

  **What to do**:
  - Read current `requirements.txt`
  - Add missing dependencies: `ultralytics`, `httpx`, `Pillow`
  - Verify all existing dependencies are correct
  - Add version constraints if needed

  **Must NOT do**:
  - No version changes to existing working dependencies
  - No removal of existing dependencies

  **Recommended Agent Profile**:
  - **Category**: `quick` - simple file edit
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 12

  **References**:
  - `AGENTS.md` - Lists dependencies (ultralytics, httpx mentioned)
  - Current `requirements.txt` - To be read and modified

  **Acceptance Criteria**:
  - [ ] `ultralytics` present in requirements.txt
  - [ ] `httpx` present in requirements.txt
  - [ ] `Pillow` or `PIL` present in requirements.txt

  **QA Scenarios**:

  Scenario: Verify all dependencies installable
    Tool: Bash
    Preconditions: requirements.txt updated
    Steps:
      1. `cd /data/lch/SAM/dataGenAgent && pip install -r requirements.txt --dry-run 2>&1 | head -20`
    Expected Result: No missing package errors
    Failure Indicators: Package not found
    Evidence: .sisyphus/evidence/task-4-deps.{ext}

  **Commit**: YES
  - Message: `chore(deps): add missing dependencies (ultralytics, httpx, Pillow)`
  - Files: `requirements.txt`

---

- [ ] 5. **Fix ValidationState Schema (Unify Definitions)**

  **What to do**:
  - Analyze current ValidationState definitions in `agents/validation.py` and `agents/orchestrator.py`
  - Choose one canonical schema
  - Update all references to use the chosen schema
  - Remove duplicate definitions from orchestrator.py (Task 8)

  Schema choice (from `agents/validation.py` - more complete):
  ```python
  class ValidationState(TypedDict):
      current_image: str
      masks: List[np.ndarray]
      annotations: dict
      quality_score: Optional[float]
      evaluation_result: str  # "pass", "regenerate", "discard"
      evaluation_details: Dict[str, Any]
  ```

  **Must NOT do**:
  - No changes to PipelineState TypedDict
  - No breaking changes to other agents' state schemas

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - schema refactoring, must be precise
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 8

  **References**:
  - `agents/validation.py:80-88` - ValidationState to keep
  - `agents/orchestrator.py:18-25` - ValidationState to consolidate
  - `graph/nodes.py:98-106` - _convert_to_validation_state function

  **Acceptance Criteria**:
  - [ ] Only ONE ValidationState definition exists in codebase
  - [ ] All references use the same ValidationState schema
  - [ ] No attribute errors when ValidationAgent processes state

  **QA Scenarios**:

  Scenario: Verify single ValidationState definition
    Tool: Bash
    Preconditions: Schema fixed
    Steps:
      1. `grep -rn "class ValidationState" /data/lch/SAM/dataGenAgent/`
      2. Count occurrences - should be exactly 1
    Expected Result: Only one ValidationState class definition
    Failure Indicators: Multiple definitions found
    Evidence: .sisyphus/evidence/task-5-schema.{ext}

  **Commit**: YES (later grouped with Task 8)
  - Message: `refactor(state): unify ValidationState schema`
  - Files: `agents/validation.py`, `agents/orchestrator.py`

---

- [ ] 6. **Refactor TextGenAgent with MiniMax Integration**

  **What to do**:
  - Modify `agents/text_generation.py`
  - Add `MiniMaxClient` for intelligent prompt generation
  - Keep vocabulary-based fallback if MiniMax unavailable
  - Use MiniMax to generate contextually appropriate prompts based on image analysis
  - Generate 3-5 prompts per image

  Prompt generation approach:
  1. Analyze image with MiniMax (describe what's in image)
  2. Use description to generate relevant prompts using vocabulary

  **Must NOT do**:
  - No breaking of existing vocabulary-based prompt generation (keep as fallback)
  - No hardcoded prompts

  **Recommended Agent Profile**:
  - **Category**: `deep` - LLM integration, requires careful prompt engineering
  - **Skills**: None required but should understand the existing vocabulary system

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Task 1)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12

  **References**:
  - `agents/text_generation.py` - Current implementation to enhance
  - `utils/minimax_client.py` - MiniMax client (Task 1)
  - `config/vocabulary.yaml` - Existing vocabulary structure

  **Acceptance Criteria**:
  - [ ] TextGenAgent uses MiniMax for prompt generation when available
  - [ ] Falls back to rule-based generation when MiniMax unavailable
  - [ ] Generates 3-5 prompts per image

  **QA Scenarios**:

  Scenario: TextGenAgent uses MiniMax for prompt generation
    Tool: Bash
    Preconditions: MiniMax accessible
    Steps:
      1. Create test state with current_image set
      2. Run TextGenAgent.process()
      3. Check generated_prompts are contextually relevant
    Expected Result: Prompts generated using MiniMax LLM
    Failure Indicators: Rule-based prompts only, no LLM calls
    Evidence: .sisyphus/evidence/task-6-textgen.{ext}

  **Commit**: YES
  - Message: `feat(textgen): integrate MiniMax LLM for prompt generation`
  - Files: `agents/text_generation.py`

---

- [ ] 7. **Create QualityReviewAgent using MiniMax**

  **What to do**:
  - Create new `agents/quality_review.py`
  - Design agent to review quality of converted data
  - Use MiniMax to evaluate:
    - Mask completeness and accuracy
    - Text-mask alignment
    - Overall annotation quality
  - Generate quality report with pass/fail and suggestions

  **Must NOT do**:
  - No VLM calls (use MiniMax only for review)
  - No changes to existing pipeline flow

  **Recommended Agent Profile**:
  - **Category**: `deep` - new agent creation with LLM integration
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Task 1, 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 15

  **References**:
  - `agents/validation.py` - Quality evaluation pattern to follow
  - `utils/minimax_client.py` - MiniMax client (Task 1)
  - `config/prompts.yaml` - Existing prompt templates

  **Acceptance Criteria**:
  - [ ] File created: `agents/quality_review.py`
  - [ ] QualityReviewAgent class with process() method
  - [ ] Generates quality report with scores and suggestions

  **QA Scenarios**:

  Scenario: QualityReviewAgent generates quality report
    Tool: Bash
    Preconditions: Sample annotations available
    Steps:
      1. Create mock state with sample annotations
      2. Run QualityReviewAgent.process()
      3. Check quality_report in returned state
    Expected Result: Quality report with pass/fail and suggestions
    Failure Indicators: No report generated, errors
    Evidence: .sisyphus/evidence/task-7-quality-review.{ext}

  **Commit**: YES
  - Message: `feat(quality): add QualityReviewAgent using MiniMax`
  - Files: `agents/quality_review.py`

---

- [ ] 8. **Remove Duplicate Agents from orchestrator.py**

  **What to do**:
  - Remove duplicate ValidationAgent and DistillationAgent classes from `agents/orchestrator.py`
  - These are duplicates of the ones in `agents/validation.py` and `agents/distillation.py`
  - Keep only the DataOrchestrator class (for backward compatibility)
  - Or mark orchestrator.py as deprecated if not needed

  **Must NOT do**:
  - No changes to agents/validation.py or agents/distillation.py
  - No breaking of any code that imports from orchestrator.py

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - removing code, must ensure no breakage
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Task 5)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 12

  **References**:
  - `agents/orchestrator.py:35-99` - Duplicate ValidationAgent
  - `agents/orchestrator.py:102-157` - Duplicate DistillationAgent
  - `agents/validation.py` - Canonical ValidationAgent
  - `agents/distillation.py` - Canonical DistillationAgent

  **Acceptance Criteria**:
  - [ ] No duplicate ValidationAgent class in codebase
  - [ ] No duplicate DistillationAgent class in codebase
  - [ ] test_integration.py still imports successfully

  **QA Scenarios**:

  Scenario: Verify no duplicate agent classes
    Tool: Bash
    Preconditions: Duplicates removed
    Steps:
      1. `grep -n "class ValidationAgent" /data/lch/SAM/dataGenAgent/agents/*.py`
      2. `grep -n "class DistillationAgent" /data/lch/SAM/dataGenAgent/agents/*.py`
    Expected Result: Only one definition each (in validation.py and distillation.py)
    Failure Indicators: Multiple definitions
    Evidence: .sisyphus/evidence/task-8-dedup.{ext}

  **Commit**: YES
  - Message: `refactor(orchestrator): remove duplicate agent classes`
  - Files: `agents/orchestrator.py`

---

- [ ] 9. **Fix Distillation Agent Wiring**

  **What to do**:
  - Analyze how distillation is called in the pipeline
  - Fix node_distillation to populate `image_paths` and `output_dir` in state
  - Verify DistillationAgent.process() receives required fields

  **Must NOT do**:
  - No changes to DistillationAgent.process() signature
  - No changes to output format

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - debugging pipeline wiring
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 12

  **References**:
  - `agents/distillation.py:91-117` - process() method expecting image_paths, output_dir
  - `graph/nodes.py:230-262` - node_distillation implementation

  **Acceptance Criteria**:
  - [ ] DistillationAgent receives image_paths in state
  - [ ] DistillationAgent receives output_dir in state
  - [ ] No KeyError when distillation runs

  **QA Scenarios**:

  Scenario: Distillation receives required fields
    Tool: Bash
    Preconditions: Wiring fixed
    Steps:
      1. Run pipeline with 3 test images
      2. Check logs for distillation success
    Expected Result: Distillation completes without KeyError
    Failure Indicators: KeyError for image_paths or output_dir
    Evidence: .sisyphus/evidence/task-9-wiring.{ext}

  **Commit**: YES
  - Message: `fix(distillation): populate required fields before calling agent`
  - Files: `graph/nodes.py`

---

- [ ] 10. **Fix node_distillation to Populate Required Fields**

  **What to do**:
  - Modify `graph/nodes.py` node_distillation function
  - Extract image paths from completed_annotations
  - Set output_dir from pipeline output path
  - Use checkpoint mechanism to track progress

  **Must NOT do**:
  - No changes to state schema
  - No breaking of other nodes

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - node function fix
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 9 - same issue)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 12

  **References**:
  - `graph/nodes.py:230-262` - Current implementation to fix
  - `graph/pipeline.py:46-126` - Pipeline context

  **Acceptance Criteria**:
  - [ ] node_distillation sets image_paths from completed_annotations
  - [ ] node_distillation sets output_dir correctly
  - [ ] Tar shards and JSONL created in correct location

  **QA Scenarios**:

  Scenario: Verify output structure
    Tool: Bash
    Preconditions: Pipeline run completed
    Steps:
      1. Check output directory for shard_*.tar files
      2. Check for annotations.jsonl
    Expected Result: Proper output structure
    Failure Indicators: Missing files, wrong locations
    Evidence: .sisyphus/evidence/task-10-node-dist.{ext}

  **Commit**: YES (grouped with Task 9)
  - Message: `fix(nodes): populate distillation fields correctly`
  - Files: `graph/nodes.py`

---

- [ ] 11. **Add Checkpoint Integration to main.py**

  **What to do**:
  - Modify `main.py` to use checkpoint save/load during pipeline execution
  - Save checkpoint after each image processed
  - Load checkpoint on startup if exists
  - Add --checkpoint CLI argument handling

  **Must NOT do**:
  - No changes to checkpoint.py utility
  - No breaking of existing checkpoint functionality

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - main.py modification
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 12

  **References**:
  - `main.py:226-248` - Existing checkpoint save code
  - `utils/checkpoint.py` - Checkpoint utilities
  - `AGENTS.md` - Usage examples with --checkpoint

  **Acceptance Criteria**:
  - [ ] Pipeline saves checkpoint after each image
  - [ ] Pipeline resumes from checkpoint on restart
  - [ ] --checkpoint argument works as documented

  **QA Scenarios**:

  Scenario: Checkpoint save/load works
    Tool: Bash
    Preconditions: Pipeline run started
    Steps:
      1. Run pipeline with --checkpoint test.json
      2. Interrupt with Ctrl+C
      3. Run again with same --checkpoint
      4. Verify resume from last position
    Expected Result: Pipeline resumes, doesn't reprocess images
    Failure Indicators: Reprocesses images, checkpoint ignored
    Evidence: .sisyphus/evidence/task-11-checkpoint.{ext}

  **Commit**: YES
  - Message: `feat(checkpoint): integrate checkpoint save/load in main pipeline`
  - Files: `main.py`

---

- [ ] 12. **Run Integration Test with Small Image Set**

  **What to do**:
  - Create test directory with 5-10 sample images
  - Run pipeline: `python main.py --input test_images --output test_output --max-images 10`
  - Verify pipeline completes without error
  - Check output files created

  **Must NOT do**:
  - No modifications to pipeline during test (fix issues in Task 13)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - testing full pipeline
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO (depends on all previous)
  - **Parallel Group**: Wave 4 (sequential)
  - **Blocks**: Task 13

  **References**:
  - `test_integration.py` - Existing integration test patterns
  - `datasets/训练集/训练集/data4/` - Sample images available

  **Acceptance Criteria**:
  - [ ] Pipeline completes without exception
  - [ ] Output directory has tar shards
  - [ ] Output directory has annotations.jsonl
  - [ ] At least 1 image successfully processed

  **QA Scenarios**:

  Scenario: Full pipeline run on 5 test images
    Tool: Bash
    Preconditions: Test images in place
    Steps:
      1. `mkdir -p /tmp/test_images /tmp/test_output`
      2. Copy 5 images to test_images
      3. Run: `cd /data/lch/SAM/dataGenAgent && conda run -n langchain_lch python main.py --input /tmp/test_images --output /tmp/test_output --max-images 5`
      4. Check /tmp/test_output for results
    Expected Result: Pipeline completes, output exists
    Failure Indicators: Exception, no output files
    Evidence: .sisyphus/evidence/task-12-integration.{ext}

  **Commit**: NO
  - Message: -
  - Files: -

---

- [ ] 13. **Debug and Fix Pipeline Errors**

  **What to do**:
  - Analyze any errors from Task 12
  - Fix issues one by one
  - Re-run pipeline until Task 12 acceptance criteria met
  - Document each fix

  **Must NOT do**:
  - No major refactoring during debug (postpone to later)
  - No ignoring errors

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - debugging, may need systematic approach
  - **Skills**: `systematic-debugging` - use when bug fixing

  **Parallelization**:
  - **Can Run In Parallel**: NO (sequential debug)
  - **Parallel Group**: Wave 4 (sequential after Task 12)
  - **Blocks**: Task 14

  **References**:
  - Error output from Task 12
  - `utils/logger.py` - Logging configuration
  - `graph/pipeline.py` - Pipeline structure

  **Acceptance Criteria**:
  - [ ] All critical errors fixed
  - [ ] Pipeline runs to completion
  - [ ] Task 12 acceptance criteria met

  **QA Scenarios**:

  Scenario: Debug iteration
    Tool: Bash
    Preconditions: Error in Task 12
    Steps:
      1. Identify error from output
      2. Fix issue
      3. Re-run pipeline
      4. Repeat until success
    Expected Result: Pipeline completes successfully
    Failure Indicators: Same error persists
    Evidence: .sisyphus/evidence/task-13-debug-N.{ext} (N=iteration)

  **Commit**: YES (per fix)
  - Message: `fix(<component>): <issue description>`
  - Files: <fixed files>

---

- [ ] 14. **Verify Tar Shards + JSONL Output**

  **What to do**:
  - Verify tar shard structure
  - Verify JSONL format and content
  - Validate annotations have required fields
  - Check mask RLE encoding

  **Must NOT do**:
  - No modifications to output (verify only)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - verification
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO (after Task 13)
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 15

  **References**:
  - `agents/distillation.py` - Output format
  - `utils/rle.py` - RLE encoding
  - COCO format specification for expected fields

  **Acceptance Criteria**:
  - [ ] shard_*.tar files are valid tar archives
  - [ ] annotations.jsonl has one JSON object per line
  - [ ] Each record has image_path, annotations, quality_score
  - [ ] Mask RLE decodes correctly

  **QA Scenarios**:

  Scenario: Verify output structure and format
    Tool: Bash
    Preconditions: Task 12/13 complete
    Steps:
      1. List output directory: `ls -la /tmp/test_output/`
      2. Check tar contents: `tar -tf /tmp/test_output/shard_0000.tar | head`
      3. Validate JSONL: `python -c "import json; [json.loads(l) for l in open('/tmp/test_output/annotations.jsonl')]"`
    Expected Result: Valid tar and JSONL
    Failure Indicators: Corrupt files, invalid JSON
    Evidence: .sisyphus/evidence/task-14-output.{ext}

  **Commit**: NO
  - Message: -
  - Files: -

---

- [ ] 15. **Run Quality Review on Converted Batch**

  **What to do**:
  - Use QualityReviewAgent to evaluate converted data
  - Run review on all converted images
  - Generate quality report with pass/fail per image
  - Aggregate quality metrics

  **Must NOT do**:
  - No modifications to data during review

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - quality review
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO (after Task 14)
  - **Parallel Group**: Wave 5
  - **Blocks**: Task 16

  **References**:
  - `agents/quality_review.py` - QualityReviewAgent (Task 7)
  - Output from Task 14

  **Acceptance Criteria**:
  - [ ] Quality review runs on all converted images
  - [ ] Report generated with per-image scores
  - [ ] Overall batch quality score calculated

  **QA Scenarios**:

  Scenario: Quality review execution
    Tool: Bash
    Preconditions: Converted batch in Task 14 output
    Steps:
      1. Run quality review script on /tmp/test_output
      2. Check quality_report.json generated
    Expected Result: Quality report exists
    Failure Indicators: Review fails, no report
    Evidence: .sisyphus/evidence/task-15-review.{ext}

  **Commit**: NO
  - Message: -
  - Files: -

---

- [ ] 16. **Fix Quality Issues Identified by Review**

  **What to do**:
  - Analyze quality report from Task 15
  - Identify common issues in failed/poor quality images
  - Fix pipeline components to address issues
  - Re-run quality review on fixed batch

  **Must NOT do**:
  - No over-engineering solutions
  - No ignoring systemic issues

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - fixing quality issues
  - **Skills**: `systematic-debugging` if issues are bugs

  **Parallelization**:
  - **Can Run In Parallel**: NO (after Task 15)
  - **Parallel Group**: Wave 5
  - **Blocks**: Task 17

  **References**:
  - Quality report from Task 15
  - Issues in annotations, refinement, or validation

  **Acceptance Criteria**:
  - [ ] Major quality issues addressed
  - [ ] Re-review shows improvement
  - [ ] Failed images reviewed and categorized

  **QA Scenarios**:

  Scenario: Fix and re-review quality
    Tool: Bash
    Preconditions: Quality issues identified
    Steps:
      1. Fix identified issues
      2. Re-run quality review
      3. Compare scores before/after
    Expected Result: Improved quality scores
    Failure Indicators: Same or worse scores
    Evidence: .sisyphus/evidence/task-16-fix-quality.{ext}

  **Commit**: YES
  - Message: `fix(quality): address issues identified in review`
  - Files: <fixed files>

---

- [ ] 17. **Final Verification of Data Quality**

  **What to do**:
  - Final quality review pass
  - Verify batch meets quality threshold
  - Document final batch statistics
  - Confirm first batch conversion complete

  **Must NOT do**:
  - No further modifications after this

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high` - final verification
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO (final step)
  - **Parallel Group**: Wave 5
  - **Blocks**: None (final)

  **References**:
  - Quality report from Task 16
  - Original requirements

  **Acceptance Criteria**:
  - [ ] Batch quality meets threshold (e.g., 80% pass rate)
  - [ ] All converted images documented
  - [ ] First batch conversion declared complete

  **QA Scenarios**:

  Scenario: Final quality verification
    Tool: Bash
    Preconditions: All fixes complete
    Steps:
      1. Final quality review
      2. Generate summary report
      3. Confirm completion
    Expected Result: Quality threshold met
    Failure Indicators: Quality below threshold
    Evidence: .sisyphus/evidence/task-17-final.{ext}

  **Commit**: YES
  - Message: `chore: first batch conversion complete`
  - Files: Quality report

---

## Final Verification Wave

- [ ] F1. **Pipeline Compliance Audit** — `oracle`
  Verify all pipeline components use correct APIs:
  - MiniMax for TextGenAgent
  - Qwen3-VL-32B for ValidationAgent
  - No Kimi/Moonshot API calls
  Output: `API Usage [PASS/FAIL] | Components [N/N correct] | VERDICT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `python -m py_compile` on all modified files, check for:
  - Syntax errors
  - Import errors
  - Type errors
  Output: `Syntax [PASS/FAIL] | Imports [PASS/FAIL] | VERDICT`

- [ ] F3. **Integration Test** — `unspecified-high`
  Run full pipeline on test images:
  - 5-10 test images through complete pipeline
  - Verify tar shards created
  - Verify JSONL valid
  Output: `Pipeline [PASS/FAIL] | Output [N/N valid] | VERDICT`

- [ ] F4. **Quality Review Verification** — `unspecified-high`
  Verify quality review works:
  - QualityReviewAgent generates report
  - Report has required fields
  Output: `Quality Review [PASS/FAIL] | Report Valid [YES/NO] | VERDICT`

---

## Commit Strategy

- **Per Task**: Commit after each task that modifies files
- **Message Format**: `type(scope): description`
  - `feat(api)`: New API client utilities
  - `fix(validation)`: ValidationAgent fixes
  - `feat(textgen)`: TextGenAgent enhancements
  - `refactor(state)`: Schema unification
  - `chore(deps)`: Dependency updates
  - `fix(<component>)`: Bug fixes

---

## Success Criteria

### Verification Commands
```bash
# Test MiniMax client
cd /data/lch/SAM/dataGenAgent && python -c "from utils.minimax_client import MiniMaxClient; print('MiniMax OK')"

# Test VLM client  
cd /data/lch/SAM/dataGenAgent && python -c "from utils.vlm_client import VLMClient; print('VLM OK')"

# Verify no Kimi calls
grep -r "moonshot\|kimi" /data/lch/SAM/dataGenAgent/agents/ || echo "No Kimi references"

# Run pipeline
cd /data/lch/SAM/dataGenAgent && conda run -n langchain_lch python main.py --input /path/to/images --output /path/to/output

# Verify output
ls -la /path/to/output/shard_*.tar
head -1 /path/to/output/annotations.jsonl | python -m json.tool
```

### Final Checklist
- [ ] All "Must Have" items present
- [ ] All "Must NOT Have" items absent
- [ ] MiniMax integrated for text generation
- [ ] Qwen3-VL-32B integrated for validation
- [ ] Pipeline runs end-to-end
- [ ] Tar shards + JSONL output created
- [ ] Quality review generates report
- [ ] First batch successfully converted