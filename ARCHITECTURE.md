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

## AI call sites still on raw `fetch` (migrate to `AI.ask`)

- `readForge` — line 4878
- `readProjects` — line 4933
- `applyFormula` — line 5952
- `stressTestFormula` — line 6031
- `generateFormulas` — line 6085
- `startSim` — line 6760
- `sendSimResponse` — line 6813
- `endSim` — line 6886
- `viewThroughLens` — line 8459
- `runLensRead` — line 8539
- `runRecalibrate` — line 8684
- `sendRigChat` — line 8754
- `saveTrain` — line 9002
- `generateTrainSession` — line 9063
- `generateAnchorWord` — line 11035
- `generateFormulaAI` — line 11181

## Declared more than once (the LAST declaration wins — keep order when moving)

`setVP`

## Function map (generated — do not edit)

698 top-level nodes (430 functions). `spread` = how many times wider a chamber's code is spread through the file than its real size (1× = contiguous). `runs` = how many separate pieces a chamber's code is split into; `largest run` = share of its lines in the biggest piece. `ready` = one piece (wrap as-is) · `mostly contiguous` = carve the big piece, move the strays · `scattered` = move before carving · `carved` = already inside a `// #region`.

| owner | nodes | lines of code | runs | largest run | status |
|---|---|---|---|---|---|
| `core` | 8 | 108 | 1 | 100% | carved |
| `core:shell` | 21 | 203 | 11 | 56% | — |
| `core:ai` | 37 | 395 | 4 | 72% | — |
| `core:sync` | 14 | 188 | 3 | 58% | — |
| `core:visual` | 20 | 85 | 10 | 26% | — |
| `core:startup` | 52 | 217 | 21 | 20% | — |
| `component:arsenal` | 96 | 794 | 1 | 100% | carved |
| `load` | 17 | 343 | 8 | 43% | scattered |
| `map` | 66 | 689 | 10 | 51% | scattered |
| `aim` | 5 | 80 | 3 | 55% | scattered |
| `fire` | 2 | 38 | 2 | 50% | scattered |
| `reload` | 7 | 110 | 5 | 35% | scattered |
| `train` | 16 | 263 | 6 | 57% | scattered |
| `sim` | 33 | 656 | 3 | 95% | carved |
| `formulas` | 32 | 801 | 3 | 72% | carved |
| `wiring` | 202 | 2577 | 16 | 30% | scattered |
| `projects` | 21 | 297 | 3 | 80% | carved |
| `forge` | 15 | 159 | 4 | 52% | scattered |
| `lens` | 34 | 618 | 2 | 74% | carved |

<details><summary><code>core</code> — 8 nodes</summary>

`System`:11878, `System.registerChamber = fun`:11894, `[ { id: 'load'`:11901, `System.router = {`:11912, `(function () {`:11931, `window.addEventListener('pop`:11947, `(function () {`:11956, `AI`:11965

</details>

<details><summary><code>core:shell</code> — 21 nodes</summary>

`D`:3534, `setVP`:3592, `setVP`:4112, `enter`:4139, `go`:4147, `tick`:4168, `tog`:4286, `tags`:4287, `setSt`:4288, `setFm`:4289, `now`:4353, `ls`:4373, `goHome`:7979, `initQuoteObserver`:8877, `_goQuote`:8887, `go = function(c) { _goQuote(`:8888, `CHAMBER_NAMES`:10600, `toggleChamberMenu`:10606, `closeChamberMenu`:10622, `drawerGo`:10630, `updateNavCurrent`:10635

</details>

<details><summary><code>core:ai</code> — 37 nodes</summary>

`WHO`:4398, `localThink`:4408, `fmtLocal`:4410, `wrapResp`:4418, `callAI`:4420, `rigChatHistory`:8701, `AI_WORKER_KEY`:11435, `AI_MODEL_KEY`:11436, `AI_DEFAULT_MODEL`:11437, `getChamberScope`:11443, `setChamberScope`:11447, `getWorkerUrlForChamber`:11451, `saveWorkerUrlForChamber`:11458, `getAIModelForChamber`:11470, `saveAIModelForChamber`:11477, `getAIModel`:11485, `saveAIModel`:11489, `scanModels`:11526, `rebuildAllModelSelects`:11610, `renderIncompatibleList`:11623, `restoreScannedModels`:11640, `AI_STATES_KEY`:11657, `aiHistory`:11660, `AI_CHAMBER_CONTEXT`:11663, `getWorkerUrl`:11678, `saveWorkerUrl`:11682, `updateChamberStatus`:11686, `getAIStates`:11694, `saveAIStates`:11698, `toggleAIPanel`:11702, `ensureWorkerConfig`:11719, `syncAllUrls`:11733, `updateAllStatuses`:11743, `aiKeyDown`:11750, `clearAIChat`:11757, `appendAIMsg`:11763, `sendAIChat`:11773

</details>

<details><summary><code>core:sync</code> — 14 nodes</summary>

`DR_KEYS`:10658, `exportAll`:10664, `importAll`:10696, `KV_SYNC_DEBOUNCE_MS`:11266, `_kvSyncTimer`:11267, `_kvSyncing`:11268, `getKVWorkerUrl`:11270, `buildStateSnapshot`:11276, `kvScheduleSync`:11288, `kvPushState`:11295, `kvPullState`:11323, `kvSetSyncStatus`:11350, `kvToggleSyncPanel`:11369, `toggleChamberScope`:11499

</details>

<details><summary><code>core:visual</code> — 20 nodes</summary>

`chaos`:3549, `pressure`:3550, `resolve`:3551, `CV`:3557, `cx`:3558, `CW`:3559, `mouse`:3560, `mTarget`:3561, `vp`:3562, `vpTarget`:3563, `VP_CHAMBER`:3565, `resizeCV`:3574, `lp`:3590, `SPHERE`:3602, `rotPoint`:3659, `CHAMBER_MODE`:3693, `NIF`:3721, `drawFrame`:4118, `vc`:4305, `tkn`:4317

</details>

<details><summary><code>core:startup</code> — 52 nodes</summary>

`window.onerror = function(ms`:3491, `(function(){ const s=localSt`:3530, `(function(){ const s=localSt`:3533, `window.addEventListener('res`:3581, `resizeCV();`:3583, `setTimeout(resizeCV`:3584, `setTimeout(resizeCV`:3585, `document.addEventListener('m`:3587, `document.addEventListener('t`:3588, `(function initSphere() {`:3614, `CV.addEventListener('touchst`:3679, `CV.addEventListener('mousedo`:3685, `CV.addEventListener('click'`:3788, `CV.addEventListener('touchst`:3789, `setVP('entry');`:4133, `drawFrame();`:4134, `const _go5=go; go=function(c`:5525, `const _enter5=enter; enter=f`:5526, `const _enter3=enter; enter=f`:6967, `document.addEventListener('k`:6969, `renderArsenal();`:6976, `renderReloads();`:6977, `renderReloadAnchorCurrent();`:6978, `tick();`:6979, `initIndependence();`:6980, `setInterval(tick`:6983, `setInterval(()=>updateGhosts`:6985, `(function migrateOrbPos() {`:7038, `(function nedRestore(){`:7888, `setTimeout(orbTryInit`:8197, `document.addEventListener('D`:8200, `setTimeout(initQuoteObserver`:8886, `setTimeout(()=>{ updateStrea`:9108, `IfStatement`:9202, `IfStatement`:10502, `DR_KEYS.push('dr_custom_form`:11247, `DR_KEYS.push('dr_rigs');`:11248, `DR_KEYS.push('dr_anchor_word`:11249, `DR_KEYS.push('dr_pfe');`:11250, `DR_KEYS.push('dr_ws');`:11251, `DR_KEYS.push('dr_ned_nodes')`:11252, `DR_KEYS.push('dr_simlog');`:11253, `DR_KEYS.push('dr_carried_len`:11254, `DR_KEYS.push('dr_lens_histor`:11255, `DR_KEYS.push('dr_arsenal_flo`:11256, `DR_KEYS.push('dr_arsenal_arc`:11257, `DR_KEYS.push('dr_ars_log');`:11258, `DR_KEYS.push('dr_ars_chain')`:11259, `(function kvInitPanel() {`:11387, `(function patchLocalStorage(`:11399, `(function kvAutoLoad() {`:11408, `(function restoreAIPanels() `:11833

</details>

<details><summary><code>component:arsenal</code> — 96 nodes</summary>

`ARS_CAP`:12009, `ARS_FLOW_KEY`:12010, `ARS_ARCH_KEY`:12011, `arsFlow`:12012, `_arsAgg`:12013, `_arsSel`:12014, `arsFilter`:12015, `arsEditing`:12016, `arsDelArm`:12017, `arsId`:12019, `arsEsc`:12020, `arsMigrate`:12022, `arsTrim`:12035, `arsenalSave`:12046, `arsenalPull`:12063, `arsAggregate`:12078, `orbThreadPts`:12093, `orbTraceSpline`:12110, `orbSplineAt`:12118, `orbDrawArsenalFlow`:12136, `arsActiveInput`:12173, `arsAIInput`:12185, `arsGrabAI`:12187, `document.addEventListener('s`:12195, `arsInsert`:12200, `arsStatus`:12207, `arsEnsureDrawer`:12214, `arsToggle`:12257, `arsSetOrigin`:12267, `arsRender`:12269, `arsUpdate`:12312, `arsRemove`:12325, `arsUnloadFrom`:12338, `arsUse`:12367, `arsSaveInput`:12378, `arsSaveAI`:12386, `arsEdit`:12394, `arsEditCancel`:12395, `arsEditSave`:12396, `arsDelete`:12403, `arsUnload`:12416, `ARS_CARRY_KEY`:12429, `arsCarry`:12430, `arsCap`:12432, `arsLastReply`:12434, `arsLogFlow`:12442, `arsTakeTo`:12454, `arsCarryBlock`:12483, `(function () {`:12507, `arsCarryPill`:12544, `arsCarryClear`:12561, `(function () { const _g = go`:12562, `ARS_LOG_KEY`:12566, `arsLog`:12567, `arsTab`:12568, `arsTail`:12570, `arsChName`:12571, `arsFmtT`:12572, `arsRecordReply`:12574, `arsSetTab`:12594, `arsLogToggle`:12599, `arsTrailToggle`:12600, `arsTrailHTML`:12602, `arsRenderActivity`:12615, `arsEntryFromLog`:12640, `arsLogSave`:12644, `arsLogTake`:12650, `ARS_RAW_N`:12665, `ARS_GIST_N`:12666, `arsTyped`:12667, `arsLogViewMap`:12668, `arsReplyOf`:12670, `arsDedupe`:12673, `arsCave`:12682, `arsCaveOK`:12718, `arsGist`:12725, `arsCompact`:12735, `arsCleanUser`:12762, `document.addEventListener('i`:12778, `arsEntryText`:12787, `arsLogViewToggle`:12791, `arsStatsHTML`:12792, `ARS_CHAIN_KEY`:12809, `arsChain`:12810, `arsChainAdd`:12812, `arsChainTo`:12821, `arsHistoryFor`:12828, `arsSaveWith`:12845, `arsToast`:12854, `arsSaveHere`:12868, `(function () {`:12881, `IfStatement`:12897, `arsCarryPill();`:12898, `arsCompact();`:12899, `arsMigrate();`:12901, `arsIsLoad`:12904

</details>

<details><summary><code>load</code> — 17 nodes</summary>

`toArsenal`:4355, `loadArsenalItem`:4375, `renderArsenal`:4384, `localLoad`:4474, `runLoad`:4650, `buildFlow`:5036, `setMode`:6140, `revealAILoad`:6163, `loadMemQ`:8931, `loadPatternEntries`:8935, `loadCritSource`:8943, `getAnchorWords`:11008, `saveAnchorWords`:11011, `generateAnchorWord`:11015, `saveAnchorWord`:11050, `_currentAnchorWord`:11058, `displayAnchorWord`:11060

</details>

<details><summary><code>map</code> — 66 nodes</summary>

`mapRatio`:3552, `updateGhosts`:4261, `addVar`:4306, `syncVars`:4323, `addDep`:4330, `updateDepSel`:4337, `getMapData`:4341, `localMap`:4556, `MAP_PHRASES`:4696, `mapT2`:4697, `runMap`:4699, `readMap`:4726, `readWiring`:4752, `toggleSolveDetail`:6296, `renderMapNodal`:9751, `MG`:9762, `MC`:9763, `mZoom`:9764, `mPanInitialized`:9765, `mSelected`:9766, `mDragStart`:9767, `mPanning`:9768, `mTouchStart`:9769, `mPinchDist`:9770, `mapInited`:9771, `M_UNDO_MAX`:9773, `mUndoStack`:9774, `mSnapshot`:9776, `mPushUndo`:9777, `mapUndo`:9783, `mapRedo`:9790, `updateMapUndoButtons`:9797, `saveMapGraph`:9804, `initMapGraph`:9808, `syncWiringNodesToMap`:9828, `initMapCanvas`:9847, `resizeMapCanvas`:9878, `mNodeScreen`:9887, `mHitNode`:9890, `drawMap`:9900, `mapClick`:9977, `mapMouseDown`:9992, `mapMouseMove`:9999, `mapMouseUp`:10014, `mapTouchStart`:10018, `mapTouchMove`:10035, `mapTouchEnd`:10065, `updateMapHint`:10073, `addMapNode`:10078, `deleteMapNode`:10099, `showMapAddForm`:10112, `pickMapLayer`:10116, `sitMaps`:10719, `saveSitMaps`:10721, `sitMapCreate`:10725, `sitMapDelete`:10735, `smCanvases`:10742, `smInitCanvas`:10744, `smHitNode`:10788, `smSave`:10794, `smAddNode`:10801, `smDraw`:10812, `renderSitMaps`:10828, `smToggle`:10864, `_rmOrig`:10878, `renderMapNodal = function() `:10879

</details>

<details><summary><code>aim</code> — 5 nodes</summary>

`carryTo`:4291, `localAim`:4510, `AIM_PHRASES`:4668, `aimT`:4669, `runAim`:4671

</details>

<details><summary><code>fire</code> — 2 nodes</summary>

`localFire`:4586, `runFire`:4802

</details>

<details><summary><code>reload</code> — 7 nodes</summary>

`saveReload`:4363, `renderReloads`:4389, `localReload`:4607, `runReload`:4822, `renderReloadAnchorCurrent`:11079, `correctAnchorWord`:11093, `renderAnchorHistory`:11105

</details>

<details><summary><code>train</code> — 16 nodes</summary>

`incUse`:4372, `GRAD_SKILLS`:6128, `logSelfCheck`:6178, `logSelfCheckAttempt`:6195, `showGraduation`:6207, `renderGraduationGrid`:6224, `initIndependence`:6283, `TRAIN_SKILLS`:8894, `setEx`:8896, `nextEx`:8908, `setConf`:8914, `MEM_QS`:8919, `saveTrain`:8952, `generateTrainSession`:9024, `updateStreak`:9084, `renderTrainLog`:9097

</details>

<details><summary><code>sim</code> — 33 nodes</summary>

`currentMode`:6126, `_endSim2`:6245, `endSim = async function() {`:6246, `_runWeekly2`:6267, `runWeekly = async function()`:6268, `runSolve`:6305, `MENTAL_MODELS`:6444, `runRead`:6487, `feedSimToIntelligence`:6527, `getPatternEntries`:6576, `getCritTarget`:6584, `runWeekly`:6601, `simType`:6688, `simDiff`:6689, `simHistory`:6690, `simActive`:6691, `simTurnCount`:6692, `SIM_TYPES`:6694, `SIM_DIFFICULTY`:6704, `setSimType`:6710, `setSimDiff`:6715, `buildSimSystem`:6720, `startSim`:6736, `sendSimResponse`:6796, `endSim`:6856, `localSimDebrief`:6922, `resetSim`:6930, `addSimMsg`:6941, `renderSimLog`:6956, `initSim`:6963, `_go3`:6965, `const _go3=go; go=function(c`:6965, `_enter3`:6967

</details>

<details><summary><code>formulas</code> — 32 nodes</summary>

`FORMULAS`:5534, `currentFormCat`:5824, `setFormCat`:5826, `renderFormulas`:5833, `toggleFormula`:5886, `practiseFormula`:5895, `applyFormula`:5916, `stressTestFormula`:6004, `generateFormulas`:6055, `initFormulas`:6109, `_go4`:6113, `go = function(c) { _go4(c); `:6114, `_enter4`:6115, `enter = function(c) { _enter`:6116, `customFormulas`:10885, `saveCustomFormulas`:10887, `toggleCustomFormulaForm`:10891, `addCustomFormula`:10899, `deleteCustomFormula`:10911, `renderCustomFormulas`:10916, `stressTestFormulaByIndex`:10941, `stressTestCustomFormula`:10947, `editCustomFormula`:10953, `saveCustomFormulaEdit`:10995, `MATH_SYMBOLS`:11119, `initSymbolKeyboard`:11129, `insertSymbol`:11137, `generateFormulaAI`:11149, `_lastGeneratedFormula`:11219, `addGeneratedFormula`:11221, `_initFormOrig`:11239, `initFormulas = function() {`:11240

</details>

<details><summary><code>wiring</code> — 202 nodes</summary>

`PFE`:3507, `WS`:3532, `ifMode`:3708, `ifModeTarget`:3709, `ifThinking`:3712, `ifThinkTimer`:3713, `ifX`:3722, `ifY`:3723, `ifVX`:3724, `ifVY`:3725, `ifSZ`:3726, `ifBR`:3727, `ifTY`:3728, `ifPH`:3729, `ifLR`:3730, `ifANG`:3731, `ifR`:3732, `ifLAY`:3733, `ifN`:3736, `ifInit`:3744, `ifPulses`:3787, `ifUpdate`:3791, `ifDraw`:3941, `ifInited`:4109, `ifEnsureInit`:4110, `flowNodes`:4965, `flowEdges`:4966, `flowDragging`:4967, `flowOffset`:4968, `flowPan`:4969, `flowPanStart`:4970, `flowScale`:4971, `flowCanvas`:4972, `flowW`:4973, `flowAnimFrame`:4974, `flowBuilt`:4975, `NODE_COLORS`:4977, `initFlowCanvas`:4988, `drawFlowEmpty`:5013, `runForceLayout`:5186, `drawFlow`:5228, `flowMouseDown`:5356, `flowMouseMove`:5374, `flowMouseUp`:5394, `flowWheel`:5400, `flowTouchStart`:5407, `flowTouchMove`:5412, `canvasPos`:5417, `flowScreenToWorld`:5422, `flowHitNode`:5426, `showTooltip`:5435, `showFlowNodeDetail`:5445, `resetFlow`:5469, `getFlowInsight`:5478, `initFlow`:5521, `_go5`:5525, `_enter5`:5526, `ORB`:6990, `orbDrag`:7031, `orbDragMoved`:7032, `orbPan`:7033, `orbCustomPos`:7034, `orbConnections`:7035, `orbDefaultConnections`:7052, `orbGetNodeXY`:7063, `orbSavePositions`:7079, `orbInitConnections`:7083, `orbInit`:7098, `editModalOpen`:7277, `editModalClose`:7287, `editTab`:7291, `eNodeRefreshSel`:7301, `eNodeLoad`:7308, `eNodeSave`:7331, `eNodeToggleVisible`:7344, `eNodeClone`:7350, `eNodeAdd`:7363, `eNodeDelete`:7376, `eNodeAddConn`:7389, `eNodeRemConn`:7401, `eNodeStatus`:7408, `efLoad`:7411, `efSync`:7423, `efRenderLayers`:7435, `efMoveLayer`:7470, `efSetLayerThickness`:7479, `efAddLayer`:7490, `efDeleteLayer`:7496, `efSave`:7503, `efReset`:7509, `ewLoad`:7512, `ewSync`:7522, `ewSave`:7529, `pfeOpen`:7537, `pfeClose`:7546, `pfePopulate`:7553, `pfeSync`:7566, `pfeRenderLayers`:7577, `pfeAddLayer`:7617, `pfeDeleteLayer`:7622, `pfeSave`:7628, `pfeReset`:7635, `nedWirePreview`:7641, `NED_COLORS`:7653, `nedNode`:7656, `nedOpen`:7658, `nedRefreshConn`:7694, `nedSetColor`:7710, `nedPreview`:7717, `nedSave`:7727, `nedToggleVisible`:7740, `nedAddConn`:7749, `nedRemoveConn`:7759, `nedClone`:7766, `nedDivide`:7780, `nedMergeStart`:7804, `nedMergeConfirm`:7809, `nedAddNew`:7839, `nedDelete`:7854, `nedPersist`:7866, `nedStatus`:7874, `nedClose`:7879, `orbResize`:7893, `orbHitTest`:7899, `orbPointerDown`:7915, `orbPointerMove`:7928, `orbPointerUp`:7954, `orbEnter`:7962, `orbDraw`:7993, `orbRingVis`:8177, `orbTryInit`:8187, `BRAIN_MAP_DEFAULTS`:9116, `LAYER_COLORS`:9190, `LAYER_LABELS`:9197, `brainMap`:9201, `NG`:9208, `initNodalData`:9210, `saveNodalGraph`:9244, `saveBrainMap`:9247, `NC`:9252, `nodalInited`:9253, `nPan`:9254, `nPanInitialized`:9255, `nZoom`:9256, `nConnecting`:9257, `nSelected`:9258, `nConnectFrom`:9259, `nDragging`:9260, `nDragStart`:9261, `nDragMoved`:9262, `nPanning`:9263, `nPanStart`:9264, `N_UNDO_MAX`:9267, `nUndoStack`:9268, `nRedoStack`:9269, `nSnapshot`:9271, `nPushUndo`:9274, `nodalUndo`:9280, `nodalRedo`:9289, `updateUndoButtons`:9298, `setNMode`:9305, `startConnectMode`:9307, `startAddNode`:9315, `cancelAddNode`:9319, `confirmAddNode`:9325, `deselectNode`:9332, `updateNHint`:9340, `initNodalCanvas`:9345, `resizeNodalCanvas`:9389, `nodeScreen`:9399, `screenToWorld`:9405, `hitNode`:9409, `nodalClick`:9419, `hitEdgeTest`:9439, `handleNodalTap`:9457, `nodalMouseDown`:9493, `nodalMouseMove`:9504, `nodalMouseUp`:9519, `nTouchStart`:9525, `nPinchDist`:9526, `nodalTouchStart`:9527, `nodalTouchMove`:9547, `nodalTouchEnd`:9581, `showNodeDetail`:9590, `hideNodeDetail`:9600, `startConnectFromDetail`:9605, `deleteSelectedNode`:9610, `drawNodal`:9623, `renderWiring`:9744, `toggleLayer`:10121, `obsLayer`:10124, `pickObsLayer`:10125, `nodalAddLayer`:10131, `pickAddNodeLayer`:10132, `addObs`:10138, `addObsToLayer`:10173, `_goWiring`:10204, `go = function(c) {`:10205, `_enterWiring`:10210, `enter = function(c) {`:10211, `_rwOrig`:10873, `renderWiring = function() {`:10874

</details>

<details><summary><code>projects</code> — 21 nodes</summary>

`project`:3672, `readProjects`:4898, `projects`:10225, `saveProjects`:10227, `projAdd`:10231, `projDelete`:10251, `projToggle`:10257, `projCycleStatus`:10262, `projSaveNotes`:10269, `projAddTask`:10275, `projToggleTask`:10284, `projDeleteTask`:10291, `renderProjTasks`:10297, `projCanvases`:10311, `initProjCanvas`:10313, `projHitNode`:10367, `saveProjCanvas`:10377, `projAddNode`:10384, `drawProjCanvas`:10396, `renderProjects`:10426, `renderProjects_init`:10481

</details>

<details><summary><code>forge</code> — 15 nodes</summary>

`readForge`:4844, `FORGE_DEFAULTS`:10492, `forgeTools`:10501, `fgStatus`:10507, `fgPickStatus`:10509, `fgAdd`:10515, `fgCycleStatus`:10532, `fgRemove`:10540, `renderForge`:10546, `editForgeTool`:10570, `saveForgeTool`:10588, `_goForge`:10642, `go = function(c) {`:10643, `_entForge`:10649, `enter = function(c) {`:10650

</details>

<details><summary><code>lens</code> — 34 nodes</summary>

`LENS_LIBRARY`:8216, `currentLensCat`:8299, `lensHistory`:8300, `setLensCat`:8302, `renderLensLibrary`:8309, `renderCurrentLensGrid`:8350, `selectCurrentLens`:8359, `lensCarryFromMap`:8371, `lensReadMode`:8382, `setLensReadMode`:8384, `populateLensSelects`:8396, `carryLensTo`:8405, `viewThroughLens`:8416, `runLensRead`:8475, `renderLensPattern`:8559, `RIG_MOTIVES`:8580, `currentRigMotive`:8589, `currentRigSpace`:8590, `selectRigMotive`:8592, `selectRigSpace`:8612, `saveCurrentRig`:8622, `getCurrentRigSummary`:8642, `runRecalibrate`:8654, `clearRigChat`:8703, `appendRigChatBubble`:8709, `sendRigChat`:8720, `CAM_NODES`:8772, `currentCamCat`:8835, `setCamNodeCat`:8837, `renderCamNodes`:8844, `_goLens`:8861, `go = function(c) {`:8862, `_enterLens`:8866, `enter = function(c) {`:8867

</details>
