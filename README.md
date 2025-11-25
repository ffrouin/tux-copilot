# Tux Copilot

Tux Copilot turns your terminal into a smart, sandboxed AI coding assistant powered by local or remote LLMs.

## 🚀 Overview

Tux Copilot provides an interactive AI assistant directly inside your Linux terminal. It launches a secure, isolated sandbox container where the AI can:

* Create, edit, and manage files safely
* Execute shell commands inside the sandbox
* Generate code, scripts, configs, and documentation
* Run tools without exposing your real system
* Interact with your environment via a clean, extensible tool API

This keeps your actual machine completely safe while allowing the AI to work with real Linux tools.

## ✨ Features

* **Sandboxed Execution**: All commands run inside an ephemeral Docker container
* **Secure File API**: AI can create new files but *never overwrite existing ones* (configurable)
* **Command Tools**: Exposed safe utilities like `ls`, `cat`, `grep`, `sed`, etc.
* **Script Execution**: AI can mark generated scripts as executable and run them in the sandbox
* **Session Persistence**: Work persists inside the container until you stop the session
* **Markdown-friendly terminal output**
* **Works with any LLM**: Local (llama.cpp, ollama) or remote (OpenAI, Anthropic, etc.)

## 🛡 Security

Tux Copilot is designed with safety in mind:

* The AI **never touches your host system**
* The AI **cannot rewrite existing files** (optional strict mode)
* Network access inside the sandbox can be disabled
* Commands are executed with minimal privileges
* Everything happens inside a disposable container

## 🔧 Requirements

* Docker or Podman
* Python 3.10+
* An LLM provider (local or remote)

## 📦 Installation

```bash
pip install tux-copilot
```

Or run directly from the repo:

```bash
git clone https://github.com/youruser/tux-copilot
cd tux-copilot
python3 -m tux_copilot
```

## ▶️ Usage

Start the assistant:

```bash
tux-copilot
```

Example interaction:

```
user> create a bash script that monitors CPU temperature
ai> saved as monitor.sh
user> chmod +x monitor.sh
user> ./monitor.sh
```

To exit:

```
exit
quit
bye
```

## ⚙️ Configuration

`~/.tux_copilot/config.yaml`:

```yaml
sandbox_image: debian:stable
allow_overwrite: false
llm_provider: openai
model: gpt-4.1
```

## 🔌 Extending Tools

Tux Copilot supports custom tool hooks:

* Add new safe commands
* Provide structured APIs
* Integrate tests or CI utilities

Example (Python):

```python
from tux_copilot.tools import register_tool

@register_tool
def my_custom_tool(args):
    return "Hello from tool"
```

## 📝 License

MIT or Apache-2.0 (choose based on your needs)

## 🤝 Contributing

Pull requests are welcome! Feel free to add tools, improve sandboxing, or enhance documentation.

## ⭐ Why Tux Copilot?

Because your terminal deserves a copilot too—and with full Linux power, safety, and privacy.

