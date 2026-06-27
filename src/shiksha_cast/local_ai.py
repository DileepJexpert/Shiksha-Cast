from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


class LocalAIUnavailable(RuntimeError):
    """The configured local model service is not reachable or usable."""


@dataclass(frozen=True)
class OllamaModel:
    name: str
    size: int | None = None
    modified_at: str | None = None


def ollama_available(url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/api/tags", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def list_ollama_models(url: str) -> list[OllamaModel]:
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/api/tags", timeout=5) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise LocalAIUnavailable(f"Could not reach Ollama at {url}. Is it running? ({e.reason})") from e
    except Exception as e:
        raise LocalAIUnavailable(f"Could not list Ollama models at {url}: {e}") from e

    models = []
    for item in payload.get("models", []):
        if isinstance(item, dict) and item.get("name"):
            models.append(
                OllamaModel(
                    name=str(item["name"]),
                    size=item.get("size"),
                    modified_at=item.get("modified_at"),
                )
            )
    return models


def ollama_generate_json(
    url: str,
    model: str,
    prompt: str,
    *,
    temperature: float = 0.6,
    timeout_s: int = 900,
) -> str:
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{url.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            payload = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        if "not found" in detail.lower() or e.code == 404:
            raise LocalAIUnavailable(
                f"Ollama model '{model}' not found. Pull it first: ollama pull {model}"
            ) from e
        raise LocalAIUnavailable(f"Ollama error (HTTP {e.code}): {detail}") from e
    except urllib.error.URLError as e:
        raise LocalAIUnavailable(f"Could not reach Ollama at {url}. Is it running? ({e.reason})") from e

    response = payload.get("response", "")
    if not response:
        raise LocalAIUnavailable("Ollama returned an empty response.")
    return str(response)
