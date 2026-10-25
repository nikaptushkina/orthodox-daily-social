"""Build one day's posts from posts/<date>/content.json and days/<date>.json.

    python3 -m social.build 2026-10-25            # stills, Reel cover, post.json, preview
    python3 -m social.build 2026-10-25 --video    # also a silent test video of the Reel
    python3 -m social.build 2026-10-25 --no-reel  # leave the Reel out entirely
    python3 -m social.build 2026-10-25 --stills   # redo the images only, keeping the finished Reel

Writes JPEGs, the Reel cover, post.json (what to publish) and preview.jpg (a
contact sheet for the pull request) into posts/<date>/. The Reel video itself,
with Kokoro voice-over and music, is made by social.voice in the "Add voice and
music to the Reel" workflow once the branch is pushed.
Scripture is always taken word for word from the day's data or from
assets/psalter-lxx2012.json; content.json only says which reading to use.
"""
import argparse
import html as htmllib
import json
import os
import re
import sys

from . import templates as T
from .render import render_cover, render_reel, render_stills

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def clean(text):
    text = re.sub(r"<[^>]+>", "", text or "").replace("\u00ad", "")  # soft hyphens inside words
    return re.sub(r"\s+", " ", htmllib.unescape(text)).strip()


def reading_verses(day, index):
    readings = day.get("readings") or []
    if index >= len(readings):
        raise SystemExit(f"reading index {index} not in this day's {len(readings)} readings")
    r = readings[index]
    verses = [{"n": v.get("verse"), "c": v.get("chapter"), "t": clean(v.get("content"))}
              for v in (r.get("passage") or [])]
    if not verses:
        raise SystemExit(f"reading {index} ({r.get('display')}) has no passage text")
    return r, verses


def psalm_verses(name, first=None, last=None):
    from .psalm_plan import psalter
    psalms = psalter()
    if name not in psalms:
        raise SystemExit(f"{name} is not in assets/psalter-lxx2012.json")
    out = []
    for k, t in psalms[name].items():
        n = int(k)
        if (first is None or n >= first) and (last is None or n <= last):
            out.append({"n": n, "t": clean(t)})
    return out


def chunk(verses, budget):
    """Split verses into groups of roughly `budget` characters, never splitting a verse."""
    def ends_sentence(v):
        return re.search(r"[.?!;:][”’\"')]*\s*$", v["t"]) is not None

    groups, cur, size = [], [], 0
    for v in verses:
        n = len(v["t"])
        # Break before this verse when the group is full and ends a sentence;
        # if it ends mid-sentence, allow up to 60% extra before forcing a break.
        if cur and size + n > budget and (ends_sentence(cur[-1]) or size + n > budget * 1.6):
            groups.append(cur)
            cur, size = [], 0
        cur.append(v)
        size += n
    if cur:
        groups.append(cur)
    # Fold a very short last group into the previous one.
    if len(groups) > 1 and sum(len(v["t"]) for v in groups[-1]) < budget * 0.25:
        groups[-2].extend(groups.pop())
    return groups


def ref_label(book, verses):
    """'Luke 7:1–5' or 'Luke 7:36–8:3' for a group of verses."""
    a, b = verses[0], verses[-1]
    span = f"{a['n']}" if a["n"] == b["n"] else f"{a['n']}–{b['n']}"
    if not a.get("c"):  # psalms from the Psalter: "Psalm 102:1–3"
        return f"{book}:{span}"
    if a.get("c") == b.get("c"):
        return f"{book} {a['c']}:{span}"
    return f"{book} {a['c']}:{a['n']}–{b['c']}:{b['n']}"


def reading_book(r):
    """The book's name for labels. Orthocal gives "OT" for Old Testament (Vespers) readings
    and "Apostol" for Epistles, so take the name from the display text instead."""
    book = r.get("book") or ""
    if book in ("OT", "Apostol", "") or not re.match(r"^[0-9]?\s?[A-Za-z]", book):
        display = (r.get("display") or "").split(" - ")[-1]
        m = re.match(r"^(.+?)\s+\d+[.:]", display)
        book = m.group(1) if m else display
    return book


def reading_ref(r):
    """'Isaiah 63:15–64:5, 8–9' from Orthocal's 'Composite 16 - Isaiah 63.15-64.5, 8-9'."""
    display = (r.get("display") or "").split(" - ")[-1]
    return display.replace(".", ":").replace("-", "–")


def is_composite(r):
    """Orthocal's 'Composite N - ...' readings come as one unnumbered block."""
    passage = r.get("passage") or []
    return (r.get("display") or "").startswith("Composite") or (
        len(passage) == 1 and not passage[0].get("book") and len(passage[0].get("content") or "") > 400)


def reel_spec(content, day):
    """The Reel's screens: Scripture word for word, grouped into screens."""
    reel = content.get("reel")
    if not reel:
        return None
    spec = dict(reel)
    if "screens" not in spec:
        if "psalm" in spec:
            p = spec["psalm"]
            verses = psalm_verses(p["name"], p.get("from"), p.get("to"))
            groups = chunk(verses, spec.get("screen_chars", 230))
            spec["screens"] = [{"label": ref_label(p["name"], g), "verses": g} for g in groups]
        else:
            r, verses = reading_verses(day, spec["reading"]["index"])
            book = spec.get("ref_book") or reading_book(r)
            spec["_reading"] = {"book": book, "display": r.get("display"), "source": r.get("source")}
            spec.setdefault("ref", reading_ref(r))
            if is_composite(r):
                # One block of text stitched from several places, with no real verse numbers:
                # split it by sentence and label every screen with the whole reference.
                text = " ".join(v["t"] for v in verses)
                sentences = [{"n": "", "t": t} for t in re.split(r"(?<=[.?!;])\s+(?=[A-Z“\"‘'])", text) if t.strip()]
                groups = chunk(sentences, spec.get("screen_chars", 230))
                spec["screens"] = [{"label": spec["ref"], "verses": g} for g in groups]
            else:
                groups = chunk(verses, spec.get("screen_chars", 230))
                spec["screens"] = [{"label": ref_label(book, g), "verses": g} for g in groups]
    return spec


def load_day(date):
    content = load_json(os.path.join(ROOT, "posts", date, "content.json"))
    day_path = os.path.join(ROOT, "days", f"{date}.json")
    day = load_json(day_path) if os.path.exists(day_path) else {}
    return content, day


def contact_sheet(outdir, names):
    from PIL import Image
    thumbs = []
    for n in names:
        im = Image.open(os.path.join(outdir, n)).convert("RGB")
        h = 540
        thumbs.append(im.resize((round(im.width * h / im.height), h)))
    W = sum(t.width for t in thumbs) + 12 * (len(thumbs) - 1)
    sheet = Image.new("RGB", (W, 540), "white")
    x = 0
    for t in thumbs:
        sheet.paste(t, (x, 0))
        x += t.width + 12
    sheet.save(os.path.join(outdir, "preview.jpg"), quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--no-reel", action="store_true", help="leave the Reel out")
    ap.add_argument("--video", action="store_true", help="also render a silent test video of the Reel")
    ap.add_argument("--stills", action="store_true",
                    help="re-render only the Story and carousel; keep the Reel already in post.json")
    args = ap.parse_args()

    cfg = load_json(os.path.join(ROOT, "config.json"))
    site = cfg["site_url"]
    outdir = os.path.join(ROOT, "posts", args.date)
    content, day = load_day(args.date)

    stills, items, preview = [], [], []

    # Story (every day)
    if content.get("story"):
        s = dict(content["story"])
        s.setdefault("calendar_label", cfg["calendar_label"])
        stills += T.story(s, site)
        items.append({"id": "story", "type": "STORY", "media": ["story.jpg"]})
        preview.append("story.jpg")

    # Feed carousel (by weekday)
    feed = content.get("feed")
    if feed:
        kind = feed["kind"]
        if kind == "week_ahead":
            feed.setdefault("calendar_label", cfg["calendar_label"])
            slides = T.week_ahead(feed, site)
        elif kind == "saint":
            icon = feed.get("icon")
            if icon:  # "assets/icons/....jpg" (from the nightly lookup) or "icon.jpg" (added to this day's folder)
                path = icon if os.path.isabs(icon) else (
                    os.path.join(outdir, icon) if os.path.exists(os.path.join(outdir, icon)) else os.path.join(ROOT, icon))
                if not os.path.exists(path):
                    raise SystemExit(f"icon not found: {icon}")
                feed = dict(feed, icon="file://" + os.path.abspath(path))
            slides = T.saint(feed, site)
        elif kind == "feast":
            slides = T.feast(feed, site)
        elif kind == "word":
            r, verses = reading_verses(day, feed["reading"]["index"])
            book = feed.get("ref_book") or reading_book(r) or feed["book_title"]
            pages = [{"ref": ref_label(book, g), "verses": g} for g in chunk(verses, feed.get("page_chars", 560))]
            slides = T.word(feed, pages, site)
        else:
            raise SystemExit(f"unknown feed kind: {kind}")
        # Feed slides get a prefix so they don't collide with the Story.
        slides = [(f"feed-{n}", h, w, hh) for n, h, w, hh in slides]
        stills += slides
        names = [n for n, *_ in slides]
        items.append({"id": "feed", "type": "CAROUSEL", "media": names, "caption": feed["caption"]})
        preview += names

    written = render_stills(stills, outdir)

    # Reel (Wednesday psalm, Saturday Vespers or Gospel). Here only its cover; the
    # video with voice and music is added by the workflow (social.voice).
    reel = content.get("reel")
    old_post = os.path.join(outdir, "post.json")
    if reel and args.stills and os.path.exists(old_post):
        kept = [i for i in load_json(old_post).get("items", []) if i.get("type") == "REEL"]
        items += kept
        preview += [i["cover"] for i in kept if i.get("cover") and os.path.exists(os.path.join(outdir, i["cover"]))]
    elif reel and not args.no_reel:
        spec = reel_spec(content, day)
        built = T.reel(spec, site)
        cover = os.path.join(outdir, "reel-cover.jpg")
        if args.video:
            render_reel(built, os.path.join(outdir, "reel.mp4"), cover)
        else:
            render_cover(built, cover)
        written.append("reel-cover.jpg")
        items.append({"id": "reel", "type": "REEL", "media": ["reel.mp4"], "cover": "reel-cover.jpg",
                      "caption": reel["caption"], "duration": built["duration"], "audio": "pending"})
        preview.append("reel-cover.jpg")

    post = {"date": args.date, "calendar": cfg["calendar_label"], "tradition": cfg["tradition"], "items": items}
    with open(os.path.join(outdir, "post.json"), "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=1)
    if preview:
        contact_sheet(outdir, preview)
    print(json.dumps({"written": written,
                      "items": [i["id"] for i in items]}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
