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
body{background:var(--bg);color:var(--body);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;padding:24px 18px 70px;-webkit-font-smoothing:antialiased}
.wrap{max-width:900px;margin:0 auto}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--crimson);font-weight:700;margin-bottom:6px}
h1{font-size:25px;color:var(--ink);letter-spacing:-.02em;margin-bottom:4px}
.sub{font-size:12.5px;color:var(--muted);margin-bottom:18px}

/* Mode toggle: This Week vs Season Summary -- the two things checked on
   different cadences shouldn't share one long scroll. */
.modes{display:flex;gap:8px;margin-bottom:18px}
.mode{flex:1;text-align:center;padding:11px;border:1px solid var(--line);background:var(--panel);
  border-radius:9px;font-size:14px;font-weight:600;cursor:pointer;color:var(--body)}
.mode.on{background:var(--ink);color:#fff;border-color:var(--ink)}

.view{display:none} .view.on{display:block}

.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:16px}
h2{font-size:15px;color:var(--ink);margin-bottom:3px}
.note{font-size:12px;color:var(--muted);margin-bottom:12px}

/* --- This Week view --- */
.weeknav{display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap}
.weeknav select{font-size:14px;padding:7px 10px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--ink)}
.navbtn{width:34px;height:34px;border:1px solid var(--line);background:var(--panel);border-radius:7px;
  cursor:pointer;font-size:16px;color:var(--body);line-height:1}
.navbtn:disabled{opacity:.35;cursor:default}
.weektitle{font-size:16px;font-weight:700;color:var(--ink);margin-left:auto}
.latest{font-size:10px;background:#EFF5F1;color:var(--ok);padding:2px 8px;border-radius:20px;font-weight:700;margin-left:6px;vertical-align:2px}

table{border-collapse:collapse;font-size:13px;width:100%}
th{text-align:left;font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);font-weight:600;padding:7px 8px;border-bottom:1px solid var(--line)}
th.num{text-align:right}
td{padding:9px 8px;border-bottom:1px solid #F2F4F5}
td.rank{color:var(--muted);width:20px}
td.tm{font-weight:600;color:var(--ink)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
tr.bad td{background:#FBE9EC} tr.warn td{background:#FDF9F0}
.pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700}
.pill.bad{background:#F6C7CE;color:#8E0D22} .pill.warn{background:#F5E1C0;color:#8A5A0E}

.weeksum{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap}
.wcard{flex:1;min-width:110px;background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:11px 13px}
.wcard .k{font-size:9.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}
.wcard .v{font-size:20px;font-weight:700;color:var(--ink)}
.wcard.bad .v{color:var(--bad)} .wcard.warn .v{color:var(--warn)}

/* --- Season Summary view --- */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 15px}
.card .k{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.card .v{font-size:23px;font-weight:700;color:var(--ink);line-height:1}
.card.bad .v{color:var(--bad)} .card.warn .v{color:var(--warn)}
th.tm{text-align:left} td.avgc{text-align:center;padding:0}
.cell{display:block;padding:5px 2px;border-radius:3px;font-variant-numeric:tabular-nums;text-align:center}
.list td{padding:8px 10px}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--muted);margin-top:10px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:5px;vertical-align:-2px}
.ver{font-size:10px;letter-spacing:.08em;background:#141414;color:#fff;padding:3px 9px;border-radius:20px;vertical-align:5px;font-weight:700}
.jsfail{background:#FBE9EC;border:1px solid #C8102E;color:#8E0D22;padding:12px 14px;border-radius:8px;font-size:13px;margin-bottom:16px;font-family:monospace;white-space:pre-wrap}
.priv{font-size:11px;color:var(--warn);border:1px dashed var(--warn);border-radius:6px;padding:8px 11px;margin-bottom:14px;background:#FDF9F3}
</style></head><body><div class="wrap">

<div class="eyebrow">Fairfield Dynasty · Commissioner Only</div>
<h1>Lineup Efficiency Tracker <span class="ver">BUILD v2 · TWO-VIEW</span></h1>
<div class="sub" id="sub"></div>
<noscript><div class="jsfail">JavaScript is disabled — this page cannot render without it.</div></noscript>
<div class="jsfail" id="jsfail" style="display:none"></div>

<div class="modes">
  <div class="mode on" data-m="week">This Week</div>
  <div class="mode" data-m="season">Season Summary</div>
</div>

<!-- ============ THIS WEEK ============ -->
<div class="view on" id="view-week">
  <div class="weeknav">
    <button class="navbtn" id="prevBtn">&larr;</button>
    <select id="seasonSel"></select>
    <select id="weekSel"></select>
    <button class="navbtn" id="nextBtn">&rarr;</button>
    <div class="weektitle" id="weekTitle"></div>
  </div>

  <div class="weeksum" id="weeksum"></div>

  <div class="panel">
    <div id="weektable"></div>
  </div>
</div>

<!-- ============ SEASON SUMMARY ============ -->
<div class="view" id="view-season">
  <div class="cards" id="cards"></div>

  <div class="panel">
    <h2>Season averages</h2>
    <div class="note">Mean of each team's weekly figures. Below 70% is marked — see Section 6 of the constitution for the season-level standard.</div>
    <div id="savg"></div>
  </div>

  <div class="panel">
    <h2>Violations — below 50%, all-time</h2>
    <div class="note">The ratified weekly threshold under Section 6.2.</div>
    <table class="list" id="viol"></table>
  </div>

  <div class="panel">
    <div class="priv">Commissioner view only — the 50–60% band is not a league rule and carries no penalty. Use it to decide where to look, not what to enforce.</div>
    <h2>Review tier — 50% to 60%, all-time</h2>
    <table class="list" id="rev"></table>
  </div>
</div>

</div>
<script>
const D = __PAYLOAD__;
const fmt = v => v.toFixed(1);
function boot(){

document.getElementById('sub').textContent =
  `${D.recs.length} team-weeks · ${D.seasons.length} seasons · generated ${D.generated}`;

// ---------------- Mode toggle ----------------
document.querySelectorAll('.mode').forEach(m => m.onclick = () => {
  document.querySelectorAll('.mode').forEach(x => x.classList.toggle('on', x === m));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('on'));
  document.getElementById('view-' + m.dataset.m).classList.add('on');
});

// ---------------- This Week ----------------
// Build a flat, chronologically sorted list of every (season, week) that
// actually has data, so prev/next and the dropdowns always land on a real
// week instead of a blank one.
const points = [];
D.seasons.slice().sort().forEach(s => {
  D.weeks.forEach(w => {
    if (D.recs.some(r => r.season === s && r.week === w)) points.push({season: s, week: w});
  });
});
let ptIdx = points.length - 1;   // default: latest real week

const seasonSel = document.getElementById('seasonSel');
const weekSel = document.getElementById('weekSel');
seasonSel.innerHTML = D.seasons.slice().sort().reverse().map(s => `<option value="${s}">${s}</option>`).join('');

function weeksForSeason(s){ return [...new Set(points.filter(p => p.season === s).map(p => p.week))]; }

function syncSelectors(){
  const cur = points[ptIdx];
  seasonSel.value = cur.season;
  weekSel.innerHTML = weeksForSeason(cur.season).map(w => `<option value="${w}">Week ${w}</option>`).join('');
  weekSel.value = cur.week;
}

function drawWeek(){
  const cur = points[ptIdx];
  const isLatest = ptIdx === points.length - 1;
  document.getElementById('weekTitle').innerHTML =
    `${cur.season} · Week ${cur.week}` + (isLatest ? '<span class="latest">LATEST</span>' : '');
  document.getElementById('prevBtn').disabled = ptIdx === 0;
  document.getElementById('nextBtn').disabled = ptIdx === points.length - 1;

  const rows = D.recs.filter(r => r.season === cur.season && r.week === cur.week)
                      .slice().sort((a,b) => a.eff - b.eff);

  const nBad = rows.filter(r => r.eff < D.VIOLATION).length;
  const nWarn = rows.filter(r => r.eff >= D.VIOLATION && r.eff < D.REVIEW).length;
  document.getElementById('weeksum').innerHTML = `
    <div class="wcard"><div class="k">Teams reported</div><div class="v">${rows.length}</div></div>
    <div class="wcard bad"><div class="k">Violations</div><div class="v">${nBad}</div></div>
    <div class="wcard warn"><div class="k">Review tier</div><div class="v">${nWarn}</div></div>`;

  let h = '<table><thead><tr><th></th><th>Team</th><th class="num">Actual</th><th class="num">Optimal</th><th class="num">Efficiency</th></tr></thead><tbody>';
  rows.forEach((r,i) => {
    const cls = r.eff < D.VIOLATION ? 'bad' : (r.eff < D.REVIEW ? 'warn' : '');
    const pill = r.eff < D.VIOLATION ? '<span class="pill bad">VIOLATION</span>'
               : r.eff < D.REVIEW ? '<span class="pill warn">REVIEW</span>' : '';
    h += `<tr class="${cls}"><td class="rank">${i+1}</td><td class="tm">${r.team} ${pill}</td>
          <td class="num">${fmt(r.actual)}</td><td class="num">${fmt(r.optimal)}</td>
          <td class="num" style="font-weight:700">${fmt(r.eff)}%</td></tr>`;
  });
  document.getElementById('weektable').innerHTML = rows.length ? h + '</tbody></table>' : '<div class="note">No data for this week.</div>';

  syncSelectors();
}

document.getElementById('prevBtn').onclick = () => { if (ptIdx > 0) { ptIdx--; drawWeek(); } };
document.getElementById('nextBtn').onclick = () => { if (ptIdx < points.length-1) { ptIdx++; drawWeek(); } };
seasonSel.onchange = () => {
  const wks = weeksForSeason(seasonSel.value);
  const target = {season: seasonSel.value, week: wks[wks.length-1]};
  ptIdx = points.findIndex(p => p.season === target.season && p.week === target.week);
  drawWeek();
};
weekSel.onchange = () => {
  ptIdx = points.findIndex(p => p.season === seasonSel.value && p.week === Number(weekSel.value));
  drawWeek();
};
drawWeek();

// ---------------- Season Summary ----------------
function shade(v){
  if(v < D.VIOLATION) return 'background:#FBE9EC;color:#C8102E;font-weight:700';
  if(v < D.REVIEW)    return 'background:#FDF3E4;color:#9A6512;font-weight:600';
  if(v >= 85)         return 'background:#EFF5F1;color:#2F7D4F';
  return '';
}
const nV = D.violations.length, nR = D.review.length, per = (nV/D.seasons.length).toFixed(1);
document.getElementById('cards').innerHTML = `
 <div class="card"><div class="k">Team-weeks</div><div class="v">${D.recs.length}</div></div>
 <div class="card bad"><div class="k">Violations &lt;50%</div><div class="v">${nV}</div></div>
 <div class="card"><div class="k">Per season</div><div class="v">${per}</div></div>
 <div class="card warn"><div class="k">Review 50–60%</div><div class="v">${nR}</div></div>`;

let sh = '<table><thead><tr><th class="tm">Team</th>'
       + D.seasons.slice().sort().reverse().map(s=>`<th>${s}</th>`).join('') + '</tr></thead><tbody>';
D.teams.forEach(t=>{
  sh += `<tr><td class="tm">${t}</td>` + D.seasons.slice().sort().reverse().map(s=>{
    const a = (D.seasonAvg[s]||{})[t];
    return `<td class="avgc"><span class="cell" style="${a!==undefined&&a<70?'background:#FBE9EC;color:#C8102E;font-weight:700':''}">${a===undefined?'–':fmt(a)}</span></td>`;
  }).join('') + '</tr>';
});
document.getElementById('savg').innerHTML = sh + '</tbody></table>';

function list(el, arr, cls){
  document.getElementById(el).innerHTML = arr.length===0
   ? '<tr><td style="color:#767E82">None.</td></tr>'
   : arr.map(r=>`<tr><td><span class="pill ${cls}">${fmt(r.eff)}%</span></td>
      <td><strong>${r.team}</strong></td><td>${r.season} · Week ${r.week}</td>
      <td style="color:#767E82">${r.actual.toFixed(1)} of ${r.optimal.toFixed(1)} pts</td></tr>`).join('');
}
list('viol', D.violations, 'bad');
list('rev',  D.review,  'warn');
}
try { boot(); } catch (e) {
  var box = document.getElementById('jsfail');
  box.style.display = 'block';
  box.textContent = 'Dashboard failed to render:\n' + (e && e.stack ? e.stack : e);
}
</script></body></html>
"""


if __name__ == "__main__":
    main()
