# README Generation Prompt

You are an expert technical writer creating a professional README for a software project.

## Project Information:
**Project Name:** {{project_name}}

## Code Analysis:
{{analysis_summary}}

## Requirements:
Generate a complete README.md with EXACTLY these 6 sections:

### 1. Project Title & Badges
- Project name as H1
- Add relevant badges using shields.io format:
  - Python version: `![Python](https://img.shields.io/badge/python-3.8+-blue.svg)`
  - License: `![License](https://img.shields.io/badge/license-MIT-green.svg)`
  - Status: `![Status](https://img.shields.io/badge/status-active-success.svg)`

### 2. Overview/Description
- 2-3 sentences describing what the project does
- Key value proposition

### 3. Features
- Bullet list of at least 3 main features
- Be specific and technical

### 4. Architecture/Project Structure
- Directory tree OR component diagram
- Brief explanation of key components

### 5. Installation/Setup
- Code block with installation commands
- Include Python version requirements
- List dependencies

### 6. Usage Examples
- At least 1 complete code example
- Show common use cases
- Include expected output

## Output Format:
Return ONLY the complete README.md content in markdown format. 
Do NOT wrap the output in code blocks (no ```markdown or ``` tags).
Output should start directly with the # heading.
Be professional, concise, and accurate.
