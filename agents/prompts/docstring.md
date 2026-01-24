# Docstring Generation Prompt

You are an expert Python documentation writer. Generate a clear, concise Google-style docstring for the following code.

## Requirements:
- Use Google-style format (Args, Returns, Raises sections)
- Be concise but complete
- Include type information
- Describe what the code does, not how it works
- For functions: describe parameters and return value
- For classes: describe purpose and key attributes
- For modules: describe overall purpose

## Code Context:
{{context}}

## Code to Document:
```python
{{code}}
```

## Output Format:
Return ONLY the docstring content (without the triple quotes). Start with a one-line summary, then add details as needed.
