import json
import os

from openai import OpenAI

MODEL = "gpt-6-luna"
MAX_TOKENS = 50

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


def get_model_response(prompt):
    if prompt in RESPONSE_CACHE:
        print("CACHE HIT")
        return RESPONSE_CACHE[prompt]

    print("CACHE MISS")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.responses.create(
        model=MODEL,
        input=prompt,
        max_output_tokens=MAX_TOKENS,
    )
    text = response.output_text.strip()
    RESPONSE_CACHE[prompt] = text
    _save_cache()
    return text


def stream_model_response(prompt):
    if prompt in RESPONSE_CACHE:
        print("CACHE HIT")
        yield RESPONSE_CACHE[prompt]
        return

    print("CACHE MISS")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    stream = client.responses.create(
        model=MODEL,
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
