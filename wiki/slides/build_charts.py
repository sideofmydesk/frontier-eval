"""Build the pilot result charts as 1600x900 PNG images.

Reads results/pilot-1/summary.json and checker-summary.json. Each chart is an
HTML page with inline SVG, rendered by headless Microsoft Edge.
Usage: python build_charts.py [--edge <path>]
Output: ../images/chart-NN-<name>.png

Chart rules followed: colour follows the entity (with the plugin = blue,
without = orange, everywhere); text is always ink, never the series colour;
every chart with two or more series has a legend and direct value labels;
intervals are drawn wherever a number is an estimate. Palettes were checked
with the dataviz validator for colour-blind separation and contrast.
"""

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE.parent / "images"
EDGE_DEFAULT = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
PLUGIN, WITHOUT = "#2a78d6", "#eb6834"
TIER = {"Fable 5.2": "#1baf7a", "Opus 5.5": "#eda100", "Sonnet 5.5": "#e87ba4", "Haiku 5.5": "#008300"}
ARM_NAME = {"plugin": "With the plugin", "baseline": "Without the plugin"}
ARM_COLOR = {"plugin": PLUGIN, "baseline": WITHOUT}
MODEL_NAME = {"opus55": "Claude Opus 5.5", "fable52": "Claude Fable 5.2"}
W, H = 1424, 500  # chart canvas

CSS = f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:1600px;height:900px;overflow:hidden}}
body{{background:{SURFACE};color:{INK};font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;padding:56px 88px 48px;display:flex;flex-direction:column}}
.kicker{{font-size:20px;letter-spacing:.14em;text-transform:uppercase;color:{MUTED};font-weight:600;display:flex;align-items:center;gap:14px}}
.kicker i{{display:inline-block;width:36px;height:4px;background:{PLUGIN};border-radius:2px}}
h1{{font-size:46px;line-height:1.12;font-weight:700;letter-spacing:-.02em;margin-top:14px;max-width:1400px}}
.sub{{font-size:24px;line-height:1.35;color:{MUTED};margin-top:10px;max-width:1380px}}
.chart{{flex:1;display:flex;align-items:center;margin-top:8px}}
svg{{width:{W}px;height:{H}px;overflow:visible}}
svg text{{font-family:inherit}}
.note{{font-size:18px;color:{MUTED};line-height:1.35;margin-bottom:14px;max-width:1420px}}
.foot{{display:flex;justify-content:space-between;align-items:center;font-size:18px;color:{MUTED};border-top:2px solid {GRID};padding-top:14px}}
.foot b{{color:{INK};font-weight:600}}
.brand{{display:flex;align-items:center;gap:12px}}
"""
LOGO = f"""<svg style="width:30px;height:30px" viewBox="0 0 28 28"><rect x="2" y="15" width="24" height="3" rx="1.5" fill="{INK}"/><rect x="5" y="18" width="2.5" height="8" rx="1" fill="{INK}"/><rect x="20.5" y="18" width="2.5" height="8" rx="1" fill="{INK}"/><rect x="14" y="5" width="9" height="10" rx="1" fill="none" stroke="{INK}" stroke-width="2"/><path d="M16.5 8.5h4M16.5 11.5h4" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/></svg>"""
BASE_NOTE = "Pilot: 15 real pull requests, 2 models, 2 repeats, 120 reviews. Exploratory; the cases and their answers are public."


def t(x, y, s, size=22, weight=400, fill=INK, anchor="start"):
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>'


def legend(items, x=0, y=20):
    out, cx = [], x
    for name, color in items:
        out.append(f'<rect x="{cx}" y="{y - 15}" width="18" height="18" rx="4" fill="{color}"/>')
        out.append(t(cx + 28, y, name, 21, 400, INK))
        cx += 28 + len(name) * 11.5 + 40
    return "".join(out)


def bar(x, y0, y1, w, color):
    """Vertical bar from baseline y0 up to y1, rounded at the data end only."""
    h = y0 - y1
    if h <= 0:
        return ""
    r = min(4, h)
    return (f'<path d="M{x:.1f},{y0:.1f} V{y1 + r:.1f} Q{x:.1f},{y1:.1f} {x + r:.1f},{y1:.1f} H{x + w - r:.1f} '
            f'Q{x + w:.1f},{y1:.1f} {x + w:.1f},{y1 + r:.1f} V{y0:.1f} Z" fill="{color}"/>')


def whisker(x, ylo, yhi):
    return (f'<line x1="{x:.1f}" y1="{ylo:.1f}" x2="{x:.1f}" y2="{yhi:.1f}" stroke="{INK}" stroke-width="2"/>'
            f'<line x1="{x - 7:.1f}" y1="{ylo:.1f}" x2="{x + 7:.1f}" y2="{ylo:.1f}" stroke="{INK}" stroke-width="2"/>'
            f'<line x1="{x - 7:.1f}" y1="{yhi:.1f}" x2="{x + 7:.1f}" y2="{yhi:.1f}" stroke="{INK}" stroke-width="2"/>')


def grouped_bars(groups, ymax, fmt, ticks, legend_items, top=70, bottom=H - 56, left=70, bw=64):
    """groups: [(label, [(color, value, lo, hi), ...])]"""
    out = [legend(legend_items)]
    sy = lambda v: bottom - (v / ymax) * (bottom - top)
    for v in ticks:
        out.append(f'<line x1="{left}" y1="{sy(v):.1f}" x2="{W}" y2="{sy(v):.1f}" stroke="{GRID}" stroke-width="1.5"/>')
        out.append(t(left - 12, sy(v) + 7, fmt(v), 19, 400, MUTED, "end"))
    gw = (W - left) / len(groups)
    for gi, (label, bars) in enumerate(groups):
        n = len(bars)
        total = n * bw + (n - 1) * 14
        x0 = left + gi * gw + (gw - total) / 2
        for bi, (color, v, lo, hi) in enumerate(bars):
            x = x0 + bi * (bw + 14)
            out.append(bar(x, bottom, sy(v), bw, color))
            if lo is not None:
                out.append(whisker(x + bw / 2, sy(lo), sy(hi)))
            top_y = sy(hi if hi is not None else v)
            out.append(t(x + bw / 2, top_y - 12, fmt(v), 24, 700, INK, "middle"))
        out.append(t(left + gi * gw + gw / 2, bottom + 36, label, 23, 600, INK, "middle"))
    out.append(f'<line x1="{left}" y1="{bottom}" x2="{W}" y2="{bottom}" stroke="{MUTED}" stroke-width="2"/>')
    return "".join(out)


def interval_rows(rows, lo, hi, fmt, ticks, zero_label, left=520, top=40, row_h=None, right=W - 150):
    """rows: [(label, sublabel, color, value, vlo, vhi, tag)]  horizontal dot-and-interval plot."""
    row_h = row_h or (H - top - 70) / len(rows)
    sx = lambda v: left + (v - lo) / (hi - lo) * (right - left)
    out = []
    for v in ticks:
        out.append(f'<line x1="{sx(v):.1f}" y1="{top - 10}" x2="{sx(v):.1f}" y2="{top + row_h * len(rows)}" stroke="{GRID}" stroke-width="1.5"/>')
        out.append(t(sx(v), top + row_h * len(rows) + 30, fmt(v), 19, 400, MUTED, "middle"))
    out.append(f'<line x1="{sx(0):.1f}" y1="{top - 18}" x2="{sx(0):.1f}" y2="{top + row_h * len(rows)}" stroke="{INK}" stroke-width="2"/>')
    out.append(t(sx(0), top + row_h * len(rows) + 60, zero_label, 19, 600, INK, "middle"))
    for i, (label, sub, color, v, vlo, vhi, tag) in enumerate(rows):
        y = top + row_h * i + row_h / 2
        out.append(t(0, y - 4, label, 24, 600, INK))
        if sub:
            out.append(t(0, y + 24, sub, 19, 400, MUTED))
        out.append(f'<line x1="{sx(vlo):.1f}" y1="{y:.1f}" x2="{sx(vhi):.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="6" stroke-linecap="round" opacity="0.45"/>')
        out.append(f'<circle cx="{sx(v):.1f}" cy="{y:.1f}" r="11" fill="{color}" stroke="{SURFACE}" stroke-width="3"/>')
        out.append(t(right + 24, y + (2 if tag else 8), fmt(v), 26, 700, INK))
        if tag:
            out.append(t(right + 24, y + 28, tag, 18, 600, MUTED))
    return "".join(out)


def hstack(rows, xmax, fmt, legend_items, left=330, top=64, bar_h=44, gap=30, total_fmt=None, right=W - 130):
    """rows: [(label, sublabel, [(color, value, text_color), ...])]"""
    out = [legend(legend_items)]
    sx = lambda v: (v / xmax) * (right - left)
    for i, (label, sub, parts) in enumerate(rows):
        y = top + i * (bar_h + gap)
        out.append(t(0, y + bar_h / 2 + (0 if sub else 8), label, 23, 600, INK))
        if sub:
            out.append(t(0, y + bar_h / 2 + 26, sub, 18, 400, MUTED))
        x = left
        for color, v, tc in parts:
            w = sx(v)
            if w <= 0:
                continue
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w - 2, 1):.1f}" height="{bar_h}" rx="4" fill="{color}"/>')
            if w > 62:
                out.append(t(x + 10, y + bar_h / 2 + 8, fmt(v), 21, 700, tc))
            x += w
        if total_fmt:
            out.append(t(x + 14, y + bar_h / 2 + 8, total_fmt(sum(p[1] for p in parts)), 24, 700, INK))
    return "".join(out)


BARE = {}


def page(kicker, title, sub, svg, note, n, total):
    BARE[n] = svg
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="kicker"><i></i>{kicker}</div><h1>{title}</h1><div class="sub">{sub}</div>'
            f'<div class="chart"><svg viewBox="0 0 {W} {H}">{svg}</svg></div>'
            f'<div class="note">{note}</div>'
            f'<div class="foot"><div class="brand">{LOGO}<span><b>FrontierEval</b> \u00b7 Side of My Desk</span></div>'
            f'<div>Pilot results \u00b7 November 2026 \u00b7 chart {n} of {total}</div></div></body></html>')


def build(S, C, N):
    E = S["estimates"]
    pc = lambda v: f"{100 * v:.0f}%"
    pts = lambda v: f"{100 * v:+.0f} pts"
    charts = []
    arm_legend = [(ARM_NAME["plugin"], PLUGIN), (ARM_NAME["baseline"], WITHOUT)]

    def cell_groups(metric):
        g = []
        for m in ("opus55", "fable52"):
            g.append((MODEL_NAME[m], [(ARM_COLOR[a], E[f"{m}/{a}:{metric}"]["value"], E[f"{m}/{a}:{metric}"]["lo"], E[f"{m}/{a}:{metric}"]["hi"])
                                      for a in ("plugin", "baseline")]))
        return g

    r = {k: E[k]["value"] for k in E}
    # 1 recall
    charts.append(("01-recall", page(
        "Result 1", "Without the plugin, each model found about twice as many known issues",
        "Share of the benchmark's known issues that a review reported (recall). Higher is better.",
        grouped_bars(cell_groups("recall_all"), 1.0, pc, [0, .25, .5, .75, 1.0], arm_legend),
        "Lines show 95% intervals from resampling the 15 pull requests. " + BASE_NOTE, 1, 12)))
    # 2 precision
    charts.append(("02-precision", page(
        "Result 2", "The plugin said less, and more of what it said matched a known issue",
        "Share of a review's findings that match one of the benchmark's known issues (precision). Higher is better.",
        grouped_bars(cell_groups("precision_all"), 1.0, pc, [0, .25, .5, .75, 1.0], arm_legend),
        "This is a floor: the benchmark's list is incomplete, so a correct finding it lacks counts against precision. See chart 10. "
        "Lines show 95% intervals.", 2, 12)))
    # 3 deltas
    rows = []
    for metric, name in (("recall_all", "Known issues found"), ("precision_all", "Findings that match")):
        for m in ("opus55", "fable52"):
            e = E[f"{m}:plugin_minus_baseline:{metric}"]
            rows.append((name, MODEL_NAME[m], PLUGIN, e["value"], e["lo"], e["hi"], None))
    charts.append(("03-plugin-effect", page(
        "The deltas", "What adding the plugin changed, on each model",
        "With the plugin minus without it, in percentage points. Left of the line the plugin did worse; right of it, better.",
        interval_rows(rows, -0.6, 0.6, pts, [-.6, -.4, -.2, .2, .4, .6], "no difference"),
        "Dot is the estimate; the band is its 95% interval. None of the four bands crosses the line: the plugin clearly found fewer "
        "known issues and clearly had a higher match rate, on both models.", 3, 12)))
    # 4 hypothesis
    er, ep = E["fable_minus_opus:plugin_advantage:recall_all"], E["fable_minus_opus:plugin_advantage:precision_all"]
    rows = [("Match rate (precision)", "Plugin's edge: +32 pts on Opus 5.5, +17 pts on Fable 5.2", PLUGIN, ep["value"], ep["lo"], ep["hi"], "clear"),
            ("Known issues found (recall)", "Plugin's gap: \u221235 pts on Opus 5.5, \u221241 pts on Fable 5.2", PLUGIN, er["value"], er["lo"], er["hi"], "not clear")]
    charts.append(("04-hypothesis", page(
        "The hypothesis test", "Did the plugin help less on the newer model? Partly.",
        "Plugin's effect on Fable 5.2 minus its effect on Opus 5.5, in percentage points. Left of the line supports \u201cplugins age badly\u201d.",
        interval_rows(rows, -0.4, 0.2, pts, [-.4, -.3, -.2, -.1, .1, .2], "same on both models", left=640, top=70, row_h=150),
        "On match rate, the plugin's edge was about 15 points smaller on the newer model, and the interval excludes zero. On issues found, "
        "the difference is inside the noise. On Fable 5.2 the plugin's bug reviewers were Opus 5.5, so this cannot say why.", 4, 12)))
    # 5 findings per review
    rows = []
    for m in ("opus55", "fable52"):
        for a in ("plugin", "baseline"):
            f, u = r[f"{m}/{a}:findings_per_run"], r[f"{m}/{a}:unmatched_per_run"]
            rows.append((ARM_NAME[a], MODEL_NAME[m], [("#3d3c39", f - u, "#ffffff"), ("#c9c8c2", u, INK)]))
    charts.append(("05-volume", page(
        "Result 3", "About 2 findings per review with the plugin, 10 to 11 without",
        "Average findings per review, split by whether the judge matched them to a known issue.",
        hstack(rows, 12.5, lambda v: f"{v:.1f}", [("Matches a known issue", "#3d3c39"), ("No match in the benchmark", "#c9c8c2")],
               total_fmt=lambda v: f"{v:.1f}"),
        "\u201cNo match\u201d does not mean wrong. A checker model judged about half of these to be real issues the benchmark lacks (chart 10).", 5, 12)))
    # 6 cost by tier
    order = ["Fable 5.2", "Opus 5.5", "Sonnet 5.5", "Haiku 5.5"]
    rows = []
    for m in ("opus55", "fable52"):
        for a in ("plugin", "baseline"):
            tiers = S["tiers"][f"{m}/{a}"]
            rows.append((ARM_NAME[a], MODEL_NAME[m] + " session",
                         [(TIER[k], tiers[k]["cost_per_run"], INK) for k in order if k in tiers and tiers[k]["cost_per_run"] >= 0.01]))
    charts.append(("06-cost", page(
        "Result 4", "The plugin cost about 1.5 times as much, and part of the bill was a different model",
        "Estimated cost per review in US dollars, split by the model that did the work.",
        hstack(rows, 2.1, lambda v: f"${v:.2f}", [(k, TIER[k]) for k in order], total_fmt=lambda v: f"${v:.2f}"),
        "In a Fable 5.2 session the plugin sent its bug review to Opus 5.5, as its instructions say. Haiku 5.5 costs under 1 cent per review and is not drawn. "
        "Costs are Claude Code's estimates.", 6, 12)))
    # 7 delegation
    d = S["delegation"]
    groups = []
    for m in ("opus55", "fable52"):
        n = d[m]["plugin_runs"]
        none = d[m]["runs_with_no_subagents"]
        groups.append((MODEL_NAME[m], [("#3d3c39", (n - none) / n, None, None), ("#c9c8c2", none / n, None, None)]))
    charts.append(("07-delegation", page(
        "Result 5", "Opus 5.5 skipped the plugin's multi-agent process in 13 of 30 reviews",
        "Share of plugin reviews in which the session launched the subagents the plugin asks for, or did the review itself.",
        grouped_bars(groups, 1.0, pc, [0, .25, .5, .75, 1.0], [("Launched subagents", "#3d3c39"), ("Did the review itself", "#c9c8c2")], bw=90),
        f"When Opus 5.5 skipped the subagents, a review cost ${d['opus55']['no_subagents']['cost_per_run']:.2f} against "
        f"${d['opus55']['with_subagents']['cost_per_run']:.2f}, and found a similar share of known issues "
        f"({pc(d['opus55']['no_subagents']['recall'])} against {pc(d['opus55']['with_subagents']['recall'])}). 30 plugin reviews per model.", 7, 12)))
    # 8 per case dumbbells
    svg = [legend(arm_legend)]
    panel_w, gapx, top, bottom = 540, 130, 96, H - 34
    cases = S["per_case"]
    rh = (bottom - top) / len(cases)
    for pi, m in enumerate(("opus55", "fable52")):
        x0 = 150 + pi * (panel_w + gapx)
        sx = lambda v: x0 + v * panel_w
        svg.append(t(x0 + panel_w / 2, top - 30, MODEL_NAME[m], 23, 700, INK, "middle"))
        for v in (0, .5, 1):
            svg.append(f'<line x1="{sx(v):.1f}" y1="{top - 8}" x2="{sx(v):.1f}" y2="{bottom}" stroke="{GRID}" stroke-width="1.5"/>')
            svg.append(t(sx(v), bottom + 24, pc(v), 17, 400, MUTED, "middle"))
        for i, c in enumerate(cases):
            y = top + rh * i + rh / 2
            if pi == 0:
                svg.append(t(0, y + 6, f"{c['project'].replace('_dot_', '.')} {i % 3 + 1}", 17, 400, MUTED))
            vals = {}
            for a in ("plugin", "baseline"):
                cc = c[f"{m}/{a}"]
                vals[a] = cc["found"] / cc["golden"] if cc["golden"] else None
            if None not in vals.values():
                svg.append(f'<line x1="{sx(vals["plugin"]):.1f}" y1="{y:.1f}" x2="{sx(vals["baseline"]):.1f}" y2="{y:.1f}" stroke="#c9c8c2" stroke-width="4"/>')
            tie = None not in vals.values() and abs(vals["plugin"] - vals["baseline"]) < 1e-9
            for a in ("baseline", "plugin"):
                if vals[a] is not None:
                    # On a tie, draw the two dots side by side so neither hides the other.
                    dx = (9 if a == "baseline" else -9) if tie else 0
                    svg.append(f'<circle cx="{sx(vals[a]) + dx:.1f}" cy="{y:.1f}" r="9" fill="{ARM_COLOR[a]}" stroke="{SURFACE}" stroke-width="2.5"/>')
    wins = {m: sum(1 for c in cases if c[f"{m}/plugin"]["golden"] and c[f"{m}/baseline"]["golden"] and
                   c[f"{m}/plugin"]["found"] / c[f"{m}/plugin"]["golden"] > c[f"{m}/baseline"]["found"] / c[f"{m}/baseline"]["golden"]) for m in MODEL_NAME}
    ties = {m: sum(1 for c in cases if c[f"{m}/plugin"]["golden"] and c[f"{m}/baseline"]["golden"] and
                   abs(c[f"{m}/plugin"]["found"] / c[f"{m}/plugin"]["golden"] - c[f"{m}/baseline"]["found"] / c[f"{m}/baseline"]["golden"]) < 1e-9) for m in MODEL_NAME}
    charts.append(("08-per-case", page(
        "Case by case", "The gap is broad, not driven by a few pull requests",
        "Share of known issues found on each of the 15 pull requests, both repeats combined.",
        "".join(svg),
        f"With the plugin, the review found a larger share on {wins['opus55']} of 15 pull requests with Opus 5.5 and {wins['fable52']} of 15 with Fable 5.2. "
        f"The two tied on {ties['opus55']} and {ties['fable52']}. Each pull request has 2 to 8 known issues, so single rows move in large steps.", 8, 12)))
    # 9 consistency
    groups = []
    for m in ("opus55", "fable52"):
        groups.append((MODEL_NAME[m], [(ARM_COLOR[a], S["consistency"][f"{m}/{a}"]["found_both_given_found_any"], None, None) for a in ("plugin", "baseline")]))
    charts.append(("09-consistency", page(
        "Result 6", "The plugin was less repeatable from one run to the next",
        "Of the known issues a setup found at least once in two runs, the share it found both times.",
        grouped_bars(groups, 1.0, pc, [0, .25, .5, .75, 1.0], arm_legend),
        "Each pull request was reviewed twice per setup. A reviewer that finds different things each time is harder to rely on. "
        "No intervals are shown; these are counts from 45 to 53 known issues per setup.", 9, 12)))
    # 10 checker
    rows = []
    for a in ("plugin", "baseline"):
        tot = {"real": 0, "cannot_tell": 0, "not_real": 0}
        for m in ("opus55", "fable52"):
            for k, v in C["verdicts_by_cell"][f"{m}/{a}"].items():
                tot[k] += v
        n = sum(tot.values())
        rows.append((ARM_NAME[a], f"{n} findings", [("#3d3c39", tot["real"] / n, "#ffffff"), ("#a3a29b", tot["cannot_tell"] / n, INK), ("#dddcd6", tot["not_real"] / n, INK)]))
    charts.append(("10-unmatched", page(
        "A check on the benchmark", "Most findings the benchmark did not list still looked real",
        "A checker model's verdict on all 543 findings that matched no known issue, judged against each pull request's diff.",
        hstack(rows, 1.0, pc, [("Real issue", "#3d3c39"), ("Cannot tell from the diff", "#a3a29b"), ("Not a real issue", "#dddcd6")], top=110, bar_h=64, gap=70),
        "So the match rates in chart 2 understate both setups. This is one model's opinion from the diff alone, and it has not been checked by hand.", 10, 12)))
    # 11 severity
    sev = ["Critical", "High", "Medium", "Low"]
    groups = []
    for s in sev:
        bars = []
        for a in ("plugin", "baseline"):
            g = sum(S["severity"][f"{m}/{a}"].get(s, {}).get("golden", 0) for m in MODEL_NAME)
            f = sum(S["severity"][f"{m}/{a}"].get(s, {}).get("found", 0) for m in MODEL_NAME)
            bars.append((ARM_COLOR[a], f / g if g else 0, None, None))
        groups.append((s, bars))
    charts.append(("11-severity", page(
        "By severity", "The gap holds at every severity, and is widest on low-severity issues",
        "Share of known issues found, by the severity the benchmark's reviewers gave them. Both models combined.",
        grouped_bars(groups, 1.0, pc, [0, .25, .5, .75, 1.0], arm_legend),
        "Critical issues are few (8 to 10 per setup across all runs), so that pair is the least certain. No intervals are shown.", 11, 12)))
    # 12 new issues
    ov = N["overlap"]
    rows = [("Listed in the benchmark", "for these 15 pull requests", [("#c9c8c2", 53, INK)]),
            ("Not listed, judged real", "distinct issues, by a checker model", [(WITHOUT, ov["baseline_only"], INK), ("#3d3c39", ov["both"], "#ffffff"), (PLUGIN, ov["plugin_only"], "#ffffff")])]
    charts.append(("12-new-issues", page(
        "Beyond the benchmark", "The reviews surfaced 123 issues the benchmark does not list",
        "Distinct issues in the 15 pull requests. The lower bar is split by which setup found each new issue.",
        hstack(rows, 135, lambda v: f"{v:.0f}",
               [("Found only without the plugin", WITHOUT), ("Found by both", "#3d3c39"), ("Found only with the plugin", PLUGIN), ("Benchmark's list", "#c9c8c2")],
               top=110, bar_h=64, gap=70, total_fmt=lambda v: f"{v:.0f}"),
        f"Reviews without the plugin found {N['distinct_found_by_arm']['baseline']} of the 123; reviews with it found {N['distinct_found_by_arm']['plugin']}. "
        "“Real” is one checker model’s verdict from the diff alone. It has not been confirmed by hand.", 12, 12)))
    return charts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--edge", default=EDGE_DEFAULT)
    args = p.parse_args()
    S = json.load(open(ROOT / "results" / "pilot-1" / "summary.json", encoding="utf-8"))
    C = json.load(open(ROOT / "results" / "pilot-1" / "new-issues-summary.json", encoding="utf-8"))
    N = C
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        built = build(S, C, N)
        for name, html_text in built:
            html = Path(tmp) / f"{name}.html"
            html.write_text(html_text, encoding="utf-8")
            shot = Path(tmp) / f"{name}.png"
            subprocess.run([args.edge, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            f"--user-data-dir={Path(tmp) / 'profile'}", "--window-size=1600,900", f"--screenshot={shot}", html.as_uri()],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            for _ in range(100):
                if shot.exists() and shot.stat().st_size > 0:
                    break
                time.sleep(0.2)
            else:
                raise SystemExit(f"Edge did not produce {shot}")
            shutil.copyfile(shot, OUT / f"chart-{name}.png")
            print("wrote", f"chart-{name}.png")
        # Plain figures for the paper: the chart alone, on white, at double resolution.
        FIG = ROOT / "paper" / "figures"
        FIG.mkdir(parents=True, exist_ok=True)
        for i, (name, _) in enumerate(built, start=1):
            html = Path(tmp) / f"fig-{name}.html"
            html.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>*{{margin:0;padding:0}}html,body{{background:#fff;overflow:hidden}}'
                            f'body{{padding:24px 24px 28px;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:{INK}}}'
                            f'svg{{width:{W}px;height:{H}px;overflow:visible}}svg text{{font-family:inherit}}</style></head>'
                            f'<body><svg viewBox="0 0 {W} {H}">{BARE[i]}</svg></body></html>', encoding="utf-8")
            shot = Path(tmp) / f"fig-{name}.png"
            subprocess.run([args.edge, "--headless", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                            f"--user-data-dir={Path(tmp) / 'profile'}", f"--window-size={W + 48},{H + 60}", f"--screenshot={shot}", html.as_uri()],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
            for _ in range(100):
                if shot.exists() and shot.stat().st_size > 0:
                    break
                time.sleep(0.2)
            else:
                raise SystemExit(f"Edge did not produce {shot}")
            shutil.copyfile(shot, FIG / f"fig-{name}.png")
        print("wrote", len(built), "paper figures")


if __name__ == "__main__":
    main()
