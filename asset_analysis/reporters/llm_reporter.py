from __future__ import annotations

import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from .base import BaseReporter, ReporterOutput
from .prompt_builder import build_report_prompt


class LLMReporter(BaseReporter):
    name = "llm"

    def __init__(self, mode: str = "llm"):
        self.mode = mode
        self.provider = os.getenv("ASSET_ANALYSIS_LLM_PROVIDER")
        self.api_key = os.getenv("ASSET_ANALYSIS_LLM_API_KEY")
        self.base_url = os.getenv("ASSET_ANALYSIS_LLM_BASE_URL")
        self.model = os.getenv("ASSET_ANALYSIS_LLM_MODEL")

    def render(self, result) -> ReporterOutput:
        self._validate_config()
        prompt = build_report_prompt(result)
        markdown = self._call_provider(prompt)
        return ReporterOutput(
            mode=self.mode,
            used="llm",
            provider=self.provider,
            model=self.model,
            report_md=markdown,
        )

    def _validate_config(self) -> None:
        missing = []
        if not self.provider:
            missing.append("ASSET_ANALYSIS_LLM_PROVIDER")
        if not self.api_key:
            missing.append("ASSET_ANALYSIS_LLM_API_KEY")
        if not self.base_url:
            missing.append("ASSET_ANALYSIS_LLM_BASE_URL")
        if not self.model:
            missing.append("ASSET_ANALYSIS_LLM_MODEL")
        if missing:
            raise ValueError(f"Missing LLM reporter configuration: {', '.join(missing)}")

    def _call_provider(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Explain the provided asset analysis report context in Markdown only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        request = Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                raw = json.loads(response.read().decode("utf-8", errors="replace"))
        except (URLError, OSError, TimeoutError, json.JSONDecodeError) as exc:
            raise ValueError(f"LLM reporter request failed: {exc}") from exc

        content = _extract_content(raw)
        if not content:
            raise ValueError("LLM reporter returned an empty response.")
        return content


def _extract_content(payload: dict) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        message = choices[0].get("message", {})
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                chunks = [item.get("text", "") for item in content if isinstance(item, dict)]
                return "".join(chunks)
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    return ""
