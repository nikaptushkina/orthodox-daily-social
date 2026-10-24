"""Which psalm goes in a given Wednesday's Reel.

The rotation is the whole Psalter, Psalm 1 to Psalm 151 in Septuagint
numbering, from assets/psalter-lxx2012.json (public domain, built by
scripts/fetch_psalter.py in the nightly workflow). A psalm too long for one
Reel is split into consecutive parts, so each Wednesday moves on to the next
part or psalm and nothing repeats until the whole Psalter has been read.
Dates listed in psalm-plan.json "dates" override the rotation for that day.

    python3 -m social.psalm_plan 2026-10-28    # that Wednesday's psalm
    python3 -m social.psalm_plan --list        # the full rotation
"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PSALTER = os.path.join(ROOT, "assets", "psalter-lxx2012.json")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def psalter():
    if not os.path.exists(PSALTER):
        raise SystemExit("The Psalter has not been downloaded yet (assets/psalter-lxx2012.json is missing). "
                         "Run the 'Fetch calendar days' workflow in the Actions tab; it builds the Psalter on its first run.")
    return _load(PSALTER)["psalms"]


def rotation():
    plan = _load(os.path.join(ROOT, "psalm-plan.json"))
    psalms = psalter()
    budget = plan.get("max_chars_per_reel", 900)
    out = []
    for name in plan.get("order") or list(psalms):
        verses = [(int(k), len(t)) for k, t in psalms[name].items()]
        parts, cur, size = [], [], 0
        for n, length in verses:
            if cur and size + length > budget:
                parts.append(cur)
                cur, size = [], 0
            cur.append(n)
            size += length
        if cur:
            parts.append(cur)
        if len(parts) > 1 and sum(l for n, l in verses if n in parts[-1]) < budget * 0.35:
            parts[-2].extend(parts.pop())
        for i, p in enumerate(parts):
            entry = {"name": name, "from": p[0], "to": p[-1]}
            if len(parts) > 1:
                entry["part"] = f"{i + 1} of {len(parts)}"
            out.append(entry)
    return out


def for_date(date):
    plan = _load(os.path.join(ROOT, "psalm-plan.json"))
    if date.isoformat() in plan.get("dates", {}):
        return plan["dates"][date.isoformat()]
    start = dt.date.fromisoformat(plan["start"])
    rot = rotation()
    return rot[((date - start).days // 7) % len(rot)]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        rot = rotation()
        for i, e in enumerate(rot):
            part = f" (part {e['part']})" if e.get("part") else ""
            print(f"{i + 1:3d}. {e['name']}:{e['from']}–{e['to']}{part}")
        print(f"{len(rot)} Wednesdays, about {len(rot) / 52:.1f} years before the cycle repeats")
        return
    print(json.dumps(for_date(dt.date.fromisoformat(sys.argv[1]))))


if __name__ == "__main__":
    main()
