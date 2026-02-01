# QUICKSTART: GenAI Pipeline Automation

**Get running in 10 minutes.**

---

## Prerequisites Check (2 min)

```bash
# Python 3.8+
python --version

# Git
git --version

# You have: Windows OS, Google account, internet
```

---

## Step 1: Setup Google Cloud Credentials (5 min, ONE-TIME)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/dashboard)
2. Click "Create Project" → name it `GenAI_Automation`
3. Enable Google Drive API:
   - APIs & Services → Enable APIs → Search "Google Drive" → Enable
4. Create OAuth 2.0 credentials:
   - Credentials → Create Credentials → OAuth 2.0 Client (Desktop Application)
   - Download JSON file
5. Save credentials:
   ```bash
   cp ~/Downloads/credentials.json automation/config/
   ```

---

## Step 2: Install & Authenticate (3 min)

```bash
cd automation

# Install Python packages
pip install --upgrade google-auth-oauthlib google-api-python-client pydantic networkx

# One-time authentication (opens browser)
python scripts/auth_setup.py

# Verify
python scripts/auth_setup.py --verify-only
```

---

## Step 3: Run Pipeline (NOW!)

### Option A: Full Pipeline (Recommended)

```bash
cd automation

# This runs everything automatically:
# 1. Stage 1 (local, ~15 min)
# 2. Upload to Drive
# 3. Trigger Stage 2 on Colab (GPU, ~45 min)
# 4. Download results

python scripts/orchestrate_pipeline.py
```

### Option B: Using Windows Launcher

```bash
cd automation

# Full pipeline
pipeline.bat

# Or specific stages
pipeline.bat stage1
pipeline.bat stage2
pipeline.bat download
```

---

## Monitor Execution

### Stage 1 (Local, ~15 min)

- Watch console output
- Logs saved to: `automation/logs/execution_*.json`

### Stage 2 (Colab, ~45 min)

1. Open [Google Colab](https://colab.research.google.com)
2. Follow the Colab link provided by orchestrator
3. OR: Manually open `automation/colab/GenAI_Pipeline_Stage2.ipynb`
4. Enable GPU: Runtime > Change runtime type > T4 GPU
5. Run all cells (Ctrl+F9)

---

## Get Results

```bash
# Automatically downloaded to:
pipeline_outputs/<timestamp>/
├── generated_docs/
├── docstrings/
├── README.md
└── execution_summary.json
```

Or manually download from Google Drive:
- [Google Drive](https://drive.google.com) → GenAI_Pipeline_Automation → stage2_outputs

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Token not found" | Run: `python scripts/auth_setup.py` |
| "credentials.json missing" | Download from Google Cloud Console, save to `automation/config/` |
| Stage 1 fails | Check: `automation/logs/execution_*.json` |
| Colab: "No GPU" | Runtime > Change runtime type > T4 GPU |
| Colab: "Timeout" | Increase timeout in `automation/config/pipeline_config.yaml` |

---

## What Happened?

**Before automation:**
1. Run Stage 1 ← Manual
2. Zip output ← Manual
3. Upload to Colab ← Manual
4. Unzip ← Manual
5. Run Stage 2 ← Manual
6. Download ← Manual

**After automation:**
```bash
python scripts/orchestrate_pipeline.py
```
✅ Everything happens automatically

---

## Next Steps

- **Customize repo:** Edit `proj-GenAI/src/main.py` (change `repo_url`)
- **Tweak LLM:** Edit Colab notebook (change `model_id`)
- **Understand architecture:** Read `automation/ARCHITECTURE.md`
- **Advanced usage:** Read `automation/README.md`

---

## Need Help?

- Execution logs: `automation/logs/`
- Architecture docs: `automation/ARCHITECTURE.md`
- Detailed guide: `automation/README.md`
- Script errors: Add `--debug` flag (future feature)

---

**That's it! Happy automating. 🚀**
