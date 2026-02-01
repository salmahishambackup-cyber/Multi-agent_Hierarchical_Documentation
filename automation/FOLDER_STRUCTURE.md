# FOLDER STRUCTURE & FILE ORGANIZATION

## Complete Automation Solution Layout

```
Multi-agent_Hierarchical_Documentation/
│
├── automation/                              ← NEW: AUTOMATION SOLUTION
│   ├── pipeline.bat                         ← Windows launcher (main entry point)
│   │
│   ├── config/
│   │   ├── pipeline_config.yaml             ← Configuration (editable)
│   │   ├── credentials.json                 ← Google OAuth (CREATED by auth)
│   │   └── token.json                       ← Auth token (CREATED by auth)
│   │
│   ├── scripts/
│   │   ├── orchestrate_pipeline.py          ← MAIN ORCHESTRATOR (main entry)
│   │   ├── auth_setup.py                    ← One-time authentication
│   │   ├── stage1_runner.py                 ← Execute Stage 1 locally
│   │   ├── drive_manager.py                 ← Google Drive operations
│   │   └── colab_executor.py                ← Colab notebook trigger
│   │
│   ├── colab/
│   │   └── GenAI_Pipeline_Stage2.ipynb      ← Colab notebook template
│   │
│   ├── logs/                                ← CREATED: Execution logs
│   │   ├── execution_20240101_120000.json   ← Detailed execution log
│   │   ├── execution_20240101_130000.json
│   │   └── ...
│   │
│   ├── README.md                            ← Complete usage guide
│   ├── QUICKSTART.md                        ← Quick start (5 min)
│   ├── ARCHITECTURE.md                      ← Design document
│   ├── INTEGRATION.md                       ← Integration patterns
│   ├── EXECUTION_FLOW.md                    ← Step-by-step flow
│   └── requirements.txt                     ← Python dependencies
│
├── proj-GenAI/                              ← EXISTING: Stage 1 (local)
│   └── src/
│       ├── main.py                          ← Stage 1 entry point
│       ├── pipeline/
│       │   └── orchestrator.py
│       ├── analysis/                        ← AST analysis
│       │   ├── ast_extractor.py
│       │   ├── component_extractor.py
│       │   └── ...
│       ├── agents/                          ← Agent implementations
│       │   ├── base_agent.py
│       │   └── ...
│       └── data/
│           └── artifacts/                   ← Stage 1 OUTPUTS
│               ├── ast/                     ← Abstract syntax trees
│               │   ├── repo_deepwiki.json
│               │   ├── component_ast.json
│               │   └── ... [~150 files]
│               ├── components/              ← Code components
│               │   ├── deepwiki_components.json
│               │   └── ... [~280 files]
│               ├── dependencies/            ← Dependency graphs
│               │   └── ... [~95 files]
│               └── transfer_20240101_120000/  ← Timestamped package
│                   ├── ast/
│                   ├── components/
│                   └── dependencies/
│
├── pipeline_outputs/                        ← CREATED: Stage 2 results
│   ├── 20240101_120000/                     ← Timestamped run
│   │   ├── generated_docs/                  ← Generated documentation
│   │   │   ├── module_documentation.md
│   │   │   ├── architecture_overview.md
│   │   │   ├── api_reference.md
│   │   │   └── ... [~40+ docs]
│   │   ├── docstrings/                      ← Generated docstrings
│   │   │   ├── deepwiki_core.json
│   │   │   ├── deepwiki_utils.json
│   │   │   └── ... [~20+ modules]
│   │   ├── README.md                        ← Auto-generated README
│   │   └── execution_summary.json           ← Execution details
│   │
│   └── 20240101_140000/                     ← Previous run
│       └── ...
│
├── Agents/                                  ← EXISTING: Documentation agents
│   ├── Core/
│   ├── Prompts/
│   └── Sub/
│
├── Docsys/                                  ← EXISTING: Documentation system
├── Demo/                                    ← EXISTING: Demo code
├── Utils/                                   ← EXISTING: Utilities
│
├── main.py                                  ← EXISTING: Stage 2 entry
├── requirements.txt                         ← EXISTING: Stage 2 dependencies
├── README.md                                ← Project README
├── QUICKSTART.md                            ← Project quickstart
├── MIGRATION_GUIDE.md                       ← Migration docs
└── .gitignore                               ← UPDATED: Add automation secrets
```

---

## Key Files Reference

### Main Entry Points

| File | Purpose | Command |
|------|---------|---------|
| `automation/pipeline.bat` | Windows batch launcher | `pipeline.bat` |
| `automation/scripts/orchestrate_pipeline.py` | Python orchestrator | `python scripts/orchestrate_pipeline.py` |
| `automation/scripts/auth_setup.py` | Authentication setup | `python scripts/auth_setup.py` |

### Configuration

| File | Purpose |
|------|---------|
| `automation/config/pipeline_config.yaml` | Pipeline configuration (editable) |
| `automation/config/credentials.json` | Google OAuth credentials (auto-created, DO NOT COMMIT) |
| `automation/config/token.json` | Auth token (auto-created, DO NOT COMMIT) |

### Documentation

| File | Purpose |
|------|---------|
| `automation/README.md` | Complete user guide |
| `automation/QUICKSTART.md` | 5-minute quick start |
| `automation/ARCHITECTURE.md` | Design & architecture |
| `automation/INTEGRATION.md` | Integration patterns |
| `automation/EXECUTION_FLOW.md` | Step-by-step execution flow |

### Scripts

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `stage1_runner.py` | Run Stage 1 locally | `proj-GenAI/src/main.py` | `artifacts/transfer_*/` |
| `drive_manager.py` | Google Drive operations | Token + files | Drive folders |
| `colab_executor.py` | Trigger Colab | Config | URL + instructions |
| `orchestrate_pipeline.py` | Main orchestrator | All above | Complete pipeline |

### Data Directories

| Directory | Source | Content | Size |
|-----------|--------|---------|------|
| `proj-GenAI/src/data/artifacts/ast/` | Stage 1 | AST JSON files | ~45 MB |
| `proj-GenAI/src/data/artifacts/components/` | Stage 1 | Component metadata | ~23 MB |
| `proj-GenAI/src/data/artifacts/dependencies/` | Stage 1 | Dependency graphs | ~12 MB |
| `pipeline_outputs/<timestamp>/` | Stage 2 | Generated documentation | ~34 MB |

---

## File Generation Timeline

### Before First Run

```
automation/
├── config/
│   └── pipeline_config.yaml          [CREATED - manual]
├── scripts/
│   ├── orchestrate_pipeline.py       [CREATED - manual]
│   ├── auth_setup.py                 [CREATED - manual]
│   ├── stage1_runner.py              [CREATED - manual]
│   ├── drive_manager.py              [CREATED - manual]
│   └── colab_executor.py             [CREATED - manual]
└── colab/
    └── GenAI_Pipeline_Stage2.ipynb   [CREATED - manual]
```

### During `auth_setup.py`

```
automation/config/
├── credentials.json                  [UPLOADED by user]
└── token.json                        [CREATED by auth_setup.py]
```

### During `orchestrate_pipeline.py --stage1-only`

```
proj-GenAI/src/data/artifacts/
├── ast/                              [UPDATED/CREATED by Stage 1]
├── components/                       [UPDATED/CREATED by Stage 1]
├── dependencies/                     [UPDATED/CREATED by Stage 1]
└── transfer_20240101_120000/         [CREATED by stage1_runner.py]
    ├── ast/
    ├── components/
    └── dependencies/

automation/logs/
└── execution_20240101_120000.json    [CREATED by orchestrator]
```

### During Drive upload

```
Google Drive/
└── GenAI_Pipeline_Automation/        [CREATED by drive_manager]
    └── stage2_inputs/                [CREATED by drive_manager]
        └── stage1_20240101_120000/   [CREATED by drive_manager]
            ├── ast/
            ├── components/
            └── dependencies/
```

### During Stage 2 (Colab)

```
Google Drive/
└── GenAI_Pipeline_Automation/
    └── stage2_outputs/               [CREATED by Colab notebook]
        ├── generated_docs/
        ├── docstrings/
        ├── README.md
        └── execution_summary.json
```

### During download

```
pipeline_outputs/
└── 20240101_120000/                  [CREATED by drive_manager]
    ├── generated_docs/
    ├── docstrings/
    ├── README.md
    └── execution_summary.json
```

---

## .gitignore Updates

```bash
# Sensitive files (MUST add)
automation/config/credentials.json
automation/config/token.json

# Generated outputs (optional, but recommended)
automation/logs/
pipeline_outputs/

# Python
__pycache__/
*.pyc
.pytest_cache/
```

---

## Backup & Versioning

### On Google Drive (Persistent)

```
GenAI_Pipeline_Automation/
├── stage2_inputs/
│   ├── stage1_20240101_120000/       ← Timestamped input v1
│   ├── stage1_20240101_140000/       ← Timestamped input v2
│   └── stage1_20240102_090000/       ← Timestamped input v3
│
└── stage2_outputs/                   ← Latest outputs
    ├── generated_docs/
    ├── docstrings/
    └── ...
```

### Local Execution Logs

```
automation/logs/
├── execution_20240101_120000.json    ← Full audit trail
├── execution_20240101_140000.json
├── execution_20240102_090000.json
└── ...
```

### Recovery

```bash
# Get full execution history
cat automation/logs/execution_*.json | python -m json.tool

# Restore previous run (from Drive)
# Copy from: GenAI_Pipeline_Automation/stage2_inputs/stage1_<timestamp>/

# Verify Drive sync (local cache)
# Check: .../stage2_inputs/ for all timestamped versions
```

---

## Storage Usage Estimates

| Item | Size | Note |
|------|------|------|
| Stage 1 artifacts | ~80 MB | Per repo analysis |
| Colab temp files | ~50 MB | Cleaned after Stage 2 |
| Stage 2 outputs | ~35 MB | Final documentation |
| Execution logs | ~50 KB | Per run |
| **Total per run** | **~115 MB** | Minimal |
| **Google Drive free tier** | **15 GB** | Sufficient for ~130 runs |
| **Local disk** | **200 MB** | For code + outputs |

---

## Cleanup & Maintenance

### Remove Old Outputs

```python
# Optional: Delete old local outputs
import shutil
from pathlib import Path

old_runs = sorted(Path('pipeline_outputs').glob('*'))
for run in old_runs[:-5]:  # Keep last 5
    shutil.rmtree(run)
```

### Clean Execution Logs

```bash
# Keep only recent logs
cd automation/logs
ls -t | tail -n +21 | xargs rm  # Keep last 20
```

### Clear Local Cache (Optional)

```bash
# Remove transfer packages (already on Drive)
rm -rf proj-GenAI/src/data/artifacts/transfer_*
```

---

## Summary

- **Total files added:** 11 (scripts + docs + configs)
- **Directories created:** 4 (scripts, config, colab, logs)
- **Entry points:** 2 (batch + Python)
- **Documentation files:** 6 (comprehensive guides)
- **Configuration files:** 1 (YAML)
- **Dependencies:** 5 packages (Python)

**Ready to use immediately after:**
1. Creating credentials.json
2. Running auth_setup.py
3. Executing orchestrate_pipeline.py
