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
* **Script Execution**: AI can mark generated scripts as executable and run them in the sandbox
* **Markdown-friendly terminal output**
* **Works with any LLM**: Local (llama.cpp, ollama) or remote (OpenAI, Anthropic, etc.)

## 🛡 Security

Tux Copilot is designed with safety in mind:

* The AI **never touches your host system**
* Network access inside the sandbox can be disabled
* Everything happens inside a disposable container

## 🔧 Requirements

* Docker or Podman
* Python 3.10+
* An LLM provider (local or remote)

## 📦 Installation

```
git clone https://github.com/youruser/tux-copilot
```

## ▶️ Usage

Start the assistant:

```
cd tux-copilot
python3 tux_copilot.py
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

## 📝 License

MIT or Apache-2.0 (choose based on your needs)

## 🤝 Contributing

Pull requests are welcome! Feel free to add tools, improve sandboxing, or enhance documentation.

## ⭐ Why Tux Copilot?

Because your terminal deserves a copilot too—and with full Linux power, safety, and privacy.

