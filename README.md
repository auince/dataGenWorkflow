# Multi-Agent Data Generation Pipeline

A LangChain/LangGraph-based multi-agent system for infrared image pseudo-label generation with VLM evaluation.

## Architecture

The pipeline uses 7 specialized agents coordinated through a LangGraph StateGraph:

| Agent | Purpose |
|-------|---------|
| **Ingestion** | Load and validate input images, remove duplicates and low-quality images |
| **Annotation** | Generate initial segmentation masks using SAM3 |
| **Text Generation** | Create text descriptions for segmented objects |
| **Refinement** | Improve mask quality and boundary accuracy |
| **Validation** | Evaluate masks using VLM (Qwen3-VL-32B-Instruct) across 5 dimensions |
| **Distillation** | Package approved annotations into training-ready format |
| **Discard** | Handle low-quality samples that fail validation |

### Pipeline Flow

```
START -> ingestion -> next_image -> annotation -> text_generation
                                         -> refinement -> validation
                                         -> (routing)
                                             pass -> distillation -> next_image
                                             regenerate -> increment_iteration -> annotation
                                             discard -> discard -> next_image
```

The pipeline supports up to 3 regeneration attempts per image with progressively relaxed thresholds.

## Requirements

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py --input /path/to/images --output /path/to/output
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--input DIR` | Input directory containing images to process (required) |
| `--output DIR` | Output directory for generated pseudo-labels (required) |
| `--max-images N` | Maximum number of images to process (default: all) |
| `--checkpoint PATH` | Resume from checkpoint file |
| `--verbose, -v` | Enable verbose logging |

### Examples

```bash
# Process all images in directory
python main.py --input ./images --output ./output

# Limit to 100 images
python main.py --input ./images --output ./output --max-images 100

# Resume from checkpoint
python main.py --input ./images --output ./output --checkpoint checkpoint.json

# Enable verbose logging
python main.py --input ./images --output ./output --verbose
```

## Output Format

The pipeline produces two types of outputs:

1. **JSONL metadata** (`annotations.jsonl`): One JSON record per line containing:
   - Image path
   - Segmentation masks (polygon coordinates or RLE)
   - Text descriptions
   - Quality scores
   - VLM evaluation details

2. **Tar shards** (`shard_0000.tar`, etc.): Archived image-mask pairs for training

### Directory Structure

```
output/
├── annotations.jsonl    # Metadata for all annotations
├── shard_0000.tar      # Training data shards
├── shard_0001.tar
└── metrics.json        # Pipeline statistics
```

## VLM Evaluation

The validation agent evaluates masks across 5 dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Mask Completeness | 25% | Are all objects fully segmented? |
| Boundary Accuracy | 20% | Are boundaries crisp and accurate? |
| Text-Mask Alignment | 20% | Does mask match the text description? |
| False Positive Detection | 15% | Are there spurious mask regions? |
| Small Target Detection | 20% | Are small targets properly captured? |

Decision thresholds:
- Score >= 7.0: **pass** (use masks)
- Score 5.0-6.9: **regenerate** (retry with adjusted parameters)
- Score < 5.0: **discard** (quality too poor)

## Checkpoint and Resume

The pipeline saves checkpoints automatically on interrupt or error. To resume:

```bash
python main.py --input ./images --output ./output --checkpoint checkpoint.json
```

Checkpoints preserve:
- Processed image count
- Iteration state per image
- Pipeline progress
