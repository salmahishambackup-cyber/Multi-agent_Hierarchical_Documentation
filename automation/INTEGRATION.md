# INTEGRATION GUIDE

## How to Integrate GenAI Pipeline Automation Into Your Workflow

### For Research Teams

#### Scenario: Documenting a New Repository

1. **Change the target repository:**
   ```python
   # Edit proj-GenAI/src/main.py
   repo_url = "https://github.com/YOUR_OWNER/YOUR_REPO.git"
   ```

2. **Run pipeline:**
   ```bash
   cd automation
   python scripts/orchestrate_pipeline.py
   ```

3. **Get documentation:**
   ```bash
   # Results in: pipeline_outputs/<timestamp>/
   ```

---

### For CI/CD Integration

#### GitHub Actions Example

```yaml
# .github/workflows/auto-docs.yml
name: Auto-generate Documentation

on:
  push:
    branches: [main]
    paths: ['src/**']

jobs:
  document:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r automation/requirements.txt
      
      - name: Authenticate
        env:
          GCP_CREDENTIALS: ${{ secrets.GCP_CREDENTIALS }}
        run: |
          echo "$GCP_CREDENTIALS" > automation/config/credentials.json
      
      - name: Run pipeline
        run: |
          cd automation
          python scripts/orchestrate_pipeline.py
      
      - name: Upload docs
        uses: actions/upload-artifact@v3
        with:
          name: generated-docs
          path: pipeline_outputs/*/
```

---

### For Batch Processing

#### Process Multiple Repositories

```python
# process_repos.py
import subprocess
from pathlib import Path

repos = [
    "https://github.com/org/repo1.git",
    "https://github.com/org/repo2.git",
    "https://github.com/org/repo3.git",
]

for repo_url in repos:
    # Update proj-GenAI/src/main.py
    # Run pipeline
    # Save results
    
    print(f"Processing: {repo_url}")
    subprocess.run([
        "python", "automation/scripts/orchestrate_pipeline.py"
    ], check=True)
```

---

### For Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y git
COPY automation/requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Set entry point
ENTRYPOINT ["python", "automation/scripts/orchestrate_pipeline.py"]
CMD []
```

**Usage:**
```bash
docker build -t genai-pipeline .
docker run -v /local/path:/output genai-pipeline
```

---

### For Scheduled Execution

#### Windows Task Scheduler

1. Create batch file: `run_pipeline.bat`
   ```batch
   @echo off
   cd /d "C:\path\to\project"
   cd automation
   python scripts/orchestrate_pipeline.py >> logs\scheduled_run.log 2>&1
   ```

2. Create task:
   - Task Scheduler > Create Basic Task
   - Name: "GenAI Pipeline"
   - Trigger: Daily at 2:00 AM
   - Action: Start program `run_pipeline.bat`

#### Linux/Mac (Cron)

```bash
# Add to crontab -e
0 2 * * * /path/to/project/automation/run_pipeline.sh >> /var/log/pipeline.log 2>&1
```

Create `run_pipeline.sh`:
```bash
#!/bin/bash
cd /path/to/project/automation
python scripts/orchestrate_pipeline.py
```

---

### For Web Integration

#### Flask Web Service

```python
# web_app.py
from flask import Flask, jsonify, request
import subprocess
from pathlib import Path

app = Flask(__name__)

@app.route('/api/pipeline/run', methods=['POST'])
def run_pipeline():
    """Trigger pipeline via HTTP."""
    
    repo_url = request.json.get('repo_url')
    
    # Update repo in proj-GenAI/src/main.py
    # Call orchestrator
    result = subprocess.run([
        'python', 'automation/scripts/orchestrate_pipeline.py'
    ], capture_output=True, text=True)
    
    return jsonify({
        'status': 'success' if result.returncode == 0 else 'failed',
        'message': result.stdout
    })

@app.route('/api/pipeline/status/<timestamp>', methods=['GET'])
def get_status(timestamp):
    """Check pipeline status."""
    
    log_file = Path(f'automation/logs/execution_{timestamp}.json')
    if log_file.exists():
        import json
        with open(log_file) as f:
            data = json.load(f)
        return jsonify(data)
    
    return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
```

---

### For Monitoring & Alerts

#### Slack Notifications

```python
# notify_slack.py
import json
import requests
from pathlib import Path

def send_slack_notification(execution_log_path: str, webhook_url: str):
    """Send execution summary to Slack."""
    
    with open(execution_log_path) as f:
        log = json.load(f)
    
    message = {
        "text": "GenAI Pipeline Execution Report",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Pipeline*: `{log['pipeline_start']}`\n*Status*: `{log['stages']['stage1']['status']}`"
                }
            }
        ]
    }
    
    requests.post(webhook_url, json=message)

# Usage in orchestrator
send_slack_notification('automation/logs/latest.json', $SLACK_WEBHOOK)
```

---

### For Cost Optimization

#### Colab Spot Instances (Future)

```python
# Use Colab API to select cost-optimized instances
# Requires Colab Pro + API access
```

#### Model Selection for Different Hardware

```python
# Adapt model based on available GPU
if gpu_memory < 8:
    model = "distilbert-base-uncased"  # Smaller model
else:
    model = "zephyr-7b-alpha"  # Full model
```

---

## Common Integration Patterns

### Pattern 1: Documentation as Part of Release

```yaml
# On release creation, auto-generate docs
on:
  release:
    types: [created]
```

### Pattern 2: Continuous Documentation

```yaml
# Weekly documentation refresh
on:
  schedule:
    - cron: '0 2 * * 0'  # Sunday 2 AM
```

### Pattern 3: On-Demand via UI

```python
# Serverless function (AWS Lambda, Google Cloud Functions)
def trigger_pipeline(event, context):
    subprocess.run(['python', 'scripts/orchestrate_pipeline.py'])
    return {'statusCode': 200}
```

---

## Troubleshooting Integration

### Issue: Token expires in CI/CD

**Solution:** Store refresh token in secrets, auto-refresh in orchestrator

```python
# In orchestrator
if token_expired():
    refresh_token()
    save_new_token_to_secrets()
```

### Issue: Large repos timeout on Colab

**Solution:** Increase timeout or split processing

```yaml
# In pipeline_config.yaml
max_runtime_seconds: 7200  # 2 hours
```

### Issue: Drive quota exceeded

**Solution:** Implement cleanup logic

```python
# Delete old outputs after 30 days
def cleanup_old_outputs():
    drive_manager.delete_outputs_before(days=30)
```

---

## Best Practices

1. **Version your credentials:**
   - Store `credentials.json` in secret management system
   - Never commit to Git

2. **Monitor execution:**
   - Set up alerts for failures
   - Track cost/quota usage

3. **Test first:**
   - Use `--stage1-only` to test local changes
   - Don't run full pipeline on every commit

4. **Cache intermediate results:**
   - Keep Stage 1 outputs on Drive
   - Reuse for multiple Stage 2 runs

5. **Document your setup:**
   - Record which model you use
   - Document custom parameters
   - Keep execution logs

---

## Support

For issues:
- Check `automation/logs/` for execution details
- Review `ARCHITECTURE.md` for design decisions
- Refer to `README.md` for detailed documentation
