"""
OpenAI client wrapper.

Provides `get_completion(prompt)` which uses the `openai` package if present
or falls back to the REST API via `requests`. The API key is obtained from
`integrations.openai_helper.get_openai_api_key()` or environment.

This module does not call the API automatically; the application should call
`get_completion` when ready and with valid network access.
"""
from typing import Optional, Dict, Any
import os
import json
import logging

try:
    import openai
except Exception:
    openai = None

try:
    import requests
except Exception:
    requests = None

from integrations.openai_helper import get_openai_api_key

logger = logging.getLogger(__name__)


def _get_api_key() -> Optional[str]:
    return get_openai_api_key()


def get_completion(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 512) -> Optional[str]:
    """Return a text completion for `prompt` or None on failure.

    - If the `openai` package is installed, it will be used.
    - Otherwise the function attempts a direct HTTP call using `requests`.
    """
    api_key = _get_api_key()
    if not api_key:
        logger.error("OpenAI API key not found; set OPENAI_API_KEY in environment or .env")
        return None

    # Prefer official package
    if openai is not None:
        try:
            client = openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.exception(f"OpenAI package request failed: {e}")

    # Fallback to requests
    if requests is None:
        logger.error("Neither `openai` nor `requests` installed; cannot call OpenAI API")
        return None

    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        r.raise_for_status()
        j = r.json()
        return j['choices'][0]['message']['content']
    except Exception as e:
        logger.exception(f"OpenAI HTTP request failed: {e}")
        return None


if __name__ == '__main__':
    # Simple CLI test (does not run automatically in imports)
    import sys
    if len(sys.argv) > 1:
        prompt = ' '.join(sys.argv[1:])
    else:
        prompt = 'Say hello in one sentence.'
    print(get_completion(prompt))
