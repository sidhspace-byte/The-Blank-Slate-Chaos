# THE SYSTEM — architecture & migration guide

Single-file app (`index.html`), hosted on GitHub Pages, offline via `sw.js`. This file is the map for
turning it from one 13k-line global script into **chambers + shared components**, one chamber at a time,
**without a big-bang rewrite** and **without changing any `dr_*` storage key**.

**Rollback:** git tag `pre-components` = the last build before this work (`git checkout pre-components -- index.html`).

## Layout of `index.html`'s main script

```
// #region CORE                       System (bus · registry · router) + AI client
// #region COMPONENT: arsenal         store · flow threads · drawer · activity log · chain · caveman
// #region CHAMBER: <id>              (one per chamber, as each is migrated — see steps below)
legacy code                           everything not yet migrated, untouched
```
Rules for regions: `// #region NAME` … `// #endregion`. A region owns its functions **and** its state.
Chambers talk to each other only through the **bus** or **registry**, never by calling each other's functions.

## Core API (already live)

| | |
|---|---|
| `System.registerChamber({id, input, resp, aiInput, onEnter, persist, handoffs})` | chamber contract; only `id` required. Defaults: `resp = <id>-resp-body`, `aiInput = ai-input-<id>`. |
| `System.chambers[id]` | registry. The node map, drawer and arsenal read from here — no hardcoded id lists. |
| `System.on(event, fn)` / `System.emit(event, data)` | events: `reply {chamber,user,reply,entryId}` · `handoff {from,to,…}` · `arsenal:save` · `chamber:enter {id}` · `home`. A throwing handler never stops the others. |
| `System.router` | every chamber has a link (`#/aim`); back button steps through chambers; deep links open the chamber (via `orbEnter`, so the home canvas is disabled correctly). |
| `AI.ask({chamber, system, user \| messages, maxTokens})` → `{text, error, status, model}` | the **only** way to call a model. Resolves URL + model per chamber, checks HTTP status, normalises `body`/`choices`, raises the token budget for reasoning models, never returns reasoning as the answer. |

## Planned shared components (status)

| component | replaces | status |
|---|---|---|
| AI client | 18 copy-pasted `fetch` blocks | **live** — `callAI` (Load/Map/Aim/Fire/Reload) and `sendAIChat` (12 chat panels) migrated; rest listed below |
| Arsenal controls | per-chamber save/list code | **live** (drawer, `+save`, chain, log) |
| ChamberShell (header, carried-context box, handoff buttons) | 3 carry boxes · 8 `carryTo` buttons | planned |
| AIChatPanel | 12 identical chat panels | planned |
| ResponseBox | 7 response boxes + think indicator | planned |
| HistoryList / InlineEditor | `renderArsenal`, `renderReloads`, formula/forge inline edit | planned |

## Steps to migrate ONE chamber (do them in this order, push after each)

1. Add `// #region CHAMBER: <id>` / `// #endregion` and **move that chamber's functions into it** (use the generated map below).
   Function declarations hoist, so moving them is safe. Top-level `const`/`let`/IIFE statements run in order — move them only if nothing earlier reads them.
2. Move its `go` wrapper into `System.registerChamber({id, onEnter})`; delete the wrapper.
3. Replace any raw `fetch(workerUrl…)` with `AI.ask(...)`.
4. Replace inter-chamber function calls with `System.emit` / registry lookups.
5. List the `dr_*` keys it owns in `persist`; keep key names **unchanged**.
6. Move its HTML panel next to the others and swap hand-copied pieces for shared components as they land.
7. Run the node tests, push, check on the phone, tick it off here.

**Order:** Load → Map → Aim → Fire (they already hand off to each other) → Reload → Sim/Train/Projects → Formulas/Forge/Lens. Wiring + the node map last, if at all (own render loop).

## Migration status

See the generated table at the bottom (`status` column). **Carved** = the chamber's main body already sits inside a
`// #region CHAMBER: <id>`; its stray pieces elsewhere in the file are still to be moved in. **None of the 12 chambers is *migrated* yet**
(migrated = steps 2–6 above done); carving is only step 1.

## Gotchas found while mapping (read before moving code)

- **Monkey-patching is everywhere.** Many functions are wrapped by reassignment: `const _x = fn; fn = function(){ _x(); … }`
  (`go`, `enter`, `endSim`, `runWeekly`, `renderWiring`, `renderMapNodal`, `initFormulas`). Declarations hoist, so *moving a declaration is safe*,
  but the wrapper statements are **order-dependent** — keep each wrapper after the declaration it wraps and in the same relative order as the others.
  The generator pairs each wrapper with its owner. Fold them into `onEnter` when the chamber migrates.
- **`core:startup`** (init calls, listeners, IIFEs, `setInterval`s) runs top-to-bottom at load. Don't reorder it; it's deliberately its own bucket.
- **`setVP` is declared twice** — the *last* declaration wins. Keep their relative order if you move either.
- **Top-level `const`/`let` are not hoisted.** Move state variables only if nothing earlier in the file reads them at load time.
- Ownership in the map is a heuristic. The line ranges and the "nothing else changed" proof are exact (real parser).

## Tools

```bash
npm i acorn                                   # once, anywhere
export NODE_PATH=<dir containing node_modules>
python3 tools/function-map.py                 # regenerate the map + this file
python3 tools/function-map.py --carve sim,lens   # wrap the largest contiguous run of each in a region (comments only)
node tools/ast-map.js index.html              # raw top-level nodes as JSON (exact line ranges)
```
After any carve/move: re-run `ast-map.js` and confirm the node sequence is unchanged (or changed only as intended) and `node --check` passes.
