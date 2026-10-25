"""Publish one day's approved posts to Instagram.

Runs in GitHub Actions after a posts pull request is merged and the media is
live on GitHub Pages. Reads posts/<date>/post.json, publishes each item
(Story, carousel, Reel) through the Instagram API with Instagram Login, and
records what it published in posts/<date>/published.json so nothing is ever
posted twice.

Needs two repository secrets: IG_USER_ID and IG_ACCESS_TOKEN.
Standard library only.

    python3 scripts/publish.py 2026-10-25              # publish everything now
    python3 scripts/publish.py 2026-10-25 --when-due   # only what is due (posting_times in config.json)
    python3 scripts/publish.py 2026-10-25 --dry-run    # show what would happen
"""
import argparse
import subprocess
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(ROOT, "config.json")))
API = f"https://graph.instagram.com/{CONFIG['graph_api_version']}"


class ApiError(Exception):
    pass


def call(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        url += "?" + data.decode()
        data = None
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise ApiError(f"{method} {path} failed ({e.code}): {body}") from None


def media_url(date, name):
    return f"{CONFIG['pages_base_url']}/posts/{date}/{urllib.parse.quote(name)}"


def wait_until_live(url, tries=30):
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(10)
    raise ApiError(f"media is not reachable yet: {url}")


def wait_until_ready(container, token, tries=60):
    for _ in range(tries):
        status = call("GET", container, {"fields": "status_code,status", "access_token": token})
        code = status.get("status_code")
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise ApiError(f"container {container} failed: {status}")
        time.sleep(10)
    raise ApiError(f"container {container} was not ready in time")


def create(user, token, **params):
    params["access_token"] = token
    return call("POST", f"{user}/media", params)["id"]


def publish_container(user, token, container):
    wait_until_ready(container, token)
    return call("POST", f"{user}/media_publish", {"creation_id": container, "access_token": token})["id"]


def publish_item(date, item, user, token):
    kind = item["type"]
    urls = [media_url(date, m) for m in item["media"]]
    for u in urls:
        wait_until_live(u)
    if kind == "STORY":
        c = create(user, token, media_type="STORIES", image_url=urls[0])
    elif kind == "CAROUSEL":
        children = [create(user, token, image_url=u, is_carousel_item="true") for u in urls]
        for ch in children:
            wait_until_ready(ch, token)
        c = create(user, token, media_type="CAROUSEL", children=",".join(children), caption=item.get("caption", ""))
    elif kind == "REEL":
        params = dict(media_type="REELS", video_url=urls[0], caption=item.get("caption", ""), share_to_feed="true")
        if item.get("cover"):
            cover = media_url(date, item["cover"])
            wait_until_live(cover)
            params["cover_url"] = cover
        c = create(user, token, **params)
    else:
        raise ApiError(f"unknown item type {kind}")
    return publish_container(user, token, c)


def due_time(date, item):
    """When an item may go out: the Story as soon as it is approved, feed posts at
    that weekday's time in config.json "posting_times" (local time in "timezone")."""
    tz = ZoneInfo(CONFIG["timezone"])
    day = dt.date.fromisoformat(date)
    times = CONFIG.get("posting_times", {})
    key = "story" if item["type"] == "STORY" else day.strftime("%A").lower()
    value = str(times.get(key, "00:00"))
    hh, mm = (int(x) for x in value.split(":")) if ":" in value else (0, 0)
    return dt.datetime(day.year, day.month, day.day, hh, mm, tzinfo=tz)


def when_label(due):
    if due.hour == 0 and due.minute == 0:
        return "as soon as it is approved"
    if due.hour == 12 and due.minute == 0:
        return due.strftime("%A at noon")
    return due.strftime("%A at %-I:%M %p").replace(":00 ", " ").replace("AM", "am").replace("PM", "pm")


def record(folder, item_id):
    """Commit and push published.json right after each post (in GitHub Actions), so a later run
    never posts the same thing twice, even if this run stops while waiting."""
    if os.environ.get("RECORD_PUSH") != "1":
        return
    rel = os.path.relpath(os.path.join(folder, "published.json"), ROOT)
    cmds = [["git", "add", rel], ["git", "commit", "-q", "-m", f"Published {item_id} [skip ci]"],
            ["git", "pull", "-q", "--rebase"], ["git", "push", "-q"]]
    for c in cmds:
        r = subprocess.run(c, cwd=ROOT, capture_output=True, text=True)
        if r.returncode and c[1] != "commit":
            print("  could not save the record yet:", (r.stderr or r.stdout).strip()[:200])
            return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--when-due", action="store_true",
                    help="only publish items whose posting time has come (and only on their own day)")
    ap.add_argument("--wait", type=int, default=0, metavar="SECONDS",
                    help="with --when-due: stay and post later items when their time comes, waiting at most this long")
    args = ap.parse_args()
    started = time.time()
    while True:
        status, next_due = publish_pass(args)
        if not (args.when_due and args.wait and next_due):
            break
        now = dt.datetime.now(ZoneInfo(CONFIG["timezone"]))
        seconds = (next_due - now).total_seconds() + 20
        if time.time() + seconds - started > args.wait:
            print(f"Next post is due {when_label(next_due)}; handing over to a new run.")
            out = os.environ.get("GITHUB_OUTPUT")
            if out:
                with open(out, "a") as f:
                    f.write(f"continue=true\ncontinue_date={args.date}\n")
            break
        print(f"Waiting until {when_label(next_due)} for the next post…", flush=True)
        time.sleep(max(0, seconds))
    return status


def publish_pass(args):
    """Publish what is due now. Returns (exit status, the next later posting time today or None)."""
    now = dt.datetime.now(ZoneInfo(CONFIG["timezone"]))
    next_due = None

    folder = os.path.join(ROOT, "posts", args.date)
    post = json.load(open(os.path.join(folder, "post.json"), encoding="utf-8"))
    done_path = os.path.join(folder, "published.json")
    done = json.load(open(done_path)) if os.path.exists(done_path) else {}

    user = os.environ.get("IG_USER_ID", "")
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    if not args.dry_run and not (user and token):
        print("IG_USER_ID / IG_ACCESS_TOKEN are not set: nothing published.")
        return 1, None

    failures = 0
    for item in post["items"]:
        if item["id"] in done:
            print(f"{item['id']}: already published ({done[item['id']]['media_id']})")
            continue
        due = due_time(args.date, item)
        if args.dry_run:
            print(f"{item['id']}: would publish {item['type']} with {item['media']}, {when_label(due)}")
            continue
        if args.when_due:
            if now.date() > due.date():
                print(f"{item['id']}: not posted, its day is over. To post it anyway, run "
                      f"'Publish approved posts' by hand with the date {args.date}.")
                continue
            if now < due:
                wait = f"{due:%A}, its own day" if (due.hour, due.minute) == (0, 0) else when_label(due)
                print(f"{item['id']}: approved, waiting until {wait}")
                if due.date() == now.date() and (next_due is None or due < next_due):
                    next_due = due
                continue
        try:
            media_id = publish_item(args.date, item, user, token)
        except ApiError as e:
            failures += 1
            print(f"{item['id']}: FAILED: {e}")
            continue
        done[item["id"]] = {"media_id": media_id, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(done_path, "w") as f:
            json.dump(done, f, indent=1)
        print(f"{item['id']}: published as {media_id}", flush=True)
        record(folder, item["id"])
    return (1 if failures else 0), next_due


if __name__ == "__main__":
    sys.exit(main())
