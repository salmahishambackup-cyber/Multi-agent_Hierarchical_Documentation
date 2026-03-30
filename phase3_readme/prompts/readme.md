# README Generation Prompt

You are an expert technical writer creating a professional README for a software project.

## STRICT RULES — read these first:
1. **No hallucinations.** ONLY document modules, functions, classes, and dependencies that appear in the Code Analysis below. If something is not listed there, do NOT mention it.
2. **No generic filler.** Every sentence must be traceable to a specific item in the Code Analysis. Do NOT write "various features", "multiple components", or any vague language.
3. **Use {{project_name}} as the project name.** Never use "updated", "my project", or any other placeholder.
4. **Ground every claim.** If you mention a feature, reference the real function or class that implements it (e.g., "`extract_ast_info()` in `analyzer/ast_extractor.py`"). If you cannot point to a concrete symbol, omit the claim.

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
- 2-3 sentences describing the **business purpose** of the project (what problem it solves)
- Infer the purpose ONLY from the module names, function names, class names, and descriptions provided in the Code Analysis
- Mention the domain/industry context only if clearly identifiable from function/class names
- Key value proposition from a user/business perspective

### 3. Features
- At least 3-5 features, each linked to a **real function or class** from the Code Analysis
- Format: "`function_name()` in `module_path` — one-line description from docstring"
- Do NOT invent features. Each feature must map to a symbol in the Code Analysis.

### 4. Architecture/Project Structure
- Show the actual file structure using ONLY the modules listed in the Code Analysis
- Briefly explain each module's role using the function descriptions provided
- Do NOT add files or directories that are not in the Code Analysis

### 5. Installation/Setup
- Code block with installation commands
- Include Python version requirements
- List the **actual** external dependencies from the Code Analysis by name

### 6. Usage Examples
- At least 1 complete code example using the **actual** module/function names from Code Analysis
- Show the main entry point or primary workflow (if identified in the Code Analysis)
- Include expected output or description of results based on function return types

## Output Format:
Return ONLY the complete README.md content in markdown format.
Do NOT wrap the output in code blocks (no ```markdown or ``` tags).
Output should start directly with the # heading.
Be professional, concise, and accurate. If the Code Analysis does not provide enough information for a section, say so briefly rather than inventing content.
