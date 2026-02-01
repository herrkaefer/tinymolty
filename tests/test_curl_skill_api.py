#!/usr/bin/env python3
"""
Run Moltbook API checks using curl patterns from skill.md.
"""
import json
import os
import subprocess
from pathlib import Path


def _load_api_key() -> str:
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    data = json.loads(cred_path.read_text())
    api_key = data.get("api_key")
    if not api_key:
        raise SystemExit("Missing api_key in credentials.json")
    return api_key


def _run(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def main() -> None:
    api_key = _load_api_key()
    base = "https://www.moltbook.com/api/v1"
    verbose = os.getenv("CURL_VERBOSE") == "1"
    # Use -v only so JSON stays on stdout; verbose headers go to stderr.
    curl_debug_flags = "-v" if verbose else ""

    print(f"API_KEY={api_key}")

    status_cmd = (
        f"curl -sS {curl_debug_flags} -w '\\nHTTP %{ '{http_code}' }\\n' "
        f"\"{base}/agents/status\" "
        f"-H \"Authorization: Bearer {api_key}\""
    )
    print(f"STATUS_CMD={status_cmd}")
    code, status_out, err = _run(status_cmd)
    print("--- status ---")
    if code != 0:
        print(err.strip() or status_out.strip())
        raise SystemExit(code)
    if verbose and err.strip():
        print(err.strip())
    print(status_out[:500])

    me_cmd = (
        f"curl -sS {curl_debug_flags} -w '\\nHTTP %{ '{http_code}' }\\n' "
        f"\"{base}/agents/me\" "
        f"-H \"Authorization: Bearer {api_key}\""
    )
    print(f"ME_CMD={me_cmd}")
    code, me_out, err = _run(me_cmd)
    print("--- me ---")
    if code != 0:
        print(err.strip() or me_out.strip())
        raise SystemExit(code)
    if verbose and err.strip():
        print(err.strip())
    print(me_out[:500])

    # 1) Get a post ID (new posts)
    feed_cmd = (
        f"curl -sS {curl_debug_flags} \"{base}/feed?sort=new&limit=25\" "
        f"-H \"Authorization: Bearer {api_key}\""
    )
    print(f"FEED_CMD={feed_cmd}")
    code, out, err = _run(feed_cmd)
    print("--- feed ---")
    if code != 0:
        print(err.strip() or out.strip())
        raise SystemExit(code)
    if verbose and err.strip():
        print(err.strip())

    try:
        payload = json.loads(out)
        posts = payload.get("posts", [])
    except Exception as exc:
        print("Feed parse failed:", exc)
        print(out[:200])
        raise SystemExit(1)

    if not posts:
        raise SystemExit("No posts found in feed")

    # Prefer a post not authored by the current agent
    try:
        me_data = json.loads(me_out)
        me_id = me_data.get("agent", {}).get("id")
    except Exception:
        me_id = None

    post_id = ""
    for post in posts:
        author = post.get("author") or {}
        author_id = author.get("id")
        if me_id and author_id == me_id:
            continue
        post_id = post.get("id", "")
        if post_id:
            break

    if not post_id:
        raise SystemExit("No suitable non-self post found in feed")

    print(f"POST_ID={post_id}")

    # 1.5) Get post details
    post_cmd = (
        f"curl -sS {curl_debug_flags} -w '\\nHTTP %{ '{http_code}' }\\n' "
        f"\"{base}/posts/{post_id}\" "
        f"-H \"Authorization: Bearer {api_key}\""
    )
    print(f"POST_CMD={post_cmd}")
    code, out, err = _run(post_cmd)
    print("--- post ---")
    if code != 0:
        print(err.strip() or out.strip())
    else:
        if verbose and err.strip():
            print(err.strip())
        print(out[:500])

    # 2) Upvote
    upvote_cmd = (
        f"curl -sS {curl_debug_flags} -w '\\nHTTP %{ '{http_code}' }\\n' "
        f"-X POST \"{base}/posts/{post_id}/upvote\" "
        f"-H \"Authorization: Bearer {api_key}\""
    )
    print(f"UPVOTE_CMD={upvote_cmd}")
    code, out, err = _run(upvote_cmd)
    print("--- upvote ---")
    if code != 0:
        print(err.strip() or out.strip())
    else:
        if verbose and err.strip():
            print(err.strip())
        print(out[:500])

    # 3) Comment
    comment_cmd = (
        f"curl -sS {curl_debug_flags} -w '\\nHTTP %{ '{http_code}' }\\n' "
        f"-X POST \"{base}/posts/{post_id}/comments\" "
        f"-H \"Authorization: Bearer {api_key}\" "
        f"-H \"Content-Type: application/json\" "
        f"-d '{{\"content\":\"Test comment from curl\"}}'"
    )
    print(f"COMMENT_CMD={comment_cmd}")
    code, out, err = _run(comment_cmd)
    print("--- comment ---")
    if code != 0:
        print(err.strip() or out.strip())
    else:
        if verbose and err.strip():
            print(err.strip())
        print(out[:500])


if __name__ == "__main__":
    main()
