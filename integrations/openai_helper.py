"""
OpenAI helper: loads `OPENAI_API_KEY` from `.env` or environment.
"""
import os
try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


def get_openai_api_key() -> str | None:
    """Return the OpenAI API key from env, .env file, or config.yaml."""
    if load_dotenv is not None:
        try:
            load_dotenv()
        except Exception:
            pass

    key = os.getenv('OPENAI_API_KEY')
    if key and key.strip() and not key.startswith("YOUR_"):
        return key.strip()

    try:
        from integrations.config_helper import load_config
        cfg = load_config()
        key_from_cfg = cfg.get('openai', {}).get('api_key')
        if key_from_cfg and str(key_from_cfg).strip() and not str(key_from_cfg).startswith("YOUR_"):
            return str(key_from_cfg).strip()
    except Exception:
        pass

    return key if key else None
