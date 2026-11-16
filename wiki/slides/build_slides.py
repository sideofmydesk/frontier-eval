"""Build the wiki home-page slides as 1600x900 PNG images.

Each slide is a small HTML page rendered by headless Microsoft Edge.
Usage: python build_slides.py [--edge <path to msedge.exe>]
Output: ../images/slide-N-<name>.png

Design rules followed: one system sans throughout; numbers and text in ink,
never in the accent colour; the accent (blue) is used only for marks.
"""

import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "images"
EDGE_DEFAULT = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1600px;height:900px;overflow:hidden}
body{background:#fcfcfb;color:#0b0b0b;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
     padding:72px 88px 64px;display:flex;flex-direction:column}
.kicker{font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:#52514e;font-weight:600;display:flex;align-items:center;gap:14px}
.kicker i{display:inline-block;width:36px;height:4px;background:#2a78d6;border-radius:2px}
h1{font-size:68px;line-height:1.08;font-weight:700;letter-spacing:-.02em;margin-top:22px;max-width:1320px}
h1.big{font-size:96px;max-width:1300px}
.sub{font-size:32px;line-height:1.35;color:#52514e;margin-top:26px;max-width:1240px}
.grow{flex:1;display:flex;flex-direction:column;justify-content:center}
.foot{display:flex;justify-content:space-between;align-items:center;font-size:20px;color:#52514e;border-top:2px solid #e6e5e1;padding-top:20px}
.foot b{color:#0b0b0b;font-weight:600}
.brand{display:flex;align-items:center;gap:12px}
.cards{display:grid;gap:28px}
.c3{grid-template-columns:repeat(3,1fr)}
.c4{grid-template-columns:repeat(4,1fr)}
.card{background:#fff;border:2px solid #e6e5e1;border-radius:16px;padding:34px 32px}
.card .bar{width:48px;height:6px;background:#2a78d6;border-radius:3px;margin-bottom:22px}
.card h3{font-size:31px;line-height:1.2;font-weight:700}
.card p{font-size:23px;line-height:1.4;color:#52514e;margin-top:14px}
.num{font-size:84px;line-height:1;font-weight:700;letter-spacing:-.03em}
.num small{font-size:40px;font-weight:600;color:#52514e;letter-spacing:0}
.label{font-size:24px;line-height:1.35;color:#0b0b0b;font-weight:600;margin-top:16px}
.note{font-size:20px;line-height:1.4;color:#52514e;margin-top:10px}
.step{position:relative}
.step .n{width:56px;height:56px;border-radius:50%;background:#2a78d6;color:#fff;font-size:28px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:20px}
.tl{position:relative;margin:10px 40px 0;height:250px}
.tl .line{position:absolute;left:0;right:0;top:44px;height:4px;background:#d3d2cc;border-radius:2px}
.tl .pt{position:absolute;top:0;width:420px;margin-left:-210px;text-align:center}
.tl .dot{width:28px;height:28px;border-radius:50%;background:#fcfcfb;border:6px solid #52514e;margin:32px auto 0}
.tl .pt.key .dot{background:#2a78d6;border-color:#2a78d6}
.tl .when{font-size:22px;color:#52514e;font-weight:600;height:28px}
.tl .what{font-size:29px;font-weight:700;margin-top:18px;line-height:1.2}
.tl .why{font-size:21px;color:#52514e;margin-top:8px;line-height:1.35}
.callout{background:#fff;border:2px solid #e6e5e1;border-left:8px solid #2a78d6;border-radius:12px;padding:26px 32px;font-size:30px;line-height:1.35;font-weight:600}
.callout span{color:#52514e;font-weight:400}
.pair{display:grid;grid-template-columns:1fr 120px 1fr;gap:0;align-items:stretch}
.pair .vs{display:flex;align-items:center;justify-content:center;font-size:40px;color:#52514e;font-weight:600}
.q{font-size:120px;line-height:1;font-weight:700;color:#0b0b0b}
.tag{display:inline-block;font-size:19px;font-weight:600;color:#52514e;border:2px solid #d3d2cc;border-radius:999px;padding:6px 16px;margin-bottom:18px}
.pending{display:inline-flex;align-items:center;gap:10px;font-size:20px;font-weight:600;color:#52514e;border:2px solid #d3d2cc;border-radius:999px;padding:8px 18px}
.pending i{width:12px;height:12px;border-radius:50%;border:3px solid #52514e;display:inline-block}
"""

LOGO = """<svg width="34" height="34" viewBox="0 0 28 28"><rect x="2" y="15" width="24" height="3" rx="1.5" fill="#0b0b0b"/><rect x="5" y="18" width="2.5" height="8" rx="1" fill="#0b0b0b"/><rect x="20.5" y="18" width="2.5" height="8" rx="1" fill="#0b0b0b"/><rect x="14" y="5" width="9" height="10" rx="1" fill="none" stroke="#0b0b0b" stroke-width="2"/><path d="M16.5 8.5h4M16.5 11.5h4" stroke="#0b0b0b" stroke-width="1.6" stroke-linecap="round"/></svg>"""


def foot(n, right="Pilot in preparation \u00b7 November 2026"):
    return f'<div class="foot"><div class="brand">{LOGO}<span><b>FrontierEval</b> \u00b7 Side of My Desk</span></div><div>{right} \u00b7 {n} / 6</div></div>'


SLIDES = [
    ("1-title", f"""
<div class="grow">
  <div class="kicker"><i></i>FrontierEval</div>
  <h1 class="big">Do your AI plugins age badly?</h1>
  <div class="sub">A repeatable test of whether an AI coding plugin still earns its place each time a new model ships. First subject: the official code-review plugin for Claude Code.</div>
</div>
{foot(1)}"""),

    ("2-problem", f"""
<div class="kicker"><i></i>The problem</div>
<h1>The plugin was written for yesterday's model.</h1>
<div class="grow">
  <div class="tl">
    <div class="line"></div>
    <div class="pt" style="left:14%"><div class="when">September 2026</div><div class="dot"></div><div class="what">Claude Opus 5.5 released</div><div class="why">Already available when the plugin was rewritten</div></div>
    <div class="pt key" style="left:50%"><div class="when">October 2026</div><div class="dot"></div><div class="what">Plugin's current instructions adopted</div><div class="why">A rewrite of how it reviews code</div></div>
    <div class="pt" style="left:86%"><div class="when">November 2026</div><div class="dot"></div><div class="what">Claude Fable 5.2 released</div><div class="why">Newer than the plugin's instructions</div></div>
  </div>
  <div class="callout" style="margin-top:34px">Hypothesis: plugins age badly. <span>Instructions written for an older model help less on a newer one, and may hold it back.</span></div>
</div>
{foot(2)}"""),

    ("3-value", f"""
<div class="kicker"><i></i>Why it matters</div>
<h1>What this gives a team</h1>
<div class="grow">
  <div class="cards c3">
    <div class="card"><div class="bar"></div><h3>A decision before you upgrade</h3><p>When a model ships, know whether to keep, retune, or drop a plugin. Evidence in place of impressions.</p></div>
    <div class="card"><div class="bar"></div><h3>Proof of which model did the work</h3><p>Every request is recorded: the model asked for and the model that answered. Quality and cost are attributed correctly.</p></div>
    <div class="card"><div class="bar"></div><h3>A small bill</h3><p>The whole pilot runs under a $150 ceiling. One plugin review cost about 78 cents.</p></div>
  </div>
</div>
{foot(3)}"""),

    ("4-how", f"""
<div class="kicker"><i></i>How to use it</div>
<h1>Four steps, repeated on every model release</h1>
<div class="grow">
  <div class="cards c4">
    <div class="card step"><div class="n">1</div><h3>Pin</h3><p>Fix the exact model, the plugin version, and the tool version.</p></div>
    <div class="card step"><div class="n">2</div><h3>Run twice</h3><p>Same real pull requests: once with the plugin, once with a plain request to review.</p></div>
    <div class="card step"><div class="n">3</div><h3>Record</h3><p>Log every request: which model answered, how many tokens, any switch to another model.</p></div>
    <div class="card step"><div class="n">4</div><h3>Compare</h3><p>Score both against issues that human reviewers already found.</p></div>
  </div>
</div>
{foot(4)}"""),

    ("5-findings", f"""
<div class="kicker"><i></i>What we have found so far</div>
<h1>Four things we did not expect</h1>
<div class="grow">
  <div class="cards c4">
    <div class="card"><div class="num">3</div><div class="label">models did the work in one "single-model" review</div><div class="note">The plugin picks its own models. We chose one; 32 requests went to three.</div></div>
    <div class="card"><div class="num">1 <small>vs</small> 12</div><div class="label">issues reported: plugin vs plain prompt</div><div class="note">Six were known. The plugin was right and narrow. The plain prompt was broad and noisy.</div></div>
    <div class="card"><div class="num">0</div><div class="label">warnings when a different model answered</div><div class="note">In testing, the tool's own summary still credited the model we asked for.</div></div>
    <div class="card"><div class="num">2.6<small>\u00d7</small></div><div class="label">cost of a plugin review vs a plain one</div><div class="note">About $0.78 against $0.30, on the same pull request.</div></div>
  </div>
  <div class="note" style="margin-top:26px;font-size:21px">Early observations from set-up runs on one pull request. These are not pilot results.</div>
</div>
{foot(5)}"""),

    ("6-result", f"""
<div class="kicker"><i></i>The result we are waiting for</div>
<h1>Does the plugin help less on the newer model?</h1>
<div class="grow">
  <div class="pair">
    <div class="card"><div class="tag">Released before the plugin's instructions</div><h3>Claude Opus 5.5</h3><div class="q" style="margin-top:18px">?</div><p>How much better is review with the plugin than without it</p></div>
    <div class="vs">vs</div>
    <div class="card"><div class="tag">Released after the plugin's instructions</div><h3>Claude Fable 5.2</h3><div class="q" style="margin-top:18px">?</div><p>The same measure, on the newer model</p></div>
  </div>
  <div style="display:flex;justify-content:space-between;align-items:center;margin-top:30px">
    <div class="note" style="font-size:24px;margin:0;max-width:1050px">If plugins age badly, the left number is larger than the right. 120 reviews of 15 real pull requests will tell us.</div>
    <div class="pending"><i></i>Results pending</div>
  </div>
</div>
{foot(6)}"""),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--edge", default=EDGE_DEFAULT)
    args = p.parse_args()
    OUT.mkdir(exist_ok=True)
    # Edge can still hold its profile files for a moment after exiting.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for name, body in SLIDES:
            html = Path(tmp) / f"{name}.html"
            html.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>', encoding="utf-8")
            png = OUT / f"slide-{name}.png"
            # Render into the temp dir (no spaces in the path, separate browser profile),
            # wait for the file, then copy it into place.
            shot = Path(tmp) / f"{name}.png"
            subprocess.run([args.edge, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            f"--user-data-dir={Path(tmp) / 'profile'}", "--window-size=1600,900",
                            f"--screenshot={shot}", html.as_uri()],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            for _ in range(100):
                if shot.exists() and shot.stat().st_size > 0:
                    break
                time.sleep(0.2)
            else:
                raise SystemExit(f"Edge did not produce {shot}")
            shutil.copyfile(shot, png)
            print("wrote", png.name, png.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
