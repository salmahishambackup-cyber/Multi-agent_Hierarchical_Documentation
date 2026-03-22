# Multi-Agent Hierarchical Documentation

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

A multi-agent documentation generation system that automatically analyzes codebases and generates comprehensive, high-quality documentation using LLMs.

## Overview

This system combines static code analysis with LLM-powered generation to create professional documentation for software projects. It features a 5-phase pipeline that extracts code structure, generates docstrings, creates README files, validates output, and evaluates quality.

**Key Features:**
- **Multi-language support**: Python, Java, JavaScript, TypeScript, C, C++, C#
- **Intelligent analysis**: AST extraction, dependency graphs, component clustering
- **LLM-powered generation**: Google-style docstrings and comprehensive READMEs
- **Memory efficient**: 4-bit quantization, caching, and smart device management
- **Production-ready**: Validation, evaluation, and iterative improvement

## Architecture

The system is organized into 5 distinct phases:

```
multi-agent_hierarchical_documentation/
├── phase1_analysis/           # Static code analysis (tree-sitter)
│   ├── agents/               # StructuralAgent for orchestration
│   └── analyzer/             # AST, dependencies, components
├── phase2_docstrings/        # Docstring generation
│   ├── agents/               # Writer agent
│   └── prompts/              # Templates
├── phase3_readme/            # README generation
│   ├── prompts/              # README templates
│   └── readme_generator.py  # README creation logic
├── phase4_validation/        # Quality validation
│   ├── agents/               # Critic agent
│   └── validator.py          # Heuristic checks
├── phase5_evaluation/        # Quality evaluation
│   ├── prompts/              # Evaluation templates
│   └── evaluator.py          # Metrics and scoring
├── orchestrator.py           # Main pipeline coordinator
├── utils/                    # Shared utilities
└── schemas/                  # JSON schemas for validation
```

### Pipeline Phases

**Phase 1: Static Analysis**
- Parses source code using tree-sitter
- Extracts AST, dependencies, and component clusters
- Supports 7 programming languages
- No LLM calls (fast and deterministic)
- Outputs: `ast.json`, `dependencies_normalized.json`, `components.json`

**Phase 2: Docstring Generation**
- Generates Google-style docstrings using LLM
- Dependency-aware topological ordering
- Content-based caching for efficiency
- Handles modules, functions, and classes
- Output: `doc_artifacts.json`

**Phase 3: README Generation**
- Creates comprehensive README with 6 sections
- Uses code analysis summary as context
- Includes working badges, examples, and structure
- Output: `README.md` in repository root

**Phase 4: Validation**
- Validates README structure and content
- Checks for required sections
- Heuristic quality checks
- Provides feedback for improvements
- Output: In-memory validation results

**Phase 5: Evaluation**
- Evaluates documentation quality (clarity, completeness, consistency, usability)
- Provides numerical scores and feedback
- Output: `evaluation_report.json`

## Installation

### Requirements
- Python 3.8+
- GPU recommended (but not required)
- CUDA for GPU acceleration (optional)

### Install Dependencies

```bash
pip install transformers accelerate torch sentencepiece tree-sitter tree-sitter-languages networkx psutil pydantic

# For 4-bit quantization (recommended for GPU)
pip install bitsandbytes
```

### Clone Repository

```bash
git clone https://github.com/SalmaHisham/Multi-agent_Hierarchical_Documentation.git
cd Multi-agent_Hierarchical_Documentation
```

## Usage

### Quick Start

```python
from orchestrator import Orchestrator

# Initialize orchestrator
orch = Orchestrator(
    repo_path="/path/to/your/project",
    artifacts_dir="./artifacts",
    model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
    device="auto",  # Use GPU if available
    quantize=True,  # 4-bit quantization
    use_structural_agent=True  # Enhanced Phase 1
)

# Run all phases
results = orch.run_all()

# Cleanup GPU memory
orch.cleanup()
```

### Run Individual Phases

```python
# Phase 1: Static analysis
phase1_results = orch.run_phase1()
print(f"Modules: {phase1_results['stats']['modules']}")
print(f"Functions: {phase1_results['stats']['functions']}")
print(f"Classes: {phase1_results['stats']['classes']}")

# Phase 2: Docstring generation
phase2_results = orch.run_phase2()
print(f"Total: {phase2_results['stats']['total']}")
print(f"Generated: {phase2_results['stats']['generated']}")

# Phase 3: README generation
phase3_results = orch.run_phase3()
print(f"README: {phase3_results['readme_path']}")

# Phase 4: Validation
phase4_results = orch.run_phase4()
print(f"Valid: {phase4_results['all_valid']}")

# Phase 5: Evaluation
phase5_results = orch.run_phase5()
print(f"Score: {phase5_results['evaluation']['overall']}/10")
```

### Using Jupyter Notebook

Open `demo.ipynb` in Jupyter or Google Colab for an interactive walkthrough of all phases.

### Output Locations

All artifacts are saved to the `artifacts_dir` (default: `./artifacts`):

| Phase | Output | Location |
|-------|--------|----------|
| 1 | AST data | `./artifacts/ast.json` |
| 1 | Dependencies | `./artifacts/dependencies_normalized.json` |
| 1 | Components | `./artifacts/components.json` |
| 2 | Docstrings | `./artifacts/doc_artifacts.json` |
| 2 | Cache | `./artifacts/cache/` |
| 3 | README | `<repo_path>/README.md` |
| 4 | Validation | In-memory only |
| 5 | Evaluation | `./artifacts/evaluation_report.json` |

See `ALL_OUTPUTS_GUIDE.md` for complete details.

## Configuration Options

### Model Selection

```python
# Lightweight model for speed (recommended for T4 GPU)
model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct"

# More capable model (requires more memory)
model_id="Qwen/Qwen2.5-Coder-3B-Instruct"
```

### Memory Optimization

```python
Orchestrator(
    quantize=True,           # Use 4-bit quantization
    device="auto",           # Automatic device selection
    max_new_tokens=512,      # Limit generation length
)
```

### Phase 1 Options

```python
# Use enhanced StructuralAgent (recommended)
use_structural_agent=True

# Enable optional features
enable_performance_monitoring=True  # Track execution time/memory
enable_edge_case_detection=True     # Detect circular imports, etc.
enable_validation=True              # Validate output schemas
```

## Advanced Features

### Edge Case Detection
- Circular import detection
- Monolithic file detection
- Generated code detection

### Performance Monitoring
- Per-stage timing
- Memory usage tracking
- Optimization suggestions

### Determinism Enforcement
- Sorted outputs
- Reproducible results
- Deduplication

### Schema Validation
- AST format validation
- Dependency graph validation
- Component format validation

## Documentation

- **Complete Guide**: `ALL_OUTPUTS_GUIDE.md` - Comprehensive documentation
- **Navigation Index**: `DOCUMENTATION_INDEX.md` - Master index of all documentation
- **Output Summary**: `OUTPUT_LOCATION_SUMMARY.md` - Overview of outputs

## Troubleshooting

### Out of Memory (GPU)
```python
# Enable quantization
quantize=True

# Use smaller model
model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct"

# Reduce token limits
max_new_tokens=256
```

### Import Errors
```bash
# Clear cached bytecode
find . -type f -name '*.pyc' -delete
find . -type d -name '__pycache__' -exec rm -rf {} +

# Restart Python kernel/runtime
```

### Model Loading Issues
```bash
# Install bitsandbytes for quantization
pip install bitsandbytes

# Set environment variable
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
```

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

See LICENSE file for details.

## Citation

If you use this system in your research, please cite:

```bibtex
@software{multi_agent_documentation,
  title={Multi-Agent Hierarchical Documentation},
  author={Salma Hisham and Contributors},
  year={2024},
  url={https://github.com/SalmaHisham/Multi-agent_Hierarchical_Documentation}
}
```

---

*Generated by Multi-Agent Hierarchical Documentation System*
