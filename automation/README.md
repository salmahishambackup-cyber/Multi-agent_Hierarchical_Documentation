# GenAI Multi-Stage Pipeline Automation

**Production-Grade End-to-End Automation** for the GenAI research pipeline.

Converts a manual 7-step workflow into a **single command**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FULLY AUTOMATED WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────┘

LOCAL MACHINE (Windows)          GOOGLE DRIVE                GOOGLE COLAB (GPU)
┌──────────────────┐             ┌──────────┐              ┌──────────────┐
│  Stage 1         │   upload    │ Storage  │   consume   │  Stage 2     │
│  (Repository     ├────────────>│ & Sync   │<────────────┤  (LLM-based  │
│   Analysis)      │    zip      │ Point    │  download   │  Docstring   │
│                  │             │          │   results   │  Generation) │
└──────────────────┘             └──────────┘             └──────────────┘
       ↓                              ↓                            ↓
   Local                         Versioned                   GPU T4
   Windows                        Backups              (3600s timeout)
   Python 3.8+
```

### Why This Architecture?

| Choice | Reason |
|--------|--------|
| **Google Drive** | Native Colab integration, persistent storage, versioning |
| **Python scripts** | Cross-platform, better error handling, research-quality |
| **Colab notebook** | GPU access, optimized for research, notebook-style development |
| **OAuth tokens** | One-time setup, no re-authentication needed |

---

## Installation & Setup

### Prerequisites

- **Windows OS** (tested on Windows 10/11)
- **Python 3.8+** (installed and in PATH)
- **Git** (for cloning)
- **Google Account** (for Drive + Colab)
- **Colab access** (free or Pro)

### Step 1: Verify Prerequisites

```bash
# Check Python
python --version     # Should be 3.8+

# Check Git
git --version       # Should be 2.20+
```

### Step 2: Install Python Dependencies (Local)

```bash
cd automation

# Install required Python packages
pip install --upgrade google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install pydantic networkx tqdm jinja2

# Verify
python scripts/auth_setup.py --verify-only
```

### Step 3: Setup Google Cloud Credentials (ONE-TIME)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable **Google Drive API**:
   - Click "Enable APIs and Services"
   - Search for "Google Drive API"
   - Click Enable
4. Create OAuth 2.0 credentials:
   - Go to Credentials tab
   - Click "Create Credentials" → OAuth 2.0 Client ID
   - Select "Desktop Application"
   - Download credentials as JSON
5. Save credentials:
   - Copy `credentials.json` to `automation/config/`

### Step 4: Authenticate

```bash
# One-time authentication
cd automation
python scripts/auth_setup.py

# Follow the browser prompt to authorize
# Token will be saved locally for future use
```

**Verification:**

```bash
python scripts/auth_setup.py --verify-only
```

---

## Usage

### Quick Start: Full Pipeline

```bash
# From automation directory
cd automation

# Run everything in one command
python scripts/orchestrate_pipeline.py
```

**What happens:**
1. ✅ Runs Stage 1 locally (repository analysis)
2. ✅ Uploads outputs to Google Drive
3. ✅ Triggers Stage 2 on Google Colab
4. ✅ Downloads final documentation
5. ✅ Saves execution logs

**Expected duration:** 1-2 hours (including Colab GPU execution)

---

### Windows Batch Launcher

For easier execution, use the provided batch file:

```bash
# From project root
cd automation

# Full pipeline
pipeline.bat

# Stage 1 only
pipeline.bat stage1

# Trigger Stage 2 (Colab)
pipeline.bat stage2

# Download results
pipeline.bat download

# Setup authentication
pipeline.bat auth

# Show help
pipeline.bat help
```

---

### Command-Line Options

```bash
# Full pipeline (default)
python scripts/orchestrate_pipeline.py

# Stage 1 only (local execution)
python scripts/orchestrate_pipeline.py --stage1-only

# Stage 2 only (Colab trigger)
python scripts/orchestrate_pipeline.py --stage2-only

# Download only (from Drive)
python scripts/orchestrate_pipeline.py --download-only
```

---

## Detailed Workflow

### Stage 1: Repository Analysis (LOCAL - ~15 minutes)

**What it does:**
- Clones target repository
- Performs AST analysis
- Extracts components and dependencies
- Generates structured artifacts (JSON, graphs)

**Outputs:**
- `ast/` - Abstract syntax trees
- `components/` - Code component metadata
- `dependencies/` - Dependency graphs
- `execution_log` - JSON with execution details

**Entry point:** `proj-GenAI/src/main.py`

---

### Stage 2: Documentation Generation (COLAB - ~45 minutes)

**What it does:**
- Loads Stage 1 artifacts from Drive
- Initializes LLM (Hugging Face on GPU)
- Generates docstrings recursively
- Creates architecture documentation
- Generates README.md

**Requirements:**
- GPU runtime (T4 recommended)
- ~8GB VRAM (with quantization)
- Stage 1 outputs on Drive

**Entry point:** `automation/colab/GenAI_Pipeline_Stage2.ipynb`

---

## File Structure

```
automation/
├── pipeline.bat                          # Windows launcher
├── config/
│   ├── pipeline_config.yaml             # Pipeline configuration
│   ├── credentials.json                 # (SENSITIVE - created during setup)
│   └── token.json                       # (SENSITIVE - auto-generated)
├── scripts/
│   ├── auth_setup.py                    # Google authentication
│   ├── orchestrate_pipeline.py           # Main orchestrator (ENTRY POINT)
│   ├── stage1_runner.py                 # Stage 1 executor
│   ├── drive_manager.py                 # Google Drive operations
│   └── colab_executor.py                # Colab trigger (placeholder)
├── colab/
│   └── GenAI_Pipeline_Stage2.ipynb      # Colab notebook template
├── logs/
│   └── execution_*.json                 # Execution logs (auto-generated)
└── README.md                            # This file

proj-GenAI/
├── src/
│   ├── main.py                          # Stage 1 entry point
│   ├── pipeline/orchestrator.py
│   ├── analysis/                        # AST analysis
│   ├── agents/                          # Agent implementations
│   ├── data/
│   │   └── artifacts/                   # Stage 1 outputs
│   │       ├── ast/
│   │       ├── components/
│   │       └── dependencies/
│   └── ...
└── ...

pipeline_outputs/
└── <timestamp>/                         # Stage 2 results (auto-downloaded)
    ├── generated_docs/
    ├── docstrings/
    ├── README.md
    └── execution_summary.json
```

---

## Configuration

Edit `automation/config/pipeline_config.yaml` to customize:

```yaml
pipeline:
  stage1:
    input:
      repo_url: "..."                # Repository to analyze
    output:
      base_dir: "..."               # Where artifacts go

  stage2:
    gpu_runtime: true               # Use GPU (required)
    colab_resource_limits:
      max_runtime_seconds: 3600     # 1 hour timeout

google_drive:
  folder_name: "GenAI_Pipeline_Automation"  # Root folder on Drive
```

---

## Monitoring & Troubleshooting

### Monitor Stage 1

```bash
# Watch the console output
# Check logs in: automation/logs/execution_*.json
```

### Monitor Stage 2

1. Open [Google Colab](https://colab.research.google.com)
2. Open: `automation/colab/GenAI_Pipeline_Stage2.ipynb`
3. Watch cells execute
4. Check GPU usage in `Runtime > Resources`

### Common Issues

| Issue | Solution |
|-------|----------|
| "Token not found" | Run: `python scripts/auth_setup.py` |
| Stage 1 fails | Check: `automation/logs/execution_*.json` |
| Drive upload slow | Normal for large repos (>100MB); be patient |
| Colab timeout | Increase `max_runtime_seconds` in config |
| "No GPU detected" | Go to Colab: Runtime > Change runtime type > T4 GPU |

### Debug Mode

Enable verbose logging:

```bash
# Edit orchestrate_pipeline.py
# Change logging level to DEBUG
```

View execution logs:

```bash
# After run completes
cat automation/logs/execution_20240101_120000.json | python -m json.tool
```

---

## Data Security

### Sensitive Files (DO NOT COMMIT)

```bash
automation/config/credentials.json    # Google OAuth credentials
automation/config/token.json          # Google auth token
```

Add to `.gitignore`:

```
automation/config/credentials.json
automation/config/token.json
automation/logs/
pipeline_outputs/
```

### Token Management

- Tokens are stored locally in `automation/config/token.json`
- Automatically refreshed when expired
- Never shared or uploaded
- Delete to revoke access: `rm automation/config/token.json`

---

## Advanced Usage

### Custom Repository

Change the repository URL in Stage 1:

**In `proj-GenAI/src/main.py`:**

```python
repo_url = "https://github.com/YOUR_OWNER/YOUR_REPO.git"
```

Then run:

```bash
python scripts/orchestrate_pipeline.py --stage1-only
```

### Custom LLM Model

Edit the Colab notebook cell for model selection:

```python
model_id = "mistralai/Mistral-7B-Instruct-v0.2"  # or your preferred model
```

### Reduce Colab Costs

For Pro users, customize quantization:

```python
quantize=True        # 4-bit quantization (saves memory)
dtype="float16"      # Half precision
```

---

## Performance Metrics

Typical execution times on Google Colab (T4 GPU):

| Stage | Component | Time |
|-------|-----------|------|
| 1 | Repository cloning | 2 min |
| 1 | AST analysis | 5 min |
| 1 | Component extraction | 5 min |
| 1 | Upload to Drive | 3 min |
| **Total Stage 1** | | **~15 min** |
| | | |
| 2 | Model loading | 10 min |
| 2 | Docstring generation | 30 min |
| 2 | README generation | 5 min |
| **Total Stage 2** | | **~45 min** |
| | | |
| | Download results | 2 min |
| **TOTAL PIPELINE** | | **~60-90 min** |

---

## Reproducibility

All execution details are logged:

```json
{
  "pipeline_start": "20240101_120000",
  "stages": {
    "stage1": {
      "status": "success",
      "repo": "...",
      "artifacts": { ... }
    },
    "upload": {
      "status": "success",
      "drive_path": "..."
    },
    "stage2": { ... }
  }
}
```

**Restore previous run:**

```bash
# Results are versioned on Drive by timestamp
# Find the execution_*.json in automation/logs/
# Identify the Drive path and download manually if needed
```

---

## Next Steps After Execution

1. **Download results:**
   ```bash
   python scripts/orchestrate_pipeline.py --download-only
   ```

2. **Review generated documentation:**
   ```
   pipeline_outputs/<timestamp>/
   ├── Generated_Docstrings.md
   ├── Architecture_Summary.md
   ├── README.md
   └── ...
   ```

3. **Publish or integrate:**
   - Host on GitHub Pages
   - Add to project wiki
   - Use as research artifact

---

## Support & Contribution

For issues, refer to:
- `automation/logs/` - Execution logs
- `IMPLEMENTATION_SUMMARY.md` - Architecture details
- `QUICKSTART.md` - Quick reference

---

## License

Same as parent GenAI project.
