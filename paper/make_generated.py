"""Generate the paper's tables and bibliography from data files.

Tables come from results/pilot-1/*.json, so no result number in a table is
typed by hand. Bibliography entries for arXiv papers come from
paper/arxiv-abstracts.json, which was retrieved from arXiv's API.

Usage: python make_generated.py     (writes paper/generated/*.tex and refs.bib)
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
GEN = HERE / "generated"
S = json.load(open(ROOT / "results" / "pilot-1" / "summary.json", encoding="utf-8"))
N = json.load(open(ROOT / "results" / "pilot-1" / "new-issues-summary.json", encoding="utf-8"))
A = json.load(open(HERE / "arxiv-abstracts.json", encoding="utf-8"))
E = S["estimates"]
CELLS = [("opus55", "plugin", "Opus 5.5", "Plugin"), ("opus55", "baseline", "Opus 5.5", "No plugin"),
         ("fable52", "plugin", "Fable 5.2", "Plugin"), ("fable52", "baseline", "Fable 5.2", "No plugin")]


def pc(k, signed=False):
    e = E[k]
    f = (lambda v: f"{100 * v:+.1f}") if signed else (lambda v: f"{100 * v:.1f}")
    return f"{f(e['value'])} & [{f(e['lo'])}, {f(e['hi'])}]"


def num(k, d=2):
    e = E[k]
    return f"{e['value']:.{d}f}"


def write(name, text):
    (GEN / name).write_text(text, encoding="utf-8", newline="\n")


def main():
    GEN.mkdir(exist_ok=True)

    # Table: main results
    rows = []
    for m, a, mn, an in CELLS:
        k = f"{m}/{a}"
        t = S["totals"][k]
        rows.append(f"{mn} & {an} & {t['runs']} & {pc(k + ':recall_all')} & {pc(k + ':precision_all')} & "
                    f"{num(k + ':findings_per_run', 1)} & {num(k + ':unmatched_per_run', 1)} & \\${num(k + ':cost_per_run')} \\\\")
    write("tab_main.tex", "\n".join(rows) + "\n")

    # Table: strict profile
    rows = []
    for m, a, mn, an in CELLS:
        k = f"{m}/{a}"
        rows.append(f"{mn} & {an} & {pc(k + ':recall_strict')} & {pc(k + ':precision_strict')} \\\\")
    write("tab_strict.tex", "\n".join(rows) + "\n")

    # Table: differences
    rows = []
    for prof, pn in (("all", "All"), ("strict", "Strict")):
        for m, mn in (("opus55", "Opus 5.5: plugin $-$ no plugin"), ("fable52", "Fable 5.2: plugin $-$ no plugin")):
            rows.append(f"{pn} & {mn} & {pc(f'{m}:plugin_minus_baseline:recall_{prof}', True)} & {pc(f'{m}:plugin_minus_baseline:precision_{prof}', True)} \\\\")
        rows.append(f"{pn} & Difference between models (Fable $-$ Opus) & {pc(f'fable_minus_opus:plugin_advantage:recall_{prof}', True)} & "
                    f"{pc(f'fable_minus_opus:plugin_advantage:precision_{prof}', True)} \\\\")
        if prof == "all":
            rows.append("\\midrule")
    write("tab_diff.tex", "\n".join(rows) + "\n")

    # Table: consistency
    rows = []
    for m, a, mn, an in CELLS:
        c = S["consistency"][f"{m}/{a}"]
        rows.append(f"{mn} & {an} & {c['golden_with_two_runs']} & {c['found_in_both']} & {c['found_in_one']} & {c['found_in_neither']} & "
                    f"{100 * c['found_both_given_found_any']:.0f}\\% \\\\")
    write("tab_consistency.tex", "\n".join(rows) + "\n")

    # Table: severity
    rows = []
    for sev in ("Critical", "High", "Medium", "Low"):
        cells = []
        for m, a, _, _ in CELLS:
            v = S["severity"][f"{m}/{a}"].get(sev, {"golden": 0, "found": 0})
            cells.append(f"{v['found']}/{v['golden']}")
        rows.append(f"{sev} & " + " & ".join(cells) + " \\\\")
    write("tab_severity.tex", "\n".join(rows) + "\n")

    # Table: cost by model
    rows = []
    for m, a, mn, an in CELLS:
        t = S["tiers"][f"{m}/{a}"]
        g = lambda k: (f"{t[k]['cost_per_run']:.2f}" if k in t and t[k]["cost_per_run"] >= 0.005 else ("$<$0.01" if k in t else "--"))
        tot = sum(v["cost_per_run"] for v in t.values())
        req = sum(v["requests_per_run"] for v in t.values())
        rows.append(f"{mn} & {an} & {req:.1f} & {g('Fable 5.2')} & {g('Opus 5.5')} & {g('Sonnet 5.5')} & {g('Haiku 5.5')} & {tot:.2f} \\\\")
    write("tab_cost.tex", "\n".join(rows) + "\n")

    # Table: delegation
    rows = []
    for m, mn in (("opus55", "Opus 5.5"), ("fable52", "Fable 5.2")):
        d = S["delegation"][m]
        for key, label in (("with_subagents", "Launched subagents"), ("no_subagents", "No subagents")):
            x = d[key]
            if x["runs"] == 0:
                rows.append(f"{mn} & {label} & 0 & -- & -- & -- \\\\")
            else:
                rows.append(f"{mn} & {label} & {x['runs']} & {100 * x['recall']:.1f} & {100 * x['precision']:.1f} & \\${x['cost_per_run']:.2f} \\\\")
    write("tab_delegation.tex", "\n".join(rows) + "\n")

    # Table: checker verdicts
    rows = []
    for m, a, mn, an in CELLS:
        v = N["verdicts_by_cell"][f"{m}/{a}"]
        n = sum(v.values())
        rows.append(f"{mn} & {an} & {n} & {v.get('real', 0)} ({100 * v.get('real', 0) / n:.0f}\\%) & {v.get('cannot_tell', 0)} ({100 * v.get('cannot_tell', 0) / n:.0f}\\%) & "
                    f"{v.get('not_real', 0)} ({100 * v.get('not_real', 0) / n:.0f}\\%) \\\\")
    write("tab_checker.tex", "\n".join(rows) + "\n")

    # Table: new issues by category
    cats = N["by_category"]
    pa, ba = N["by_arm_and_category"]["plugin"], N["by_arm_and_category"]["baseline"]
    rows = [f"{c.replace('_', ' ')} & {n} & {pa.get(c, 0)} & {ba.get(c, 0)} \\\\" for c, n in cats.items()]
    rows.append("\\midrule")
    rows.append(f"Total & {N['distinct_new_issues']} & {N['distinct_found_by_arm']['plugin']} & {N['distinct_found_by_arm']['baseline']} \\\\")
    write("tab_newissues.tex", "\n".join(rows) + "\n")

    # Bibliography
    keys = {
        "rudyk2026aging": "2608.24641", "salsabil2026survives": "2609.00468", "gloaguen2026agentsmd": "2602.11988",
        "li2026skillsbench": "2602.12670", "ying2026openskilleval": "2605.23657", "han2026sweskills": "2603.15401",
        "cho2026harness": "2605.26731", "meincke2025cot": "2506.07142", "wang2024advanced": "2411.02093",
        "chen2023chatgpt": "2307.09009", "ma2023regression": "2311.11123", "sclar2023sensitivity": "2310.11324",
        "kapoor2024agents": "2407.01502", "cemri2025mas": "2503.13657", "kim2025scaling": "2512.08296",
        "tran2026single": "2604.02460", "zheng2023judging": "2306.05685", "panickssery2024self": "2404.13076",
        "spiliopoulou2025favorites": "2508.06709", "ramos2024memorizing": "2411.13323", "liang2025illusion": "2506.12286",
        "badertdinov2025rebench": "2505.20411", "miller2024errorbars": "2411.00640", "bjarnason2026randomness": "2602.07150",
        "zhang2026aacr": "2601.19494", "zeng2025swr": "2509.01494", "zhang2026ccrab": "2603.23448",
        "pereira2026crbench": "2603.11078", "li2022codereviewer": "2203.09095", "sun2025bitsai": "2501.15134",
        "gao2024equality": "2410.20247", "cai2025substitution": "2504.04715", "bhatt2024cyberseceval": "2404.13161",
        "cui2024orbench": "2405.20947",
    }

    def esc(s):
        for a, b in (("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_")):
            s = s.replace(a, b)
        return s

    bib = []
    for key, aid in keys.items():
        o = A[aid]
        authors = o["authors"]
        au = " and ".join(authors[:8]) + (" and others" if len(authors) > 8 else "")
        note = o.get("journal_ref") or ""
        if not note and o.get("comment") and "ccepted" in o["comment"]:
            note = o["comment"]
        bib.append("@misc{%s,\n  author = {%s},\n  title = {{%s}},\n  year = {%s},\n  eprint = {%s},\n  archivePrefix = {arXiv},\n"
                   "  howpublished = {arXiv:%s}%s\n}\n" % (key, esc(au), esc(o["title"]), o["published"][:4], aid, aid,
                                                             (",\n  note = {%s}" % esc(note)) if note else ""))
    bib.append("""@misc{martian2026bench,
  author = {{Martian}},
  title = {{Code Review Bench}},
  year = {2026},
  howpublished = {\\url{https://github.com/withmartian/code-review-benchmark}},
  note = {Commit e616e84, accessed 15 November 2026}
}
""")
    bib.append("""@misc{anthropic2026plugin,
  author = {{Anthropic}},
  title = {{code-review plugin, claude-plugins-official}},
  year = {2026},
  howpublished = {\\url{https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-review}},
  note = {Commit 9780cf4, accessed 15 November 2026}
}
""")
    bib.append("""@misc{anthropic2026refusals,
  author = {{Anthropic}},
  title = {{Refusals and fallback}},
  year = {2026},
  howpublished = {\\url{https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback}},
  note = {Claude platform documentation, accessed 15 November 2026}
}
""")
    bib.append("""@misc{anthropic2026modelconfig,
  author = {{Anthropic}},
  title = {{Model configuration}},
  year = {2026},
  howpublished = {\\url{https://code.claude.com/docs/en/model-config}},
  note = {Claude Code documentation, accessed 15 November 2026}
}
""")
    bib.append("""@misc{anthropic2026effort,
  author = {{Anthropic}},
  title = {{Effort}},
  year = {2026},
  howpublished = {\\url{https://platform.claude.com/docs/en/build-with-claude/effort}},
  note = {Claude platform documentation, accessed 15 November 2026}
}
""")
    (HERE / "refs.bib").write_text("\n".join(bib), encoding="utf-8", newline="\n")
    print("wrote", len(list(GEN.glob("*.tex"))), "table fragments and", len(bib), "bibliography entries")


if __name__ == "__main__":
    main()
