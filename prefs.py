"""
prefs.py – Centralized configuration for TUX Copilot

This module provides a single place for all global configuration values used
across the Copilot runtime: model settings, sandbox paths, image/container
names, and environment-dependent options.

All environment variables use the prefix: TUX_COPILOT_
"""

from __future__ import annotations
import os

# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------

LMSTUDIO_URL = os.getenv(
    "TUX_COPILOT_LMSTUDIO_URL",
    "http://localhost:1234/v1/chat/completions"
)

MODEL = os.getenv(
    "TUX_COPILOT_MODEL",
    "openai/gpt-oss-20b"
)

# ---------------------------------------------------------------------------
# Sandbox (Docker) configuration
# ---------------------------------------------------------------------------

IMAGE_NAME = os.getenv(
    "TUX_COPILOT_IMAGE",
    "tux-copilot:latest"
)

CONTAINER_NAME = os.getenv(
    "TUX_COPILOT_CONTAINER",
    "tux_copilot"
)

# Host directory mounted into the container (/workdir inside the container)
WORKDIR_HOST = os.getenv(
    "TUX_COPILOT_SANDBOX_WORKDIR",
    "./sandbox_workdir"
)

# ---------------------------------------------------------------------------
# Runtime / I/O preferences
# ---------------------------------------------------------------------------

TIMEOUT_CONNECT = float(os.getenv("TUX_COPILOT_TIMEOUT_CONNECT", "60"))
TIMEOUT_READ    = float(os.getenv("TUX_COPILOT_TIMEOUT_READ",    "300"))
TIMEOUT_WRITE   = float(os.getenv("TUX_COPILOT_TIMEOUT_WRITE",   "60"))
TIMEOUT_POOL    = float(os.getenv("TUX_COPILOT_TIMEOUT_POOL",    "60"))

# Enable verbose logging? 1 = yes, 0 = no
DEBUG = bool(int(os.getenv("TUX_COPILOT_DEBUG", "0")))

