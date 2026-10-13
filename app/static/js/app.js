/**
 * RailOpt-IR Main Application Logic & Signaling System Controller
 */

let yardSchematic = null;
let state = null;
let isPlaying = false;
let playInterval = null;
let playbackSpeed = 5;
let selectedKavachTrainId = 'TR_DN_VB_22436'; // Default to Vande Bharat

document.addEventListener('DOMContentLoaded', () => {
  initRenderers();
  bindUIEvents();
  fetchState();
});

function initRenderers() {
  yardSchematic = new OccVideoWallRenderer('yardSchematicCanvas');

  // Callback when user clicks on a signal post on the canvas
  window.onSignalSelected = (sig) => {
    updateSignalInspectorUI(sig);
  };
}

async function fetchState() {
  try {
    const res = await fetch('/api/state');
    state = await res.json();
    renderAll();
  } catch (err) {
    console.error('Failed to fetch state:', err);
  }
}

function renderAll() {
  if (!state) return;

  // 1. Update Track & Signaling Canvas
  yardSchematic.setData(state);

  // 2. Render Indian Railways Signal Telemetry Counts
  renderSignalAspectTelemetry(state.signals);

  // 3. Render KAVACH (TCAS) In-Cab ATP Telemetry
  renderKavachConsole(state.kavach);

  // 4. Render Active Train Table
  renderTrainTable(state.trains, state.live_positions, state.optimized.schedule);

  // 5. Render Section Controller Advisories
  renderAdvisories(state.advisories);

  // 6. Update Safety Conflicts Feed
  renderConflicts(state.baseline?.conflicts, state.optimized?.conflicts);

  // 7. Update Clock Display
  updateClockDisplay(state.current_sim_time_sec);

  // 8. Populate Signal Dropdown if not already done
  populateSignalDropdown(state.signals);
}

function renderSignalAspectTelemetry(signals) {
  if (!signals) return;

  let greenCount = 0;
  let doubleYellowCount = 0;
  let yellowCount = 0;
  let redCount = 0;

  signals.forEach(sig => {
    if (sig.is_failed || sig.aspect === 'RED') redCount++;
    else if (sig.aspect === 'YELLOW') yellowCount++;
    else if (sig.aspect === 'DOUBLE_YELLOW') doubleYellowCount++;
    else if (sig.aspect === 'GREEN') greenCount++;
  });

  if (document.getElementById('countSigGreen')) {
    document.getElementById('countSigGreen').innerText = `${greenCount} Signals`;
    document.getElementById('countSigDoubleYellow').innerText = `${doubleYellowCount} Signals`;
    document.getElementById('countSigYellow').innerText = `${yellowCount} Signals`;
    document.getElementById('countSigRed').innerText = `${redCount} Signals`;
  }
}

function renderKavachConsole(kavachList) {
  const container = document.getElementById('kavachConsoleContainer');
  const select = document.getElementById('selectKavachTrain');

  if (!kavachList || kavachList.length === 0) {
    container.innerHTML = `
      <div class="col-span-5 p-4 text-center text-slate-400 text-xs">
        Locomotives entering section. Radio link synchronizing with KAVACH trackside balises...
      </div>
    `;
    return;
  }

  // Populate train selector if needed
  if (select.children.length === 0) {
    select.innerHTML = kavachList.map(k => `
      <option value="${k.train_id}">${k.train_number} - ${k.train_name}</option>
    `).join('');
    select.value = selectedKavachTrainId;
  }

  // Find currently selected train's telemetry
  let activeData = kavachList.find(k => k.train_id === selectedKavachTrainId) || kavachList[0];
  selectedKavachTrainId = activeData.train_id;

  // Aspect color mapping
  const aspectConfig = {
    'GREEN': { text: 'GREEN (Clear)', bg: 'bg-emerald-500', glow: 'shadow-[0_0_15px_#10b981]' },
    'DOUBLE_YELLOW': { text: 'DOUBLE YELLOW (Attention)', bg: 'bg-amber-400', glow: 'shadow-[0_0_15px_#f59e0b]' },
    'YELLOW': { text: 'YELLOW (Caution)', bg: 'bg-amber-500', glow: 'shadow-[0_0_15px_#f59e0b]' },
    'RED': { text: 'RED (Danger)', bg: 'bg-rose-500', glow: 'shadow-[0_0_15px_#ef4444]' },
  };

  const asp = aspectConfig[activeData.target_signal_aspect] || aspectConfig['GREEN'];

  container.innerHTML = `
    <!-- 1. Cab Signal Aspect Repeater -->
    <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col items-center justify-center text-center">
      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">In-Cab Aspect</span>
      <div class="w-10 h-10 rounded-full ${asp.bg} ${asp.glow} flex items-center justify-center font-black text-slate-950 text-sm mb-2 ring-2 ring-white/20">
        ${activeData.target_signal_aspect === 'DOUBLE_YELLOW' ? 'YY' : activeData.target_signal_aspect[0]}
      </div>
      <span class="text-xs font-bold text-slate-200">${asp.text}</span>
      ${activeData.route_feather ? '<span class="text-[10px] text-sky-400 font-bold mt-1 bg-sky-950 px-1.5 py-0.5 rounded border border-sky-800">Route Feather ON</span>' : ''}
    </div>

    <!-- 2. Target Distance to Signal -->
    <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Target Signal</span>
      <div>
        <div class="text-xs font-semibold text-slate-300 truncate">${activeData.target_signal_name}</div>
        <div class="text-xl font-black font-mono text-amber-400 mt-1">${activeData.target_signal_distance_m} m</div>
        <span class="text-[10px] text-slate-400">Distance to Post</span>
      </div>
    </div>

    <!-- 3. Movement Authority (MA) -->
    <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Movement Authority</span>
      <div>
        <div class="text-xl font-black font-mono text-emerald-400 mt-1">${activeData.movement_authority_m} m</div>
        <span class="text-[10px] text-slate-400">Safe Braking Envelope</span>
      </div>
    </div>

    <!-- 4. Speed Supervision Curve -->
    <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Speed Supervision</span>
      <div>
        <div class="flex items-baseline space-x-1.5 mt-1">
          <span class="text-xl font-black font-mono text-sky-400">${activeData.current_speed_kmh}</span>
          <span class="text-xs text-slate-400 font-mono">/ ${activeData.permitted_speed_kmh} km/h</span>
        </div>
        <span class="text-[10px] text-slate-400">Actual vs Ceiling Speed</span>
      </div>
    </div>

    <!-- 5. KAVACH SPAD Safety Status -->
    <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 flex flex-col justify-between">
      <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Safety Status</span>
      <div>
        <div class="flex items-center space-x-1.5 mt-1">
          <span class="w-2.5 h-2.5 rounded-full ${activeData.spad_alert === 'NORMAL' ? 'bg-emerald-400 shadow-[0_0_8px_#10b981]' : 'bg-rose-500 shadow-[0_0_8px_#ef4444]'}"></span>
          <span class="text-xs font-bold ${activeData.spad_alert === 'NORMAL' ? 'text-emerald-400' : 'text-rose-400'} font-mono">${activeData.spad_alert}</span>
        </div>
        <span class="text-[10px] text-slate-400 mt-1 block">UHF Radio Link OK</span>
      </div>
    </div>
  `;
}

function renderAdvisories(advisories) {
  const container = document.getElementById('advisoriesContainer');
  if (!advisories || advisories.length === 0) {
    container.innerHTML = `<div class="p-4 text-center text-slate-400 text-xs">Section operating normally. No active precedence orders.</div>`;
    return;
  }

  container.innerHTML = advisories.map(adv => `
    <div class="p-3.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:border-slate-600 transition flex flex-col space-y-2">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <span class="px-2 py-0.5 rounded text-[11px] font-bold ${adv.action_type === 'LOOP_DIVERSION' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}">
            ${adv.action_type.replace('_', ' ')}
          </span>
          <span class="font-mono text-xs font-bold text-slate-300">${adv.advisory_id}</span>
        </div>
        <span class="text-[11px] font-semibold px-2 py-0.5 rounded ${adv.priority_level === 'CRITICAL' ? 'bg-rose-500/20 text-rose-300' : 'bg-purple-500/20 text-purple-300'}">
          ${adv.priority_level}
        </span>
      </div>

      <div class="text-xs font-bold text-slate-100">
        ${adv.action_summary}
      </div>

      <div class="text-[11px] text-slate-400 leading-relaxed">
        ${adv.detailed_rationale}
      </div>

      <div class="flex items-center justify-between pt-1 border-t border-slate-700/60 text-xs">
        <span class="text-emerald-400 font-semibold text-[11px]">⚡ ${adv.impact_kpi}</span>
        <button onclick="acknowledgeAdvisory(event)" class="px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold transition">
          Acknowledge
        </button>
      </div>
    </div>
  `).join('');
}

function renderConflicts(baseConflicts, optConflicts) {
  const badge = document.getElementById('conflictResolvedBadge');
  const resolvedCount = Math.max(0, (baseConflicts?.length || 0) - (optConflicts?.length || 0));
  badge.innerText = `${resolvedCount} Conflicts Resolved by AI`;

  const container = document.getElementById('conflictsContainer');
  const activeConflicts = optConflicts || [];

  if (activeConflicts.length === 0) {
    container.innerHTML = `
      <div class="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-lg text-emerald-300 text-xs flex items-center space-x-2">
        <span class="text-emerald-400 font-bold">✓</span>
        <span>All section headways and station loop constraints satisfied! 0 active conflicts.</span>
      </div>
    `;
    return;
  }

  container.innerHTML = activeConflicts.map(c => `
    <div class="p-2.5 bg-rose-950/30 border border-rose-800/40 rounded-lg text-xs space-y-1">
      <div class="flex items-center justify-between text-rose-300 font-bold">
        <span>⚠️ ${c.conflict_type}</span>
        <span>${c.location_station}</span>
      </div>
      <div class="text-slate-300 text-[11px]">${c.description}</div>
    </div>
  `).join('');
}

function renderTrainTable(trains, livePositions, optSchedule) {
  const tbody = document.getElementById('trainTableBody');
  if (!trains) return;

  const posMap = {};
  (livePositions || []).forEach(p => posMap[p.train_id] = p);

  tbody.innerHTML = trains.map(t => {
    const pos = posMap[t.id] || {};
    const destSt = t.direction === 'DOWN' ? 'ALJN' : 'GZB';
    const schedEntry = optSchedule?.[t.id]?.[destSt];
    const delayMins = Math.round((schedEntry?.delay_sec || 0) / 60);

    return `
      <tr class="border-b border-slate-800 hover:bg-slate-800/40 text-xs transition">
        <td class="py-2.5 px-3">
          <div class="flex items-center space-x-2">
            <span class="w-2.5 h-2.5 rounded-full" style="background-color: ${t.color_hex}"></span>
            <span class="font-mono font-bold text-slate-100">${t.number}</span>
          </div>
        </td>
        <td class="py-2.5 px-3 text-slate-300 font-medium">${t.name}</td>
        <td class="py-2.5 px-3">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300">
            ${t.category}
          </span>
        </td>
        <td class="py-2.5 px-3 font-mono font-semibold ${t.direction === 'DOWN' ? 'text-sky-400' : 'text-indigo-400'}">
          ${t.direction}
        </td>
        <td class="py-2.5 px-3 font-mono text-slate-200">
          ${pos.current_km !== undefined ? `${pos.current_km} km` : '--'}
        </td>
        <td class="py-2.5 px-3 font-mono text-slate-200 font-bold">
          ${pos.current_speed_kmh !== undefined ? `${pos.current_speed_kmh} km/h` : '--'}
        </td>
        <td class="py-2.5 px-3 font-mono font-semibold ${pos.track && pos.track.includes('LOOP') ? 'text-amber-400' : 'text-emerald-400'}">
          ${pos.track || 'MAIN_LINE'}
        </td>
        <td class="py-2.5 px-3 font-semibold ${pos.status === 'RUNNING' ? 'text-emerald-400' : (pos.status === 'DWELLING_AT_STATION' ? 'text-amber-400' : 'text-slate-400')}">
          ${pos.status || '--'}
        </td>
        <td class="py-2.5 px-3 font-mono font-bold ${delayMins > 5 ? 'text-rose-400' : 'text-emerald-400'}">
          +${delayMins}m
        </td>
      </tr>
    `;
  }).join('');
}

function updateClockDisplay(timeSec) {
  const hh = Math.floor(timeSec / 3600);
  const mm = Math.floor((timeSec % 3600) / 60);
  const ss = timeSec % 60;
  const timeStr = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;

  const clock = document.getElementById('simClockDisplay');
  if (clock) clock.innerText = timeStr;
  const fsClock = document.getElementById('fsClockDisplay');
  if (fsClock) fsClock.innerText = timeStr;
  const slider = document.getElementById('timeSlider');
  if (slider) slider.value = timeSec;
}

function populateSignalDropdown(signals) {
  const select = document.getElementById('selectSignalToFault');
  if (!signals || select.children.length > 0) return;

  select.innerHTML = signals.map(s => `
    <option value="${s.id}">${s.name} (Km ${s.km}) [${s.direction}]</option>
  `).join('');

  select.addEventListener('change', () => {
    const sig = state.signals.find(s => s.id === select.value);
    if (sig) updateSignalInspectorUI(sig);
  });
}

function updateSignalInspectorUI(sig) {
  const select = document.getElementById('selectSignalToFault');
  if (select) select.value = sig.id;

  const aspectEl = document.getElementById('inspectedSigAspect');
  if (aspectEl) {
    aspectEl.innerText = `Aspect: ${sig.aspect} ${sig.is_failed ? '(FAULT CLAMP)' : ''}`;
    aspectEl.className = sig.is_failed || sig.aspect === 'RED' ? 'font-bold text-rose-400' : (sig.aspect === 'GREEN' ? 'font-bold text-emerald-400' : 'font-bold text-amber-400');
  }

  const faultBtn = document.getElementById('btnToggleSignalFault');
  if (faultBtn) {
    faultBtn.innerText = sig.is_failed ? '✓ Normal' : 'Clamp Red';
    faultBtn.className = sig.is_failed ? 'px-2.5 py-1 rounded bg-emerald-700 hover:bg-emerald-600 text-white font-bold text-xs transition shadow font-mono' : 'px-2.5 py-1 rounded bg-rose-700 hover:bg-rose-600 text-white font-bold text-xs transition shadow font-mono';
  }
}

function toggleFullscreen() {
  const container = document.getElementById('videoWallContainer');
  if (!container) return;

  const isFs = !!document.fullscreenElement || container.classList.contains('fullscreen-active');

  if (!isFs) {
    if (container.requestFullscreen) {
      container.requestFullscreen().catch(() => {
        container.classList.add('fullscreen-active');
        if (yardSchematic) yardSchematic.resize();
      });
    } else if (container.webkitRequestFullscreen) {
      container.webkitRequestFullscreen();
    } else {
      container.classList.add('fullscreen-active');
      if (yardSchematic) yardSchematic.resize();
    }
  } else {
    if (document.exitFullscreen && document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen();
    }
    container.classList.remove('fullscreen-active');
    setTimeout(() => {
      if (yardSchematic) yardSchematic.resize();
    }, 100);
  }
}

function bindUIEvents() {
  // Fullscreen button in header & Exit button in HUD
  const fsBtn = document.getElementById('btnToggleFullscreen');
  if (fsBtn) fsBtn.addEventListener('click', toggleFullscreen);

  const exitFsBtn = document.getElementById('btnExitFullscreen');
  if (exitFsBtn) exitFsBtn.addEventListener('click', toggleFullscreen);

  document.addEventListener('fullscreenchange', () => {
    const container = document.getElementById('videoWallContainer');
    const isFs = !!document.fullscreenElement;
    if (container) {
      if (isFs) container.classList.add('fullscreen-active');
      else container.classList.remove('fullscreen-active');
    }
    setTimeout(() => {
      if (yardSchematic) yardSchematic.resize();
    }, 100);
  });

  // ESC key listener for fallback fullscreen
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const container = document.getElementById('videoWallContainer');
      if (container && container.classList.contains('fullscreen-active')) {
        container.classList.remove('fullscreen-active');
        setTimeout(() => {
          if (yardSchematic) yardSchematic.resize();
        }, 100);
      }
    }
  });

  // Kavach train selector
  document.getElementById('selectKavachTrain').addEventListener('change', (e) => {
    selectedKavachTrainId = e.target.value;
    if (state) renderKavachConsole(state.kavach);
  });

  // Time scrubber
  const slider = document.getElementById('timeSlider');
  slider.addEventListener('input', (e) => {
    const val = parseInt(e.target.value);
    setSimulationTime(val);
  });

  // Play / Pause (header and fullscreen HUD sync)
  const playBtn = document.getElementById('playPauseBtn');
  const fsPlayBtn = document.getElementById('fsPlayPauseBtn');

  const handlePlayToggle = () => {
    isPlaying = !isPlaying;
    const txt = isPlaying ? '❚❚ Pause' : '▶ Play';
    if (playBtn) playBtn.innerHTML = txt;
    if (fsPlayBtn) fsPlayBtn.innerHTML = txt;
    if (isPlaying) {
      startPlayback();
    } else {
      stopPlayback();
    }
  };

  if (playBtn) playBtn.addEventListener('click', handlePlayToggle);
  if (fsPlayBtn) fsPlayBtn.addEventListener('click', handlePlayToggle);

  // Disruption: Inject Train Delay
  document.getElementById('btnInjectDelay').addEventListener('click', async () => {
    const trainSelect = document.getElementById('selectDisruptTrain');
    const delayMins = parseInt(document.getElementById('inputDisruptMinutes').value) || 15;
    const trainId = trainSelect.value;

    try {
      await fetch('/api/inject-delay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ train_id: trainId, delay_sec: delayMins * 60 })
      });
      await fetchState();
    } catch (e) {
      console.error(e);
    }
  });

  // Disruption: Toggle Signal Failure
  document.getElementById('btnToggleSignalFault').addEventListener('click', async () => {
    const select = document.getElementById('selectSignalToFault');
    const sigId = select.value;
    const sig = state.signals.find(s => s.id === sigId);
    if (!sig) return;

    const newFailedState = !sig.is_failed;
    try {
      await fetch('/api/toggle-signal-failure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signal_id: sigId, is_failed: newFailedState })
      });
      await fetchState();
      const updatedSig = state.signals.find(s => s.id === sigId);
      if (updatedSig) updateSignalInspectorUI(updatedSig);
    } catch (e) {
      console.error(e);
    }
  });

  // Disruption: Toggle TSR
  document.getElementById('toggleTSR').addEventListener('change', async (e) => {
    const active = e.target.checked;
    try {
      await fetch('/api/toggle-tsr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tsr_id: 'TSR-01', active })
      });
      await fetchState();
    } catch (e) {
      console.error(e);
    }
  });

  // Re-run Optimization Button
  document.getElementById('btnRunOptimizer').addEventListener('click', async () => {
    const btn = document.getElementById('btnRunOptimizer');
    btn.innerHTML = `<span class="animate-spin mr-1">⟳</span> Solving with OR-Tools...`;
    try {
      await fetch('/api/optimize', { method: 'POST' });
      await fetchState();
    } finally {
      btn.innerHTML = `⚡ Solve with Google OR-Tools`;
    }
  });

  // Reset Simulation
  document.getElementById('btnResetScenario').addEventListener('click', async () => {
    await fetch('/api/reset', { method: 'POST' });
    await fetchState();
  });
}

function startPlayback() {
  if (playInterval) clearInterval(playInterval);
  playInterval = setInterval(async () => {
    let curr = state.current_sim_time_sec + (playbackSpeed * 2);
    if (curr > 59400) curr = 50400; // loop back to 14:00
    setSimulationTime(curr);
  }, 100);
}

function stopPlayback() {
  if (playInterval) clearInterval(playInterval);
}

async function setSimulationTime(timeSec) {
  if (!state) return;
  state.current_sim_time_sec = timeSec;
  updateClockDisplay(timeSec);

  // 1. Recompute local live train positions
  const live = recomputeLivePositions(timeSec, state.optimized.schedule);
  state.live_positions = live;

  // 2. Recompute dynamic signal aspects according to Indian Railways Block Working (GR 9.02)
  const signals = recomputeSignalsState(live, state.signals, state.optimized.schedule);
  state.signals = signals;

  // 3. Recompute KAVACH (TCAS) In-Cab ATP Telemetry
  const kavach = recomputeKavachTelemetry(live, signals);
  state.kavach = kavach;

  // 4. Update Signal Aspect Telemetry Counters
  renderSignalAspectTelemetry(signals);

  // 5. Update Signal Inspector if currently inspected signal changes
  const select = document.getElementById('selectSignalToFault');
  if (select && select.value) {
    const inspected = signals.find(s => s.id === select.value);
    if (inspected) updateSignalInspectorUI(inspected);
  }

  // 6. Re-render Visual Mimic Panel and Tables
  yardSchematic.setData(state);
  renderTrainTable(state.trains, live, state.optimized.schedule);
  if (state.kavach) renderKavachConsole(state.kavach);
}

function recomputeLivePositions(simTimeSec, schedule) {
  const downSeq = state.corridor.stations.map(s => s.code);
  const upSeq = [...downSeq].reverse();
  const stMap = {};
  state.corridor.stations.forEach(s => stMap[s.code] = s);

  return state.trains.map(train => {
    const stSeq = train.direction === 'DOWN' ? downSeq : upSeq;
    const tSched = schedule[train.id] || {};
    const originSt = stSeq[0];
    const destSt = stSeq[stSeq.length - 1];

    const originDep = tSched[originSt]?.dep || 0;
    const destArr = tSched[destSt]?.arr || 0;

    let status = 'RUNNING';
    let km = stMap[originSt].km;
    let speed = train.max_speed_kmh;
    let track = 'MAIN_LINE';

    if (simTimeSec < originDep) {
      status = 'NOT_ENTERED';
      speed = 0;
    } else if (simTimeSec >= destArr) {
      status = 'CLEARED_SECTION';
      km = stMap[destSt].km;
      speed = 0;
    } else {
      for (let idx = 0; idx < stSeq.length - 1; idx++) {
        const s1 = stSeq[idx];
        const s2 = stSeq[idx + 1];
        const e1 = tSched[s1];
        const e2 = tSched[s2];
        if (!e1 || !e2) continue;

        if (simTimeSec >= e1.arr && simTimeSec <= e1.dep) {
          status = e1.dwell_sec > 0 ? 'DWELLING_AT_STATION' : 'RUNNING';
          km = stMap[s1].km;
          speed = 0;
          track = e1.track;
          break;
        } else if (simTimeSec > e1.dep && simTimeSec < e2.arr) {
          const prog = (simTimeSec - e1.dep) / Math.max(1, e2.arr - e1.dep);
          km = +(stMap[s1].km + prog * (stMap[s2].km - stMap[s1].km)).toFixed(1);
          speed = Math.round(Math.abs(stMap[s2].km - stMap[s1].km) / ((e2.arr - e1.dep) / 3600));
          track = 'BLOCK_SECTION';
          break;
        }
      }
    }

    return {
      train_id: train.id,
      train_number: train.number,
      train_name: train.name,
      category: train.category,
      direction: train.direction,
      current_km: km,
      current_speed_kmh: speed,
      length_meters: train.length_meters || 650,
      status: status,
      track: track,
      color_hex: train.color_hex,
      priority_weight: train.priority_weight
    };
  });
}

const ASPECT_RANK = {
  'RED': 3,
  'YELLOW': 2,
  'GREEN': 1
};

function applyAspect(aspectMap, sigId, newAspect) {
  const current = aspectMap[sigId] || 'GREEN';
  if ((ASPECT_RANK[newAspect] || 1) > (ASPECT_RANK[current] || 1)) {
    aspectMap[sigId] = newAspect;
  }
}

function recomputeSignalsState(livePositions, baseSignals, schedule) {
  if (!baseSignals || baseSignals.length === 0) return [];

  // Clone signal definitions - default all clear (GREEN)
  const signalsOut = baseSignals.map(s => ({
    ...s,
    aspect: s.is_failed ? 'RED' : 'GREEN',
    route_feather_active: false
  }));

  const aspectMap = {};
  const featherMap = {};
  signalsOut.forEach(s => {
    aspectMap[s.id] = s.is_failed ? 'RED' : 'GREEN';
    featherMap[s.id] = false;
  });

  ['DOWN', 'UP'].forEach(dir => {
    const isDown = dir === 'DOWN';
    const dirSignals = signalsOut.filter(s => s.direction === dir);
    if (isDown) {
      dirSignals.sort((a, b) => a.km - b.km);
    } else {
      dirSignals.sort((a, b) => b.km - a.km);
    }

    const activeTrains = (livePositions || []).filter(
      p => p.direction === dir && (p.status === 'RUNNING' || p.status === 'DWELLING_AT_STATION')
    );

    activeTrains.forEach(tr => {
      const trFront = tr.current_km;
      const isDwellingInLoop = tr.status === 'DWELLING_AT_STATION' && tr.track && tr.track.includes('LOOP');

      // 1. Locate the signal mast immediately crossed by train
      let controlledIdx = -1;
      for (let i = 0; i < dirSignals.length; i++) {
        const sig = dirSignals[i];
        if (isDown) {
          if (sig.km <= trFront) controlledIdx = i;
        } else {
          if (sig.km >= trFront) controlledIdx = i;
        }
      }

      if (controlledIdx >= 0) {
        const sig0 = dirSignals[controlledIdx];

        if (isDwellingInLoop) {
          // Train is resting in station loop line; main running line is clear!
          // Loop Starter signal holds the train at RED
          const strSig = dirSignals.find(s => s.signal_type === 'STARTER' && s.station_code && tr.track.includes(s.station_code));
          if (strSig) {
            applyAspect(aspectMap, strSig.id, 'RED');
          }
        } else {
          // Rule specified by user:
          // 1. Crossed signal Sk snaps to RED
          applyAspect(aspectMap, sig0.id, 'RED');

          // 2. Previous signal Sk-1 turns YELLOW
          if (controlledIdx - 1 >= 0) {
            applyAspect(aspectMap, dirSignals[controlledIdx - 1].id, 'YELLOW');
          }

          // 3. Two signals behind Sk-2 and earlier remain GREEN!
        }
      }

      // 2. Station Entry Home Signal Route Feather Indicator for Diverging Routes
      dirSignals.forEach((sig) => {
        if (sig.signal_type === 'HOME' && sig.station_code) {
          const distToHome = isDown ? (sig.km - trFront) : (trFront - sig.km);
          // Train is approaching Home signal (within 3.0 km before Home mast)
          if (distToHome > 0.0 && distToHome <= 3.0) {
            const stSched = schedule?.[tr.train_id]?.[sig.station_code];
            if (stSched && (stSched.is_looped || (stSched.track && stSched.track.includes('LOOP')))) {
              featherMap[sig.id] = true;
              applyAspect(aspectMap, sig.id, 'YELLOW');
            }
          }
        }
      });
    });
  });

  return signalsOut.map(s => ({
    ...s,
    aspect: s.is_failed ? 'RED' : (aspectMap[s.id] || 'GREEN'),
    route_feather_active: s.is_failed ? false : !!featherMap[s.id]
  }));
}

function recomputeKavachTelemetry(livePositions, signalsState) {
  if (!livePositions || !signalsState) return [];

  const kavachList = [];
  const activeTrains = livePositions.filter(p => p.status === 'RUNNING' || p.status === 'DWELLING_AT_STATION');

  activeTrains.forEach(p => {
    const isDown = p.direction === 'DOWN';
    const trKm = p.current_km;

    // Filter signals ahead of locomotive
    const aheadSignals = signalsState.filter(s => {
      if (s.direction !== p.direction) return false;
      return isDown ? (s.km > trKm + 0.02) : (s.km < trKm - 0.02);
    });

    if (isDown) {
      aheadSignals.sort((a, b) => a.km - b.km);
    } else {
      aheadSignals.sort((a, b) => b.km - a.km);
    }

    if (aheadSignals.length > 0) {
      const targetSig = aheadSignals[0];
      const distMeters = Math.max(0, Math.round(Math.abs(targetSig.km - trKm) * 1000));
      const aspect = targetSig.aspect;

      let maMeters = 0;
      let permSpeed = 0;

      if (aspect === 'GREEN') {
        maMeters = distMeters + 3600;
        permSpeed = p.priority_weight >= 90 ? 130.0 : 110.0;
        if (p.category === 'BOXN_FREIGHT' || p.category === 'CONCOR') permSpeed = 75.0;
      } else if (aspect === 'DOUBLE_YELLOW') {
        maMeters = distMeters + 1800;
        permSpeed = 75.0;
      } else if (aspect === 'YELLOW') {
        maMeters = distMeters;
        permSpeed = 30.0;
      } else { // RED
        maMeters = 0;
        permSpeed = 0.0;
      }

      let spadAlert = 'NORMAL';
      if (aspect === 'RED' && distMeters < 250 && p.current_speed_kmh > 0) {
        spadAlert = 'EMERGENCY_BRAKE';
      } else if (p.current_speed_kmh > permSpeed + 5) {
        spadAlert = 'OVERSPEED_WARNING';
      }

      kavachList.push({
        train_id: p.train_id,
        train_number: p.train_number,
        train_name: p.train_name,
        direction: p.direction,
        current_km: trKm,
        current_speed_kmh: p.current_speed_kmh,
        target_signal_name: targetSig.name,
        target_signal_aspect: aspect,
        target_signal_distance_m: distMeters,
        movement_authority_m: maMeters,
        permitted_speed_kmh: permSpeed,
        spad_alert: spadAlert,
        route_feather: !!targetSig.route_feather_active
      });
    }
  });

  return kavachList;
}

function acknowledgeAdvisory(event) {
  const el = event.target;
  el.innerText = '✓ Executed';
  el.classList.add('bg-emerald-700', 'text-white');
  el.disabled = true;
}
