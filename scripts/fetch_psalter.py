"""Download the public-domain LXX2012 Psalter and save it as assets/psalter-lxx2012.json.

LXX2012 ("Septuagint in American English 2012") is public domain and is
distributed by eBible.org. This keeps the Septuagint numbering (Psalm 50
is "Have mercy on me, O God", and there is a Psalm 151).

Runs in GitHub Actions (it needs internet access). Standard library only.

    python3 scripts/fetch_psalter.py
"""
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "psalter-lxx2012.json")
SOURCES = [
    ("vpl", "https://ebible.org/Scriptures/eng-lxx2012_vpl.zip"),
    ("usfm", "https://ebible.org/Scriptures/eng-lxx2012_usfm.zip"),
]


def download(url):
    req = urllib.request.Request(url, headers={"User-Agent": "orthodox-daily-social"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def tidy(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace(" ,", ",").replace(" .", ".").replace(" ;", ";").replace(" :", ":")


def parse_vpl(data):
    """Lines like: PSA 50:1 Have mercy on me, God, ..."""
    psalter = {}
    for line in data.decode("utf-8-sig").splitlines():
        m = re.match(r"^PSA\s+(\d+):(\d+)\s+(.*)$", line.strip())
        if m:
            ps, v, t = int(m.group(1)), int(m.group(2)), tidy(m.group(3))
            if t:
                psalter.setdefault(f"Psalm {ps}", {})[str(v)] = t
    return psalter


def parse_usfm(data):
    text = data.decode("utf-8-sig")
    # Drop footnotes and cross references, keep the words of \w ...|...\w*.
    text = re.sub(r"\\f\s.*?\\f\*", "", text, flags=re.S)
    text = re.sub(r"\\x\s.*?\\x\*", "", text, flags=re.S)
    text = re.sub(r"\\\+?w\s+([^|\\]*)(\|[^\\]*)?\\\+?w\*", r"\1", text)
    psalter, chapter, verse, buf = {}, None, None, []

    def flush():
        if chapter and verse and buf:
            t = tidy(" ".join(buf))
            if t:
                psalter.setdefault(f"Psalm {chapter}", {})[str(verse)] = t

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("\\c "):
            flush()
            chapter, verse, buf = int(line.split()[1]), None, []
            continue
        if line.startswith("\\d") or line.startswith("\\s") or line.startswith("\\h") or line.startswith("\\toc") \
                or line.startswith("\\mt") or line.startswith("\\id") or line.startswith("\\ide"):
            continue  # superscriptions, headings, book titles are not verse text
        for part in re.split(r"(\\v\s+\d+\w?\s)", line):
            m = re.match(r"\\v\s+(\d+)\w?\s", part)
            if m:
                flush()
                verse, buf = int(m.group(1)), []
            elif verse is not None:
                cleaned = re.sub(r"\\[a-z]+\d*\*?", " ", part)
                buf.append(cleaned)
    flush()
    return psalter


def from_zip(kind, blob):
    z = zipfile.ZipFile(io.BytesIO(blob))
    if kind == "vpl":
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        return parse_vpl(b"\n".join(z.read(n) for n in names))
    names = [n for n in z.namelist() if n.lower().endswith((".usfm", ".sfm")) and "PSA" in n.upper()]
    return parse_usfm(b"\n".join(z.read(n) for n in names))


def check(psalter):
    problems = []
    if len(psalter) < 150:
        problems.append(f"only {len(psalter)} psalms found")
    if "Psalm 151" not in psalter:
        problems.append("no Psalm 151, so this is not Septuagint numbering")
    p50 = (psalter.get("Psalm 50") or {}).get("1", "")
    if "mercy" not in p50.lower():
        problems.append(f"Psalm 50:1 does not read like 'Have mercy': {p50[:60]!r}")
    return problems


def main():
    errors = []
    for kind, url in SOURCES:
        try:
            psalter = from_zip(kind, download(url))
        except Exception as e:
            errors.append(f"{url}: {e}")
            continue
        problems = check(psalter)
        if problems:
            errors.append(f"{url}: " + "; ".join(problems))
            continue
        ordered = {f"Psalm {n}": psalter[f"Psalm {n}"] for n in sorted(int(k.split()[1]) for k in psalter)}
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"_source": f"LXX2012 Septuagint in American English 2012, public domain, from {url}",
                       "psalms": ordered}, f, ensure_ascii=False, indent=1)
        total = sum(len(v) for v in ordered.values())
        print(f"Saved {len(ordered)} psalms ({total} verses) from {url} to {OUT}")
        return 0
    print("Could not build the Psalter:\n" + "\n".join(errors))
    return 1


if __name__ == "__main__":
    sys.exit(main())
