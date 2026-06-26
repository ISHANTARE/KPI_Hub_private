"""
OpenAI helper: loads `OPENAI_API_KEY` from `.env` or environment.
"""
import os
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def get_openai_api_key() -> str | None:
    """Return the OpenAI API key from env or .env file if present."""
    # Try to load .env if python-dotenv is available
    if load_dotenv is not None:
        try:
            # load .env from workspace root
            load_dotenv()
        except Exception:
            pass

    return os.getenv('OPENAI_API_KEY')
