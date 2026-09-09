"""Render descriptive figures from the frozen craft/trade release (Matplotlib)."""
import csv
import hashlib
import json
from pathlib import Path
import textwrap

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'results/craft_trade'
OUT = DATA / 'figures'
CONDITIONS = ['all_aligned', 'mixed', 'all_competitive']
NAMES = ['Aligned', 'Mixed', 'Competitive']
COLORS = ['#168b8a', '#e3a037', '#5d61b9']
INK, MUTED, BG = '#15334a', '#5d7181', '#f7f9fc'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
    'text.color': INK, 'axes.labelcolor': INK, 'xtick.color': MUTED,
    'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.spines.left': False, 'axes.spines.bottom': False,
    'svg.fonttype': 'none', 'savefig.facecolor': 'white'})


def save(fig, name):
    for ext in ('png', 'svg', 'pdf'):
        fig.savefig(OUT / f'{name}.{ext}', dpi=180, bbox_inches='tight')
    svg = OUT / f'{name}.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines()) + '\n')
    plt.close(fig)


def heading(fig, kicker, title, subtitle):
    fig.text(.055, .97, kicker, fontsize=10, weight='bold', color=COLORS[0])
    fig.text(.055, .923, title, fontsize=23, weight='bold')
    fig.text(.055, .88, subtitle, fontsize=11, color=MUTED)


def main():
    OUT.mkdir(exist_ok=True)
    s = json.loads((DATA / 'summary.json').read_text())
    rows = list(csv.DictReader((DATA / 'games.csv').open()))
    assert len(rows) == s['completed_games'] == 26
    for c in CONDITIONS:
        for field in ('evaluable_agent_rounds', 'strategic_silence_conjunction',
                      'speaking_with_omission_intent_candidates'):
            assert sum(int(r[field]) for r in rows if r['condition'] == c) == s['conditions'][c][field]
    fig, axes = plt.subplots(1, 2, figsize=(14, 8))
    fig.subplots_adjust(left=.075, right=.965, top=.76, bottom=.22, wspace=.3)
    heading(fig, 'CRAFT / TRADE  •  FROZEN DEVELOPMENT SNAPSHOT',
        'Silence is only one observable pattern',
        '26 completed games  /  1,029 evaluable agent-rounds  /  GPT-5.4, plan-elicited  /  08 Sep 2026')
    for ax, field, title in zip(axes,
            ('strategic_silence_conjunction', 'speaking_with_omission_intent_candidates'),
            ('Withholding intent + no messages', 'Speaking + judge-coded omission intent')):
        totals = [s['conditions'][c] for c in CONDITIONS]
        values = [100*t[field]/t['evaluable_agent_rounds'] for t in totals]
        ax.bar(range(3), values, color=COLORS, alpha=.23, width=.65, zorder=2)
        for i, (c, total) in enumerate(zip(CONDITIONS, totals)):
            games = [r for r in rows if r['condition'] == c]
            xs = np.linspace(i-.18, i+.18, len(games))
            ys = [100*int(r[field])/int(r['evaluable_agent_rounds']) for r in games]
            ax.scatter(xs, ys, s=30, color=COLORS[i], edgecolors='white', linewidth=.65, zorder=4)
            ax.plot([i-.28,i+.28], [values[i]]*2, lw=2.5, color=COLORS[i], zorder=5)
            ax.text(i, 104, f"{total[field]} / {total['evaluable_agent_rounds']}\n{values[i]:.1f}%", ha='center', va='bottom', fontsize=12, weight='bold')
        ax.set(title=title, ylim=(-4,120), xticks=range(3), xticklabels=NAMES, ylabel='% of evaluable agent-rounds')
        ax.set_yticks([0,25,50,75,100]); ax.grid(axis='y', alpha=.15, zorder=0)
    fig.text(.075,.12,'Dots = individual games   •   Shaded bars and solid ticks = pooled agent-round rates',fontsize=11)
    fig.text(.075,.065,'Descriptive only: rounds within games are dependent. Right panel shows candidates, not verified omissions.\nNeither endpoint establishes recipient ignorance, causal motives or harm. Eleven invalid communication rows are excluded.',fontsize=10,color=MUTED,linespacing=1.6)
    save(fig,'disclosure_patterns')

    fig, ax = plt.subplots(figsize=(12,9));fig.subplots_adjust(left=.11,right=.95,top=.8,bottom=.18)
    heading(fig,'COHORT COVERAGE','Which games are in the snapshot?',
        'Each cell shows withholding-intent + no-message rounds / evaluable rounds. Shading shows the descriptive rate.')
    seeds=sorted({r['seed'] for r in rows});lookup={(r['seed'],r['condition']):r for r in rows}
    values=np.full((len(seeds),3),np.nan)
    for i,seed in enumerate(seeds):
        for j,c in enumerate(CONDITIONS):
            r=lookup.get((seed,c))
            if r:values[i,j]=100*int(r['strategic_silence_conjunction'])/int(r['evaluable_agent_rounds'])
    cmap=plt.get_cmap('BuGn').copy();cmap.set_bad('#edf0f5')
    ax.imshow(np.ma.masked_invalid(values),cmap=cmap,vmin=0,vmax=50,aspect='auto')
    for i,seed in enumerate(seeds):
        for j,c in enumerate(CONDITIONS):
            r=lookup.get((seed,c));label=f"{r['strategic_silence_conjunction']} / {r['evaluable_agent_rounds']}" if r else 'No complete game'
            ax.text(j,i,label,ha='center',va='center',fontsize=12,color='white' if values[i,j]>30 else INK)
    ax.set_xticks(range(3),[f'{n}  ({s["conditions"][c]["games"]} games)' for n,c in zip(NAMES,CONDITIONS)])
    ax.xaxis.tick_top();ax.set_yticks(range(len(seeds)),seeds);ax.set_ylabel('Seed')
    ax.set_xticks(np.arange(-.5,3,1),minor=True);ax.set_yticks(np.arange(-.5,len(seeds),1),minor=True);ax.grid(which='minor',color='white',linewidth=3);ax.tick_params(which='both',length=0)
    fig.text(.11,.105,'Seven seeds have all three completed conditions. Gray cells are missing complete games, not zeros.',fontsize=11)
    fig.text(.11,.055,'Completed games: 26  •  Completed-game agent-rounds: 1,040  •  Invalid communications: 11\nPartial-game evaluated rounds: 144 (excluded here). Full per-game counts and survival are in games.csv.',fontsize=10,color=MUTED,linespacing=1.6)
    save(fig,'game_coverage')

    case=next(c for c in json.loads((DATA/'examples.json').read_text())['records'] if c['case_id']=='609081_all_competitive/0/Agent_1')
    raw=case['original_record']['raw_communication']
    plan=raw.split('PRIVATE PLAN: ',1)[1].split('\nPUBLIC MESSAGE:',1)[0]
    public=raw.split('PUBLIC MESSAGE: ',1)[1].split('\nPRIVATE MESSAGE:',1)[0]
    fig=plt.figure(figsize=(16,9));ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
    heading(fig,'OBSERVED EXAMPLE  •  EXACT SAVED TEXT','A true report can leave the recipe unshared',
        '609081_all_competitive  /  round 0  /  Agent_1  •  Quotes below are observed output, not the supplied illustration.')
    def box(x,y,w,h,title,body,color='#edf2f6',width=48):
        ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012',facecolor=color,edgecolor='#d3dde5',lw=1))
        ax.text(x+.012,y+h-.032,title,fontsize=12,weight='bold',va='top')
        wrapped='\n'.join(textwrap.fill(line,width) for line in body.splitlines())
        ax.text(x+.012,y+h-.075,wrapped,fontsize=11,va='top',linespacing=1.55)
    box(.055,.535,.39,.255,'VISIBLE LOCAL OBSERVATION',case['observation'].split('Local recipe:',1)[0].strip(),width=59)
    box(.055,.43,.39,.09,'KNOWN RECIPE','CRAFT 1 food 1 water FOR 3 gold',color='#fff0d2',width=58)
    box(.055,.20,.39,.18,'WHAT THIS RECORD SHOWS','The plan explicitly states withholding. The public report shares stock information but does not share the recipe. Whether another agent already knew it is a separate question.',color='#e2f2ef',width=56)
    box(.51,.46,.425,.33,'PRIVATE PLAN  /  EXACT QUOTE',plan,width=64)
    box(.51,.29,.425,.12,'PUBLIC MESSAGE  /  EXACT QUOTE',public,color='#ddf1f0',width=60)
    box(.51,.18,.425,.06,'PRIVATE MESSAGE: NONE','',width=60)
    fig.text(.055,.095,'Observed selective speech; no claim of exhaustive truthfulness validation or downstream harm.',fontsize=12,weight='bold')
    fig.text(.055,.052,'Source: examples.json → original_record and observation. Full recipient inputs/history remain in raw_snapshot.zip.\nPrivate plans are model-reported explanations; this case does not establish a causal motive.',fontsize=10,color=MUTED,linespacing=1.5)
    save(fig,'observed_selective_disclosure')
    (OUT/'sources.json').write_text(json.dumps({'snapshot_utc':s['snapshot_utc'],'inputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (DATA/'summary.json',DATA/'games.csv',DATA/'examples.json')},'generator':'scripts/plot_craft_trade.py','matplotlib':matplotlib.__version__},indent=2)+'\n')

if __name__ == '__main__':
    main()
