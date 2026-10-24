"""Brand tokens and shared HTML pieces (from the Orthodox Daily design system)."""
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
LOGO = "file://" + os.path.join(ROOT, "assets", "cross.svg")

INK = "#0F172A"
BODY = "#334155"
TEXT_BODY = "#475569"
MUTED = "#64748B"
BORDER = "#E2E8F0"
PAGE = "#F8FAFC"
HEAVEN = "linear-gradient(180deg, #E0F2FE 0%, #F1F5F9 52%, #FFE4E6 100%)"
NIGHT = "linear-gradient(180deg, #0E1526 0%, #11141D 52%, #1A1321 100%)"
CROSS_RULE = "linear-gradient(90deg, #7DB9E8, #E890A8)"

# Liturgical accents: one thin rule or small icon per slide.
ACCENTS = {
    "feast": "#B7832F",       # Feasts of the Lord, Nativity, Pascha
    "theotokos": "#0369A1",   # Feasts of the Theotokos
    "martyr": "#BE123C",      # Martyrs
    "lent": "#6B4E8A",        # Great Lent and Holy Week
    "pentecost": "#3F7A5A",   # Pentecost
    "ordinary": "#64748B",    # Ordinary days, memorial Saturdays
}

# Soft backgrounds that go with each accent.
TINTS = {
    "feast": "linear-gradient(180deg, #F8FAFC 0%, #FBF5EA 60%, #F6EBD6 100%)",
    "theotokos": "linear-gradient(180deg, #E0F2FE 0%, #EFF6FB 55%, #F8FAFC 100%)",
    "martyr": "linear-gradient(180deg, #F8FAFC 0%, #FFF1F2 55%, #FFE4E6 100%)",
    "lent": "linear-gradient(180deg, #F8FAFC 0%, #F3EFF8 55%, #EAE3F3 100%)",
    "pentecost": "linear-gradient(180deg, #F8FAFC 0%, #EEF6F1 55%, #E1EFE6 100%)",
    "ordinary": HEAVEN,
}

FAST_DOT = {"none": "#3F7A5A", "fast": "#6B4E8A", "fish": "#0369A1", "dairy": "#B7832F"}


def accent(key):
    return ACCENTS.get(key or "ordinary", ACCENTS["ordinary"])


def tint(key):
    return TINTS.get(key or "ordinary", HEAVEN)


def esc(text):
    return html.escape(str(text or ""), quote=True)


def font_faces():
    faces = [
        ("Crimson Text", "CrimsonText-Regular.ttf", 400, "normal"),
        ("Crimson Text", "CrimsonText-Italic.ttf", 400, "italic"),
        ("Crimson Text", "CrimsonText-SemiBold.ttf", 600, "normal"),
        ("Crimson Text", "CrimsonText-SemiBoldItalic.ttf", 600, "italic"),
        ("Crimson Text", "CrimsonText-Bold.ttf", 700, "normal"),
        ("Crimson Text", "CrimsonText-BoldItalic.ttf", 700, "italic"),
        ("Geist", "Geist-Regular.ttf", 400, "normal"),
        ("Geist", "Geist-Medium.ttf", 500, "normal"),
        ("Geist", "Geist-SemiBold.ttf", 600, "normal"),
        ("Geist", "Geist-Bold.ttf", 700, "normal"),
    ]
    out = []
    for family, file, weight, style in faces:
        url = "file://" + os.path.join(FONTS, file)
        out.append(f"@font-face{{font-family:'{family}';src:url('{url}') format('truetype');"
                   f"font-weight:{weight};font-style:{style};}}")
    return "\n".join(out)


BASE_CSS = """
*{box-sizing:border-box}
body{margin:0}
.serif{font-family:'Crimson Text',serif}
.sans{font-family:'Geist',sans-serif}
.caps{font-variant-caps:all-small-caps}
.fit{overflow:hidden;min-height:0}
"""

# Shrinks the font size of every [data-fit] box until its content fits.
# Children size their text in em, so one number scales the whole block.
FIT_JS = """
function overflows(box){
  var r=box.getBoundingClientRect(), top=Infinity, bottom=-Infinity, wide=false;
  for(var i=0;i<box.children.length;i++){
    var c=box.children[i].getBoundingClientRect();
    top=Math.min(top,c.top); bottom=Math.max(bottom,c.bottom);
    if(box.children[i].scrollWidth>box.children[i].clientWidth+1) wide=true;
  }
  if(top===Infinity) return false;
  return (bottom-top)>r.height+1 || wide || box.scrollWidth>box.clientWidth+1;
}
function fitAll(){
  document.querySelectorAll('[data-fit]').forEach(function(box){
    var size=parseFloat(getComputedStyle(box).fontSize), min=size*0.5, guard=0;
    while(overflows(box)&&size>min&&guard<120){
      size-=1; box.style.fontSize=size+'px'; guard++;
    }
  });
  document.body.setAttribute('data-fitted','1');
}
"""


def page(width, height, body, css=""):
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<style>{font_faces()}{BASE_CSS}{css}</style><script>{FIT_JS}</script></head>"
            f"<body style='width:{width}px;height:{height}px;overflow:hidden'>{body}</body></html>")


def arrow(color="#475569"):
    return (f"<svg width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='{color}' stroke-width='1.6' "
            f"stroke-linecap='round' stroke-linejoin='round' aria-hidden='true'><path d='M5 12h14M13 6l6 6-6 6'/></svg>")


def rule(color, width=96, height=4):
    return f"<div style='width:{width}px;height:{height}px;border-radius:2px;background:{color};flex-shrink:0'></div>"


def label(text, size=30, color=MUTED, spacing=8):
    return (f"<div class='serif caps' style='font-size:{size}px;font-weight:600;letter-spacing:{spacing}px;"
            f"color:{color}'>{esc(text)}</div>")


def footer(site, right_html="", border="rgba(15,23,42,0.12)", logo=True, color=BODY):
    logo_html = f"<img src='{LOGO}' alt='' style='width:40px;height:40px'>" if logo else ""
    return (f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"border-top:1px solid {border};padding-top:30px;flex-shrink:0'>"
            f"<div style='display:flex;align-items:center;gap:16px'>{logo_html}"
            f"<div class='serif caps' style='font-size:28px;font-weight:600;letter-spacing:4px;color:{color}'>{esc(site)}</div></div>"
            f"<div class='sans' style='display:flex;align-items:center;gap:12px;font-size:24px;color:{TEXT_BODY}'>{right_html}</div></div>")


def counter_header(text, counter):
    return (f"<div style='display:flex;justify-content:space-between;align-items:center;flex-shrink:0'>"
            f"{label(text)}<div class='sans' style='font-size:24px;color:{MUTED}'>{esc(counter)}</div></div>")


def verse_html(verses, num_size="0.48em", num_color="#B7832F"):
    parts = []
    for v in verses:
        n = esc(v.get("n", ""))
        t = esc(v.get("t", ""))
        num = (f"<span class='sans' style='font-size:{num_size};font-weight:600;color:{num_color};"
               f"vertical-align:super'>{n}</span> ") if n else ""
        parts.append(num + t)
    return " ".join(parts)
