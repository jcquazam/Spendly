import ast

from prompts import CALCULATOR_PROMPT

ALLOWED_CHARACTERS = set("0123456789 +-*/%().")
MAX_EXPONENT = 100

# AST node types that make up a plain arithmetic expression
ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.UAdd,
    ast.USub,
)


def validate_expression(expression):
    """Return True only if the expression uses allowed characters and is well-formed math.

    The expression is parsed with ast but never evaluated.
    """
    if not expression.strip():
        return False
    if not all(char in ALLOWED_CHARACTERS for char in expression):
        return False
    try:
        tree = ast.parse(expression.strip(), mode="eval")
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            return False
        # Stop expressions like 9**9**9 that would be enormous if ever evaluated
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if not (isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant)):
                return False
            if abs(node.right.value) > MAX_EXPONENT:
                return False
    return True

# Set to True to skip the Anthropic API and use a fake response instead.
# Set to False to call the real API (needs the ANTHROPIC_API_KEY environment variable).
DEMO_MODE = True

user_input = input("Enter a math question: ")
prompt = CALCULATOR_PROMPT.format(user_input=user_input)

if DEMO_MODE:
    # Pretend the model answered with this expression
    expression = "500 * 25 / 100"
else:
    # Imported here so demo mode works without the anthropic package installed
    import anthropic

    # Reads the API key from the ANTHROPIC_API_KEY environment variable
    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=16000,
        messages=[{"role": "user", "content": prompt}],
    )

    # The response is a list of content blocks; keep the text one
    expression = ""
    for block in response.content:
        if block.type == "text":
            expression = block.text.strip()

if validate_expression(expression):
    print(expression)
else:
    print("Invalid model response")
