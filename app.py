import os, json, time
from flask import Flask, request, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder="static")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")

DEFAULT_SETTINGS = {
    "app_name": "Veyra AI",
    "language": "English",
    "dark_mode": True,
    "tts": False,
    "context_size": 4096,
    "model_name": "gemma3:1b",
    "api_base": "http://127.0.0.1:11434/v1",
    "api_key": "",
    "search_provider": "exa",
    "search_api_key": "",
    "results_per_search": 5,
    "memory_lock": False,
    "memory_mapping": True,
    "weight_repacking": True,
    "auto_offload": True,
    "auto_navigate": True,
    "hf_token": "",
    "use_hf_token": False
}

def read_json(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback

def write_json(path, value):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2)

def settings():
    current = read_json(SETTINGS_FILE, {})
    merged = DEFAULT_SETTINGS | current
    return merged

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.get("/api/settings")
def get_settings():
    s = settings()
    # Never send credentials back to the browser.
    s["api_key"] = "configured" if s.get("api_key") else ""
    s["search_api_key"] = "configured" if s.get("search_api_key") else ""
    s["hf_token"] = "configured" if s.get("hf_token") else ""
    return jsonify(s)

@app.post("/api/settings")
def save_settings():
    incoming = request.get_json(force=True) or {}
    old = settings()
    allowed = set(DEFAULT_SETTINGS.keys())
    for k, v in incoming.items():
        if k not in allowed:
            continue
        # Preserve secret values when UI submits the "configured" placeholder.
        if k in ("api_key", "search_api_key", "hf_token") and v == "configured":
            continue
        old[k] = v
    write_json(SETTINGS_FILE, old)
    return jsonify({"ok": True})

@app.get("/api/chats")
def get_chats():
    return jsonify(read_json(CHATS_FILE, []))

@app.post("/api/chats")
def save_chats():
    write_json(CHATS_FILE, request.get_json(force=True) or [])
    return jsonify({"ok": True})

@app.post("/api/chat")
def chat():
    body = request.get_json(force=True) or {}
    messages = body.get("messages", [])
    s = settings()
    base = (s.get("api_base") or "").rstrip("/")
    if not base:
        return jsonify({"error": "Set an OpenAI-compatible API Base URL in Settings first."}), 400
    headers = {"Content-Type": "application/json"}
    if s.get("api_key"):
        headers["Authorization"] = "Bearer " + s["api_key"]
    payload = {
        "model": s.get("model_name") or "gemma3:1b",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }
    try:
        r = requests.post(base + "/chat/completions", headers=headers, json=payload, timeout=180)
        r.raise_for_status()
        data = r.json()
        answer = data["choices"][0]["message"]["content"]
        return jsonify({"answer": answer})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Could not reach the model endpoint. Check that your model server is running and the API Base URL/model name are correct. Details: " + str(e)}), 502
    except (KeyError, ValueError, TypeError):
        return jsonify({"error": "The endpoint returned an unexpected response. It must support OpenAI-compatible /chat/completions."}), 502

@app.post("/api/search")
def search():
    body = request.get_json(force=True) or {}
    query = (body.get("query") or "").strip()
    s = settings()
    provider = s.get("search_provider", "exa")
    key = s.get("search_api_key", "")
    if not query:
        return jsonify({"error": "Enter a search query."}), 400
    if not key:
        return jsonify({"error": "Add a search API key in Settings. Web search is optional and uses a third-party provider."}), 400
    try:
        if provider == "exa":
            r = requests.post("https://api.exa.ai/search",
                headers={"x-api-key": key, "Content-Type": "application/json"},
                json={"query": query, "numResults": int(s.get("results_per_search", 5)), "contents": {"text": True}},
                timeout=30)
            r.raise_for_status()
            raw = r.json().get("results", [])
            results = [{"title": x.get("title","Untitled"), "url": x.get("url",""), "snippet": (x.get("text") or "")[:800]} for x in raw]
        else:
            return jsonify({"error": "This starter currently implements Exa search. Choose Exa or extend app.py for another provider."}), 400
        return jsonify({"results": results})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Search request failed: " + str(e)}), 502

@app.get("/api/health")
def health():
    return jsonify({"ok": True, "time": int(time.time())})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
