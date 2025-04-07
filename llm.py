#!/usr/bin/env python3
import sys
import json
import argparse
import requests
import time
from requests.exceptions import RequestException

DEFAULT_MODEL = "qwen2.5-coder:7b"
API_URL = "http://123.456.678.90:11434/api/generate"
PROMPT_PREFIX = "Please answer this question keep it short and to the point: "

def print_plain(text):
    sys.stdout.write(text)
    sys.stdout.flush()

def print_yellow(text):
    YELLOW = "\033[33m"
    RESET = "\033[0m"
    sys.stdout.write(YELLOW + text + RESET)
    sys.stdout.flush()

def print_cyan(text):
    CYAN = "\033[36m"
    RESET = "\033[0m"
    sys.stdout.write(CYAN + text + RESET)
    sys.stdout.write("\n")
    sys.stdout.flush()

def print_bright_magenta(text):
    BRIGHT_MAGENTA = "\033[95m"
    RESET = "\033[0m"
    sys.stdout.write(BRIGHT_MAGENTA + text + RESET)
    sys.stdout.write("\n")
    sys.stdout.flush()

def generate(prompt, model):
    """Call the API with the given prompt and model using streaming."""
    payload = {
        "model": model,
        "prompt": PROMPT_PREFIX + prompt,
        "stream": True
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=15
        )
        response.raise_for_status()
        return response
    except RequestException as e:
        print(f"\033[91mError connecting to Ollama server: {str(e)}\033[0m")
        sys.exit(1)

def flush_pending(pending, state):
    """
    Process the accumulated pending text based on the current state.
    
    States:
      - "plain": Look for a backtick marker.
          * If found, flush plain text up to it. Then, if three backticks are detected,
            switch to code_pending mode.
          * Otherwise (single backtick) switch to inline mode.
      - "inline": Look for the next single backtick; when found, flush the inline code in yellow.
      - "code_pending": We have just seen the opening triple-backticks.
            Wait for a newline so we can inspect the first line.
            If that line (stripped) is "bash" or "sh", discard it and switch to code mode.
            Otherwise, include it as part of the code block and switch to code mode.
      - "code": Look for the next triple-backticks; when found, flush the code block in cyan.
    """
    while True:
        if state == "plain":
            pos = pending.find("`")
            if pos == -1:
                break  # no marker found
            if pos > 0:
                print_plain(pending[:pos])
            # Check if we have triple backticks.
            if pending[pos:pos+3] == "```":
                pending = pending[pos+3:]
                state = "code_pending"
            else:
                # single backtick marker → switch to inline mode.
                pending = pending[pos+1:]
                state = "inline"
        elif state == "inline":
            pos = pending.find("`")
            if pos == -1:
                break  # waiting for closing single backtick
            print_yellow(pending[:pos])
            pending = pending[pos+1:]
            state = "plain"
        elif state == "code_pending":
            # Wait until we see a newline (i.e. a complete first line).
            pos = pending.find("\n")
            if pos == -1:
                break  # not enough yet, wait for more tokens
            first_line = pending[:pos]
            pending = pending[pos+1:]
            if first_line.strip() in ["bash", "sh"]:
                # Detected language marker; discard it.
                state = "code"
            else:
                # Not a recognized marker; include the line in code.
                pending = first_line + "\n" + pending
                state = "code"
        elif state == "code":
            pos = pending.find("```")
            if pos == -1:
                break  # waiting for closing triple backticks
            print_cyan(pending[:pos])
            pending = pending[pos+3:]
            state = "plain"
    return pending, state

def process_stream(response, debug=False, raw=False):
    """
    Process the streaming response using a state machine.
    
    The states are:
      - "plain": normal text output.
      - "inline": inline code (delimited by single backticks) printed in yellow.
      - "code_pending": after detecting opening triple-backticks, waiting for a newline to check for a language marker.
      - "code": code block output (delimited by triple backticks) printed in cyan.
    
    Tokens are accumulated in a pending buffer and flushed when complete markers are found.
    Finally, after receiving final metadata, T/s is calculated and printed in bright magenta.
    If debug is enabled, a JSON list of all received tokens is printed.
    """
    pending = ""
    state = "plain"  # initial state
    debug_tokens = []
    
    for line in response.iter_lines():
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Check for final metadata.
        if data.get("done") and "eval_count" in data and "eval_duration" in data:
            if pending:
                if state == "plain":
                    print_plain(pending)
                elif state == "inline":
                    print_yellow(pending)
                elif state in ["code_pending", "code"]:
                    print_cyan(pending)
                pending = ""
                state = "plain"
            eval_count = data.get("eval_count")
            eval_duration = data.get("eval_duration")
            tps = (eval_count / eval_duration) * 1e9
            print_bright_magenta(f"\nT/s: {tps:.1f}")
            if debug:
                print("\nDebug tokens:", json.dumps(debug_tokens))
            continue

        token = data.get("response", "")
        debug_tokens.append(token)
        if raw:
            print_plain(token)
        else:
            pending += token
            pending, state = flush_pending(pending, state)

    if pending:
        if state == "plain":
            print_plain(pending)
        elif state == "inline":
            print_yellow(pending)
        elif state in ["code_pending", "code"]:
            print_cyan(pending)

def main():
    parser = argparse.ArgumentParser(
        description="\033[1mCLI wrapper for Ollama API\033[0m",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\033[32mExamples:\n"
               "  python llm.py 'how to grep for multiple patterns'\n"
               "  python llm.py --MODEL mistral 'explain docker networks'\n"
               "  python llm.py --DEBUG --RAW 'ffmpeg command to convert mp3 to opus'\033[0m"
    )
    parser.add_argument("prompt", nargs="+", help="\033[36mPrompt to send to the LLM\033[0m")
    parser.add_argument("--MODEL", default=DEFAULT_MODEL, help="\033[33mModel to use (default: %(default)s)\033[0m")
    parser.add_argument("--DEBUG", action="store_true", help="\033[35mEnable debug mode to print received tokens\033[0m")
    parser.add_argument("--RAW", action="store_true", help="\033[34mOutput raw text without formatting\033[0m")
    args = parser.parse_args()

    prompt_text = " ".join(args.prompt)
    response = generate(prompt_text, args.MODEL)
    process_stream(response, debug=args.DEBUG, raw=args.RAW)

if __name__ == "__main__":
    main()
