"""Eight 3:2 preview images in the demo's story order, plus captions.md (captions only, nothing beside them).

Page shots come from the live site; video beats from the raw b-roll captures (never the rendered video,
which has captions burned in). 16:9 frames are letterboxed in their own background colour.
"""

import subprocess
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

URL = "https://naturebingo.vercel.app/?town=Hawkesbury"
OUT = Path("previews")
W, H = 1500, 1000

CAPTIONS = {
    "1-card": "Nature Bingo: a card of the 16 things most likely out near your town this October. Tap a square when you find it.",
    "2-sparse": "Around Hawkesbury, iNaturalist has about 3,000 research-grade records in total. Too few to rank a town on its own.",
    "3-towns": "TabPFN, an open-weight model, learns from ten years of Octobers across 48 towns between Ottawa and Montreal.",
    "4-backtest": "Blind test on October 2025: the model's card beat last October's list in 23 towns, tied 14, lost 11.",
    "5-local": "Hawkesbury's card, ranked on my laptop's GPU in 19 seconds. No model API in the loop.",
    "6-limits": "The card states what it cannot know: last October people photographed 3 of its 16 squares, and unphotographed is not absent.",
    "7-park": "I walked Hawkesbury's card at Confederation Park on 6 October 2026, under the Franco-Ontarian flag.",
    "8-walk": "In about half an hour, 2 of 16 confirmed by photo: Canada geese and a mallard. Ring-billed gulls probable.",
}


def frame(src, t, dst):
    Path(dst).unlink(missing_ok=True)  # a seek past the end writes nothing; never reuse the last frame
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-update", "1", str(dst)], check=True)
    assert Path(dst).exists(), f"no frame at {t}s in {src}"


def letterbox(png, dst):
    im = Image.open(png).convert("RGB")
    bg = im.getpixel((4, 4))
    scale = W / im.width
    im = im.resize((W, round(im.height * scale)), Image.LANCZOS)
    out = Image.new("RGB", (W, H), bg)
    out.paste(im, (0, (H - im.height) // 2))
    out.save(dst)


def crop32(png, dst, cx=0.5):
    im = Image.open(png).convert("RGB")
    cw = round(im.height * 1.5)
    x0 = min(max(round(cx * im.width - cw / 2), 0), im.width - cw)
    im.crop((x0, 0, x0 + cw, im.height)).resize((W, H), Image.LANCZOS).save(dst)


HIGHLIGHT = """() => {
  const el = document.querySelectorAll('.notes p')[1];
  const s = document.createElement('style');
  s.textContent = '.hl{background:linear-gradient(transparent 55%, rgba(190,86,235,.45) 55%);color:#F1EBE2}';
  document.head.append(s);
  el.innerHTML = el.innerHTML.replace(/(people photographed \\d+ of the \\d+ things on this town's card)/, '<span class=hl>$1</span>');
}"""


def page(pg, dst, selector=None, offset=24, zoom=None, js=None):
    pg.goto(URL, wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    if zoom:
        pg.evaluate(f"document.documentElement.style.zoom = '{zoom}'")
    if js:
        pg.evaluate(js)
    # room below the last section, so any section can be scrolled to the top of the frame
    pg.evaluate("document.body.style.paddingBottom = '1400px'")
    if selector:
        pg.evaluate("([s, o]) => window.scrollTo(0, document.querySelector(s).getBoundingClientRect().top + window.scrollY - o)",
                    [selector, offset])
    pg.wait_for_timeout(1200)
    pg.screenshot(path=str(dst))


def main():
    OUT.mkdir(exist_ok=True)
    tmp = OUT / "_frame.png"
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        pg = b.new_page(viewport={"width": W, "height": H}, color_scheme="dark")
        page(pg, OUT / "1-card.png")
        page(pg, OUT / "6-limits.png", ".notes", 140, zoom=1.6, js=HIGHLIGHT)
        page(pg, OUT / "8-walk.png", ".walk", 20, zoom=1.75)
        b.close()

    frame("broll/clips/c03_inat_map.webm", 19, tmp); letterbox(tmp, OUT / "2-sparse.png")
    frame("broll/clips/c05_towns.webm", 12.5, tmp); letterbox(tmp, OUT / "3-towns.png")
    frame("broll/clips/c07_backtest.webm", 26, tmp); letterbox(tmp, OUT / "4-backtest.png")
    frame("broll/clips/c06_terminal.webm", 11, tmp); letterbox(tmp, OUT / "5-local.png")
    frame("broll/drone/DJI_0004.MOV", 54, tmp); crop32(tmp, OUT / "7-park.png", cx=0.58)
    tmp.unlink()

    lines = []
    for name, cap in CAPTIONS.items():
        assert len(cap) <= 140, (name, len(cap))
        assert "â€”" not in cap and "â€“" not in cap, name
        f = OUT / f"{name}.png"
        im = Image.open(f)
        mb = f.stat().st_size / 1e6
        ok = im.size == (W, H) and mb < 5
        print(f"{'ok ' if ok else 'BAD'} {name}  {im.size}  {mb:.1f} MB  caption {len(cap)}")
        lines += [f"## {name}", "", cap, ""]
    (OUT / "captions.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
