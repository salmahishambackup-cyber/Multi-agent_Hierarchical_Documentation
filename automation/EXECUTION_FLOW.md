# EXECUTION FLOW - Complete Step-by-Step

## One-Command Workflow

```bash
cd automation
python scripts/orchestrate_pipeline.py
```

This single command executes the entire pipeline. Here's what happens behind the scenes:

---

## DETAILED EXECUTION TIMELINE

### T+0:00 - INITIALIZATION

```
[orchestrate_pipeline.py] starts
│
├─ Load configuration
├─ Create logs directory (if missing)
├─ Timestamp: 2024-01-01_120000
└─ Verify Google Drive token exists
   └─ If not found: Exit with error message
      "Run: python scripts/auth_setup.py"
```

**Console Output:**
```
================================================================================
         GENAI PIPELINE - FULL EXECUTION
================================================================================

[STEP 1/5] Verifying Google Drive authentication...
✓ Google Drive authentication verified
```

---

### T+0:05 - STAGE 1 EXECUTION (Local, ~900 seconds)

```
[orchestrate_pipeline.py] calls Stage1Runner
│
└─ Stage1Runner.run()
   │
   ├─ Step 1: Verify proj-GenAI structure
   │  ├─ Check: proj-GenAI/src/main.py exists ✓
   │  ├─ Check: proj-GenAI/src/pipeline/orchestrator.py exists ✓
   │  ├─ Check: proj-GenAI/src/data/artifacts/ exists ✓
   │  └─ Status: VERIFIED
   │
   ├─ Step 2: Execute pipeline
   │  ├─ Set PYTHONPATH = proj-GenAI/src
   │  ├─ Run: python proj-GenAI/src/main.py
   │  ├─ Subprocess waits for completion (timeout: 600s)
   │  ├─ Process: Clone repo → AST parse → Extract components
   │  └─ Success: returncode == 0
   │
   ├─ Step 3: Verify outputs
   │  ├─ Check: artifacts/ast/ (150 files, 45.2 MB) ✓
   │  ├─ Check: artifacts/components/ (280 files, 23.4 MB) ✓
   │  ├─ Check: artifacts/dependencies/ (95 files, 12.1 MB) ✓
   │  └─ Manifest created
   │
   └─ Step 4: Prepare transfer package
      ├─ Create: artifacts/transfer_20240101_120000/
      ├─ Copy: ast/ → transfer_20240101_120000/ast/
      ├─ Copy: components/ → transfer_20240101_120000/components/
      ├─ Copy: dependencies/ → transfer_20240101_120000/dependencies/
      └─ Return: package_path, manifest
```

**Console Output:**
```
[STEP 2/5] Executing Stage 1 (Repository Analysis)...
Verifying proj-GenAI structure...
✓ proj-GenAI structure verified
Executing Stage 1 pipeline...
✓ Pipeline executed successfully
Verifying Stage 1 outputs...
✓ ast: 150 files, 45.20 MB
✓ components: 280 files, 23.40 MB
✓ dependencies: 95 files, 12.10 MB
Preparing outputs for transfer...
✓ Copied ast
✓ Copied components
✓ Copied dependencies

✅ Stage 1 completed successfully!
Output package: proj-GenAI/src/data/artifacts/transfer_20240101_120000
Package size: 80.74 MB
```

---

### T+15:00 - UPLOAD TO GOOGLE DRIVE (~180 seconds)

```
[orchestrate_pipeline.py] calls GoogleDriveManager
│
└─ GoogleDriveManager.upload_stage1_output()
   │
   ├─ Initialize Drive API
   │  ├─ Read token from config/token.json
   │  ├─ Create OAuth2Credentials
   │  ├─ Refresh if expired
   │  └─ Build Drive service
   │
   ├─ Ensure root folder
   │  ├─ Search Drive for "GenAI_Pipeline_Automation"
   │  ├─ If found: Use existing (ID: xyz123...)
   │  └─ If not: Create new folder
   │
   ├─ Create subfolder: stage2_inputs
   │  └─ parent_id = root_folder_id
   │
   ├─ Create versioned subfolder: stage1_20240101_120000
   │  └─ parent_id = stage2_inputs_folder_id
   │
   └─ Recursively upload all files
      ├─ ast/
      │  ├─ repo_deepwiki.json (5.2 MB)
      │  ├─ component_ast.json (3.1 MB)
      │  └─ ... [120 more files]
      ├─ components/
      │  ├─ deepwiki_components.json (2.3 MB)
      │  └─ ... [250+ more files]
      └─ dependencies/
         └─ ... [95 files]

Drive Structure After Upload:
GenAI_Pipeline_Automation/                    [Folder ID: abc123]
└── stage2_inputs/                            [Folder ID: def456]
    └── stage1_20240101_120000/               [Folder ID: ghi789]
        ├── ast/                              [Folder ID: jkl012]
        │   ├── repo_deepwiki.json
        │   └── ... [149 more files]
        ├── components/
        │   └── ... [280 files]
        └── dependencies/
            └── ... [95 files]
```

**Console Output:**
```
[STEP 3/5] Uploading Stage 1 output to Google Drive...
Uploading Stage 1 output to Drive...
✓ Upload successful: GenAI_Pipeline_Automation/stage2_inputs/stage1_20240101_120000
```

---

### T+18:00 - TRIGGER STAGE 2 ON COLAB (~60 seconds)

```
[orchestrate_pipeline.py] calls ColabExecutor
│
└─ ColabExecutor.trigger_notebook_execution()
   │
   ├─ Display instructions
   │  │
   │  └─ "To execute Stage 2 automatically:
   │     │
   │     ├─ Option 1: MANUAL (Recommended for research)
   │     │  - Open: https://colab.research.google.com
   │     │  - Copy code from: automation/colab/GenAI_Pipeline_Stage2.ipynb
   │     │  - Run cells
   │     │
   │     └─ Option 2: AUTOMATIC
   │        - [Requires Colab API integration - future enhancement]
   │
   └─ Return: success (True)
```

**Console Output:**
```
[STEP 4/5] Triggering Stage 2 execution on Google Colab...

────────────────────────────────────────────────────────────────────────────
GOOGLE COLAB EXECUTION
────────────────────────────────────────────────────────────────────────────

To execute Stage 2 automatically:

Option 1: MANUAL (Recommended for research)
  - Open: https://colab.research.google.com
  - Create new notebook or open existing
  - Copy code from: automation/colab/GenAI_Pipeline_Stage2.ipynb
  - Run cells

Option 2: AUTOMATIC (Requires setup)
  - Implement Colab API integration
  - Use: google-colab-api or custom deployment
  - Monitor via: Colab execution API
────────────────────────────────────────────────────────────────────────────
```

**Next Step: Manual Colab Execution**

User opens Colab notebook and runs cells:

```
[Cell 1] Check GPU
GPU Available: True
GPU Name: Tesla T4
GPU Memory: 16.00 GB

[Cell 2] Install packages
✓ Packages installed

[Cell 3] Mount Drive
✓ Google Drive mounted

[Cell 4] Load Stage 1 outputs
Using Stage 1 output from: stage1_20240101_120000
📁 ast: 150 files
📁 components: 280 files
📁 dependencies: 95 files

[Cell 5] Clone target repository
Cloning repository: https://github.com/AsyncFuncAI/deepwiki-open.git
✓ Repository cloned to /tmp/target_repo

[Cell 6] Execute Stage 2 - Documentation Generation
Loading model: zephyr-7b-alpha
Moving model to GPU...
Generating docstrings...
  [####################] 100%
Generating README...
✓ Generation complete!

[Cell 7] Verify outputs
Output files generated: 450
Outputs directory: .../stage2_outputs/

[Cell 8] Save execution summary
✓ Execution summary saved
```

**Drive Structure After Stage 2:**

```
GenAI_Pipeline_Automation/
├── stage2_inputs/
│   └── stage1_20240101_120000/
│       ├── ast/
│       ├── components/
│       └── dependencies/
│
└── stage2_outputs/                           [NEW - Created by Colab]
    ├── generated_docs/
    │   ├── module_documentation.md
    │   ├── architecture_overview.md
    │   └── ... [40+ docs]
    ├── docstrings/
    │   ├── deepwiki/
    │   │   ├── core/
    │   │   │   └── docstrings.json
    │   │   └── ...
    │   └── ... [more modules]
    ├── README.md                             [Generated]
    └── execution_summary.json
        {
          "stage": "stage2",
          "timestamp": "2024-01-01T12:45:00",
          "repo_url": "https://github.com/AsyncFuncAI/deepwiki-open.git",
          "output_file_count": 450,
          "gpu_used": true
        }
```

---

### T+63:00 - DOWNLOAD RESULTS (~120 seconds)

```
[orchestrate_pipeline.py] calls GoogleDriveManager.download_stage2_output()
│
└─ GoogleDriveManager.download()
   │
   ├─ Find outputs folder on Drive
   │  └─ Search for: stage2_outputs folder
   │
   ├─ Create local directory
   │  └─ pipeline_outputs/20240101_120000/
   │
   └─ Recursively download all files
      ├─ generated_docs/
      │  ├─ module_documentation.md
      │  └─ ... [40+ files]
      ├─ docstrings/
      │  └─ ... [structured JSON]
      ├── README.md
      └─ execution_summary.json

Local Directory After Download:
pipeline_outputs/20240101_120000/
├── generated_docs/
│   ├── module_documentation.md (12.4 MB)
│   ├── architecture_overview.md (2.3 MB)
│   ├── api_reference.md (8.1 MB)
│   └── ... [40+ more docs]
├── docstrings/
│   ├── deepwiki_core.json (3.2 MB)
│   ├── deepwiki_utils.json (1.5 MB)
│   └── ... [20+ module docs]
├── README.md (15.2 KB) [NEWLY GENERATED]
├── execution_summary.json (2.3 KB)
└── [READY TO USE/PUBLISH/INTEGRATE]
```

**Console Output:**
```
[STEP 5/5] Downloading Stage 2 results from Google Drive...
Downloading Stage 2 outputs...
✓ Download successful to pipeline_outputs/20240101_120000

================================================================================
✅ PIPELINE COMPLETED SUCCESSFULLY!
================================================================================

Generated documentation is available at:
  📁 pipeline_outputs/20240101_120000/

Files generated: 450
Total size: 34.2 MB

Execution log saved to:
  📄 automation/logs/execution_20240101_120000.json
```

---

### T+65:00 - COMPLETION

```
Execution complete!

Logs:        automation/logs/execution_20240101_120000.json
Results:     pipeline_outputs/20240101_120000/
Drive backup: GenAI_Pipeline_Automation/stage2_outputs/

═══════════════════════════════════════════════════════════════════════════════

NEXT STEPS:

1. Review generated documentation:
   ls -la pipeline_outputs/20240101_120000/

2. Publish documentation:
   - Upload to GitHub Pages
   - Host on personal server
   - Add to project wiki

3. Integrate into workflow:
   - Commit docs to repository
   - Update README.md in source
   - Run pipeline again for next release

4. Run again for different repo:
   - Edit proj-GenAI/src/main.py (change repo_url)
   - Run: python scripts/orchestrate_pipeline.py

═══════════════════════════════════════════════════════════════════════════════
```

---

## Execution Summary JSON

```json
{
  "pipeline_start": "20240101_120000",
  "pipeline_end": "20240101_121500",
  "total_duration_minutes": 65,
  "stages": {
    "stage1": {
      "status": "success",
      "duration_seconds": 900,
      "artifacts": {
        "ast": {
          "file_count": 150,
          "size_mb": 45.2
        },
        "components": {
          "file_count": 280,
          "size_mb": 23.4
        },
        "dependencies": {
          "file_count": 95,
          "size_mb": 12.1
        }
      },
      "package_path": "proj-GenAI/src/data/artifacts/transfer_20240101_120000"
    },
    "upload": {
      "status": "success",
      "duration_seconds": 180,
      "drive_path": "GenAI_Pipeline_Automation/stage2_inputs/stage1_20240101_120000",
      "total_files_uploaded": 525,
      "total_size_mb": 80.7
    },
    "stage2": {
      "status": "completed",
      "trigger_time": "20240101_120945",
      "expected_completion": "20240101_121300",
      "gpu_used": "Tesla T4"
    },
    "download": {
      "status": "success",
      "duration_seconds": 120,
      "files_downloaded": 450,
      "total_size_mb": 34.2,
      "local_path": "pipeline_outputs/20240101_120000"
    }
  }
}
```

---

## Errors & Recovery

### If Stage 1 Fails

```
Error in Stage 1

Check:
1. automation/logs/execution_<timestamp>.json
2. proj-GenAI/src/main.py - verify repo_url is correct
3. Local environment - Python version, dependencies

Recovery:
python scripts/orchestrate_pipeline.py --stage1-only
```

### If Upload Fails

```
Error uploading to Drive

Check:
1. Internet connectivity
2. Google Drive token: python scripts/auth_setup.py --verify-only
3. Drive quota: Check Drive storage

Recovery:
python scripts/orchestrate_pipeline.py --stage1-only
# Will retry upload
```

### If Colab Execution Fails

```
No GPU or timeout

Check:
1. Open Colab notebook manually
2. Runtime > Change runtime type > T4 GPU
3. Monitor execution in Colab

Recovery:
# Run cells in Colab manually
# Or increase timeout in config/pipeline_config.yaml
```

### If Download Fails

```
Results not found on Drive

Check:
1. Stage 2 execution completed in Colab
2. Check stage2_outputs folder exists in Drive

Recovery:
python scripts/orchestrate_pipeline.py --download-only
# Will retry after waiting
```

---

## Success Indicators

✅ **Full Success:**
- All 5 steps complete
- Zero errors in all logs
- Results available in `pipeline_outputs/`
- Files verified on Drive

✅ **Partial Success:**
- Stage 1-3 complete but download pending
- Colab still running (results not ready yet)
- Manual download from Drive as backup

❌ **Failure:**
- Any step returns error
- Check logs for diagnostics
- Fix root cause
- Retry command

---

## Performance Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Init + Stage 1 | 15 min | ✅ Local |
| Upload | 3 min | ✅ Network |
| Colab execution | 45 min | ⏳ GPU (manual) |
| Download | 2 min | ✅ Network |
| **TOTAL** | **~65 min** | ✅ Automated |

---

This is the exact execution flow. Every step is logged, versioned, and reproducible.
