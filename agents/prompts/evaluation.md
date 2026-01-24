# Documentation Evaluation Prompt

You are an expert documentation reviewer. Evaluate the following README documentation.

## README Content:
{{readme_content}}

## Evaluation Criteria:
Score each aspect from 0-10:

### 1. Clarity (0-10)
- Is the documentation easy to understand?
- Is the language clear and unambiguous?
- Are technical terms explained?

### 2. Completeness (0-10)
- Are all required sections present?
- Is each section adequately filled?
- Are there any missing critical details?

### 3. Consistency (0-10)
- Is formatting consistent throughout?
- Is terminology used consistently?
- Is the tone consistent?

### 4. Usability (0-10)
- Can a new user get started quickly?
- Are examples practical and runnable?
- Is installation process clear?

## Output Format:
Return a JSON object with this structure:
```json
{
  "clarity": 8,
  "completeness": 9,
  "consistency": 7,
  "usability": 8,
  "overall": 8.0,
  "strengths": ["Clear examples", "Complete installation guide"],
  "suggestions": ["Add more architecture details", "Include troubleshooting section"]
}
```

Return ONLY the JSON object, no additional text.
