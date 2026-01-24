# POC: Interactive Documentation Assistant

A proof-of-concept interactive documentation assistant optimized for Google Colab T4 GPU. This system demonstrates a complete end-to-end pipeline for generating project documentation using lightweight LLMs with 4-bit quantization.

## 🎯 Features

### Phase 1: Static Code Analysis (No LLM)
- Fast Python source parsing using **tree-sitter**
- Generates AST summaries with functions, classes, and imports
- Builds dependency graphs (internal/external)
- Identifies components through clustering

### Phase 2: Docstring Generation
- Google-style docstrings for modules, functions, and classes
- **Topological ordering** for context-aware generation
- **Content-based caching** to skip unchanged code
- Batch processing for efficiency

### Phase 3: README Generation
- Generates comprehensive README with 6 sections:
  1. Project Title & Badges
  2. Overview/Description
  3. Features
  4. Architecture/Project Structure
  5. Installation/Setup
  6. Usage Examples
- **Single LLM call** for all sections (6x reduction vs per-section)

### Phase 4: Validation & Iteration
- **Heuristic validation** using regex (1000x faster than LLM)
- Checks completeness of each section
- Iterative regeneration for failed sections (max 2 retries)

### Phase 5: Final Evaluation
- Scores documentation on 4 metrics (0-10 each):
  - **Clarity**: Easy to understand?
  - **Completeness**: All sections present?
  - **Consistency**: Formatting consistent?
  - **Usability**: Can new users get started?
- Single LLM call for all metrics

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `tree-sitter>=0.20.0,<0.21.0` - Static analysis
- `tree-sitter-languages>=1.10.0` - Language parsers
- `transformers>=4.45.0` - LLM support
- `bitsandbytes>=0.41.0` - 4-bit quantization
- `torch` - PyTorch backend
- `networkx>=3.2` - Dependency graphs
- `psutil>=5.9.0` - Memory profiling

### Interactive Chat Mode

```bash
python main.py
```

**Available Commands:**
- `document <path>` - Full pipeline
- `analyze <path>` - Phase 1 only
- `generate docstrings` - Phase 2 only
- `generate readme` - Phase 3 only
- `validate` - Phase 4 only
- `evaluate` - Phase 5 only
- `show readme` - Display README
- `show report` - Display evaluation
- `help` - Show commands
- `exit` - Quit

### Programmatic API

```python
from pipeline.orchestrator import Orchestrator

# Initialize
orchestrator = Orchestrator(
    repo_path="./my_project",
    artifacts_dir="./artifacts",
    model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
    device="auto",
    quantize=True,
)

# Run all phases
results = orchestrator.run_all()

# Or run individual phases
orchestrator.run_phase1()  # Analysis
orchestrator.run_phase2()  # Docstrings
orchestrator.run_phase3()  # README
orchestrator.run_phase4()  # Validation
orchestrator.run_phase5()  # Evaluation

# Cleanup
orchestrator.cleanup()
```

### Google Colab

Open `demo.ipynb` in Google Colab and run all cells. The notebook demonstrates the complete pipeline.

## 📁 Project Structure

```
Multi-agent_Hierarchical_Documentation/
│
├── main.py                    # Interactive chat entry point
├── demo.ipynb                 # Colab demonstration notebook
├── requirements.txt           # Dependencies
│
├── analyzer/                  # Static analysis (Phase 1)
│   ├── ast_extractor.py       # Tree-sitter parsing
│   ├── dependency_builder.py  # Dependency graph
│   ├── component_extractor.py # Component clustering
│   ├── language_router.py     # Language detection
│   ├── tree_sitter_loader.py  # Parser caching
│   └── file_metrics.py        # Code metrics
│
├── pipeline/                  # Pipeline orchestration
│   ├── orchestrator.py        # Coordinates all phases
│   ├── analyzer.py            # Phase 1 wrapper
│   ├── docstring_generator.py # Phase 2
│   ├── readme_generator.py    # Phase 3
│   ├── validator.py           # Phase 4
│   └── evaluator.py           # Phase 5
│
├── agents/                    # LLM-based agents
│   ├── writer.py              # Content generation
│   ├── critic.py              # Quality review
│   └── prompts/               # Prompt templates
│       ├── docstring.md       # Docstring prompt
│       ├── readme.md          # README prompt
│       └── evaluation.md      # Evaluation prompt
│
├── utils/                     # Utilities
│   ├── llm_client.py          # Quantized LLM interface
│   ├── io_tools.py            # File I/O
│   ├── cache.py               # Content caching
│   └── profiler.py            # Performance profiling
│
└── chat/                      # Chat interface
    ├── assistant.py           # Chat controller
    └── commands.py            # Command parser
```

## ⚙️ Configuration

### LLM Models (T4 Optimized)

**Recommended (1.5B params):**
```python
model_id = "Qwen/Qwen2.5-Coder-1.5B-Instruct"  # Fast, fits T4
```

**Alternative (3B params):**
```python
model_id = "Qwen/Qwen2.5-Coder-3B-Instruct"  # Better quality
```

### Memory Budget (T4 = 15GB)
- Model (1.5B, 4-bit): ~1.5GB
- Model (3B, 4-bit): ~3GB
- KV cache: ~1-2GB
- Python/tree-sitter: ~0.5GB
- **Safety margin: ~8GB free**

### Generation Parameters

```python
MAX_INPUT_TOKENS = 2048    # Truncate long inputs
MAX_NEW_TOKENS = 512       # Limit output length
TEMPERATURE = 0.1          # Low for consistency
TOP_P = 0.95               # Nucleus sampling
```

### Caching Strategy

```python
# Cache by content hash (first 16 chars of SHA256)
cache_key = hashlib.sha256(content.encode()).hexdigest()[:16]

# Cache locations:
# - artifacts/cache/docstrings/{hash}.json
# - artifacts/cache/readme_sections/{section}_{hash}.json
```

## 🎛️ Design Principles

1. **Colab T4 Optimized**: 15GB GPU RAM limit, 4-bit quantization
2. **Minimal & Efficient**: Small models (1.5B-3B), simple heuristics
3. **Low Token Usage**: Aggressive caching, artifact reuse
4. **Modular & Profileable**: Independent phases with timing/memory stats
5. **Reproducible**: Single script/notebook runs entire pipeline

## 📊 Example Output

```
🤖 Documentation Assistant (Colab T4 Optimized)

> document ./my_project
📂 Project: my_project

━━━ PHASE 1: Analysis ━━━ [2.1s | 0.3GB]
✅ 12 modules, 35 functions, 6 classes

━━━ PHASE 2: Docstrings ━━━ [45.2s | 3.8GB]  
✅ 47 docstrings generated (12 cached)

━━━ PHASE 3: README ━━━ [8.3s | 3.8GB]
✅ 6 sections generated

━━━ PHASE 4: Validation ━━━ [3.1s | 0.1GB]
✅ All sections valid

━━━ PHASE 5: Evaluation ━━━ [2.5s | 3.8GB]
📊 Score: 8.5/10
   Clarity: 9 | Completeness: 9 | Consistency: 8 | Usability: 8

🎉 Documentation complete! See README.md and artifacts/
```

## 🧪 Testing

### Test Phase 1 (No LLM required)

```bash
python test_analyzer.py
```

This validates tree-sitter parsing and dependency extraction.

### Test Full Pipeline

Due to the size of LLM models, full testing requires either:
1. **Google Colab T4**: Run `demo.ipynb`
2. **Local GPU**: Ensure 8GB+ VRAM with CUDA
3. **CPU Mode**: Very slow, add `--device cpu --no-quantize`

## 🔧 Troubleshooting

### Tree-sitter version conflict
```bash
pip install 'tree-sitter>=0.20.0,<0.21.0'
```

### Out of memory on GPU
- Use 1.5B model instead of 3B
- Reduce `MAX_INPUT_TOKENS` to 1024
- Enable `quantize=True`

### Slow generation
- Use GPU (`device="cuda"`)
- Enable caching (automatic)
- Reduce `MAX_NEW_TOKENS`

## 📝 Artifacts Generated

- `artifacts/ast.json` - AST summaries
- `artifacts/dependencies_normalized.json` - Dependency graph
- `artifacts/components.json` - Component clustering
- `artifacts/doc_artifacts.json` - Generated docstrings
- `artifacts/evaluation_report.json` - Quality scores
- `README.md` - Generated documentation

## 🎓 Design Rationale

### Why These Choices?

- **tree-sitter over ast module**: Faster, multi-language, byte positions
- **1.5B model over 3B**: 2x faster, fits T4, good quality for docstrings
- **4-bit quantization**: 4x memory reduction, minimal quality loss
- **Single-call README**: 6x fewer LLM calls vs per-section
- **Heuristic validation**: 1000x faster than LLM validation
- **Hash-based caching**: Skip unchanged files on re-runs

## 📄 License

[Your License Here]

## 🙏 Acknowledgments

Built with:
- [tree-sitter](https://tree-sitter.github.io/) - Code parsing
- [Qwen2.5-Coder](https://huggingface.co/Qwen) - LLM
- [Transformers](https://huggingface.co/transformers) - Model loading
- [bitsandbytes](https://github.com/TimDettmers/bitsandbytes) - Quantization
