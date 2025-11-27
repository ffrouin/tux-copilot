#!/usr/bin/env python3
"""
tools.py – LLM Utilities Driver

This module contains the full set of tool functions that the LLM is allowed to
call during a TUX Copilot session.  Each function implements a sandboxed or
container-level action such as reading/writing files, executing scripts inside
the Docker container, or returning timestamps.

The module also exposes two key structures:

• TOOLS – a mapping of tool names to their Python callables, used by the
  main driver to dispatch tool calls returned by the LLM.

• LLM_TOOLS_PAYLOAD – the JSON-schema description of all tool functions,
  supplied to the LLM in the chat-completion payload so it knows which actions
  it can request and how to format their arguments.

In short: tools.py is the centralized “LLM utilities layer” that defines what
the model can do and how it can interact with the sandboxed environment.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from prefs import (
    IMAGE_NAME, CONTAINER_NAME, WORKDIR_HOST
)

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def run_get_date() -> str:
    """Return current ISO date (YYYY-MM-DD)."""
    return time.strftime("%Y-%m-%d")


def run_get_time() -> str:
    """Return current local time (HH:MM:SS)."""
    return time.strftime("%H:%M:%S")


def run_write_file(path: str, contents: str) -> str:
    """Write ``contents`` to a file relative to :data:`WORKDIR_HOST`.

    The function refuses to overwrite an existing file – this mirrors the
    behaviour of the original driver and keeps accidental data loss out of the
    sandbox.
    """
    full_path = Path(WORKDIR_HOST) / path
    if full_path.exists():
        return f"❌ REFUSED: File already exists: {full_path}"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(contents, encoding="utf-8")
    return f"✅ File created: {full_path}"


def run_chmod_x(path: str) -> str:
    """Set executable permission on a file inside the sandbox."""
    full_path = Path(WORKDIR_HOST) / path
    if not full_path.exists():
        return f"[ERROR] File not found: {full_path}"
    # Add user/group/other execute bits
    full_path.chmod(full_path.stat().st_mode | 0o111)
    return f"✅ chmod +x applied to {full_path}"


def run_exec(path: str) -> str:
    """Execute a script inside the Docker container.

    The function expects ``path`` to be relative to ``/workdir`` within the
    container.  It uses :command:`docker exec` to run the file and captures
    stdout/stderr.  A timeout of 60 seconds protects against runaway scripts.
    """
    script_path = f"/workdir/{path}"
    cmd = ["docker", "exec", CONTAINER_NAME, script_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as e:
        return f"[ERROR] Execution failed: {e}"

    output = result.stdout.strip()
    errors = result.stderr.strip()
    if errors:
        return f"⚠ STDERR:\n{errors}\n\nSTDOUT:\n{output}"
    return f"🟢 Execution OK:\n{output}"


def run_read_file(path: str) -> str:
    """Read the contents of a file inside :data:`WORKDIR_HOST`."""
    full_path = Path(WORKDIR_HOST) / path
    if not full_path.exists():
        return f"❌ File not found: {full_path}"
    try:
        return full_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR] Failed to read file: {e}"

# ---------------------------------------------------------------------------
# Public mapping of tool names to callables
# ---------------------------------------------------------------------------
TOOLS = {
    "get_date": run_get_date,
    "get_time": run_get_time,
    "write_file": run_write_file,
    "chmod_x": run_chmod_x,
    "exec_script": run_exec,
    "read_file": run_read_file,
}

__all__ = ["TOOLS", "run_get_date", "run_get_time", "run_write_file",
           "run_chmod_x", "run_exec", "run_read_file"]

# ------------------------
# LLM tools payload
# ------------------------
LLM_TOOLS_PAYLOAD = [
    {"type":"function","function":{"name":"get_date", "description":"Return current ISO date","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"get_time", "description":"Return current local time","parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{
        "name":"write_file",
        "description":"Write a file to the sandbox. Provide path and contents.",
        "parameters":{"type":"object","properties":{"path":{"type":"string"},"contents":{"type":"string"}},"required":["path","contents"]}
    }},
    {"type":"function","function":{
        "name":"chmod_x",
        "description":"Apply chmod +x to a file inside /workdir",
        "parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
    }},
    {"type":"function","function":{
        "name":"exec_script",
        "description":"Execute a script inside the container using docker exec",
        "parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
    }},
    {"type":"function","function":{
        "name":"read_file",
        "description":"Read the contents of a file inside the sandbox. Provide path.",
        "parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
    }}
]
