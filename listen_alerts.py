"""
Alert stream listener for live category delivery over SSE.

Usage:
    python test_listen_alerts.py
    python test_listen_alerts.py --categories transient,agn
    python test_listen_alerts.py --categories all
    python test_listen_alerts.py --categories '*'
    python test_listen_alerts.py --categories all --replay earliest --no-follow
    python test_listen_alerts.py --categories all --replay earliest --limit 100 --follow
"""
import json
import argparse
import requests
import adss

BASE_URL = "https://ai-scope.cbpf.br"


def make_session(token):
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {token}"
    return s


def fetch_categories(s):
    resp = s.get(f"{BASE_URL}/adss/v1/alerts/categories")
    resp.raise_for_status()
    return resp.json()


def pick_categories(s):
    """Show registered categories and let the user pick."""
    cats = fetch_categories(s)
    print("\n=== Registered categories ===")
    if cats:
        for i, c in enumerate(cats, 1):
            desc = f"  — {c['description']}" if c.get("description") else ""
            print(f"  [{i}] {c['name']}{desc}")
    else:
        print("  (none registered — type a name manually)")
    print()
    raw = input("  Enter categories to subscribe to (comma-separated or numbers): ").strip()
    selected = []
    for token in raw.split(","):
        token = token.strip()
        if token.isdigit():
            idx = int(token) - 1
            if 0 <= idx < len(cats):
                selected.append(cats[idx]["name"])
        elif token:
            selected.append(token)
    return selected


def listen(s, categories, replay=None, limit=None, follow=True):
    """Open an SSE connection and print replayed and/or live alerts."""
    cats_param = ",".join(categories)
    mode = "live"
    if replay:
        mode = f"replay={replay}" + (" + live follow" if follow else "")
    print(f"\nListening to categories: {categories}  mode={mode}  (Ctrl+C to stop)\n")

    stream_headers = dict(s.headers)
    stream_headers["Accept"] = "text/event-stream"
    params = {"categories": cats_param, "token": s.headers["Authorization"].split(" ", 1)[1]}
    if replay:
        params["replay_from"] = replay
        params["follow"] = "true" if follow else "false"
    if limit is not None:
        params["replay_limit"] = str(limit)

    count = 0
    with requests.get(
        f"{BASE_URL}/adss/v1/alerts/stream",
        params=params,
        headers=stream_headers,
        stream=True,
    ) as resp:
        resp.raise_for_status()
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if not line.startswith("data:"):
                continue
            data = json.loads(line[len("data:"):].strip())

            if data.get("type") == "connected":
                print(f"[connected]  categories={data.get('categories')}\n")
                continue
            if data.get("type") == "replay_started":
                print(f"[replay_started] categories={data.get('categories')} from={data.get('from')}\n")
                continue
            if data.get("type") == "replay_complete":
                print(f"\n[replay_complete] count={data.get('count')}\n")
                if not follow:
                    return
                continue
            if data.get("type") == "keepalive":
                continue

            if data.get("type") == "replay":
                print_alert(data.get("payload", {}), prefix="[REPLAY]")
            else:
                print_alert(data, prefix="[LIVE] ")
            
            count += 1
            if count % 10 == 0:
                print(f"\nReceived {count} alerts so far...\n")


def print_alert(a, index=None, prefix=None):
    mag = a.get("magnitude")
    mag_s = f"{mag:.3f}" if mag is not None else "?"
    prefix = f"[{index:>6}]" if index is not None else (prefix or "[LIVE] ")
    print(
        f"{prefix}  "
        f"id={a.get('alert_id', '?'):<22s}  "
        f"src={a.get('source', '?'):<6s}  "
        f"cat={a.get('category') or '?':<16s}  "
        f"ra={str(a.get('ra') or '?'):>10}  "
        f"dec={str(a.get('dec') or '?'):>10}  "
        f"mag={mag_s:>7}  "
        f"band={a.get('filter_band') or '?'}"
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", type=str, default="all",
                        help="Comma-separated categories to stream, e.g. transient,supernova. Use '*' for all registered categories.")
    parser.add_argument("--replay", choices=["earliest", "latest"], default=None,
                        help="Replay retained Kafka messages over SSE before live follow.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum replay alerts to emit before replay completes.")
    parser.add_argument("--follow", dest="follow", action="store_true",
                        help="After replay, continue in live follow mode.")
    parser.add_argument("--no-follow", dest="follow", action="store_false",
                        help="Stop after replay completes.")
    parser.set_defaults(follow=True)
    args = parser.parse_args()

    cl = adss.ADSSClient(
        base_url=BASE_URL,
        username="matias",
        password="asdf",
    )
    s = make_session(cl.auth.token)
    print(f"Logged in as: {cl.current_user.username}")

    # --- Live stream ---
    if args.categories:
        if args.categories.strip() == "*":
            categories = [c["name"] for c in fetch_categories(s)]
        else:
            categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    else:
        categories = pick_categories(s)

    if not categories:
        print("No categories selected — nothing to listen to.")
        return

    listen(s, categories, replay=args.replay, limit=args.limit, follow=args.follow)


if __name__ == "__main__":
    main()
