import json
import os

from openai import OpenAI, OpenAIError

FAST_MODEL = "gpt-6-luna"
STRONG_MODEL = "gpt-6.1-sol"
MAX_TOKENS = 50
TIMEOUT_SECONDS = 10

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "response_cache.json")


def _load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_cache():
    tmp_path = CACHE_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(RESPONSE_CACHE, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, CACHE_FILE)


RESPONSE_CACHE = _load_cache()


def choose_model(prompt):
    if len(prompt) > 500:
        return STRONG_MODEL
    return FAST_MODEL


def get_fallback_model(primary_model):
    if primary_model == FAST_MODEL:
        return STRONG_MODEL
    if primary_model == STRONG_MODEL:
        return FAST_MODEL
    return None


def get_model_response(prompt, routing_text=None):
    if prompt in RESPONSE_CACHE:
        print("CACHE HIT")
        return RESPONSE_CACHE[prompt]

    print("CACHE MISS")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=TIMEOUT_SECONDS)
    model = choose_model(routing_text if routing_text is not None else prompt)
    print(f"MODEL: {model}")
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            max_output_tokens=MAX_TOKENS,
        )
    except OpenAIError:
        fallback_model = get_fallback_model(model)
        if fallback_model is None:
            raise
        print(f"PRIMARY MODEL FAILED: {model}")
        print(f"FALLBACK MODEL: {fallback_model}")
        response = client.responses.create(
            model=fallback_model,
            input=prompt,
            max_output_tokens=MAX_TOKENS,
        )
    text = response.output_text.strip()
    RESPONSE_CACHE[prompt] = text
    _save_cache()
    return text


def stream_model_response(prompt, routing_text=None):
    if prompt in RESPONSE_CACHE:
        print("CACHE HIT")
        yield RESPONSE_CACHE[prompt]
        return

    print("CACHE MISS")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=TIMEOUT_SECONDS)
    model = choose_model(routing_text if routing_text is not None else prompt)
    print(f"MODEL: {model}")
    stream =client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=MAX_TOKENS,
        stream=True,
    )
    chunks = []
    for event in stream:
        if event.type == "response.output_text.delta":
            chunks.append(event.delta)
            yield event.delta
    RESPONSE_CACHE[prompt] = "".join(chunks)
    _save_cache()
