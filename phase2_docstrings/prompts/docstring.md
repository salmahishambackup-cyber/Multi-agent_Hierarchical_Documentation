# Docstring Generation Prompt

You are an expert Python documentation writer. Generate a clear, concise Google-style docstring for the following code.

## Requirements:
- Use Google-style format (Args, Returns, Raises sections)
- Be concise but complete
- Include type information
- Describe WHAT the code does AND WHY it exists (business purpose)
- For functions: describe parameters and return value
- For classes: describe purpose and key attributes
- For modules: describe overall purpose and the business problem it solves
- Capture the business intent — e.g., "Matches a pool of candidates to a reference cohort" not just "Processes data"
- Infer domain context from variable/parameter names (e.g., ARPU → telecom revenue, WL/PL → whitelist/pool list matching)

## Code Context:
{{context}}

## Code to Document:
```python
{{code}}
```

## Output Format:
Return ONLY the docstring body — the text that goes between the triple quotes.
Do NOT include:
- The function definition (e.g., `def func_name(...):`)
- The class definition (e.g., `class ClassName:`)
- Triple quotes (`"""`)
- Markdown code fences (``` ```python ```)

Start with a one-line summary that captures the business purpose.
Then add technical details (Args, Returns, Raises) as needed.
Do NOT start the summary with generic phrases like "This function" or "This module" — start with an action verb or noun phrase.
