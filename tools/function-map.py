#!/usr/bin/env python3
"""Classifies every top-level node of index.html's main script (exact boundaries via tools/ast-map.js)
by owner — a chamber, core, or a component — and regenerates ARCHITECTURE.md.
    NODE_PATH=<dir containing node_modules/acorn> python3 tools/function-map.py
Ownership is a HEURISTIC (names, then the DOM ids a function touches). Verify when moving code."""
import re, os, json, subprocess, collections, sys
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
htmlp = os.path.join(root, 'index.html')
src = open(htmlp, encoding='utf-8').read(); L = src.split('\n')
amap = json.loads(subprocess.run(['node', os.path.join(root, 'tools', 'ast-map.js'), htmlp], capture_output=True, text=True, check=True).stdout)
nodes = amap['nodes']
CH = ['load','map','aim','fire','reload','train','sim','formulas','wiring','projects','forge','lens']

# ── regions already carved out ───────────────────────────────────────────────
regions = []
for i, l in enumerate(L):
    m = re.match(r'^// #region (CORE|COMPONENT: (\w+)|CHAMBER: (\w+))', l)
    if m:
        name = 'core' if m.group(1) == 'CORE' else ('component:' + m.group(2) if m.group(2) else m.group(3))
        end = next((j for j in range(i + 1, len(L)) if L[j].startswith('// #endregion')), len(L) - 1)
        regions.append((i + 1, end + 1, name))
def region_of(line):
    for a, b, n in regions:
        if a <= line <= b: return n

# ── DOM id → chamber (from the chamber panels in the HTML) ───────────────────
panels = [(i, re.search(r'id="ch-(\w+)"', l).group(1)) for i, l in enumerate(L[:amap['scriptStart']]) if re.search(r'id="ch-(\w+)"', l)]
idmap = {}; seen = collections.defaultdict(set)
for k, (i, ch) in enumerate(panels):
    j = panels[k + 1][0] if k + 1 < len(panels) else amap['scriptStart']
    for m in re.finditer(r'\bid=["\']([\w-]+)["\']', '\n'.join(L[i:j])):
        if not m.group(1).startswith('ai-'): seen[m.group(1)].add(ch)
idmap = {i: next(iter(c)) for i, c in seen.items() if len(c) == 1}
def id_vote(text):
    votes = collections.Counter()
    for t in re.findall(r"['\"`#]([A-Za-z0-9_-]{2,})", text):
        if t in idmap: votes[idmap[t]] += 2
        elif t[-1] in '-_':
            cs = {c for i, c in idmap.items() if i.startswith(t)}
            if len(cs) == 1: votes[next(iter(cs))] += 1
    return votes.most_common(1)[0][0] if votes else None

# ── name rules (first match wins) ────────────────────────────────────────────
WRAP = {'_goLens':'lens','_goWiring':'wiring','_goForge':'forge','_go4':'formulas','_go3':'sim','_go5':'wiring','_goQuote':'core:shell',
        '_enter5':'wiring','_enter4':'formulas','_enter3':'sim','_enterWiring':'wiring','_endSim2':'sim','_runWeekly2':'sim','_rwOrig':'wiring','_rmOrig':'map','_initFormOrig':'formulas'}
RULES = [
 (r'^(callAI|sendAIChat|clearAIChat|appendAIMsg|toggleAI|getWorker|saveWorker|syncAllUrls|getAIModel|saveAIModel|getAIStates|saveAIStates|getChamberScope|setChamberScope|scan|restoreScanned|classifyModel|fmtLocal|wrapResp|localThink|rebuildAllModelSelects|renderIncompatibleList|updateChamberStatus|ensureWorkerConfig|updateAllStatuses|aiKeyDown|AI_|aiHistory|aiStates|WHO$|rigChat)', 'core:ai'),
 (r'^(kv|KV_|_kv|buildStateSnapshot|DR_KEYS|getKVWorkerUrl|sw[A-Z]|exportAll|importAll|exportData|importData|toggleChamberScope)', 'core:sync'),
 (r'^(chaos|pressure|resolve|CV$|cx$|CW$|mouse$|mTarget|vp$|vpTarget|VP_CHAMBER|SPHERE|CHAMBER_MODE|NIF|vc$|resizeCV|lp$|rotPoint|drawFrame|tkn$|initSphere|window\.onerror)', 'core:visual'),
 (r'^(go$|enter$|goHome|setVP|tick$|tog$|tags$|ls$|now$|closeChamberMenu|toggleChamberMenu|drawerGo|updateNavCurrent|initQuoteObserver|CHAMBER_NAMES|D$|setSt|setFm)', 'core:shell'),
 (r'^(local)?Load\b|^(local)?load[A-Z]|^toArsenal|^renderArsenal|^generateAnchor|^saveAnchor|^displayAnchor|^getAnchorWords|_currentAnchorWord', 'load'),
 (r'^(local)?Map\b|^addVar|^map[A-Z]|^mSnapshot|^mPushUndo|^saveMapGraph|^initMapGraph|^resizeMapCanvas|^mNodeScreen|^mHitNode|^drawMap|^renderMapNodal|^syncVars|^addDep|^updateDepSel|^updateGhosts|^saveSitMaps|^sitMap|^renderSitMaps|^sm[A-Z]|^syncWiringNodesToMap|^MAP_PHRASES|^(MG|MC)$|^(mZoom|mPan|mSelected|mDragging|mTouch|mPinch|M_UNDO)|^(m|map)Undo|^(m|map)Redo', 'map'),
 (r'^(local)?Aim\b|^aim[A-Z]|^AIM_PHRASES', 'aim'),
 (r'^(local)?Fire\b|^fire[A-Z]', 'fire'),
 (r'^(local)?Reload|^renderReloads|^reload[A-Z]', 'reload'),
 (r'[Ss]im[A-Z_]|^sim|^startSim|^initSim|^endSim|^runWeekly|^getPatternEntries|^getCritTarget|^runSolve|^runRead|^SIM_|^MENTAL_MODELS|^currentMode$', 'sim'),
 (r'[Ff]ormula|^setFormCat|^initSymbol|^insertSymbol|^FORMULAS|^MATH_SYMBOLS|^currentFormCat', 'formulas'),
 (r'[Ff]orge|^fg[A-Z]|^FORGE', 'forge'),
 (r'[Ll]ens|^LENS|Rig[A-Z]|^rig|^RIG_|^CAM_NODES|^currentCamCat|CamNode|Recalibrate|Mirror', 'lens'),
 (r'[Tt]rain|Drill|^setEx|^nextEx|^setConf|^updateStreak|^incUse|^logSelfCheck|^showGraduation|^renderGraduationGrid|^initIndependence|^TRAIN|^MEM_QS|^GRAD_SKILLS', 'train'),
 (r'[Pp]roj|^PROJ', 'projects'),
 (r'^(nodal|nSnapshot|nPushUndo|setNMode|startConnectMode|startAddNode|cancelAddNode|confirmAddNode|deselectNode|updateNHint|initNodal|resizeNodalCanvas|nodeScreen|screenToWorld|hitNode|hitEdgeTest|handleNodalTap|showNodeDetail|hideNodeDetail|startConnectFromDetail|deleteSelectedNode|drawNodal|renderWiring|saveNodalGraph|saveBrainMap|updateUndoButtons|pickObsLayer|pickAddNodeLayer|addObs|eNode|ew[A-Z]|editModal|editTab|orb|Orb|ORB|ned|Ned|NED|ws|WS$|pfe|PFE|flow|Flow|ef[A-Z]|if[A-Z]|initFlow|drawFlow|runForceLayout|canvasPos|showTooltip|NODE_COLORS|toggleLayer|obsLayer|brainMap|BRAIN_MAP|LAYER_|NG$|NC$|nPan|nZoom|nConn|nSelected|nDrag|nUndo|nRedo|nTouch|nPinch|N_UNDO)', 'wiring'),
]
def owner_of(n, prev):
    nm = (n['name'] or '')
    first = nm.split(',')[0].strip()
    r = region_of(n['start'])
    if r: return r
    if n['type'] == 'ExpressionStatement':
        if re.match(r'(go|enter|endSim|runWeekly|renderWiring|renderMapNodal|initFormulas)\s*=\s*(async\s+)?function', nm):
            if prev and prev['type'] == 'VariableDeclaration' and (prev['name'] or '').startswith('_'):
                return WRAP.get(prev['name'].split(',')[0], prev.get('owner', 'unassigned'))
            return 'unassigned'
        return 'core:startup'      # init calls, listeners, IIFEs — order-dependent, keep in place
    if n['type'] == 'IfStatement': return 'core:startup'
    if first in WRAP: return WRAP[first]
    for pat, o in RULES:
        if re.search(pat, first): return o
    if n['type'] == 'FunctionDeclaration':
        v = id_vote('\n'.join(L[n['start'] - 1:n['end']]))
        if v: return v
    return 'unassigned'

prev = None
for n in nodes:
    n['owner'] = owner_of(n, prev); prev = n
# state variables sitting between two nodes of the same chamber belong to it
for i in range(1, len(nodes) - 1):
    n = nodes[i]
    if n['owner'] == 'unassigned' and n['type'] == 'VariableDeclaration':
        a = next((nodes[j]['owner'] for j in range(i - 1, -1, -1) if nodes[j]['owner'] != 'unassigned'), None)
        b = next((nodes[j]['owner'] for j in range(i + 1, len(nodes)) if nodes[j]['owner'] != 'unassigned'), None)
        if a and a == b and a in CH: n['owner'] = a

by = collections.defaultdict(list)
for n in nodes: by[n['owner']].append(n)
fns = collections.Counter(n['name'] for n in nodes if n['type'] == 'FunctionDeclaration')
dups = sorted(k for k, v in fns.items() if v > 1)

def runs_of(o):
    # maximal runs of consecutive top-level nodes owned by `o`
    out, cur = [], []
    for n in nodes:
        if n['owner'] == o: cur.append(n)
        elif cur: out.append(cur); cur = []
    if cur: out.append(cur)
    return out
def stats(o):
    items = by.get(o, [])
    if not items: return None
    lo = min(n['start'] for n in items); hi = max(n['end'] for n in items)
    loc = sum(n['end'] - n['start'] + 1 for n in items)
    runs = runs_of(o)
    best = max(runs, key=lambda r: sum(x['end'] - x['start'] + 1 for x in r)) if runs else []
    bloc = sum(x['end'] - x['start'] + 1 for x in best)
    return dict(n=len(items), loc=loc, lo=lo, hi=hi, items=items, best=best, bloc=bloc, nruns=len(runs))

# raw AI call sites
raw = []
for i, l in enumerate(L):
    if 'fetch(workerUrl' in l:
        fn = next((nd['name'] for nd in nodes if nd['type'] == 'FunctionDeclaration' and nd['start'] <= i + 1 <= nd['end']), '?')
        raw.append((fn, i + 1))

order = ['core', 'core:shell', 'core:ai', 'core:sync', 'core:visual', 'core:startup', 'component:arsenal'] + CH + ['unassigned']
rows = []
for o in order:
    s = stats(o)
    if not s: continue
    carved = any(n == o for _, _, n in regions)
    pct = round(100 * s['bloc'] / max(s['loc'], 1))
    state = ('carved' if carved else ('—' if (o not in CH) else ('**ready**' if s['nruns'] == 1 else ('mostly contiguous' if pct >= 70 else 'scattered'))))
    rows.append(f"| `{o}` | {s['n']} | {s['loc']} | {s['nruns']} | {pct}% | {state} |")

head = open(os.path.join(root, 'tools', 'ARCHITECTURE.head.md'), encoding='utf-8').read().rstrip()
out = [head, '', '## AI call sites still on raw `fetch` (migrate to `AI.ask`)', '']
out += [f'- `{fn}` — line {ln}' for fn, ln in raw] or ['- none']
out += ['', '## Declared more than once (the LAST declaration wins — keep order when moving)', '', ', '.join(f'`{d}`' for d in dups) or 'none', '',
        '## Function map (generated — do not edit)', '',
        f'{len(nodes)} top-level nodes ({fns and sum(fns.values())} functions). `spread` = how many times wider a chamber\'s code is spread through the file than its real size (1× = contiguous). '
        '`runs` = how many separate pieces a chamber\'s code is split into; `largest run` = share of its lines in the biggest piece. '
        '`ready` = one piece (wrap as-is) · `mostly contiguous` = carve the big piece, move the strays · `scattered` = move before carving · `carved` = already inside a `// #region`.', '',
        '| owner | nodes | lines of code | runs | largest run | status |', '|---|---|---|---|---|---|'] + rows + ['']
for o in order:
    s = stats(o)
    if s:
        names = ', '.join(f"`{(n['name'] or n['type']).split(',')[0][:28]}`:{n['start']}" for n in s['items'][:400])
        out += [f"<details><summary><code>{o}</code> — {s['n']} nodes</summary>", '', names, '', '</details>', '']
open(os.path.join(root, 'ARCHITECTURE.md'), 'w', encoding='utf-8').write('\n'.join(out))
if '--carve' in sys.argv:
    want = sys.argv[sys.argv.index('--carve') + 1].split(',')
    edits = []
    for o in want:
        st_ = stats(o)
        if not st_ or any(o == n for _, _, n in regions): continue
        a = st_['best'][0]['start']; b = st_['best'][-1]['end']
        while a - 2 >= 0 and L[a - 2].startswith('//'): a -= 1          # keep the section comment with its code
        edits.append((b, f'// #endregion CHAMBER: {o}')); edits.append((a - 1, f'// #region CHAMBER: {o}  — {st_["bloc"]} lines, {len(st_["best"])} nodes'))
    for pos, text in sorted(edits, key=lambda e: -e[0]): L.insert(pos, text)
    open(htmlp, 'w', encoding='utf-8').write('\n'.join(L)); print('carved:', want)
json.dump({'nodes': nodes}, open('/tmp/owners.json', 'w'))
print(f"nodes {len(nodes)} | unassigned {len(by.get('unassigned', []))} | raw AI sites {len(raw)} | duplicate decls {dups}")
for r in rows: print(r)
if '--unassigned' in sys.argv:
    print('UNASSIGNED:', ', '.join(f"{(n['name'] or n['type'])[:30]}@{n['start']}" for n in by.get('unassigned', [])))
