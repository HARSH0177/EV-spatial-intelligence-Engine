"""
tests/conftest.py  —  Shared fixtures and test environment setup.

Ensures no real external calls happen during the test suite:
- GOOGLE_CLOUD_PROJECT unset → DataAgent uses mock data
- LLM_ENABLED=false → Vertex AI calls skipped
- REQUIRE_AUTH=false → no API key needed in tests
"""

import os
import pytest

# Force mock-safe defaults before any module is imported
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "")
os.environ.setdefault("LLM_ENABLED",          "false")
os.environ.setdefault("REQUIRE_AUTH",          "false")
os.environ.setdefault("NREL_API_KEY",          "DEMO_KEY")
