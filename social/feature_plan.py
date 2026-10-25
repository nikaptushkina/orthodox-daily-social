"""Which website feature a Friday "From the website" post should show.

Goes down features.json in order and never repeats a feature until every one
has been shown (counting earlier posts in posts/*/content.json). A feature is
skipped for now if any of its screenshots hasn't been taken yet (for example
the live-stream card, which only appears on Sundays and feast days).

    python3 -m social.feature_plan 2026-10-30    # that Friday's feature
    python3 -m social.feature_plan --list         # the list, with what's been shown
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def features():
    return _load(os.path.join(ROOT, "features.json"))["features"]


def shown_before(date):
    counts = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "posts", "*", "content.json"))):
        day = os.path.basename(os.path.dirname(path))
        if day >= date:
            continue
        feed = _load(path).get("feed") or {}
        if feed.get("kind") == "feature":
            counts[feed.get("feature")] = counts.get(feed.get("feature"), 0) + 1
    return counts


def missing_shots(feat):
    return [s["file"] for s in feat.get("shots", [])
            if not os.path.exists(os.path.join(ROOT, "assets", "site", s["file"]))]


def for_date(date):
    counts = shown_before(date)
    feats = features()
    ready = [f for f in feats if not missing_shots(f)]
    if not ready:
        raise SystemExit("No feature has all its screenshots yet. Run the 'Fetch calendar days' workflow.")
    least = min(counts.get(f["id"], 0) for f in ready)
    pick = next(f for f in ready if counts.get(f["id"], 0) == least)
    skipped = [f["id"] for f in feats if missing_shots(f) and counts.get(f["id"], 0) <= least]
    return {"feature": pick["id"], "title": pick["title"], "skipped_for_missing_screenshots": skipped}


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        counts = shown_before("9999-12-31")
        for f in features():
            miss = missing_shots(f)
            print(f"{f['id']:<28} shown {counts.get(f['id'], 0)}x" + (f"  (missing: {', '.join(miss)})" if miss else ""))
        return
    print(json.dumps(for_date(sys.argv[1]), ensure_ascii=False))


if __name__ == "__main__":
    main()
