"""HTML templates for every post format, built from the design canvas.

Each function returns a list of (filename, html, width, height) for stills,
or a dict describing a Reel. Text sizes inside [data-fit] boxes are in em so
the renderer can shrink a block that would overflow.
"""
from .brand import (ACCENTS, BODY, BORDER, CROSS_RULE, FAST_DOT, HEAVEN, INK, LOGO, MUTED, NIGHT, PAGE,
                    TEXT_BODY, accent, arrow, counter_header, esc, footer, label, page, rule, tint, verse_html)

POST_W, POST_H = 1080, 1350
STORY_W, STORY_H = 1080, 1920


def _swipe(text="Swipe"):
    return f"{esc(text)} {arrow()}"


# ---------------------------------------------------------------- Story

def story(c, site):
    a = accent(c.get("accent"))
    groups = c.get("readings") or []
    cells = [("Commemorating", c.get("commemorating")), ("Fasting", c.get("fasting"))]
    for g in groups[:2]:
        cells.append((g.get("label", "Readings"), "<br>".join(esc(r) for r in g.get("refs", []))))
    cell_html = ""
    for i, (lab, val) in enumerate(cells):
        if not val:
            continue
        value = val if lab not in ("Commemorating", "Fasting") else esc(val)
        cell_html += (f"<div style='display:flex;flex-direction:column;gap:6px'>"
                      f"<div class='sans caps' style='font-size:0.6em;letter-spacing:3px;color:{MUTED};font-weight:600'>{esc(lab)}</div>"
                      f"<div class='serif' style='font-size:1em;font-weight:600;line-height:1.25'>{value}</div></div>")
    subtitle = (f"<div class='serif' style='font-style:italic;font-size:1em;color:{TEXT_BODY};line-height:1.3'>"
                f"{esc(c['subtitle'])}</div>") if c.get("subtitle") else ""
    week = (f"<div class='sans' style='font-size:0.66em;color:{MUTED}'>{esc(c['week_line'])}</div>"
            if c.get("week_line") else "")
    body = f"""
<div style="width:1080px;height:1920px;padding:250px 80px 340px;background:{HEAVEN};color:{INK};
  display:flex;flex-direction:column;justify-content:space-between;align-items:center;text-align:center;gap:40px">
  <div style="display:flex;flex-direction:column;align-items:center;gap:20px;flex-shrink:0">
    <img src="{LOGO}" alt="" style="width:64px;height:64px">
    {label(c['date_line'], size=34, spacing=10)}
    <div class="serif" style="padding:8px 24px;border-radius:999px;background:rgba(255,255,255,0.85);border:1px solid {BORDER};font-size:26px;color:{BODY}">{esc(c.get('calendar_label', 'New Calendar'))}</div>
  </div>
  <div data-fit class="fit" style="width:100%;flex:1;font-size:36px;display:flex;align-items:center">
    <div style="width:100%;background:rgba(255,255,255,0.92);border:1px solid rgba(255,255,255,0.6);border-radius:48px;
      padding:52px;display:flex;flex-direction:column;align-items:center;gap:0.72em">
      {rule(a)}
      <div class="serif" style="font-size:2.3em;font-weight:700;line-height:1;letter-spacing:-1px">{esc(c['title'])}</div>
      {subtitle}{week}
      <div style="height:1px;width:100%;background:{BORDER}"></div>
      <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0.9em 0.8em;width:100%;text-align:left">{cell_html}</div>
    </div>
  </div>
  <div class="serif caps" style="font-size:30px;font-weight:600;letter-spacing:4px;color:{BODY};flex-shrink:0">Full day · link in bio · {esc(site)}</div>
</div>"""
    return [("story.jpg", page(STORY_W, STORY_H, body), STORY_W, STORY_H)]


# ---------------------------------------------------------------- Week ahead

def week_ahead(c, site):
    rows = ""
    items = c.get("rows", [])
    for i, r in enumerate(items):
        border = f"border-bottom:1px solid {BORDER};" if i < len(items) - 1 else ""
        dot = FAST_DOT.get(r.get("fast_kind", "none"), FAST_DOT["none"])
        rows += (f"<div style='display:flex;align-items:center;gap:0.85em;padding:0.62em 0;{border}'>"
                 f"<div class='sans caps' style='width:4.6em;flex-shrink:0;white-space:nowrap;font-size:0.64em;letter-spacing:3px;color:{MUTED};font-weight:600'>{esc(r['day'])}</div>"
                 f"<div class='serif' style='flex-grow:1;font-size:1em;font-weight:600;line-height:1.15'>{esc(r['title'])}</div>"
                 f"<div class='sans' style='display:flex;align-items:center;gap:10px;font-size:0.58em;color:{TEXT_BODY};flex-shrink:0'>"
                 f"<div style='width:14px;height:14px;border-radius:50%;background:{dot}'></div>{esc(r.get('fast', ''))}</div></div>")
    banner = ""
    if c.get("banner"):
        banner = (f"<div style='border-radius:32px;background:linear-gradient(90deg,#E0F2FE 0%,#FFE4E6 100%);"
                  f"border:1px solid rgba(255,255,255,0.7);padding:30px 40px;display:flex;align-items:center;gap:24px;flex-shrink:0'>"
                  f"<svg width='44' height='44' viewBox='0 0 24 24' fill='none' stroke='{BODY}' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'><path d='M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z'/></svg>"
                  f"<div class='serif' style='font-size:36px;font-weight:600;color:{INK}'>{esc(c['banner'])}</div></div>")
    s1 = f"""
<div style="width:1080px;height:1350px;padding:88px 96px;background:linear-gradient(180deg,#F8FAFC 0%,#F1F5F9 100%);color:{INK};
  display:flex;flex-direction:column;gap:36px">
  <div style="display:flex;flex-direction:column;gap:12px;flex-shrink:0">
    {label(c['range_line'] + ' · ' + c.get('calendar_label', 'New Calendar'))}
    <h1 class="serif" style="margin:0;font-size:104px;font-weight:700;line-height:1;letter-spacing:-2px">The week ahead</h1>
  </div>
  <div data-fit class="fit" style="flex:1;font-size:38px">
    <div style="background:rgba(255,255,255,0.95);border:1px solid {BORDER};border-radius:40px;padding:12px 48px">{rows}</div>
  </div>
  {banner}
  {footer(site, '1 / 2 ' + arrow())}
</div>"""
    e = c.get("end", {})
    a = accent(e.get("accent", "feast"))
    second = (f"<p class='serif' style='margin:0;font-style:italic;font-size:0.75em;color:{TEXT_BODY}'>{esc(e['second'])}</p>"
              if e.get("second") else "")
    line = (f"<p class='serif' style='margin:0;font-size:0.8em;line-height:1.35;color:{BODY};max-width:760px'>{esc(e['line'])}</p>"
            if e.get("line") else "")
    s2 = f"""
<div style="width:1080px;height:1350px;padding:88px 96px;background:{tint(e.get('accent', 'feast'))};color:{INK};
  display:flex;flex-direction:column;justify-content:space-between;align-items:center;text-align:center;gap:32px">
  <div style="width:100%;display:flex;justify-content:space-between;align-items:center;flex-shrink:0">
    {label(e.get('kicker', 'Coming next'))}<div class="sans" style="font-size:24px;color:{MUTED}">2 / 2</div>
  </div>
  <div data-fit class="fit" style="flex:1;width:100%;font-size:48px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.7em">
    <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="{a}" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z"/></svg>
    <h1 class="serif" style="margin:0;font-size:2.4em;font-weight:700;line-height:0.98;letter-spacing:-2px">{esc(e.get('title', 'Have a blessed week'))}</h1>
    {rule(a)}
    <div style="display:flex;flex-direction:column;gap:10px">
      <p class="serif" style="margin:0;font-size:1em;font-weight:600">{esc(e.get('date', ''))}</p>{second}
    </div>
    {line}
  </div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:20px;flex-shrink:0">
    <div class="sans" style="font-size:26px;color:{TEXT_BODY}">Save this post · Follow for the daily calendar</div>
    <div style="display:flex;align-items:center;gap:16px"><img src="{LOGO}" alt="" style="width:40px;height:40px">
    <div class="serif caps" style="font-size:28px;font-weight:600;letter-spacing:4px;color:{BODY}">{esc(site)}</div></div>
  </div>
</div>"""
    return [("slide-1.jpg", page(POST_W, POST_H, s1), POST_W, POST_H),
            ("slide-2.jpg", page(POST_W, POST_H, s2), POST_W, POST_H)]


# ---------------------------------------------------------------- Saint of the day

def _arch(a):
    return (f"<div style='width:340px;height:430px;flex-shrink:0;border-radius:170px 170px 24px 24px;background:#FFFFFF;"
            f"border:2px solid {a};padding:16px'><div style='width:100%;height:100%;border-radius:154px 154px 12px 12px;"
            f"background:linear-gradient(180deg,#E0F2FE 0%,#F1F5F9 52%,#FFE4E6 100%);display:flex;align-items:center;justify-content:center'>"
            f"<img src='{LOGO}' alt='' style='width:150px;height:150px;opacity:0.9'></div></div>")


def saint(c, site):
    key = c.get("accent", "martyr")
    a = accent(key)
    s1 = f"""
<div style="width:1080px;height:1350px;padding:96px;background:{tint(key)};color:{INK};display:flex;flex-direction:column;gap:44px">
  {counter_header('Saint of the day', '1 / 3')}
  <div style="display:flex;flex-direction:column;gap:44px;flex:1;min-height:0">
    {_arch(a)}
    <div data-fit class="fit" style="flex:1;font-size:40px;display:flex;flex-direction:column;justify-content:flex-end;gap:0.6em">
      {rule(a)}
      <h1 class="serif" style="margin:0;font-size:2.7em;font-weight:700;line-height:0.95;letter-spacing:-2px">{esc(c['name'])}</h1>
      <p class="serif" style="margin:0;font-style:italic;font-size:1em;color:{TEXT_BODY};line-height:1.2">{esc(c.get('subtitle', ''))}</p>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid rgba(15,23,42,0.12);padding-top:30px;flex-shrink:0">
    <div class="serif" style="font-size:30px;color:{BODY}">{esc(c.get('dates', ''))}</div>
    <div class="sans" style="display:flex;align-items:center;gap:12px;font-size:24px;color:{TEXT_BODY}">{_swipe()}</div>
  </div>
</div>"""
    paras = "".join(f"<p class='serif' style='margin:0;font-size:1em;line-height:1.4;color:#1E293B'>{esc(p)}</p>"
                    for p in c.get("life", []))
    s2 = f"""
<div style="width:1080px;height:1350px;padding:96px;background:{PAGE};color:{INK};display:flex;flex-direction:column;gap:40px">
  {counter_header(c['name'], '2 / 3')}
  <div data-fit class="fit" style="flex:1;font-size:46px;display:flex;flex-direction:column;justify-content:center;gap:0.75em">
    {rule(a)}
    <h2 class="serif" style="margin:0;font-size:1.75em;font-weight:700;line-height:1;letter-spacing:-1px">{esc(c.get('heading', 'Who they were'))}</h2>
    {paras}
  </div>
  {footer(site, arrow(), border=BORDER)}
</div>"""
    s3 = f"""
<div style="width:1080px;height:1350px;padding:96px;background:{tint(key)};color:{INK};display:flex;flex-direction:column;
  justify-content:space-between;align-items:center;text-align:center;gap:40px">
  <div style="width:100%">{counter_header(c['name'], '3 / 3')}</div>
  <div data-fit class="fit" style="flex:1;width:100%;font-size:96px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:0.42em">
    <img src="{LOGO}" alt="" style="width:72px;height:72px">
    <p class="serif" style="margin:0;font-size:1em;font-weight:600;line-height:1.08;letter-spacing:-1px">{esc(c.get('intercession', ''))}</p>
    {rule(a)}
    <p class="serif" style="margin:0;font-style:italic;font-size:0.4em;color:{TEXT_BODY}">{esc(c.get('dates', ''))}</p>
  </div>
  <div style="display:flex;flex-direction:column;align-items:center;gap:20px;flex-shrink:0">
    <div class="sans" style="font-size:26px;color:{TEXT_BODY}">Their full life and today’s readings · link in bio</div>
    <div class="serif caps" style="font-size:28px;font-weight:600;letter-spacing:4px;color:{BODY}">{esc(site)}</div>
  </div>
</div>"""
    return [("slide-1.jpg", page(POST_W, POST_H, s1), POST_W, POST_H),
            ("slide-2.jpg", page(POST_W, POST_H, s2), POST_W, POST_H),
            ("slide-3.jpg", page(POST_W, POST_H, s3), POST_W, POST_H)]


# ---------------------------------------------------------------- Word for the day

def word(c, pages_verses, site):
    key = c.get("accent", "theotokos")
    a = accent(key)
    total = 1 + len(pages_verses)
    s1 = f"""
<div style="width:1080px;height:1350px;padding:96px;background:linear-gradient(180deg,#E0F2FE 0%,#F1F5F9 60%,#F8FAFC 100%);color:{INK};
  display:flex;flex-direction:column;justify-content:space-between;gap:40px">
  {counter_header('Word for the day', f'1 / {total}')}
  <div data-fit class="fit" style="flex:1;font-size:64px;display:flex;flex-direction:column;justify-content:center;gap:0.5em">
    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="{a}" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 19V5M8 7h7"/></svg>
    <div class="serif" style="font-size:0.62em;font-style:italic;color:{TEXT_BODY}">{esc(c.get('book_intro', ''))}</div>
    <h1 class="serif" style="margin:0;font-size:2.6em;font-weight:700;line-height:0.9;letter-spacing:-3px">{esc(c['book_title'])}</h1>
    {rule(a)}
    <div class="serif" style="font-size:1em;font-weight:600">{esc(c['ref_line'])}</div>
    <div class="sans" style="font-size:0.41em;color:{TEXT_BODY};line-height:1.5">{esc(c.get('context', ''))}<br>{esc(c.get('translation', ''))}</div>
  </div>
  {footer(site, _swipe('Swipe to read'))}
</div>"""
    out = [("slide-1.jpg", page(POST_W, POST_H, s1), POST_W, POST_H)]
    for i, pv in enumerate(pages_verses):
        n = i + 2
        last = n == total
        closing = (f"<div style='display:flex;align-items:center;gap:20px;margin-top:0.6em'><img src='{LOGO}' alt='' style='width:44px;height:44px'>"
                   f"<div class='serif' style='font-style:italic;font-size:0.7em;color:{TEXT_BODY}'>All of today’s readings are on the site.</div></div>") if last else ""
        right = "Save · Share · Link in bio" if last else arrow()
        bg = "linear-gradient(180deg,#F8FAFC 0%,#F1F5F9 55%,#E0F2FE 100%)" if last else PAGE
        s = f"""
<div style="width:1080px;height:1350px;padding:96px;background:{bg};color:{INK};display:flex;flex-direction:column;justify-content:space-between;gap:40px">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-shrink:0">
    <div style="display:flex;align-items:center;gap:20px">{rule(a, 48)}{label(pv['ref'])}</div>
    <div class="sans" style="font-size:24px;color:{MUTED}">{n} / {total}</div>
  </div>
  <div data-fit class="fit" style="flex:1;font-size:48px;display:flex;flex-direction:column;justify-content:center">
    <p class="serif" style="margin:0;font-size:1em;line-height:1.45;color:#1E293B">{verse_html(pv['verses'], num_color=a)}</p>
    {closing}
  </div>
  {footer(site, right, logo=False, border=BORDER)}
</div>"""
        out.append((f"slide-{n}.jpg", page(POST_W, POST_H, s), POST_W, POST_H))
    return out


# ---------------------------------------------------------------- Feast explainer

def feast(c, site):
    key = c.get("accent", "feast")
    a = accent(key)
    star = (f"<svg width='30' height='30' viewBox='0 0 24 24' fill='none' stroke='{a}' stroke-width='1.5' stroke-linecap='round' "
            f"stroke-linejoin='round'><path d='M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z'/></svg>")
    s1 = f"""
<div style="width:1080px;height:1350px;padding:96px;background:{tint(key)};color:{INK};display:flex;flex-direction:column;gap:44px">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-shrink:0">
    <div style="display:flex;align-items:center;gap:14px">{star}{label(c.get('kicker', 'Feast'))}</div>
    <div class="sans" style="font-size:24px;color:{MUTED}">1 / 3</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:44px;flex:1;min-height:0">
    {_arch(a)}
    <div data-fit class="fit" style="flex:1;font-size:40px;display:flex;flex-direction:column;justify-content:flex-end;gap:0.6em">
      {rule(a)}
      <h1 class="serif" style="margin:0;font-size:2.5em;font-weight:700;line-height:0.98;letter-spacing:-2px">{esc(c['name'])}</h1>
      <p class="serif" style="margin:0;font-style:italic;font-size:1em;color:{TEXT_BODY};line-height:1.2">{esc(c.get('subtitle', ''))}</p>
    </div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;border-top:1px solid rgba(15,23,42,0.12);padding-top:30px;flex-shrink:0">
    <div class="serif" style="font-size:30px;color:{BODY}">{esc(c.get('dates', ''))}</div>
    <div class="sans" style="display:flex;align-items:center;gap:12px;font-size:24px;color:{TEXT_BODY}">{_swipe()}</div>
  </div>
</div>"""
    points = "".join(
        f"<div style='display:flex;gap:0.75em;align-items:flex-start'><div class='serif' style='font-size:1.7em;font-weight:700;"
        f"line-height:0.9;color:{a};width:1.3em;flex-shrink:0'>{i + 1}</div><p class='serif' style='margin:0;font-size:1em;"
        f"line-height:1.38;color:#1E293B'>{esc(p)}</p></div>" for i, p in enumerate(c.get("meaning", [])))
    s2 = f"""
<div style="width:1080px;height:1350px;padding:96px;background:{PAGE};color:{INK};display:flex;flex-direction:column;gap:40px">
  {counter_header(c['name'], '2 / 3')}
  <div data-fit class="fit" style="flex:1;font-size:42px;display:flex;flex-direction:column;justify-content:center;gap:1em">
    <div style="display:flex;flex-direction:column;gap:0.5em">{rule(a)}
      <h2 class="serif" style="margin:0;font-size:2em;font-weight:700;line-height:1;letter-spacing:-1px">What we celebrate</h2></div>
    {points}
  </div>
  {footer(site, arrow(), logo=False, border=BORDER)}
</div>"""
    icons = {
        "Fasting": "<path d='M5 19c0-8 5-13 14-14-1 9-6 14-14 14z'/><path d='M5 19l7-7'/>",
        "Services": "<path d='M12 3c2 3 3 4.5 3 6.5a3 3 0 0 1-6 0C9 7.5 10 6 12 3z'/><rect x='9' y='13' width='6' height='8' rx='1'/>",
        "Hymns": "<path d='M9 18V6l10-2v12'/><circle cx='6.5' cy='18' r='2.5'/><circle cx='16.5' cy='16' r='2.5'/>",
    }
    rows = ""
    kept = c.get("kept", [])
    for i, k in enumerate(kept):
        icon = icons.get(k.get("label"), icons["Services"])
        border = f"border-bottom:1px solid {BORDER};" if i < len(kept) - 1 else ""
        rows += (f"<div style='display:flex;gap:0.74em;align-items:flex-start;padding:0.74em 0;{border}'>"
                 f"<svg width='44' height='44' viewBox='0 0 24 24' fill='none' stroke='{a}' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round' style='flex-shrink:0'>{icon}</svg>"
                 f"<div style='display:flex;flex-direction:column;gap:6px'><div class='sans caps' style='font-size:0.58em;letter-spacing:3px;color:{MUTED};font-weight:600'>{esc(k.get('label', ''))}</div>"
                 f"<div class='serif' style='font-size:1em;line-height:1.3'>{esc(k.get('text', ''))}</div></div></div>")
    s3 = f"""
<div style="width:1080px;height:1350px;padding:96px;background:{tint(key)};color:{INK};display:flex;flex-direction:column;gap:40px">
  {counter_header(c['name'], '3 / 3')}
  <div data-fit class="fit" style="flex:1;font-size:38px;display:flex;flex-direction:column;justify-content:center;gap:1em">
    <div style="display:flex;flex-direction:column;gap:0.6em">{rule(a)}
      <h2 class="serif" style="margin:0;font-size:2.2em;font-weight:700;line-height:1;letter-spacing:-1px">How it’s kept</h2></div>
    <div style="background:rgba(255,255,255,0.92);border:1px solid {BORDER};border-radius:40px;padding:16px 48px">{rows}</div>
  </div>
  {footer(site, 'Save · Share · Link in bio')}
</div>"""
    return [("slide-1.jpg", page(POST_W, POST_H, s1), POST_W, POST_H),
            ("slide-2.jpg", page(POST_W, POST_H, s2), POST_W, POST_H),
            ("slide-3.jpg", page(POST_W, POST_H, s3), POST_W, POST_H)]


# ---------------------------------------------------------------- Reels

MOODS = {
    "dawn": dict(sky="linear-gradient(180deg,#CFE8FB 0%,#EEF2F7 30%,#FBD9E1 60%,#E0F2FE 100%)",
                 orbA="rgba(255,255,255,0.75)", orbB="rgba(255,214,224,0.7)", rays="rgba(255,238,175,0.6)",
                 spark="#FFFFFF", ink="#0F172A", quiet="#475569", label="#475569", accent="#B7832F",
                 track="rgba(15,23,42,0.12)"),
    "vespers": dict(sky="linear-gradient(180deg,#0E1526 0%,#141A2E 35%,#1A1321 70%,#0E1526 100%)",
                    orbA="rgba(217,168,91,0.22)", orbB="rgba(242,154,172,0.16)", rays="rgba(230,198,148,0.28)",
                    spark="#E6C694", ink="#F3EEE4", quiet="#B4BAC6", label="#D9A85B", accent="#D9A85B",
                    track="rgba(255,255,255,0.15)"),
}

FADE = 0.6

# The dark Vespers Reel from the design board (VespersTitle / VespersText).
VESPERS = dict(sky="linear-gradient(180deg,#0E1526 0%,#11141D 52%,#1A1321 100%)", glow="rgba(217,168,91,0.20)",
               spark="#E6C694", ink="#F3EEE4", quiet="#B4BAC6", label="#D9A85B", gold="#E6C694",
               note="#A3AABA", accent="#D9A85B")
LAMP = ("<svg width='64' height='64' viewBox='0 0 24 24' fill='none' stroke='#D9A85B' stroke-width='1.2' "
        "stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'>"
        "<path d='M12 3c2 3 3 4.5 3 6.5a3 3 0 0 1-6 0C9 7.5 10 6 12 3z'/><rect x='9' y='13' width='6' height='8' rx='1'/></svg>")


def reel_timing(c):
    """Seconds per screen: title, verse screens (by text length), end."""
    durs = [5.0]
    for s in c["screens"]:
        chars = sum(len(v.get("t", "")) for v in s["verses"])
        durs.append(round(max(6.0, 3.0 + chars / 17.0), 2))  # about 3 words a second, plus a pause
    durs.append(6.0)
    return durs


def reel(c, site, durs=None):
    """durs: seconds per screen (title, verse screens, end). Defaults to reading-speed
    timing; social.voice passes the narration's own lengths instead."""
    vespers = c.get("style") == "vespers"
    m = MOODS.get(c.get("mood", "vespers" if vespers else "dawn"), MOODS["dawn"])
    durs = list(durs) if durs else reel_timing(c)
    if len(durs) != len(c["screens"]) + 2:
        raise ValueError(f"need {len(c['screens']) + 2} screen lengths, got {len(durs)}")
    T = round(sum(durs), 3)
    frames_css, windows, t = [], [], 0.0
    for i, d in enumerate(durs):
        s, e = t, t + d
        windows.append((s, e))
        t = e

    def pct(x):
        return f"{max(0.0, min(100.0, x / T * 100)):.4f}%"

    for i, (s, e) in enumerate(windows):
        name = f"sc{i}"
        if i == 0:
            frames_css.append(f"@keyframes {name}{{0%{{opacity:0;transform:translateY(18px)}}{pct(s + FADE)},{pct(e - FADE)}{{opacity:1;transform:translateY(0)}}{pct(e)},100%{{opacity:0;transform:translateY(-8px)}}}}")
        elif i == len(windows) - 1:
            frames_css.append(f"@keyframes {name}{{0%,{pct(s)}{{opacity:0;transform:translateY(18px)}}{pct(s + FADE)},100%{{opacity:1;transform:translateY(0)}}}}")
        else:
            frames_css.append(f"@keyframes {name}{{0%,{pct(s)}{{opacity:0;transform:translateY(18px)}}{pct(s + FADE)},{pct(e - FADE)}{{opacity:1;transform:translateY(0)}}{pct(e)},100%{{opacity:0;transform:translateY(-8px)}}}}")
    css = """
@keyframes sky{0%{background-position:50% 0%}100%{background-position:50% 100%}}
@keyframes drift1{0%{transform:translate(0,0) scale(1)}100%{transform:translate(240px,200px) scale(1.25)}}
@keyframes drift2{0%{transform:translate(0,0) scale(1.1)}100%{transform:translate(-280px,-220px) scale(0.9)}}
@keyframes rays{0%,100%{opacity:.35}50%{opacity:.75}}
@keyframes rise{0%{transform:translateY(0);opacity:0}15%{opacity:.9}85%{opacity:.9}100%{transform:translateY(-1600px);opacity:0}}
@keyframes progress{0%{transform:scaleX(0)}100%{transform:scaleX(1)}}
.screen{position:absolute;left:96px;right:96px;top:250px;bottom:420px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
""" + "\n".join(frames_css)
    sparks = ""
    for left, size, dur, delay in [(90, 8, 17, -2), (230, 5, 21, -11), (350, 9, 19, -6), (480, 6, 23, -15),
                                   (600, 8, 16, -9), (720, 5, 20, -3), (840, 9, 18, -13), (980, 6, 22, -7)]:
        sparks += (f"<div style='position:absolute;left:{left}px;top:1900px;width:{size}px;height:{size}px;border-radius:50%;"
                   f"background:{m['spark']};box-shadow:0 0 12px {m['spark']};animation:rise {dur}s linear infinite;animation-delay:{delay}s'></div>")
    if vespers:
        return _vespers_reel(c, site, T, len(windows), "\n".join(frames_css))
    ti = c["title"]
    screens = (f"<div class='screen' style='gap:32px;animation:sc0 {T}s linear infinite'>"
               f"<img src='{LOGO}' alt='' style='width:80px;height:80px'>"
               f"<div class='serif caps' style='font-size:36px;font-weight:600;letter-spacing:10px;color:{m['label']}'>{esc(ti.get('kicker', ''))}</div>"
               f"<h1 class='serif' style='margin:0;font-size:{ti.get('size', 170)}px;font-weight:700;line-height:0.92;letter-spacing:-3px;color:{m['ink']}'>{esc(ti['title'])}</h1>"
               f"{rule(m['accent'])}"
               f"<div class='serif' style='font-style:italic;font-size:48px;color:{m['quiet']}'>{esc(ti.get('subtitle', ''))}</div></div>")
    for i, s in enumerate(c["screens"]):
        screens += (f"<div class='screen' style='gap:44px;opacity:0;animation:sc{i + 1} {T}s linear infinite'>"
                    f"<div class='serif caps' style='font-size:34px;font-weight:600;letter-spacing:10px;color:{m['label']};flex-shrink:0'>{esc(s.get('label', ''))}</div>"
                    f"<div data-fit class='fit' style='width:100%;max-height:1050px;font-size:60px;display:flex;align-items:center;justify-content:center'>"
                    f"<p class='serif' style='margin:0;font-size:1em;font-weight:600;line-height:1.3;color:{m['ink']}'>{verse_html(s['verses'], num_color=m['accent'])}</p></div></div>")
    en = c.get("end", {})
    screens += (f"<div class='screen' style='gap:36px;opacity:0;animation:sc{len(windows) - 1} {T}s linear infinite'>"
                f"<img src='{LOGO}' alt='' style='width:80px;height:80px'>"
                f"<p class='serif' style='margin:0;font-size:84px;font-weight:700;line-height:1.05;letter-spacing:-1px;color:{m['ink']}'>{esc(en.get('quote', ''))}</p>"
                f"{rule(m['accent'])}"
                f"<div class='serif caps' style='font-size:34px;font-weight:600;letter-spacing:4px;color:{m['label']}'>{esc(en.get('line', 'Today’s readings · link in bio'))}</div></div>")
    body = f"""
<div style="width:1080px;height:1920px;position:relative;overflow:hidden;background:{m['sky']};background-size:100% 240%;animation:sky 18s ease-in-out infinite alternate">
  <div style="position:absolute;left:-300px;top:120px;width:1100px;height:1100px;border-radius:50%;background:radial-gradient(circle,{m['orbA']} 0%,rgba(255,255,255,0) 68%);animation:drift1 22s ease-in-out infinite alternate"></div>
  <div style="position:absolute;right:-360px;bottom:80px;width:1200px;height:1200px;border-radius:50%;background:radial-gradient(circle,{m['orbB']} 0%,rgba(255,255,255,0) 68%);animation:drift2 26s ease-in-out infinite alternate"></div>
  <div style="position:absolute;left:-200px;top:-300px;width:1480px;height:1200px;background:radial-gradient(ellipse at 50% 0%,{m['rays']} 0%,rgba(255,255,255,0) 62%);animation:rays 9s ease-in-out infinite"></div>
  <div style="position:absolute;inset:0">{sparks}</div>
  {screens}
  <div style="position:absolute;left:0;right:0;bottom:380px;display:flex;flex-direction:column;align-items:center;gap:20px">
    <div style="width:240px;height:3px;border-radius:2px;background:{m['track']};overflow:hidden"><div style="width:100%;height:100%;background:{m['accent']};transform-origin:left center;animation:progress {T}s linear infinite"></div></div>
    <div class="serif caps" style="font-size:28px;font-weight:600;letter-spacing:4px;color:{m['label']}">{esc(c.get('footer', site))}</div>
  </div>
</div>"""
    return {"html": page(STORY_W, STORY_H, body, css), "duration": T, "width": STORY_W, "height": STORY_H,
            "cover_time": 2.5}


def _vespers_reel(c, site, T, n_windows, frames_css):
    """Saturday evening Reel for Vespers readings: dark sky, a slow gold glow, rising gold sparks."""
    v = VESPERS
    css = """
@keyframes glow{0%,100%{opacity:.45}50%{opacity:.85}}
@keyframes rise{0%{transform:translateY(0);opacity:0}15%{opacity:.8}85%{opacity:.8}100%{transform:translateY(-1600px);opacity:0}}
.screen{position:absolute;left:96px;right:96px;top:250px;bottom:420px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}
""" + frames_css
    sparks = ""
    for left, size, dur, delay in [(120, 6, 20, -4), (340, 8, 24, -14), (610, 5, 18, -9), (820, 7, 22, -17), (960, 5, 26, -2)]:
        sparks += (f"<div style='position:absolute;left:{left}px;top:1900px;width:{size}px;height:{size}px;border-radius:50%;"
                   f"background:{v['spark']};box-shadow:0 0 12px {v['spark']};animation:rise {dur}s linear infinite;animation-delay:{delay}s'></div>")
    ti = c["title"]
    ref = ti.get("ref") or c.get("ref", "")
    screens = (f"<div class='screen' style='top:200px;bottom:300px;justify-content:space-between;animation:sc0 {T}s linear infinite'>"
               f"<div style='display:flex;flex-direction:column;align-items:center;gap:20px'>{LAMP}"
               f"<div class='serif caps' style='font-size:34px;font-weight:600;letter-spacing:10px;color:{v['label']}'>{esc(ti.get('kicker', 'Saturday evening'))}</div></div>"
               f"<div style='display:flex;flex-direction:column;align-items:center;gap:36px'>"
               f"<h1 class='serif' style='margin:0;font-size:{ti.get('size', 180)}px;font-weight:700;line-height:0.9;letter-spacing:-3px;color:{v['ink']}'>{esc(ti.get('title', 'Vespers'))}</h1>"
               f"<div class='serif' style='font-style:italic;font-size:52px;color:{v['quiet']}'>{esc(ti.get('subtitle', ''))}</div>"
               f"{rule(v['accent'], height=3)}"
               f"<div class='serif' style='font-size:72px;font-weight:600;color:{v['gold']}'>{esc(ref)}</div>"
               f"<div class='sans' style='font-size:28px;color:{v['note']}'>{esc(ti.get('translation', ''))}</div></div>"
               f"<div style='height:1px'></div></div>")
    for i, s in enumerate(c["screens"]):
        screens += (f"<div class='screen' style='gap:56px;opacity:0;animation:sc{i + 1} {T}s linear infinite'>"
                    f"<div class='serif caps' style='font-size:36px;font-weight:600;letter-spacing:10px;color:{v['label']};flex-shrink:0'>{esc(s.get('label', ''))}</div>"
                    f"<div data-fit class='fit' style='width:100%;max-height:1050px;font-size:66px;display:flex;align-items:center;justify-content:center'>"
                    f"<p class='serif' style='margin:0;font-size:1em;font-weight:600;line-height:1.25;color:{v['ink']}'>{verse_html(s['verses'], num_color=v['label'])}</p></div></div>")
    en = c.get("end", {})
    screens += (f"<div class='screen' style='gap:36px;opacity:0;animation:sc{n_windows - 1} {T}s linear infinite'>"
                f"{LAMP}"
                f"<p class='serif' style='margin:0;font-size:84px;font-weight:700;line-height:1.05;letter-spacing:-1px;color:{v['ink']}'>{esc(en.get('quote', ''))}</p>"
                f"{rule(v['accent'], height=3)}"
                f"<div class='serif caps' style='font-size:34px;font-weight:600;letter-spacing:4px;color:{v['gold']}'>{esc(en.get('line', 'Today’s readings · link in bio'))}</div></div>")
    body = f"""
<div style="width:1080px;height:1920px;position:relative;overflow:hidden;background:{v['sky']}">
  <div style="position:absolute;left:-100px;top:300px;width:1280px;height:1280px;border-radius:50%;background:radial-gradient(circle,{v['glow']} 0%,rgba(217,168,91,0) 65%);animation:glow 9s ease-in-out infinite"></div>
  <div style="position:absolute;inset:0">{sparks}</div>
  {screens}
  <div style="position:absolute;left:0;right:0;bottom:300px;display:flex;justify-content:center">
    <div class="serif caps" style="font-size:30px;font-weight:600;letter-spacing:4px;color:{v['gold']}">{esc(c.get('footer', site))}</div>
  </div>
</div>"""
    return {"html": page(STORY_W, STORY_H, body, css), "duration": T, "width": STORY_W, "height": STORY_H,
            "cover_time": 2.5}
