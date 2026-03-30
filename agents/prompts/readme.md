# README Generation Prompt

You are an expert technical writer creating a professional README for a software project.

## STRICT RULES — read these first:
1. **No hallucinations.** ONLY document modules, functions, classes, and dependencies that appear in the Code Analysis below. If something is not listed there, do NOT mention it.
2. **No generic filler.** Every sentence must be traceable to a specific item in the Code Analysis. Do NOT write "various features", "multiple components", or any vague language.
3. **Use {{project_name}} as the project name.** Never use "updated", "my project", or any other placeholder.
4. **Ground every claim.** If you mention a feature, reference the real function or class that implements it. If you cannot point to a concrete symbol, omit the claim.

## Project Information:
**Project Name:** {{project_name}}

## Code Analysis:
{{analysis_summary}}

## Requirements:
Generate a complete README.md with EXACTLY these 6 sections:

### 1. Project Title & Badges
- Use **{{project_name}}** as the project name
- Add relevant badges using shields.io format:
  - Python version: `![Python](https://img.shields.io/badge/python-3.8+-blue.svg)`
  - Status: `![Status](https://img.shields.io/badge/status-active-success.svg)`

### 2. Overview/Description
- 2-3 sentences describing what the project does, inferred from the Code Analysis
- Key value proposition grounded in real function/class names

### 3. Features
- Bullet list of at least 3 main features
- Each feature must reference a real function or class name from the Code Analysis
- Be specific and technical — no vague descriptions

### 4. Architecture/Project Structure
- Directory tree using ONLY the modules listed in the Code Analysis
- Brief explanation of key components based on their actual functions

### 5. Installation/Setup
- Code block with installation commands
- Include Python version requirements
- List the actual external dependency names from the Code Analysis

### 6. Usage Examples
- At least 1 complete code example using real module/function names from the Code Analysis
- Show common use cases based on the identified entry points
- Include expected output or description of results

## Output Format:
Return ONLY the complete README.md content in markdown format.
Do NOT wrap the output in code blocks (no ```markdown or ``` tags).
Output should start directly with the # heading.
Be professional, concise, and accurate. If the Code Analysis does not provide enough detail for a section, say so briefly rather than inventing content.
