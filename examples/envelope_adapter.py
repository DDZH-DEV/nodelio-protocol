"""档 B 参考：把任意 JSON 收成 Content Envelope。不要并进 NodeLio SERVER。

用法：python envelope_adapter.py < upstream.json
"""
import json
import sys


def to_envelope(raw: dict, app_id: str = "custom.app") -> dict:
    if raw.get("schema_version") == 1 and "content" in raw:
        raw.setdefault("status", "ok")
        raw.setdefault("app_id", app_id)
        return raw
    items = raw.get("items") or raw.get("data") or []
    content = []
    if isinstance(items, list):
        for i, it in enumerate(items):
            if isinstance(it, str):
                content.append({"type": "text", "id": f"t{i+1}", "text": it})
            elif isinstance(it, dict):
                content.append({
                    "type": "list_item",
                    "id": str(it.get("id") or f"i{i+1}"),
                    "title": str(it.get("title") or it.get("name") or ""),
                    "subtitle": str(it.get("subtitle") or it.get("summary") or ""),
                })
    if not content and raw.get("text"):
        content.append({"type": "text", "id": "t1", "text": str(raw["text"])})
    return {
        "schema_version": 1,
        "app_id": app_id,
        "status": "ok",
        "content": content,
        "display": {
            "card_type": "list" if any(c.get("type") == "list_item" for c in content) else "plain_result",
            "title": str(raw.get("title") or "结果"),
            "preferred_surface": "card",
            "max_items": 8,
        },
        "spoken": {"text": str(raw.get("spoken") or "已返回结果")},
    }


if __name__ == "__main__":
    src = json.load(sys.stdin)
    json.dump(to_envelope(src), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
