"""Find icons for the coming days' saints, the same way orthodoxdaily.net does.

For every saint's life in days/*.json (today onward), asks the site's own lookup,
https://orthodoxdaily.net/api/saint-image?name=<title>, which searches English
Wikipedia and Wikidata and only returns freely licensed images (preferring icons),
or nothing when it isn't confident it has the right saint. Saves the image to
assets/icons/ and records it, with its Wikimedia Commons credit, in
assets/icons/index.json. A saint with no icon is recorded too, and asked about
again after a few days in case Wikipedia has changed.

Runs in the nightly "Fetch calendar days" workflow. Standard library only.

    python3 scripts/fetch_icons.py
"""
import datetime as dt
import glob
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(ROOT, "config.json")))
ICONS = os.path.join(ROOT, "assets", "icons")
INDEX = os.path.join(ICONS, "index.json")
LOOKUP = "https://" + CONFIG["site_url"] + "/api/saint-image?name="
UA = {"User-Agent": "orthodox-daily-social (https://github.com/nikaptushkina/orthodox-daily-social)"}
RECHECK_DAYS = 3


def slug(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:80] or "saint"


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def lookup(name):
    for attempt in range(3):
        try:
            return json.loads(get(LOOKUP + urllib.parse.quote(name)).decode("utf-8"))
        except Exception as e:  # network hiccup or a 502 from Wikipedia: retry
            if attempt == 2:
                print("  lookup failed:", e)
                return None
            time.sleep(4)


def main():
    today = dt.datetime.now(ZoneInfo(CONFIG["timezone"])).date()
    os.makedirs(ICONS, exist_ok=True)
    index = json.load(open(INDEX, encoding="utf-8")) if os.path.exists(INDEX) else {}

    names = []
    for path in sorted(glob.glob(os.path.join(ROOT, "days", "*.json"))):
        if os.path.basename(path)[:10] < today.isoformat():
            continue
        day = json.load(open(path, encoding="utf-8"))
        for story in day.get("stories") or []:
            title = (story.get("title") or "").strip()
            if title and title not in names:
                names.append(title)

    found = missing = 0
    for name in names:
        known = index.get(name)
        if known and (known.get("file") or
                      (dt.date.fromisoformat(known["checked"]) > today - dt.timedelta(days=RECHECK_DAYS))):
            continue
        result = lookup(name)
        if result is None:
            continue  # couldn't ask today; try again tomorrow
        image = result.get("image")
        entry = {"checked": today.isoformat(), "file": None,
                 "page": (result.get("page") or {}).get("url")}
        if image and image.get("url"):
            ext = os.path.splitext(urllib.parse.urlparse(image["url"]).path)[1].lower()
            ext = ext if ext in (".jpg", ".jpeg", ".png", ".webp", ".gif") else ".jpg"
            rel = f"assets/icons/{slug(name)}{ext}"
            try:
                with open(os.path.join(ROOT, rel), "wb") as f:
                    f.write(get(image["url"], timeout=60))
            except Exception as e:
                print("  download failed:", name, e)
                continue
            credit = ("Icon" if image.get("isIcon") else "Image") + ": Wikimedia Commons"
            if image.get("license"):
                credit += " · " + image["license"]
            entry.update(file=rel, credit=credit, file_page=image.get("fileUrl"), is_icon=bool(image.get("isIcon")))
            found += 1
            print("icon:", name, "->", rel, f"({credit})")
        else:
            missing += 1
            print("no icon:", name, "-", result.get("reason", ""))
        index[name] = entry
        time.sleep(1)  # be gentle with the site and Wikipedia

    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(index.items())), f, ensure_ascii=False, indent=1)
    print(f"{found} new icons, {missing} saints without one")


if __name__ == "__main__":
    main()
