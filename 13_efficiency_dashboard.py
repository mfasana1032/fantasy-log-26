"""
Fairfield Dynasty League -- Weekly Lineup Efficiency Dashboard
Run this from: C:\\Users\\micha\\OneDrive\\Python\\Rndom\\Fantasy Football
(run 05_lineup_efficiency.py first -- this reads its output)

WHAT THIS DOES:
  Reads data/lineup_efficiency_worst_weeks.csv (which despite its name
  contains EVERY team-week, not just the worst ones) and builds a single
  self-contained HTML dashboard: data/efficiency_dashboard.html

  Open that file in any browser. Nothing to install, no server, no
  internet needed -- the data is baked into the file.

  Shows:
    - A season-by-season grid of every team's weekly efficiency
    - VIOLATIONS (below 50%) -- the ratified constitutional threshold
    - REVIEW (50-60%) -- commissioner-only watch tier, not a rule
    - Season averages per team, with the 70% season line marked

BEFORE RUNNING:
  Run 05_lineup_efficiency.py first.
"""

import csv
import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

VIOLATION = 50.0   # ratified: below this is a lineup requirement violation
REVIEW    = 60.0   # commissioner watch tier only -- NOT a league rule


def main():
    src = DATA_DIR / "lineup_efficiency_worst_weeks.csv"
    if not src.exists():
        raise SystemExit(f"Missing {src} -- run 05_lineup_efficiency.py first.")

    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit("No rows found in the efficiency file.")

    recs = []
    for r in rows:
        try:
            recs.append({
                "season": str(r["season"]),
                "week": int(r["week"]),
                "team": r["team"],
                "actual": float(r["actual"]),
                "optimal": float(r["optimal"]),
                "eff": float(r["efficiency_pct"]),
            })
        except (KeyError, ValueError):
            continue

    seasons = sorted({r["season"] for r in recs}, reverse=True)
    teams = sorted({r["team"] for r in recs})
    weeks = sorted({r["week"] for r in recs})

    # season averages per team (unweighted mean of weekly figures, which
    # matches how the weekly view is read; 05's own season file uses
    # total-points ratio, so small differences are expected)
    season_avg = defaultdict(dict)
    for s in seasons:
        for t in teams:
            vals = [r["eff"] for r in recs if r["season"] == s and r["team"] == t]
            if vals:
                season_avg[s][t] = sum(vals) / len(vals)

    violations = sorted([r for r in recs if r["eff"] < VIOLATION],
                        key=lambda r: (r["season"], r["week"]), reverse=True)
    review = sorted([r for r in recs if VIOLATION <= r["eff"] < REVIEW],
                    key=lambda r: (r["season"], r["week"]), reverse=True)

    payload = {
        "seasons": seasons, "teams": teams, "weeks": weeks,
        "recs": recs, "seasonAvg": {s: season_avg[s] for s in seasons},
        "violations": violations, "review": review,
        "generated": datetime.now().strftime("%b %d, %Y at %I:%M %p"),
        "VIOLATION": VIOLATION, "REVIEW": REVIEW,
    }

    out = DATA_DIR / "efficiency_dashboard.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.replace("__PAYLOAD__", json.dumps(payload)))

    print(f"Saved {out}")
    print(f"  {len(recs)} team-weeks across {len(seasons)} seasons")
    print(f"  {len(violations)} below {VIOLATION:.0f}% (violations)")
    print(f"  {len(review)} between {VIOLATION:.0f}% and {REVIEW:.0f}% (review tier)")
    print("\nOpen that file in your browser.")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lineup Efficiency — Fairfield Dynasty</title>
<style>
:root{--crimson:#C8102E;--ink:#141414;--body:#3E4448;--muted:#767E82;
--line:#E3E6E8;--panel:#fff;--bg:#F4F6F7;--warn:#D98324;--bad:#C8102E;--ok:#2F7D4F;}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--body);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;padding:28px 22px 70px;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--crimson);font-weight:700;margin-bottom:6px}
h1{font-size:27px;color:var(--ink);letter-spacing:-.02em;margin-bottom:4px}
.sub{font-size:13px;color:var(--muted);margin-bottom:22px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:26px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card .k{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.card .v{font-size:25px;font-weight:700;color:var(--ink);line-height:1}
.card.bad .v{color:var(--bad)} .card.warn .v{color:var(--warn)}
.tabs{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}
.tab{padding:7px 15px;border:1px solid var(--line);background:var(--panel);border-radius:7px;font-size:13px;cursor:pointer;color:var(--body)}
.tab.on{background:var(--crimson);color:#fff;border-color:var(--crimson);font-weight:600}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:22px;overflow-x:auto}
h2{font-size:15px;color:var(--ink);margin-bottom:3px}
.note{font-size:12px;color:var(--muted);margin-bottom:14px}
table{border-collapse:collapse;font-size:12px;width:100%}
th{text-align:center;font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:600;padding:6px 4px;border-bottom:1px solid var(--line)}
th.tm{text-align:left;min-width:120px}
td{padding:0;text-align:center;border-bottom:1px solid #F2F4F5}
td.tm{text-align:left;padding:5px 8px 5px 4px;font-weight:600;color:var(--ink);white-space:nowrap}
td.avg{font-weight:700;padding-left:8px}
.cell{display:block;padding:5px 2px;border-radius:3px;font-variant-numeric:tabular-nums}
.list{width:100%;font-size:13px}
.list td{text-align:left;padding:8px 10px;border-bottom:1px solid #F2F4F5}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:700}
.pill.bad{background:#FBE9EC;color:var(--bad)} .pill.warn{background:#FDF3E4;color:var(--warn)}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:12px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-2px}
.priv{font-size:11px;color:var(--warn);border:1px dashed var(--warn);border-radius:6px;padding:8px 11px;margin-bottom:14px;background:#FDF9F3}
</style></head><body><div class="wrap">
<div class="eyebrow">Fairfield Dynasty</div>
<h1>Lineup Efficiency Tracker</h1>
<div class="sub" id="sub"></div>
<div class="cards" id="cards"></div>
<div class="tabs" id="tabs"></div>
<div class="panel">
  <h2>Week by week</h2>
  <div class="note">Each cell is that team's lineup efficiency for the week. Shaded by severity.</div>
  <div id="grid"></div>
  <div class="legend">
    <span><i style="background:#FBE9EC"></i>Below 50% — violation</span>
    <span><i style="background:#FDF3E4"></i>50–60% — review only</span>
    <span><i style="background:#EFF5F1"></i>85%+ — strong</span>
  </div>
</div>
<div class="panel">
  <h2>Violations — below 50%</h2>
  <div class="note">The ratified threshold under Section 6 of the constitution.</div>
  <table class="list" id="viol"></table>
</div>
<div class="panel">
  <div class="priv">Commissioner view only — the 50–60% band is not a league rule and carries no penalty. Use it to decide where to look, not what to enforce.</div>
  <h2>Review tier — 50% to 60%</h2>
  <table class="list" id="rev"></table>
</div>
<div class="panel">
  <h2>Season averages</h2>
  <div class="note">Mean of each team's weekly figures.</div>
  <div id="savg"></div>
</div>
</div>
<script>
const D = __PAYLOAD__;
const fmt = v => v.toFixed(1);
function shade(v){
  if(v < D.VIOLATION) return 'background:#FBE9EC;color:#C8102E;font-weight:700';
  if(v < D.REVIEW)    return 'background:#FDF3E4;color:#9A6512;font-weight:600';
  if(v >= 85)         return 'background:#EFF5F1;color:#2F7D4F';
  return '';
}
document.getElementById('sub').textContent =
  `${D.recs.length} team-weeks · ${D.seasons.length} seasons · generated ${D.generated}`;

const nV = D.violations.length, nR = D.review.length, per = (nV/D.seasons.length).toFixed(1);
document.getElementById('cards').innerHTML = `
 <div class="card"><div class="k">Team-weeks</div><div class="v">${D.recs.length}</div></div>
 <div class="card bad"><div class="k">Violations &lt;50%</div><div class="v">${nV}</div></div>
 <div class="card"><div class="k">Per season</div><div class="v">${per}</div></div>
 <div class="card warn"><div class="k">Review 50–60%</div><div class="v">${nR}</div></div>`;

let cur = D.seasons[0];
const tabs = document.getElementById('tabs');
tabs.innerHTML = D.seasons.map(s=>`<div class="tab${s===cur?' on':''}" data-s="${s}">${s}</div>`).join('');
tabs.onclick = e => { if(!e.target.dataset.s) return; cur = e.target.dataset.s;
  [...tabs.children].forEach(c=>c.classList.toggle('on', c.dataset.s===cur)); draw(); };

function draw(){
  const idx = {};
  D.recs.filter(r=>r.season===cur).forEach(r=>{ idx[r.team+'|'+r.week]=r.eff; });
  let h = '<table><thead><tr><th class="tm">Team</th>'
        + D.weeks.map(w=>`<th>${w}</th>`).join('') + '<th>Avg</th></tr></thead><tbody>';
  const avg = D.seasonAvg[cur] || {};
  D.teams.slice().sort((a,b)=>(avg[a]??0)-(avg[b]??0)).forEach(t=>{
    h += `<tr><td class="tm">${t}</td>`;
    D.weeks.forEach(w=>{
      const v = idx[t+'|'+w];
      h += v===undefined ? '<td><span class="cell" style="color:#C9CFD2">–</span></td>'
                         : `<td><span class="cell" style="${shade(v)}">${fmt(v)}</span></td>`;
    });
    const a = avg[t];
    h += `<td class="avg" style="${a!==undefined&&a<70?'color:#C8102E':''}">${a===undefined?'–':fmt(a)}</td></tr>`;
  });
  document.getElementById('grid').innerHTML = h + '</tbody></table>';
}

function list(el, arr, cls){
  document.getElementById(el).innerHTML = arr.length===0
   ? '<tr><td style="color:#767E82">None.</td></tr>'
   : arr.map(r=>`<tr><td><span class="pill ${cls}">${fmt(r.eff)}%</span></td>
      <td><strong>${r.team}</strong></td><td>${r.season} · Week ${r.week}</td>
      <td style="color:#767E82">${r.actual.toFixed(1)} of ${r.optimal.toFixed(1)} pts</td></tr>`).join('');
}
list('viol', D.violations, 'bad');
list('rev',  D.review,  'warn');

let sh = '<table><thead><tr><th class="tm">Team</th>'
       + D.seasons.map(s=>`<th>${s}</th>`).join('') + '</tr></thead><tbody>';
D.teams.forEach(t=>{
  sh += `<tr><td class="tm">${t}</td>` + D.seasons.map(s=>{
    const a = (D.seasonAvg[s]||{})[t];
    return `<td><span class="cell" style="${a!==undefined&&a<70?'background:#FBE9EC;color:#C8102E;font-weight:700':''}">${a===undefined?'–':fmt(a)}</span></td>`;
  }).join('') + '</tr>';
});
document.getElementById('savg').innerHTML = sh + '</tbody></table>';
draw();
</script></body></html>
"""


if __name__ == "__main__":
    main()