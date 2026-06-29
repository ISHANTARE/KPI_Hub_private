"""
tests/test_ai_modules.py
-------------------------
Unit tests for Phase 5 AI modules (openai_client, ai_validator, knowledge_base).
"""

import pytest
from integrations.openai_client import sanitize_prompt, get_completion
from lib.ai_validator import extract_json_from_llm_output, validate_extracted_data
from lib.knowledge_base import search_knowledge_base

def test_sanitize_prompt():
    long_text = "a" * 15000
    cleaned = sanitize_prompt(long_text, max_chars=100)
    assert len(cleaned) == 100

def test_extract_json_from_llm_output():
    raw_response = "Here is the response:\n```json\n{\"status\": \"OK\", \"count\": 5}\n```"
    parsed = extract_json_from_llm_output(raw_response)
    assert parsed is not None
    assert parsed.get("status") == "OK"

def test_validate_extracted_data():
    valid = validate_extracted_data({"a": 1, "b": 2}, ["a", "b"])
    assert valid is True
    invalid = validate_extracted_data({"a": 1}, ["a", "b"])
    assert invalid is False

def test_search_knowledge_base():
    results = search_knowledge_base("ASIL D")
    assert len(results) > 0
    assert any(r["code"] == "ASIL D" for r in results)
