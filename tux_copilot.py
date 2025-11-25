#!/usr/bin/env python3
# -------------------------------------------------------------
# TUX Copilot Driver
#
# 1. Ensure the sandbox image exists (build if needed)
# 2. Spin up a container exposing /workdir as a volume
# 3. Start an interactive chat with your LM‑Studio endpoint
#    using function calling (get_date, get_time)
# -------------------------------------------------------------
import os
import sys
import subprocess
import json
import uuid
import time
from pathlib import Path

import httpx

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
    """
    Write `contents` to `path` relative to the shared host directory.
    Returns a short confirmation string.
    """
    full_path = Path(WORKDIR_HOST)/path          # <--- use host path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(contents, encoding="utf-8")
    return f"✅ File written to {full_path}"

TOOLS = {
    "get_date": run_get_date,
    "get_time": run_get_time,
    "write_file": run_write_file,
}

# ---------- UTILITIES ----------
def check_image():
    """Return True if image exists, else False."""
    res = subprocess.run(
        ["docker", "images", "-q", IMAGE_NAME],
        capture_output=True, text=True
    )
    return bool(res.stdout.strip())


def build_image():
    print(f"[+] Building image {IMAGE_NAME} …")
    cmd = [
        "docker", "build",
        "--no-cache",
        "-t", IMAGE_NAME,
        "."
    ]
    subprocess.check_call(cmd)


def start_container():
    """Run the sandbox container detached, mounting WORKDIR_HOST."""
    # Ensure host dir exists
    Path(WORKDIR_HOST).mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker", "run",
        "--name", CONTAINER_NAME,
        "-dti",
        "-v", f"{Path(os.path.abspath(WORKDIR_HOST)).resolve()}:/workdir",
        IMAGE_NAME,
    ]
    subprocess.check_call(cmd)
    print(f"[+] Started container {CONTAINER_NAME}")


def stop_container():
    subprocess.run(["docker", "stop", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["docker", "rm", CONTAINER_NAME], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[+] Stopped and removed container {CONTAINER_NAME}")


def add_message(messages: list[dict], role: str, content: str):
    messages.append({"role": role, "content": content})


def add_tool_call(messages: list[dict], tool_id: str, name: str, arguments: dict):
    """Append the assistant’s tool call to the message history."""
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
    """Append the tool’s output as a separate message."""
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
            # expose the two functions to the model
            "tools": [
                {"type":"function","function":{"name":"get_date","description":"Return current ISO date","parameters":{"type":"object","properties":{}}}},
                {"type":"function","function":{"name":"get_time","description":"Return current local time (HH:MM:SS)","parameters":{"type":"object","properties":{}}}},
                {"type":"function",
                 "function":{
                    "name":"write_file",
                    "description":"Write a file to the sandbox. Provide `path` and `contents`.",
                    "parameters":{
                     "type":"object",
                     "properties":{
                         "path":{"type":"string","description":"Relative path inside /workdir"},
                         "contents":{"type":"string","description":"File content"}
                     },
                     "required":["path","contents"]
                    }
                }}
            ]
        }
        resp = await client.post(LMSTUDIO_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


async def chat_loop():
    print("\n🟢 Interactive Chat Started")
    print("Type your message and press ENTER. Ctrl‑C to quit.\n")

    messages: list[dict] = []

    while True:
        try:
            user_input = input("You> ")
        except KeyboardInterrupt:
            print("\n[!] Exiting…")
            break

        add_message(messages, "user", user_input)

        # 1️⃣ Send to LLM
        response = await call_llm(messages)
        choice = response["choices"][0]["message"]

        # 2️⃣ If the model wants to call a tool
        if "tool_calls" in choice and choice["tool_calls"]:
            for tc in choice["tool_calls"]:
                tool_name = tc["function"]["name"]
                # Parse arguments JSON – LM‑Studio gives us a string, so we need to decode it.
                raw_args = tc["function"].get("arguments", "{}")
                try:
                    args_dict = json.loads(raw_args)
                except json.JSONDecodeError:
                    args_dict = {}

                tool_id = tc.get("id") or str(uuid.uuid4())

                # Log the assistant’s intent
                add_tool_call(messages, tool_id, tool_name, args_dict)

                # Execute locally with the parsed arguments
                func = TOOLS.get(tool_name)
                if func:
                    try:
                        result = func(**args_dict)   # <--- pass **kwargs
                    except TypeError as e:
                        result = f"[ERROR] {e}"
                else:
                    result = f"[ERROR] Unknown tool: {tool_name}"

                # Append the tool’s output back into the conversation
                add_tool_response(messages, tool_id, result)
            
            # 3️⃣ Ask LLM for the final answer after we fed back tool outputs
            final_resp = await call_llm(messages)
            final_msg = final_resp["choices"][0]["message"]["content"]
            add_message(messages, "assistant", final_msg)
            print(f"AI> {final_msg}")

        else:
            # Normal assistant reply
            text = choice.get("content", "")
            add_message(messages, "assistant", text)
            print(f"AI> {text}")


def main():
    # 0️⃣ Make sure we have a clean environment
    if not check_image():
        build_image()

    # 1️⃣ Start sandbox container
    start_container()

    try:
        import asyncio
        asyncio.run(chat_loop())
    finally:
        stop_container()


if __name__ == "__main__":
    main()

