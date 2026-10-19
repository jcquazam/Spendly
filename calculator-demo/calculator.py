import ast
import json
import operator

from openai import APITimeoutError, OpenAIError

from llm_service import get_model_response, stream_model_response
from prompts import CALCULATOR_PROMPT
from state_store import save_state

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


BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def evaluate_expression(expression):
    """Evaluate an arithmetic expression that has already passed validate_expression().

    Walks the ast directly and never uses eval(). Raises ZeroDivisionError on
    division by zero.
    """

    def _evaluate(node):
        if isinstance(node, ast.Expression):
            return _evaluate(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.UnaryOp):
            return UNARY_OPERATORS[type(node.op)](_evaluate(node.operand))
        if isinstance(node, ast.BinOp):
            return BINARY_OPERATORS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
        raise ValueError("Unsupported expression")

    return _evaluate(ast.parse(expression.strip(), mode="eval"))


def should_stream(user_input):
    return len(user_input) > 200


# Set to True to skip the real API and use a fake response instead.
# Set to False to call the real API (needs the OPENAI_API_KEY environment variable).
DEMO_MODE = True

user_input = input("Enter a math question: ")
prompt = CALCULATOR_PROMPT.format(user_input=user_input)

streamed = False

if DEMO_MODE:
    try:
        expression = get_model_response(prompt, routing_text=user_input)
    except APITimeoutError:
        print("Model request timed out")
        raise SystemExit(1)
    except OpenAIError:
        print("Model request failed")
        raise SystemExit(1)
else:
    # Print each chunk as it arrives and collect them into the full expression
    chunks = []
    try:
        for chunk in stream_model_response(prompt, routing_text=user_input):
            print(chunk, end="", flush=True)
            chunks.append(chunk)
    except APITimeoutError:
        print("Model request timed out")
        raise SystemExit(1)
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
    try:
        result = evaluate_expression(expression)
    except ZeroDivisionError:
        print("Calculation error: division by zero")
        raise SystemExit(1)
    except ValueError:
        print("Calculation error")
        raise SystemExit(1)
    print(f"Result: {result}")
    save_state({
        "last_user_input": user_input,
        "last_expression": expression,
        "last_result": result
    })
else:
    print("Invalid model response")
