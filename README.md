# cli-ollama

![image](https://github.com/user-attachments/assets/913d8d9c-1833-4baa-ad5b-0ee0b37b5e46)

# Local Ollama CLI Wrapper
This tool is a simple CLI wrapper for the Ollama API running a local instance of an LLM (defaults to `qwen2.5-coder:7b`). It allows you to quickly look up simple bash commands, ffmpeg options, and other command line instructions without using up any usage limits on services like Claude or ChatGPT.

## Features

- **Local Processing:** Uses the QWen 7B model running on your GPU.
- **Streamed Responses:** Processes streamed responses from the Ollama API.
- **Syntax Highlighting:**
  - **Code Blocks:** Delimited by triple backticks are printed in **cyan**.
  - **Inline Code:** Delimited by single backticks are printed in **yellow**.
- **Language Marker Stripping:** Automatically strips language markers such as `bash` or `sh` from code blocks.
- **Performance Metrics:** Calculates tokens per second (T/s) and displays them in bright magenta.
- **Debug Mode:** Optionally prints all received tokens for debugging purposes.

## Requirements

- **Server:** A server running the Ollama service with your desired model (e.g., QWen 7B).
- **Python:** Python 3 with the `requests` library installed.

## Setup

### Ollama Service Configuration

On the server, ensure that the Ollama service is accessible externally:

1. Open a terminal and edit the systemd service file:
    ```bash
    systemctl edit ollama.service
    ```
2. In the editor, add the following line under the `[Service]` section:
    ```ini
    [Service]
    Environment="OLLAMA_HOST=0.0.0.0"
    ```
3. Save and exit the editor.
4. Reload the systemd configuration and restart Ollama:
    ```bash
    systemctl daemon-reload
    systemctl restart ollama
    ```
5. On the client side, set the IP address in the wrapper file (`llm.py`) by updating:
    ```python
    API_URL = "http://100.116.219.163:11434/api/generate"
    ```
   Replace the IP with the address of your Ollama server if needed.

### Local CLI Usage

Note that this wrapper does not maintain any context or history between commands; every command is treated as a separate first prompt.

#### Running the CLI

- **Basic Usage:**
    ```bash
    python llm.py "how to view docker containers running on what network"
    ```
- **Specifying a Model:**
    ```bash
    python llm.py --MODEL deepseek-r1:14b "how to view docker containers running on what network"
    ```
- **Enabling Debug Mode:**
    ```bash
    python llm.py --DEBUG "ffmpeg command to convert mp3 to opus and reverse audio"
    ```
