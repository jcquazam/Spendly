import ast
import json

from llm_service import get_model_response, stream_model_response
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

# Set to True to skip the real API and use a fake response instead.
# Set to False to call the real API (needs the OPENAI_API_KEY environment variable).
DEMO_MODE = True

user_input = input("Enter a math question: ")
prompt = CALCULATOR_PROMPT.format(user_input=user_input)

streamed = False

if DEMO_MODE:
    expression = get_model_response(prompt)
else:
    # Print each chunk as it arrives and collect them into the full expression
    chunks = []
    try:
        for chunk in stream_model_response(prompt):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
    except Exception:
        print("Model request failed")
        raise SystemExit(1)
    print()
    expression = "".join(chunks).strip()
    streamed = True

try:
    expression = json.loads(expression)["expression"]
except (json.JSONDecodeError, TypeError, KeyError):
    print("Invalid model response")
    raise SystemExit(1)

if isinstance(expression, str) and validate_expression(expression):
    if not streamed:
        print(expression)
else:
    print("Invalid model response")
