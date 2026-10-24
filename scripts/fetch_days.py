"""Save the coming days' calendar data from Orthocal into days/YYYY-MM-DD.json.

Uses the same endpoint and settings as orthodoxdaily.net (see config.json):
/api/{tradition}/{calendar}/{y}/{m}/{d}/?translation={translation}

Standard library only. Run from the repository root:
    python3 scripts/fetch_days.py            # today + days_ahead
    python3 scripts/fetch_days.py 2026-11-08 # one date
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.request
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(ROOT, "config.json")))


def url_for(day):
    c = CONFIG
    return (f"https://orthocal.info/api/{c['tradition']}/{c['calendar']}/"
            f"{day.year}/{day.month}/{day.day}/?translation={c['translation']}")


def fetch(day):
    req = urllib.request.Request(url_for(day), headers={"User-Agent": "orthodox-daily-social"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # network hiccup: retry twice
            if attempt == 2:
                raise
            print("retrying", day, e)
            time.sleep(5)


def main():
    if len(sys.argv) > 1:
        days = [dt.date.fromisoformat(a) for a in sys.argv[1:]]
    else:
        today = dt.datetime.now(ZoneInfo(CONFIG["timezone"])).date()
        days = [today + dt.timedelta(days=i) for i in range(CONFIG["days_ahead"] + 1)]
    os.makedirs(os.path.join(ROOT, "days"), exist_ok=True)
    for day in days:
        data = fetch(day)
        data["_source"] = url_for(day)
        path = os.path.join(ROOT, "days", f"{day.isoformat()}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print("saved", path, "-", (data.get("titles") or [data.get("summary_title")])[0])


if __name__ == "__main__":
    main()
