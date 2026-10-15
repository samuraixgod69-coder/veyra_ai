# Veyra AI — starter project

A responsive, dark/glass AI chat app starter inspired by the features in your screenshots. It includes:
- Chat UI and saved chat history
- Settings for model name, context size, language, dark mode and text-to-speech
- Memory/model-loading preference toggles (saved as preferences; they do not control a model runtime by themselves)
- OpenAI-compatible chat endpoint support
- Optional Exa web search with API key
- Hugging Face token field (stored locally; not yet used to download/run models)
- Export chat history to JSON
- Mobile-friendly layout

## Run on Android / Termux

```bash
pkg update
pkg install python
cd ~/veyra-ai
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Connect a model

This starter does not bundle a language model. It connects to a model server that supports the OpenAI-compatible endpoint `/v1/chat/completions`.

Example settings for an Ollama server:
- API Base URL: `http://127.0.0.1:11434/v1`
- Model name: the exact model tag installed on that server (for example `gemma3:1b`)
- API key: leave blank for a local server

**Important:** Ollama may not run directly on your Android/Termux setup without extra work. If your model runs on another device, use that device's reachable LAN address and make sure the server allows LAN access. Do not expose an unauthenticated model server to the public internet.

## Web search

In Settings, choose Exa and add your own Exa API key. Search requests are sent to Exa, so queries leave your device. Do not paste private data into web search.

## Security / limitations

- This is a starter project, not a complete clone of PocketPal.
- Context size is a requested preference only; the model server determines the real maximum.
- Memory lock, memory mapping, weight repacking and auto offload are stored UI preferences only. Actual support depends on the inference runtime and cannot be enabled by a generic web app.
- Hugging Face token is stored in local `data/settings.json`; keep this folder private. This starter does not download gated models.
- Do not deploy this development server publicly as-is. Add authentication, HTTPS, rate limits, and secure secret storage first.
