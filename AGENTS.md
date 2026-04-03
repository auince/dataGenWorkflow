# AGENTS.md - Guidelines for Agentic Coding in dataGenAgent

This file provides guidelines for AI agents operating in the `/data/lch/SAM/dataGenAgent` codebase.

## Environment

- **Conda Environment**: `langchain_lch`
- **Python Version**: 3.14
- **Working Directory**: `/data/lch/SAM/dataGenAgent`

## Build/Lint/Test Commands

### Running the Pipeline
```bash
# Basic pipeline run
conda run -n langchain_lch python main.py --input /path/to/images --output /path/to/output

# With max images and checkpoint
conda run -n langchain_lch python main.py --input /path --output /path --max-images 100 --checkpoint /path/checkpoint.json --verbose
```

### Testing
```bash
# Run all tests
cd /data/lch/SAM/dataGenAgent && conda run -n langchain_lch pytest

# Run single test file
conda run -n langchain_lch pytest test/test_ingestion.py -v

# Run single test
conda run -n langchain_lch pytest test/test_ingestion.py::TestIngestionAgent::test_ingestion_agent_initialization -v

# Integration test (uses mocks for SAM3)
conda run -n langchain_lch python test_integration.py
```

### Syntax/Import Checking
```bash
# Compile check all Python files
cd /data/lch/SAM/dataGenAgent && python -m py_compile $(find . -name "*.py")

# Verify module imports
conda run -n langchain_lch python -c "import sys; sys.path.insert(0, '.'); from graph.pipeline import create_workflow; app = create_workflow(); print('OK')"
```

## Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local
- Always use `sys.path.insert(0, str(Path(__file__).parent.parent))` for test imports
- Group imports with blank lines between groups
```python
import os
import sys
from pathlib import Path

import cv2
import numpy as np

from agents.base import BaseAgent
from utils.logger import get_logger
```

### Async/Await
- All pipeline node functions are `async def`
- Use `await` for async operations
- Use `asyncio.run()` when calling async from sync code (e.g., in `main.py`)

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `IngestionAgent`, `LoadImagesTool`)
- **Functions/Methods**: `snake_case` (e.g., `load_images`, `_get_ingestion_agent`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`)
- **Type Variables**: `PascalCase` (e.g., `T`, `TState`)
- **Private members**: prefix with `_` (e.g., `_ingestion_agent`)

### TypedDict for State Management
```python
class IngestionState(TypedDict):
    """State schema for the ingestion pipeline."""
    image_dir: str
    images: List[ImageMetadata]
    total_found: int
```

### Logging
- Use `get_logger(__name__)` for module loggers
- Log at INFO level for normal operations
- Include relevant state in log messages
```python
logger = get_logger(__name__)
logger.info(f"Ingestion complete: {state['total_images']} images ready")
```

### Error Handling
- Raise specific exceptions with clear messages
- Use `try/except` with specific exception types
- Never use bare `except:`
```python
if not dir_path.exists():
    raise ValueError(f"Directory not found: {directory}")
```

### Agent Pattern
All agents follow this pattern:
```python
class MyAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)
        self.logger = get_logger(f"agents.{name}")

    async def process(self, state: MyState) -> MyState:
        self.logger.info("Starting processing")
        # ... processing
        return state
```

### Tool Pattern
```python
class MyToolInput(BaseTool):
    param1: str
    param2: int

class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "Does something useful"

    def _run(self, param1: str, param2: int) -> str:
        # Implementation
        return result
```

### Graph Node Pattern
```python
# Use module-level singleton for agents
_my_agent: MyAgent | None = None

def _get_my_agent() -> MyAgent:
    global _my_agent
    if _my_agent is None:
        _my_agent = MyAgent(name="my_agent")
    return _my_agent

async def node_my_process(state: PipelineState) -> PipelineState:
    agent = _get_my_agent()
    result = await agent.process(state)
    # Update state
    return state
```

### LLM API Client Pattern
```python
# MiniMax LLM client
from utils.minimax_client import get_minimax_client
client = get_minimax_client()
response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[{"role": "user", "content": "prompt"}],
)

# Qwen3-VL-32B VLM client
from utils.vlm_client import call_vlm
response = call_vlm(image_path, "prompt")
```

### Visualization Pattern
```python
from utils.visualizer import visualize_segmentation_result, visualize_validation_panel

# Save segmentation visualization (original + masks + prompt)
visualize_segmentation_result(image_path, masks, prompt, output_path=out_path)

# Save validation panel
visualize_validation_panel(image_path, masks, val_result, output_path=out_path)
```

### Data Types for Images
- Use `np.uint8` for images (OpenCV convention)
- Convert boolean masks to `np.uint8` before OpenCV operations
```python
if mask.dtype == bool:
    mask = mask.astype(np.uint8)
```

## File Structure
```
dataGenAgent/
├── agents/           # Agent implementations
│   ├── base.py      # BaseAgent abstract class
│   ├── ingestion.py  # IngestionAgent
│   ├── annotation.py # AnnotationAgent (SAM3)
│   ├── validation.py # ValidationAgent (VLM-based)
│   ├── refinement.py # RefinementAgent
│   ├── distillation.py # DistillationAgent
│   ├── text_generation.py # TextGenAgent (MiniMax LLM)
│   └── quality_review.py # QualityReviewAgent (MiniMax LLM)
├── graph/           # LangGraph workflow
│   ├── state.py     # PipelineState TypedDict
│   ├── nodes.py     # Node functions
│   ├── edges.py     # Edge routing functions
│   └── pipeline.py  # create_workflow()
├── utils/           # Utilities
│   ├── minimax_client.py  # MiniMax API client
│   ├── vlm_client.py     # Qwen3-VL-32B VLM client
│   ├── visualizer.py      # Visualization utilities
│   ├── logger.py
│   ├── checkpoint.py
│   └── image.py
├── tools/           # LangChain tools
├── config/          # Configuration files
├── test/            # Unit tests
└── main.py          # CLI entry point
```

## Key Dependencies
- `langgraph>=1.0` - Workflow orchestration
- `langchain>=1.0` - Agent framework
- `ultralytics` - SAM3 model (installed in `langchain_lch` env)
- `opencv-python` - Image processing
- `pycocotools` - RLE encoding/decoding

## API Configuration

### MiniMax LLM
- Base URL: `https://api.minimaxi.com/v1`
- Model: `MiniMax-M2.7`
- API key: Set in `OPENAI_API_KEY` env or `ApiDoc/minimax_apikey.txt`

### Qwen3-VL-32B VLM
- Base URL: `http://localhost:1285/v1`
- Model: `Qwen/Qwen3-VL-32B-Instruct`
- No API key required (local deployment)

## Common Issues
- **Async nodes**: LangGraph requires async node functions - use `ainvoke` not `invoke` in `main.py`
- **Boolean masks**: OpenCV requires `uint8` for morphology operations
- **Module imports**: Always add `sys.path.insert(0, '/data/lch/SAM/dataGenAgent')` before imports in scripts
- **VLM response parsing**: MiniMax returns responses with `</think>` tags - strip them before JSON parsing
- **Output directory**: Always use `/data/lch/SAM/dataGenAgent/output/` for visualization output
