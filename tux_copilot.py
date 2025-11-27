#!/usr/bin/env python3
# -------------------------------------------------------------
# TUX Copilot Driver (Enhanced)
#
# Features:
# 1. Sandbox Docker container for /workdir
# 2. Function-calling AI (get_date, get_time, write_file, chmod_x, exec_script, read_file)
# 3. Real-time console display of tool calls and results
# 4. Color-coded tool outputs
# -------------------------------------------------------------
import os
import sys
import subprocess
import json
import uuid
import time
from pathlib import Path

import httpx

# ---------- NEW: Rich Markdown Rendering ----------
from rich.console import Console
from rich.markdown import Markdown
from rich.text import Text
console = Console()
# --------------------------------------------------

# ---------- CONFIG ----------
IMAGE_NAME = "tux-copilot:latest"
CONTAINER_NAME = "tux_copilot"
WORKDIR_HOST = "./sandbox_code"   # host dir that will be mounted into the container
LMSTUDIO_URL = os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1/chat/completions")
MODEL = os.getenv("MODEL", "openai/gpt-oss-20b")

timeout_prefs = httpx.Timeout(
    connect=60.0,
    read=300.0,
    write=60.0,
    pool=60.0,
)

# ---------- TOOL IMPLEMENTATIONS ----------
def run_get_date() -> str:
    """Return current ISO date (YYYY-MM-DD)."""
    return time.strftime("%Y-%m-%d")

def run_get_time() -> str:
    """Return current local time (HH:MM:SS)."""
    return time.strftime("%H:%M:%S")

def run_write_file(path: str, contents: str) -> str:
    """Write `contents` to `path` relative to /workdir. Do not overwrite existing files."""
    full_path = Path(WORKDIR_HOST) / path
    if full_path.exists():
        return f"❌ REFUSED: File already exists: {full_path}"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(contents, encoding="utf-8")
    return f"✅ File created: {full_path}"

def run_chmod_x(path: str) -> str:
    """Set +x permission on a file inside sandbox."""
    full_path = Path(WORKDIR_HOST) / path
    if not full_path.exists():
        return f"[ERROR] File not found: {full_path}"
    full_path.chmod(full_path.stat().st_mode | 0o111)
    return f"✅ chmod +x applied to {full_path}"

def run_exec(path: str) -> str:
    """Execute a script inside the Docker container."""
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
    """Read contents of a file inside /workdir."""
    full_path = Path(WORKDIR_HOST) / path
    if not full_path.exists():
        return f"❌ File not found: {full_path}"
    try:
        return full_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR] Failed to read file: {e}"

TOOLS = {
    "get_date": run_get_date,
    "get_time": run_get_time,
    "write_file": run_write_file,
    "chmod_x": run_chmod_x,
    "exec_script": run_exec,
    "read_file": run_read_file,
}

# ---------- UTILITIES ----------
def check_image() -> bool:
    res = subprocess.run(["docker", "images", "-q", IMAGE_NAME], capture_output=True, text=True)
    return bool(res.stdout.strip())

def build_image():
    console.print(f"[+] Building image {IMAGE_NAME} …", style="bold green")
    subprocess.check_call(["docker", "build", "--no-cache", "-t", IMAGE_NAME, "."])

def start_container():
    Path(WORKDIR_HOST).mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        "docker", "run", "--name", CONTAINER_NAME, "-dti",
        "-v", f"{Path(os.path.abspath(WORKDIR_HOST)).resolve()}:/workdir",
        IMAGE_NAME,
    ])
    console.print(f"[+] Started container {CONTAINER_NAME}", style="bold green")

def stop_container():
    subprocess.run(["docker", "stop", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "rm", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    console.print(f"[+] Stopped and removed container {CONTAINER_NAME}", style="bold green")

def add_message(messages: list[dict], role: str, content: str):
    messages.append({"role": role, "content": content})

def add_tool_call(messages: list[dict], tool_id: str, name: str, arguments: dict):
    messages.append({
        "role": "assistant",
        "tool_calls": [{
            "id": tool_id,
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(arguments)
            }
        }]
    })

def add_tool_response(messages: list[dict], tool_id: str, result: str):
    messages.append({
        "role": "tool",
        "tool_call_id": tool_id,
        "content": result
    })

async def call_llm(messages: list[dict]):
    async with httpx.AsyncClient(timeout=timeout_prefs) as client:
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": [
                {"type":"function","function":{"name":"get_date","description":"Return current ISO date","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"get_time","description":"Return current local time","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{
                    "name":"write_file","description":"Write a file to the sandbox. Provide `path` and `contents`.",
                    "parameters":{"type":"object","properties":{"path":{"type":"string"},"contents":{"type":"string"}},"required":["path","contents"]}
                }},
                {"type":"function","function":{
                    "name":"chmod_x","description":"Apply chmod +x to a file inside /workdir",
                    "parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
                }},
                {"type":"function","function":{
                    "name":"exec_script","description":"Execute a script inside the container using docker exec",
                    "parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
                }},
                {"type":"function","function":{
                    "name":"read_file","description":"Read the contents of a file inside the sandbox. Provide `path`.",
                    "parameters":{"type":"object","properties":{"path":{"type":"string"}},"required":["path"]}
                }},
            ]
        }
        resp = await client.post(LMSTUDIO_URL, json=payload)
        resp.raise_for_status()
        return resp.json()

async def chat_loop():
    console.print("\n🟢 Interactive Chat Started", style="bold green")
    console.print("Type your message and press ENTER. Ctrl-C or 'exit' to quit.\n", style="dim")

    messages: list[dict] = []

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

        # 1 Send to LLM
        response = await call_llm(messages)
        choice = response["choices"][0]["message"]

        # 2 Tool call?
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

                # --- NEW: print tool call details ---
                if "[ERROR]" in result:
                    style = "bold red"
                elif "❌" in result or "⚠" in result:
                    style = "yellow"
                else:
                    style = "cyan"
                console.print(f"\n[Tool Call] {tool_name}({args_dict}) =>\n{result}\n", style=style)

            # Ask again after tool output
            final_resp = await call_llm(messages)
            final_msg = final_resp["choices"][0]["message"].get("content","")
            add_message(messages, "assistant", final_msg)
            console.print(Markdown(final_msg))
        else:
            # Normal assistant reply
            text = choice.get("content", "")
            add_message(messages, "assistant", text)
            console.print(Markdown(text))

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

