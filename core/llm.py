from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass
from typing import Optional, Any, Dict

from google import genai  # pip install google-genai


@dataclass
class LLMConfig:
    mode: str = "mock"  # "mock" or "vertex"
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    vertex_model: str = "gemini-1.5-flash"  # safer default for quotas
    temperature: float = 0.2
    max_output_tokens: int = 1600

    # retry controls
    max_retries: int = 7
    max_backoff_seconds: int = 30


class LLMClient:
    def __init__(self, cfg: LLMConfig):
        self.cfg = cfg
        self._client = None

    def set_runtime(self, mode: str, model: str, temperature: float):
        self.cfg.mode = mode
        self.cfg.vertex_model = model
        self.cfg.temperature = temperature

    def _get_vertex_client(self):
        if self._client is not None:
            return self._client

        project = self.cfg.vertex_project or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = self.cfg.vertex_location or os.getenv("GOOGLE_CLOUD_LOCATION") or "us-central1"

        if not project:
            raise RuntimeError("Missing GOOGLE_CLOUD_PROJECT. Set it as an env var.")

        # Vertex AI client
        self._client = genai.Client(vertexai=True, project=project, location=location)
        return self._client

    @staticmethod
    def _strip_json_fences(raw: str) -> str:
        s = (raw or "").strip()
        if s.startswith("```"):
            # remove ```json ... ``` or ``` ... ```
            s = s.split("\n", 1)[-1]
            if s.endswith("```"):
                s = s.rsplit("```", 1)[0]
        return s.strip()

    @staticmethod
    def _is_429(err: Exception) -> bool:
        msg = str(err)
        return (
            "RESOURCE_EXHAUSTED" in msg
            or "429" in msg
            or "rate limit" in msg.lower()
            or "quota" in msg.lower()
        )

    def generate_json(self, system: str, user: str) -> Dict[str, Any]:
        if self.cfg.mode == "mock":
            return {"mock": True, "text": f"SYSTEM: {system[:60]} | USER: {user[:120]}"}

        client = self._get_vertex_client()
        prompt = f"SYSTEM:\n{system}\n\nUSER:\n{user}\n"

        last_err: Optional[Exception] = None

        for attempt in range(self.cfg.max_retries):
            try:
                # Try strict JSON response first
                resp = client.models.generate_content(
                    model=self.cfg.vertex_model,
                    contents=prompt,
                    config={
                        "temperature": self.cfg.temperature,
                        "max_output_tokens": self.cfg.max_output_tokens,
                        "response_mime_type": "application/json",
                    },
                )
                raw = getattr(resp, "text", "") or ""
                raw = self._strip_json_fences(raw)
                return json.loads(raw)

            except Exception as e:
                last_err = e

                # If strict JSON failed, try plain text once per attempt, then parse
                try:
                    resp = client.models.generate_content(
                        model=self.cfg.vertex_model,
                        contents=prompt,
                        config={
                            "temperature": self.cfg.temperature,
                            "max_output_tokens": self.cfg.max_output_tokens,
                        },
                    )
                    raw = getattr(resp, "text", "") or ""
                    raw = self._strip_json_fences(raw)
                    return json.loads(raw)
                except Exception as e2:
                    last_err = e2

                # Backoff strategy (especially for 429)
                if self._is_429(last_err):
                    # exponential backoff + jitter
                    base = min(2 ** attempt, self.cfg.max_backoff_seconds)
                    sleep_s = base + random.random()  # jitter prevents sync retry storms
                    time.sleep(sleep_s)
                    continue

                # For non-429 transient issues, small delay then retry
                time.sleep(0.8 + random.random())
                continue

        # Final fallback: do NOT crash app — return error JSON
        return {
            "error": True,
            "type": "LLM_CALL_FAILED",
            "message": "LLM call failed after retries (likely quota/rate limit).",
            "details": str(last_err)[:800] if last_err else "Unknown error",
            "hint": "Try gemini-1.5-flash, reduce domains, or wait 1–2 minutes.",
        }