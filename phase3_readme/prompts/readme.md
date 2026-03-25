# README Generation Prompt

You are an expert technical writer creating a professional README for a software project.

## Project Information:
**Project Name:** {{project_name}}

## Code Analysis:
{{analysis_summary}}

## Requirements:
Generate a complete README.md with EXACTLY these 6 sections:

### 1. Project Title & Badges
- Use **{{project_name}}** as the project name (do NOT use "updated" or any placeholder)
- Add relevant badges using shields.io format:
  - Python version: `![Python](https://img.shields.io/badge/python-3.8+-blue.svg)`
  - License: `![License](https://img.shields.io/badge/license-MIT-green.svg)`
  - Status: `![Status](https://img.shields.io/badge/status-active-success.svg)`

### 2. Overview/Description
- 2-3 sentences describing the **business purpose** of the project (what problem it solves)
- Infer the purpose from the module names, function names, and class names provided above
- Mention the domain/industry context if identifiable (e.g., telecom, finance, ML pipelines)
- Key value proposition from a user/business perspective

### 3. Features
- At least 3-5 features linked to **actual functions and classes** from the Code Analysis above
- For each feature, reference the real function or class name (e.g., "`evaluate()` — runs model quality assessment")
- Be specific about what those functions do based on their names and context
- Do NOT invent generic features like "Feature 1: Analyzes data" — use real names

### 4. Architecture/Project Structure
- Show the actual file structure using the modules listed in the Code Analysis
- Briefly explain each module's role based on its name and functions
- Include a directory tree OR component diagram

### 5. Installation/Setup
- Code block with installation commands (`pip install -r requirements.txt`)
- Include Python version requirements
- List the key external dependencies found in Code Analysis

### 6. Usage Examples
- At least 1 complete code example using the actual module/function names from Code Analysis
- Show the main entry point or primary workflow
- Include expected output or description of results

## Output Format:
Return ONLY the complete README.md content in markdown format.
Do NOT wrap the output in code blocks (no ```markdown or ``` tags).
Do NOT use "updated" or any placeholder names — always use {{project_name}}.
Output should start directly with the # heading.
Be professional, concise, and accurate. Ground every claim in the actual code analysis provided.
