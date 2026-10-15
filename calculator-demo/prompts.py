CALCULATOR_PROMPT = """Convert the following natural-language math request into a mathematical expression.

Use only numbers, parentheses, and standard operators (+, -, *, /, **, %).
Return only the expression, with no explanation, no equals sign, and no surrounding text or formatting.
"%" means modulo only. Never use "%" to represent a percentage.
Convert percentages into multiplication and division by 100.

Example:
25% of 500 -> 500 * 25 / 100

Request: {user_input}
Expression:"""
