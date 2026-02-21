#!/usr/bin/env python3

"""
MEMOS CLI TOOL
==============
A minimalist utility to interact with a Memos instance directly from the 
Linux terminal via pipes and flags.

INPUT EXPECTATIONS:
- This script EXPECTS piped input for Posting and Updating.
- Advanced Feature (-c) allows posting directly from the clipboard.
- Example: `ls -la | memo` or `memo -c`

CONFIGURATION:
- Requires a file at ~/.memos.conf with:
    MEMOS_URL="https://your-instance.com"
    MEMOS_TOKEN="your_access_token"
    MEMOS_VISIBILITY="PRIVATE" (Optional: PUBLIC, PROTECTED)
    MEMOS_ADVANCED_FEATURES="true" (Enables -L, -s, and -c)

CORE ACTIONS:
- POST:   Capture stdin (or clipboard via -c) and save as a new memo.
- READ:   Retrieve the most recent memo (-L) or search by keyword (-s).
- UPDATE: Edit existing memos by ID (-U) using new piped input.
- DELETE: Remove memos by ID (-D).
"""

import sys
import os
import subprocess
import shutil
import argparse

# 1. Dependency Guard: Ensure required non-standard libraries are installed
try:
    import requests
    from dotenv import load_dotenv
    from pathlib import Path
except ImportError:
    print("Error: Missing dependencies.")
    print("Please run: sudo apt install python3-requests python3-dotenv")
    sys.exit(10)

# 2. Clipboard Integration: Supports Copying (for URLs) and Pasting (for -c flag)
def copy_to_clipboard(text):
    if shutil.which("xclip"):
        subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE).communicate(input=text.encode())
    elif shutil.which("wl-copy"):
        subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE).communicate(input=text.encode())

def get_clipboard_text():
    """Reads text from the system clipboard using xclip or wl-paste."""
    try:
        if shutil.which("xclip"):
            return subprocess.check_output(['xclip', '-selection', 'clipboard', '-o']).decode().strip()
        elif shutil.which("wl-paste"):
            return subprocess.check_output(['wl-paste']).decode().strip()
    except Exception:
        return None
    return None

# 3. Config Manager: Reads the ~/.memos.conf file and extracts credentials/feature toggles
def get_config():
    config_path = Path("~/.memos.conf").expanduser()
    if config_path.exists():
        load_dotenv(dotenv_path=config_path)
    
    url = os.getenv('MEMOS_URL')
    token = os.getenv('MEMOS_TOKEN')
    visibility = os.getenv('MEMOS_VISIBILITY', 'PRIVATE')
    adv_feat = os.getenv('MEMOS_ADVANCED_FEATURES', 'false').lower() == 'true'
    
    if not url or not token:
        print(f"Error: Credentials missing in {config_path}")
        sys.exit(12)
    return url.rstrip('/'), token, visibility, adv_feat

# 4. Read Action: Fetches the single most recent memo from the API
def list_last_memo(base_url, token):
    endpoint = f"{base_url}/api/v1/memos"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page_size": 1}
    
    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        memos = response.json().get("memos", [])
        
        if not memos:
            print("No memos found.")
            return

        last_memo = memos[0]
        memo_id = last_memo.get("name", "").split('/')[-1]
        content = last_memo.get("content", "")
        
        print(f"--- Latest Memo [ID: {memo_id}] ---")
        print(content)
        print("----------------------------------")
        print(f"URL: {base_url}/memos/{memo_id}")
        copy_to_clipboard(f"{base_url}/memos/{memo_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not list memo: {e}")
        sys.exit(13)

# 5. Search Action: Uses API filters to find content containing a specific string
def search_memos(base_url, token, query):
    endpoint = f"{base_url}/api/v1/memos"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"filter": f"content.contains('{query}')", "page_size": 5}
    
    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        memos = response.json().get("memos", [])
        
        if not memos:
            print(f"No memos found matching: '{query}'")
            return

        print(f"--- Search Results for '{query}' (Top 5) ---")
        for m in memos:
            mid = m.get("name", "").split('/')[-1]
            preview = m.get("content", "").replace("```text\n", "").replace("\n```", "").split('\n')[0][:60]
            print(f"[{mid}] {preview}...")
        print("-------------------------------------------")
    except requests.exceptions.RequestException as e:
        print(f"Error: Search failed: {e}")
        sys.exit(13)

# 6. Delete Action: Permanently removes a memo by its numeric ID
def delete_memo(base_url, token, memo_id):
    endpoint = f"{base_url}/api/v1/memos/{memo_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.delete(endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Success: Memo {memo_id} deleted.")
    except requests.exceptions.RequestException as e:
        print(f"Error: Delete failed: {e}")
        sys.exit(13)

# 7. Update Action: Replaces memo content using a PATCH request and piped input
def update_memo(base_url, token, memo_id, visibility):
    if sys.stdin.isatty():
        print("Error: No piped input detected for update.")
        sys.exit(11)
    
    input_data = sys.stdin.read().strip()
    if not input_data:
        sys.exit(0)

    endpoint = f"{base_url}/api/v1/memos/{memo_id}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"content": f"```text\n{input_data}\n```", "visibility": visibility}
    
    try:
        url = f"{endpoint}?update_mask=content,visibility"
        response = requests.patch(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        print(f"Success: Memo {memo_id} updated.")
    except requests.exceptions.RequestException as e:
        print(f"Error: Update failed: {e}")
        sys.exit(13)

# 8. Post Action: Creates a new memo from piped data or clipboard (-c)
def post_to_memos(show_delete, show_update, from_clipboard=False):
    base_url, api_token, visibility, _ = get_config()

    if from_clipboard:
        input_data = get_clipboard_text()
        if not input_data:
            print("Error: Clipboard is empty or utility (xclip/wl-paste) not found.")
            sys.exit(11)
    else:
        if sys.stdin.isatty():
            print("Error: No piped input detected. Use -c to post from clipboard.")
            sys.exit(11)
        input_data = sys.stdin.read().strip()

    if not input_data:
        sys.exit(0)

    memo_content = f"```text\n{input_data}\n```"
    endpoint = f"{base_url}/api/v1/memos"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
    
    try:
        response = requests.post(endpoint, json={"content": memo_content, "visibility": visibility}, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        memo_id = data.get("name", "").split('/')[-1]
        full_memo_url = f"{base_url}/memos/{memo_id}"
        
        print(f"Success: {full_memo_url}")
        copy_to_clipboard(full_memo_url)

        script_name = os.path.basename(__file__)
        if show_delete: 
            print(f"To delete this memo run: {script_name} -D {memo_id}")
        if show_update: 
            print(f"To update this memo run: [command] | {script_name} -U {memo_id}")

    except requests.exceptions.RequestException as e:
        print(f"Error: API Request failed: {e}")
        sys.exit(13)

# 9. CLI Entry Point: Parses flags and routes to the correct function
if __name__ == "__main__":
    base_url, token, visibility, adv_feat = get_config()

    l_help = "List the most recent memo" if adv_feat else argparse.SUPPRESS
    s_help = "Search memos by keyword" if adv_feat else argparse.SUPPRESS
    c_help = "Post content directly from clipboard" if adv_feat else argparse.SUPPRESS

    parser = argparse.ArgumentParser(
        description="Memos CLI Tool: Post, update, or delete memos from the terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  Post a memo:           echo "Hello World" | memo
  Post from clipboard:   memo -c                (Advanced)
  Update memo #123:      echo "Update" | memo -U 123
  Delete memo #123:      memo -D 123
{"  List last memo:        memo -L" if adv_feat else ""}
        """
    )
    
    parser.add_argument("-d", action="store_true", help="Show command to self-delete")
    parser.add_argument("-u", action="store_true", help="Show command to self-update")
    parser.add_argument("-D", "--delete", metavar="ID", help="Delete a specific memo by ID")
    parser.add_argument("-U", "--update", metavar="ID", help="Update a specific memo by ID")
    parser.add_argument("-L", "--last", action="store_true", help=l_help)
    parser.add_argument("-s", "--search", metavar="QUERY", help=s_help)
    parser.add_argument("-c", "--clipboard", action="store_true", help=c_help)
    
    args = parser.parse_args()

    if args.last:
        if adv_feat:
            list_last_memo(base_url, token)
        else:
            sys.exit(12)
    elif args.search:
        if adv_feat:
            search_memos(base_url, token, args.search)
        else:
            sys.exit(12)
    elif args.clipboard:
        if adv_feat:
            post_to_memos(args.d, args.u, from_clipboard=True)
        else:
            sys.exit(12)
    elif args.delete:
        delete_memo(base_url, token, args.delete)
    elif args.update:
        update_memo(base_url, token, args.update, visibility)
    else:
        post_to_memos(args.d, args.u)

# --- CREDITS & DOCUMENTATION ---
# Memos Project: https://github.com/usememos/memos
# Author/Contributors: @steven-tey and the Memos community.
# API Documentation: https://usememos.com/docs/api/memoservice/CreateMemo
# Version Compatibility: Built for Memos v0.22.x - v0.26.1
# -------------------------------

# --- EXIT CODE REFERENCE ---
# 0:  Success
# 10: Missing Python Libraries (requests/dotenv)
# 11: No Piped Input (Standard Input is a TTY)
# 12: Missing Configuration (MEMOS_URL or MEMOS_TOKEN)
# 13: API or Network Error (Timeout, 401 Unauthorized, etc.)

