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


def run_recipe(browser, shot, path):
    r = shot["recipe"]
    vw, vh = r.get("viewport", [390, 844])
    ctx = browser.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=r.get("scale", 3),
                              is_mobile=True, has_touch=True, locale="en-US", timezone_id=CONFIG["timezone"],
                              color_scheme="dark" if r.get("dark") else "light")
    storage = dict(CONFIG.get("site_shots_storage", {}), **r.get("local_storage", {}))
    if storage:
        ctx.add_init_script("(() => { const s = %s; for (const k in s) localStorage.setItem(k, s[k]); })();"
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
        pg.wait_for_timeout(r.get("settle", 1200))  # let fade-ins finish
        if r.get("element"):
            el = pg.locator(r["element"]).first
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
