"""Render HTML pages to JPEG stills and Reels to MP4 (Playwright + ffmpeg)."""
import os
import shutil
import subprocess
import tempfile

from playwright.sync_api import sync_playwright


def _load(pg, html, tmpdir, name):
    path = os.path.join(tmpdir, name + ".html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    pg.goto("file://" + path)
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(300)
    pg.evaluate("fitAll()")


def render_stills(items, outdir):
    """items: list of (filename, html, width, height). Returns filenames written."""
    written = []
    tmp = tempfile.mkdtemp(prefix="od-stills-")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chromium")  # full Chromium, as in the previews (not the headless shell)
            for name, html, w, h in items:
                pg = browser.new_page(viewport={"width": w, "height": h})
                _load(pg, html, tmp, os.path.splitext(name)[0])
                out = os.path.join(outdir, name)
                pg.screenshot(path=out, type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": w, "height": h})
                pg.close()
                written.append(name)
            browser.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return written


def render_cover(spec, out_cover):
    """Only the Reel's cover (a single frame), for the morning preview."""
    tmp = tempfile.mkdtemp(prefix="od-cover-")
    w, h = spec["width"], spec["height"]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chromium")  # full Chromium, as in the previews (not the headless shell)
            pg = browser.new_page(viewport={"width": w, "height": h})
            _load(pg, spec["html"], tmp, "reel")
            pg.evaluate("document.getAnimations().forEach(a => a.pause())")
            pg.evaluate(f"document.getAnimations().forEach(a => {{ a.currentTime = {spec['cover_time'] * 1000}; }})")
            pg.screenshot(path=out_cover, type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": w, "height": h})
            browser.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def render_reel(spec, out_mp4, out_cover, fps=30, audio=None):
    """spec: dict from templates.reel(). Writes an H.264/AAC MP4 and a JPEG cover.
    audio: a finished soundtrack (voice and music) of the same length; silent if None."""
    tmp = tempfile.mkdtemp(prefix="od-reel-")
    frames = os.path.join(tmp, "frames")
    os.makedirs(frames)
    w, h, T = spec["width"], spec["height"], spec["duration"]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chromium")  # full Chromium, as in the previews (not the headless shell)
            pg = browser.new_page(viewport={"width": w, "height": h})
            _load(pg, spec["html"], tmp, "reel")
            pg.evaluate("document.getAnimations().forEach(a => a.pause())")
            pg.evaluate(f"document.getAnimations().forEach(a => {{ a.currentTime = {spec['cover_time'] * 1000}; }})")
            pg.screenshot(path=out_cover, type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": w, "height": h})
            total = int(round(T * fps))
            for i in range(total):
                t = i * 1000.0 / fps
                pg.evaluate(f"document.getAnimations().forEach(a => {{ a.currentTime = {t}; }})")
                pg.screenshot(path=os.path.join(frames, f"f{i:05d}.jpg"), type="jpeg", quality=90,
                              clip={"x": 0, "y": 0, "width": w, "height": h})
            browser.close()
        sound = ["-i", audio] if audio else ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-framerate", str(fps), "-i", os.path.join(frames, "f%05d.jpg"), *sound,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out_mp4,
        ], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
