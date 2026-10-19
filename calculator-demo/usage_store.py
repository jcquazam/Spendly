import json
import os
import tempfile

USAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage_metrics.json")


def load_usage():
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            usage = json.load(f)
    except (OSError, ValueError):
        return {}
    return usage if isinstance(usage, dict) else {}


def save_usage(usage):
    directory = os.path.dirname(USAGE_FILE)
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix="usage_metrics.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(usage, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, USAGE_FILE)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def record_request(tenant_id, model):
    usage = load_usage()
    tenant = usage.get(tenant_id)
    if not isinstance(tenant, dict):
        tenant = {"request_count": 0}
        usage[tenant_id] = tenant
    count = tenant.get("request_count")
    tenant["request_count"] = (count if isinstance(count, int) else 0) + 1
    tenant["last_model"] = model
    save_usage(usage)
