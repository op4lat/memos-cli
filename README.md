# Memos CLI Tool

A minimalist, pipe-friendly terminal utility for interacting with your [Memos](https://github.com/usememos/memos) instance. Think of it as your personal pastebin, but powered by Memos. This tool is built to streamline the process of capturing terminal output and managing data without leaving the command line.

## Features

* **Pipe Support:** Post any command output directly to Memos (e.g., `cat logs.txt | memos-cli.py`).
* **Clipboard Integration:** Automatically copies the URL of newly created memos for easy sharing.
* **Security-Minded Advanced Features:** The script is fully capable of posting from your clipboard, searching your history, and listing recent memos; however, these are disabled by default for security and can be enabled via configuration.

---

## Installation

### 1. Prerequisites

Ensure you have Python 3 and the necessary system utilities. You must install the clipboard utility that matches your Linux display server:

* **For X11 (most common on older/stable distros):** Install `xclip`.
* **For Wayland (default on modern GNOME/KDE/Fedora):** Install `wl-clipboard`.

```bash
# Debian/Ubuntu (X11)
sudo apt install python3-requests python3-dotenv xclip

# Debian/Ubuntu (Wayland)
sudo apt install python3-requests python3-dotenv wl-clipboard

```

### 2. Configuration

Create a configuration file at `~/.memos.conf` and add your details:

```bash
MEMOS_URL="https://your-memos-instance.com"
MEMOS_TOKEN="your_access_token_here"
MEMOS_VISIBILITY="PRIVATE"  # Options: PRIVATE, PROTECTED, PUBLIC
MEMOS_ADVANCED_FEATURES="false" # Set to true to unlock search, list, and clipboard-post

```

### 3. Setup Alias (Suggested)

To run the tool simply by typing `memo`, add this to your `~/.bashrc` or `~/.zshrc`:

```bash
alias memo='/path/to/your/script/memos-cli.py'

```

---

## Hidden Advanced Features

For **security reasons**, features that read your history or your clipboard are **hidden/disabled by default**. This prevents accidental execution of commands that might leak sensitive information in environments where the script is used on shared machines.

To unlock these, you must explicitly set `MEMOS_ADVANCED_FEATURES="true"` in your `.memos.conf`.

* **-c (Clipboard Post):** Grabs the current text in your system clipboard and posts it as a new memo. Useful for saving snippets found in a browser.
* **-L (List Last):** Fetches the most recent memo you created, displays the content, and copies the direct URL back to your clipboard.
* **-s (Search):** Performs a server-side search of your existing memos based on a keyword.

---

## Usage

| Command | Action |
| --- | --- |
| ` echo "Capture this" \| memos-cli.py ` | Post piped text to a new memo |
| `memos-cli.py -c` | Post content from clipboard (Advanced) |
| `memos-cli.py -L` | Display the most recent memo (Advanced) |
| `memos-cli.py -s "keyword"` | Search for memos (Advanced) |
| `memos-cli.py -D 123` | Delete memo with ID 123 |
| `echo "New text" \| memo -U 123` | Update memo 123 with new content |

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/op4lat/memos-cli/blob/main/LICENSE) file for details.

## Credits

* **Memos:** The open-source project at [github.com/usememos/memos](https://github.com/usememos/memos).
* **Author:** Created by [steven-tey](https://github.com/steven-tey) and the Memos community.
* **Compatibility:** Built for Memos API v1 (Tested on version 0.26.1).

---

## DISCLAIMER

I usually write my scripts in BASH. However, because I wanted robust pipeline support and BASH was not particularly friendly for this specific implementation, I decided to build this as a Python script.

Since I am not deeply familiar with Python syntax, I used **Google Gemini** to help write the code and documentation. The project was developed iteratively—adding features one at a time and testing them thoroughly to ensure reliability. As such, both the source code and the documentation were produced through an AI-human collaborative process.

