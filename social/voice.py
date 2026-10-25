"""Make a day's Reel with Kokoro voice-over and background music.

Runs in the "Add voice and music to the Reel" workflow, which starts a
Kokoro-FastAPI server next to it. For each screen of the Reel (title, verse
screens, end) it reads the text aloud, times every screen to its narration,
renders the video, lays the music underneath (quieter while the voice speaks)
and writes posts/<date>/reel.mp4, reel-cover.jpg, voice.json and updates
post.json.

    python3 -m social.voice 2026-10-28 --music ../assets/music/track.mp3
    python3 -m social.voice 2026-10-28 --fake-voice --fps 6   # offline test, tones instead of a voice

Voice, speed and music level are set in config.json under "reel_audio".
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

from . import templates as T
from .build import ROOT, load_day, load_json, reel_spec
from .render import render_reel

TITLE_LEAD, LEAD, TAIL, END_HOLD = 1.0, 0.8, 1.0, 3.0   # seconds of quiet around each clip
SILENT_END = 5.0                                        # end screen when nothing is read there

GOSPELS = {"Matthew", "Mark", "Luke", "John"}
DOXOLOGY = ("Glory to the Father, and to the Son, and to the Holy Spirit, "
            "now and ever, and unto ages of ages. Amen.")


def _book_from_display(display):
    display = (display or "").split(" - ")[-1]
    m = re.match(r"^(.+?)\s+\d+[.:]", display)
    return m.group(1) if m else display


def narration(spec):
    """What is read on each screen: [intro, screen 1, ..., closing]. '' means silence."""
    v = spec.get("voice") or {}
    kind = spec.get("kind", "")
    if "psalm" in spec:
        name = spec["psalm"]["name"]
        part = (spec.get("title") or {}).get("kicker", "")
        m = re.search(r"Part (\d+) of (\d+)", part)
        intro = f"{name}." if not m or m.group(1) == "1" else f"{name}, continued."
        closing = DOXOLOGY if not m or m.group(1) == m.group(2) else ""
    else:
        r = spec.get("_reading") or {}
        book = r.get("book") if r.get("book") in GOSPELS else _book_from_display(r.get("display"))
        if kind == "gospel" or book in GOSPELS:
            intro = f"The reading from the Holy Gospel according to Saint {book}."
            closing = "Glory to Thee, O Lord, glory to Thee."
        else:
            intro, closing = f"The reading from {book}.", ""
    intro = v.get("intro", intro)
    closing = v.get("closing", closing)
    screens = [" ".join(x["t"] for x in s["verses"]) for s in spec["screens"]]
    return [intro] + screens + [closing]


def speakable(text):
    """Small fixes so the voice reads naturally; the screen keeps the original text."""
    text = re.sub(r"[“”]", '"', text)
    text = re.sub(r"[‘’]", "'", text)
    text = text.replace("—", ", ").replace("–", ", ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+,", ",", text)
    return re.sub(r"([;:,.!?])\s*,", r"\1", text)


def synthesize(url, text, voice, speed, out):
    body = json.dumps({"model": "kokoro", "input": speakable(text), "voice": voice, "speed": speed,
                       "response_format": "wav", "stream": False}).encode()
    req = urllib.request.Request(url.rstrip("/") + "/v1/audio/speech", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r, open(out, "wb") as f:
        f.write(r.read())


def fake_voice(text, out):
    """Offline test only: a soft tone as long as the text would take to read."""
    seconds = max(1.5, len(text) / 15.0)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", f"sine=frequency=220:duration={seconds:.2f}", "-af", "volume=0.3",
                    "-ar", "24000", "-ac", "1", out], check=True)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def plan(clip_lengths):
    """Screen lengths and the time each clip starts, from the clip lengths (None = silent)."""
    durs, starts, t = [], [], 0.0
    last = len(clip_lengths) - 1
    for i, d in enumerate(clip_lengths):
        lead = TITLE_LEAD if i == 0 else LEAD
        if d is None:
            length = SILENT_END if i == last else 4.0
            starts.append(None)
        else:
            tail = END_HOLD if i == last else TAIL
            length = max(4.0, lead + d + tail)
            starts.append(round(t + lead, 3))
        durs.append(round(length, 3))
        t += length
    return durs, starts, round(t, 3)


def loudness(path):
    """Integrated loudness (LUFS) of a file; quiet parts are ignored by the measurement."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True)
    found = re.findall(r"I:\s+(-?[0-9.]+) LUFS", out.stderr)
    value = float(found[-1]) if found else -70.0
    return value if value > -69 else None


def _ff(args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def mix(clips, total, out, music=None, voice_lufs=-16.0, music_lufs=-24.0, final_lufs=-14.0):
    """clips: [(wav, start seconds)]. The voice at a steady level, the music well below it
    and ducked further while the voice speaks, then the whole track brought to final_lufs."""
    work = os.path.dirname(out)
    voice = os.path.join(work, "voice.wav")
    args, f = [], []
    for i, (path, start) in enumerate(clips):
        args += ["-i", path]
        ms = int(round(start * 1000))
        f.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]")
    n = len(clips)
    joined = "".join(f"[v{i}]" for i in range(n))
    f.append(f"{joined}amix=inputs={n}:normalize=0:duration=longest,apad,atrim=0:{total}[voice]"
             if n > 1 else f"{joined}apad,atrim=0:{total}[voice]")
    _ff(args + ["-filter_complex", ";".join(f), "-map", "[voice]", "-c:a", "pcm_s16le", voice])
    gv = voice_lufs - (loudness(voice) or voice_lufs)

    mixed = os.path.join(work, "mixed.wav")
    if music:
        gm = music_lufs - (loudness(music) or music_lufs)
        fade_out = max(0.0, total - 3.0)
        f = [f"[0:a]volume={gv:.2f}dB,asplit=2[vo][key]",
             f"[1:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total},asetpts=N/SR/TB,"
             f"volume={gm:.2f}dB,afade=t=in:st=0:d=2,afade=t=out:st={fade_out}:d=3[mus]",
             "[mus][key]sidechaincompress=threshold=0.02:ratio=4:attack=60:release=900[duck]",
             "[vo][duck]amix=inputs=2:normalize=0:duration=first[out]"]
        _ff(["-i", voice, "-stream_loop", "-1", "-i", music, "-filter_complex", ";".join(f),
             "-map", "[out]", "-c:a", "pcm_s16le", mixed])
    else:
        _ff(["-i", voice, "-af", f"volume={gv:.2f}dB", "-c:a", "pcm_s16le", mixed])
    gf = final_lufs - (loudness(mixed) or final_lufs)
    _ff(["-i", mixed, "-af", f"volume={gf:.2f}dB,alimiter=limit=0.89:level=false",
         "-ar", "48000", "-c:a", "aac", "-b:a", "192k", out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--kokoro", default=os.environ.get("KOKORO_URL", "http://localhost:8880"))
    ap.add_argument("--music", help="background music file; none if left out")
    ap.add_argument("--fake-voice", action="store_true", help="offline test: tones instead of Kokoro")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()

    cfg = load_json(os.path.join(ROOT, "config.json"))
    audio_cfg = cfg.get("reel_audio", {})
    voice, speed = audio_cfg.get("voice", "am_michael"), float(audio_cfg.get("speed", 0.9))
    outdir = os.path.join(ROOT, "posts", args.date)
    content, day = load_day(args.date)
    spec = reel_spec(content, day)
    if not spec:
        print("No Reel today.")
        return 0

    texts = narration(spec)
    tmp = tempfile.mkdtemp(prefix="od-voice-")
    try:
        paths, lengths = [], []
        for i, text in enumerate(texts):
            if not text.strip():
                paths.append(None)
                lengths.append(None)
                continue
            p = os.path.join(tmp, f"clip{i:02d}.wav")
            if args.fake_voice:
                fake_voice(text, p)
            else:
                synthesize(args.kokoro, text, voice, speed, p)
            paths.append(p)
            lengths.append(duration(p))
            print(f"screen {i}: {lengths[-1]:.1f}s  {text[:70]}")

        durs, starts, total = plan(lengths)
        audio = os.path.join(tmp, "audio.m4a")
        music = args.music if args.music and os.path.exists(args.music) else None
        if args.music and not music:
            print(f"Music file not found ({args.music}); making the Reel with voice only.")
        mix([(p, s) for p, s in zip(paths, starts) if p], total, audio, music,
            voice_lufs=float(audio_cfg.get("voice_lufs", -16)),
            music_lufs=float(audio_cfg.get("music_lufs", -24)))

        built = T.reel(spec, cfg["site_url"], durs=durs)
        render_reel(built, os.path.join(outdir, "reel.mp4"), os.path.join(outdir, "reel-cover.jpg"),
                    fps=args.fps, audio=audio)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    post_path = os.path.join(outdir, "post.json")
    post = load_json(post_path)
    for item in post["items"]:
        if item["id"] == "reel":
            item["duration"] = total
            item["audio"] = "test tones" if args.fake_voice else f"{voice} at {speed}" + (" with music" if music else "")
    with open(post_path, "w", encoding="utf-8") as f:
        json.dump(post, f, ensure_ascii=False, indent=1)
    with open(os.path.join(outdir, "voice.json"), "w", encoding="utf-8") as f:
        json.dump({"voice": voice, "speed": speed, "music": os.path.basename(music) if music else None,
                   "total": total, "screens": [{"text": t, "starts": s, "length": d}
                                               for t, s, d in zip(texts, starts, durs)]},
                  f, ensure_ascii=False, indent=1)
    print(f"Reel: {total:.1f}s with {voice} at {speed}" + (" and music" if music else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
