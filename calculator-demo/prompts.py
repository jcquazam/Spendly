CALCULATOR_PROMPT = """Convert the following natural-language math request into a mathematical expression.

Use only numbers, parentheses, and standard operators (+, -, *, /, **, %).
"%" means modulo only. Never use "%" to represent a percentage.
Convert percentages into multiplication and division by 100.

Return valid JSON in exactly this shape, with no explanation, no markdown, and no text outside the JSON:
{{
  "expression": "..."
}}
The "expression" value must contain only the mathematical expression, with no equals sign.

Example:
Request: 25% of 500
{{
  "expression": "500 * 25 / 100"
}}

Request: {user_input}
"""
