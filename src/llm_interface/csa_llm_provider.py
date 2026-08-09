"""OpenAI-compatible CSA generation client using the MetaOp LLM config."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from types import SimpleNamespace

DEFAULT_CSA_LLM_MODEL = "gpt-5.4-mini"

class CSAChatClient:
    def __init__(self, base_url, api_key, model=DEFAULT_CSA_LLM_MODEL, timeout=240):
        normalized = str(base_url).rstrip("/")
        if not re.search(r"/v\d+(?:/|$)", normalized):
            normalized += "/v1"
        self.url = normalized + "/chat/completions"
        self.models_url = normalized + "/models"
        self.api_key = api_key
        self.model = model
        self.timeout = int(timeout)

    def __call__(self, prompt):
        payload = json.dumps({
            "model": self.model,
            "temperature": 0,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"CSA LLM HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"CSA LLM request failed: {exc.reason}") from exc
        usage = body.get("usage", {})
        callback = SimpleNamespace(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
        return body["choices"][0]["message"]["content"], callback

    def list_models(self):
        request = urllib.request.Request(
            self.models_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError) as exc:
            raise RuntimeError(f"failed to list CSA LLM models: {exc}") from exc
        return [item["id"] for item in body.get("data", []) if item.get("id")]


def load_csa_chat_client(config_path, model=None):
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    api_key = os.getenv("CSA_LLM_API_KEY") or config.get("key") or config.get("api_key")
    base_url = os.getenv("CSA_LLM_BASE_URL") or config.get("base_url")
    selected_model = model or os.getenv("CSA_LLM_MODEL") or config.get("model") or DEFAULT_CSA_LLM_MODEL
    if not api_key:
        raise ValueError("CSA LLM API key is not configured")
    if not base_url:
        raise ValueError("CSA LLM base URL is not configured")
    return CSAChatClient(base_url, api_key, selected_model)
