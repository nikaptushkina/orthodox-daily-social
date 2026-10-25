"""Take real screenshots of orthodoxdaily.net for the "From the website" posts.

For every screenshot listed in features.json, opens the live site at phone size,
follows the recipe (settings to pre-set, buttons to tap, what to wait for) and saves
assets/site/<file>. When a recipe can't be followed today (for example the live-stream
card only appears on Sundays and feast days), the previous screenshot is kept.

Runs in the nightly "Fetch calendar days" workflow (Playwright + Chromium).

    python3 scripts/site_shots.py              # every screenshot
    python3 scripts/site_shots.py calendar      # only the features whose id contains "calendar"
"""
import datetime as dt
import json
import os
import shutil
import sys
import tempfile

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(ROOT, "config.json")))
OUT = os.path.join(ROOT, "assets", "site")
INDEX = os.path.join(OUT, "index.json")
BASE = "https://" + CONFIG["site_url"]


RING_JS = """
([x, y, w, h, label]) => {
  const pad = 7, small = w < 70 && h < 70;
  const ring = document.createElement('div');
  ring.className = 'od-ring';
  Object.assign(ring.style, {
    position: 'fixed', left: (x - pad) + 'px', top: (y - pad) + 'px',
    width: (w + 2 * pad) + 'px', height: (h + 2 * pad) + 'px',
    border: '4px solid #0369A1', borderRadius: small ? '999px' : '16px', boxSizing: 'border-box',
    boxShadow: '0 0 0 3px rgba(255,255,255,0.95), 0 0 0 9px rgba(3,105,161,0.28)',
    zIndex: 2147483647, pointerEvents: 'none'
  });
  document.body.appendChild(ring);
  if (label) {
    const tag = document.createElement('div');
    tag.className = 'od-ring';
    tag.textContent = label;
    // Small buttons: label underneath. Wide rows: label sits on the ring's top-right corner,
    // so it never covers the next line.
    const wide = w > 160;
    const below = y + h + pad + 34 < window.innerHeight;
    const left = wide ? Math.min(x + w - 70, window.innerWidth - 90) : Math.max(6, Math.min(x + w / 2 - 40, window.innerWidth - 86));
    const top = wide ? y - pad - 16 : (below ? y + h + pad + 8 : y - pad - 34);
    Object.assign(tag.style, {
      position: 'fixed', left: left + 'px',
      top: top + 'px', minWidth: '80px', textAlign: 'center',
      padding: '4px 10px', borderRadius: '999px', background: '#0369A1', color: '#FFFFFF',
      font: '700 14px/1.3 system-ui, -apple-system, sans-serif', letterSpacing: '0.02em',
      boxShadow: '0 4px 12px rgba(3,105,161,0.35)', zIndex: 2147483647, pointerEvents: 'none'
    });
    document.body.appendChild(tag);
  }
}
"""


def run_recipe(browser, shot, path):
    r = shot["recipe"]
    vw, vh = r.get("viewport", [390, 844])
    ctx = browser.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=r.get("scale", 3),
                              is_mobile=True, has_touch=True, locale="en-US",
                              timezone_id=r.get("timezone", CONFIG["timezone"]),
                              color_scheme="dark" if r.get("dark") else "light")
    # Quiet first-visit extras (dark-mode tip, intro animation, seasonal particles) unless a recipe wants them.
    storage = {"darkModeTipSeen": "true", "isEffectsEnabled": "false", "theme": "light"}
    storage.update(r.get("local_storage", {}))
    ctx.add_init_script(
        "(() => { const s = %s; for (const k in s) localStorage.setItem(k, s[k]);"
        " sessionStorage.setItem('homeInitialAnimationPlayed', 'true');"
        " const css = document.createElement('style');"
        " css.textContent = '[aria-label=\"Scroll to top\"]{display:none!important}';"
        " document.addEventListener('DOMContentLoaded', () => document.head.appendChild(css)); })();"
        % json.dumps(storage))
    pg = ctx.new_page()
    try:
        pg.goto(BASE + r.get("path", "/"), wait_until="domcontentloaded", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=20000)
        except Exception:
            pass
        for step in r.get("actions", []):
            if "wait" in step:
                pg.locator(step["wait"]).first.wait_for(state="visible", timeout=step.get("timeout", 30000))
            elif "click" in step:
                pg.locator(step["click"]).first.click(timeout=step.get("timeout", 15000))
            elif "scroll" in step:
                pg.locator(step["scroll"]).first.scroll_into_view_if_needed(timeout=15000)
            elif "pause" in step:
                pg.wait_for_timeout(step["pause"])
            elif "press" in step:
                pg.keyboard.press(step["press"])
            elif "eval" in step:
                pg.evaluate(step["eval"])
            elif "highlight" in step:
                # Ring the button to tap, with a small label, so the post shows exactly where to tap.
                el = pg.locator(step["highlight"]).first
                el.wait_for(state="visible", timeout=step.get("timeout", 15000))
                box = el.bounding_box()
                pg.evaluate(RING_JS, [box["x"], box["y"], box["width"], box["height"], step.get("label", "Tap")])
            elif "try_each" in step:
                # Open each match in turn until one shows what we want (e.g. a saint with an icon);
                # if none does, leave the first one open.
                buttons = pg.locator(step["try_each"])
                found = False
                for i in range(min(buttons.count(), 8)):
                    buttons.nth(i).click(timeout=15000)
                    pg.locator(step["open"]).first.wait_for(state="visible", timeout=30000)
                    try:
                        pg.locator(step["until"]).first.wait_for(state="visible", timeout=step.get("timeout", 7000))
                        found = True
                        break
                    except Exception:
                        pg.locator(step["close"]).first.click(timeout=10000)
                        pg.wait_for_timeout(500)
                if not found and step.get("required"):
                    raise RuntimeError("none of them shows " + step["until"] + " today")
                if not found:
                    buttons.first.click(timeout=15000)
                    pg.locator(step["open"]).first.wait_for(state="visible", timeout=30000)
        pg.wait_for_timeout(r.get("settle", 1200))  # let fade-ins finish
        if r.get("clip_around"):
            # Zoom in: the full width, from a little above to a little below the given element.
            c = r["clip_around"]
            box = pg.locator(c["sel"]).first.bounding_box()
            top = max(0, box["y"] - c.get("above", 60))
            bottom = min(vh, box["y"] + box["height"] + c.get("below", 160))
            pg.screenshot(path=path, animations="disabled", clip={"x": 0, "y": top, "width": vw, "height": bottom - top})
        elif r.get("clip"):
            x, y, w, h = r["clip"]
            pg.screenshot(path=path, animations="disabled", clip={"x": x, "y": y, "width": w, "height": h})
        elif r.get("element"):
            el = pg.locator(r["element"]).first
            if not any("highlight" in a for a in r.get("actions", [])):  # rings are fixed: don't scroll under them
                el.scroll_into_view_if_needed(timeout=15000)
                pg.wait_for_timeout(400)
            el.screenshot(path=path, animations="disabled")
        else:
            pg.screenshot(path=path, animations="disabled", full_page=False)
    finally:
        ctx.close()


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    feats = json.load(open(os.path.join(ROOT, "features.json"), encoding="utf-8"))["features"]
    os.makedirs(OUT, exist_ok=True)
    index = json.load(open(INDEX, encoding="utf-8")) if os.path.exists(INDEX) else {}
    today = dt.date.today().isoformat()
    ok = failed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chromium")
        for feat in feats:
            if only and only not in feat["id"]:
                continue
            for shot in feat.get("shots", []):
                if "recipe" not in shot:
                    continue
                final = os.path.join(OUT, shot["file"])
                tmp = os.path.join(tempfile.mkdtemp(prefix="od-shot-"), shot["file"])
                try:
                    run_recipe(browser, shot, tmp)
                    shutil.move(tmp, final)
                    index[shot["file"]] = {"taken": today, "feature": feat["id"]}
                    ok += 1
                    print("ok  ", shot["file"])
                except Exception as e:
                    failed += 1
                    kept = " (kept the previous one)" if os.path.exists(final) else ""
                    print("skip", shot["file"], "-", str(e).splitlines()[0][:160] + kept)
        browser.close()
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(index.items())), f, indent=1)
    print(f"{ok} screenshots taken, {failed} skipped")


if __name__ == "__main__":
    main()
