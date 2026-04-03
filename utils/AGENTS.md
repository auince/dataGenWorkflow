# Utils - AGENTS.md

## Overview

Utility modules for API clients, state management, visualization, and image processing.

## Structure

```
utils/
├── minimax_client.py   # MiniMax LLM client (MiniMax-M2.7)
├── vlm_client.py       # Qwen3-VL-32B VLM client
├── checkpoint.py       # Pipeline state persistence
├── visualizer.py      # Mask and validation visualization
├── logger.py          # Logging utility
├── image.py           # Image loading/processing
└── rle.py             # COCO RLE encoding/decoding
```

## Where to Look

**minimax_client.py**
- `get_minimax_client()` returns singleton OpenAI client for MiniMax API
- `chat()` / `stream()` for completion requests
- API key from `OPENAI_API_KEY` env or `ApiDoc/minimax_apikey.txt`

**vlm_client.py**
- `get_vlm_client()` returns singleton for Qwen3-VL-32B at localhost:1285
- `call_vlm(image, prompt)` sends image+text, returns response
- Accepts file path, URL, base64, or bytes

**checkpoint.py**
- `save_checkpoint(path, state)` / `load_checkpoint(path)` for pipeline resumability
- `CheckpointState` for serializable checkpoint data
- File locking via `fcntl` for thread-safe writes

**visualizer.py**
- `visualize_segmentation_result()` creates original+mask overlay with prompt
- `visualize_validation_panel()` creates score breakdown panel
- `save_pipeline_outputs()` batch-saves to `/data/lch/SAM/dataGenAgent/output/visualizations/`

**logger.py**
- `get_logger(__name__)` returns configured INFO-level logger

## Conventions

```python
# Get singleton client
client = get_minimax_client()

# Log module activity
logger = get_logger(__name__)
logger.info("Starting process")

# Image as numpy uint8 (OpenCV convention)
mask = mask.astype(np.uint8)
```

## Anti-Patterns

- **Do not** instantiate clients directly — use `get_minimax_client()` / `get_vlm_client()`
- **Do not** hardcode API keys — read from env or `ApiDoc/minimax_apikey.txt`
- **Do not** pass boolean masks to OpenCV — convert to `np.uint8` first

## Notes

- MiniMax base URL: `https://api.minimaxi.com/v1`, model: `MiniMax-M2.7`
- VLM base URL: `http://localhost:1285/v1`, model: `Qwen/Qwen3-VL-32B-Instruct`, no API key required
- Visualizations output to `/data/lch/SAM/dataGenAgent/output/visualizations/`
