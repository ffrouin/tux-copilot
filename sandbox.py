#!/usr/bin/env python3
"""
sandbox.py – Docker-based Sandbox Driver

This module implements the Docker-backed execution environment for TUX Copilot.
It exposes a small set of functions that manage the lifecycle of the sandbox
container: verifying that the image exists, building it when needed, and
starting or stopping the container on demand.

The main driver uses these functions to ensure that all file operations and
script executions happen inside a controlled, repeatable workspace.

In short: this module provides the sandbox runtime that powers TUX Copilot’s
isolated execution environment.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from prefs import (
    IMAGE_NAME, CONTAINER_NAME, WORKDIR_HOST
)

# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------

def check_image() -> bool:
    """Return ``True`` if the image exists locally."""
    res = subprocess.run(["docker", "images", "-q", IMAGE_NAME], capture_output=True, text=True)
    return bool(res.stdout.strip())


def build_image():
    """Build the sandbox image from the current directory.

    The function runs ``docker build`` with ``--no-cache`` to avoid stale layers.
    It prints progress messages to stdout.
    """
    print(f"[+] Building Docker image {IMAGE_NAME} …")
    subprocess.check_call(["docker", "build", "--no-cache", "-t", IMAGE_NAME, "."])


def start_container():
    """Launch a detached interactive container with the sandbox mounted."""
    Path(WORKDIR_HOST).mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        "docker",
        "run",
        "--name", CONTAINER_NAME,
        "-dti",
        "-v", f"{Path(os.path.abspath(WORKDIR_HOST)).resolve()}:/workdir",
        IMAGE_NAME,
    ])
    print(f"[+] Started container {CONTAINER_NAME}")


def stop_container():
    """Stop and remove the sandbox container."""
    subprocess.run(["docker", "stop", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "rm", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[+] Stopped and removed container {CONTAINER_NAME}")

__all__ = ["check_image", "build_image", "start_container", "stop_container"]
