"""Which psalm goes in a given Wednesday's Reel.

The rotation is every psalm in assets/psalms.json (the site's texts), in
order. A psalm too long for one Reel is split into consecutive parts, so
each Wednesday moves on to the next part or psalm, and nothing repeats
until the whole collection has been read. Dates listed in
psalm-plan.json "dates" override the rotation for that day only.

    python3 -m social.psalm_plan 2026-10-28    # that Wednesday's psalm
    python3 -m social.psalm_plan --list        # the full rotation
"""
import datetime as dt
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def rotation():
    plan = _load("psalm-plan.json")
    psalms = _load(os.path.join("assets", "psalms.json"))
    budget = plan.get("max_chars_per_reel", 900)
    order = plan.get("order") or list(psalms)
    out = []
    for name in order:
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
        # Fold a short last part back into the previous one.
        if len(parts) > 1 and sum(l for n, l in verses if n in parts[-1]) < budget * 0.35:
            parts[-2].extend(parts.pop())
        for i, p in enumerate(parts):
            entry = {"name": name, "from": p[0], "to": p[-1]}
            if len(parts) > 1:
                entry["part"] = f"{i + 1} of {len(parts)}"
            out.append(entry)
    return out


def for_date(date):
    plan = _load("psalm-plan.json")
    if date.isoformat() in plan.get("dates", {}):
        return plan["dates"][date.isoformat()]
    start = dt.date.fromisoformat(plan["start"])
    weeks = (date - start).days // 7
    rot = rotation()
    return rot[weeks % len(rot)]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for i, e in enumerate(rotation()):
            part = f" (part {e['part']})" if e.get("part") else ""
            print(f"{i + 1:2d}. {e['name']}:{e['from']}–{e['to']}{part}")
        return
    date = dt.date.fromisoformat(sys.argv[1])
    print(json.dumps(for_date(date)))


if __name__ == "__main__":
    main()
