#!/usr/bin/env python3
"""
tux_copilot.py – Main Application Driver

This script is the entrypoint for TUX Copilot. It coordinates the interaction
between the user, the local LLM endpoint, the sandbox environment, and the
tooling layer.

Its responsibilities include:
• managing the interactive chat loop,
• sending messages and tool specifications to the LLM,
• dispatching tool calls returned by the model to the appropriate functions,
• displaying results and assistant responses in a readable format,
• ensuring the sandbox container is running during the session.

In short: this script orchestrates the full Copilot runtime, linking the LLM,
the tools, and the sandbox into a unified interactive experience.
"""

from __future__ import annotations

import os
import json
import uuid
import time
from pathlib import Path

import httpx

# Rich console for pretty output ------------------------------------------
from rich.console import Console
from rich.markdown import Markdown
console = Console()

# Import the split modules --------------------------------------------------
from tools import TOOLS, LLM_TOOLS_PAYLOAD
from sandbox import check_image, build_image, start_container, stop_container

# ---------------------------------------------------------------------------
# Configuration constants – keep in sync with the split modules
# ---------------------------------------------------------------------------
from prefs import (
    LMSTUDIO_URL, MODEL, LLM_PROMPT,
    IMAGE_NAME, CONTAINER_NAME, WORKDIR_HOST,
    TIMEOUT_CONNECT, TIMEOUT_READ, TIMEOUT_WRITE, TIMEOUT_POOL,
    DEBUG
)

# HTTPX timeout configuration ----------------------------------------------
timeout_prefs = httpx.Timeout(
    connect=TIMEOUT_CONNECT,
    read=TIMEOUT_READ, # AI think
    write=TIMEOUT_WRITE,
    pool=TIMEOUT_POOL,
)

# ---------------------------------------------------------------------------
# LLM interaction helpers
# ---------------------------------------------------------------------------
async def call_llm(messages: list[dict]):
    async with httpx.AsyncClient(timeout=timeout_prefs) as client:
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": LLM_TOOLS_PAYLOAD
        }
        resp = await client.post(LMSTUDIO_URL, json=payload)
        resp.raise_for_status()
        return resp.json()

# ---------------------------------------------------------------------------
# Chat loop
# ---------------------------------------------------------------------------
async def chat_loop():
    console.print("\n🟢 Interactive Chat Started", style="bold green")
    console.print("Type your message and press ENTER. Ctrl-C or 'exit' to quit.\n", style="dim")

    messages: list[dict] = [{"role": "system", "content": LLM_PROMPT}]

    while True:
        try:
            user_input = input("You> ").strip()
        except KeyboardInterrupt:
            console.print("\n👋 Exiting cleanly…", style="bold yellow")
            break

        if user_input.lower() in {"exit", "quit", "bye"}:
            console.print("\n👋 Exiting cleanly…", style="bold yellow")
            break

        add_message(messages, "user", user_input)

        # 1. Send to LLM
        response = await call_llm(messages)
        choice = response["choices"][0]["message"]

        # 2. Handle tool calls if any
        if "tool_calls" in choice and choice["tool_calls"]:
            for tc in choice["tool_calls"]:
                tool_name = tc["function"]["name"]
                raw_args = tc["function"].get("arguments", "{}")
                try:
                    args_dict = json.loads(raw_args)
                except json.JSONDecodeError:
                    args_dict = {}

                tool_id = tc.get("id") or str(uuid.uuid4())
                add_tool_call(messages, tool_id, tool_name, args_dict)

                func = TOOLS.get(tool_name)
                if func:
                    try:
                        result = func(**args_dict)
                    except TypeError as e:
                        result = f"[ERROR] {e}"
                else:
                    result = f"[ERROR] Unknown tool: {tool_name}"

                add_tool_response(messages, tool_id, result)

                # Pretty print the call & result
                style = "bold red" if "[ERROR]" in result else ("yellow" if "❌" in result or "⚠" in result else "cyan")
                console.print(f"\ntool call {tool_name}\n{result}\n", style=style)

            # Ask again after tool output
            final_resp = await call_llm(messages)
            final_msg = final_resp["choices"][0]["message"].get("content", "")
            add_message(messages, "assistant", final_msg)
            console.print(Markdown("Tux" + "> " + final_msg))
        else:
            # Normal assistant reply
            text = choice.get("content", "")
            add_message(messages, "assistant", text)
            console.print(Markdown("Tux" + "> " + text))

# ---------------------------------------------------------------------------
# Utility helpers for message building (kept from original script)
# ---------------------------------------------------------------------------

def add_message(messages: list[dict], role: str, content: str):
    messages.append({"role": role, "content": content})

def add_tool_call(messages: list[dict], tool_id: str, name: str, arguments: dict):
    messages.append({
        "role": "assistant",
        "tool_calls": [{
            "id": tool_id,
            "type": "function",
            "function": {"name": name, "arguments": json.dumps(arguments)}
        }]
    })

def add_tool_response(messages: list[dict], tool_id: str, result: str):
    messages.append({"role": "tool", "tool_call_id": tool_id, "content": result})

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    if not check_image():
        build_image()

    start_container()

    try:
        import asyncio
        asyncio.run(chat_loop())
    finally:
        stop_container()

if __name__ == "__main__":
    main()
