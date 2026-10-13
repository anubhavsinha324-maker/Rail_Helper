/**
 * Indian Railways Dynamic Time-Distance Control Chart (Master String Chart)
 * Canvas-based high-performance renderer for Section Controllers.
 */

class StringChartRenderer {
  constructor(canvasId, tooltipId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.tooltip = document.getElementById(tooltipId);

    // Padding margins around the chart
    this.margin = { top: 40, right: 90, bottom: 50, left: 110 };

    // Time window in seconds (14:00:00 to 16:30:00)
    this.startTimeSec = 50400; // 14:00
    this.endTimeSec = 59400;   // 16:30
    this.totalDurationSec = this.endTimeSec - this.startTimeSec;

    // View mode: 'OPTIMIZED', 'BASELINE', 'SCHEDULED', 'OVERLAY'
    this.viewMode = 'OPTIMIZED';

    // State data
    this.stations = [];
    this.trains = [];
    this.optimizedSchedule = {};
    this.baselineSchedule = {};
    this.currentSimTimeSec = 52200; // 14:30
    this.hoveredTrain = null;

    this.initEvents();
    this.resize();
  }

  setData(data) {
    this.stations = data.corridor.stations || [];
    this.trains = data.trains || [];
    this.optimizedSchedule = data.optimized.schedule || {};
    this.baselineSchedule = data.baseline.schedule || {};
    this.currentSimTimeSec = data.current_sim_time_sec || 52200;
    this.overtakes = data.optimized.overtakes || [];
    this.draw();
  }

  setViewMode(mode) {
    this.viewMode = mode;
    this.draw();
  }

  setSimTime(timeSec) {
    this.currentSimTimeSec = timeSec;
    this.draw();
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = 680 * dpr;
    this.canvas.style.width = `${rect.width}` + 'px';
    this.canvas.style.height = '680px';
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = 680;
    this.draw();
  }

  initEvents() {
    window.addEventListener('resize', () => this.resize());

    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      this.handleMouseMove(mouseX, mouseY, e.clientX, e.clientY);
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.hoveredTrain = null;
      this.tooltip.classList.add('hidden');
      this.draw();
    });
  }

  // Coordinate conversions
  timeToX(timeSec) {
    const plotWidth = this.width - this.margin.left - this.margin.right;
    const norm = (timeSec - this.startTimeSec) / this.totalDurationSec;
    return this.margin.left + norm * plotWidth;
  }

  kmToY(km) {
    const plotHeight = this.height - this.margin.top - this.margin.bottom;
    const maxKm = 106.0;
    return this.margin.top + (km / maxKm) * plotHeight;
  }

  xToTime(x) {
    const plotWidth = this.width - this.margin.left - this.margin.right;
    const norm = (x - this.margin.left) / plotWidth;
    return this.startTimeSec + norm * this.totalDurationSec;
  }

  draw() {
    if (!this.width || !this.height) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    this.drawGridAndStations();
    this.drawTrajectories();
    this.drawOvertakeMarkers();
    this.drawSimTimeLine();
  }

  drawGridAndStations() {
    const ctx = this.ctx;
    const plotWidth = this.width - this.margin.left - this.margin.right;
    const plotHeight = this.height - this.margin.top - this.margin.bottom;

    // Background chart fill
    ctx.fillStyle = '#0b1120';
    ctx.fillRect(this.margin.left, this.margin.top, plotWidth, plotHeight);

    // Vertical time gridlines
    // Every 10 minutes (600s) thin, every 30 mins (1800s) prominent
    for (let t = this.startTimeSec; t <= this.endTimeSec; t += 600) {
      const x = this.timeToX(t);
      const isMajor = (t % 1800 === 0);

      ctx.beginPath();
      ctx.strokeStyle = isMajor ? '#1e293b' : '#141e33';
      ctx.lineWidth = isMajor ? 1.5 : 1;
      ctx.moveTo(x, this.margin.top);
      ctx.lineTo(x, this.height - this.margin.bottom);
      ctx.stroke();

      // Time label at top and bottom
      if (isMajor || t % 1200 === 0) {
        const hh = Math.floor(t / 3600);
        const mm = Math.floor((t % 3600) / 60);
        const timeStr = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;

        ctx.font = '600 11px JetBrains Mono, monospace';
        ctx.fillStyle = isMajor ? '#94a3b8' : '#64748b';
        ctx.textAlign = 'center';

        // Top label
        ctx.fillText(timeStr, x, this.margin.top - 12);
        // Bottom label
        ctx.fillText(timeStr, x, this.height - this.margin.bottom + 18);
      }
    }

    // Horizontal station lines
    this.stations.forEach((st) => {
      const y = this.kmToY(st.km);

      ctx.beginPath();
      ctx.strokeStyle = st.is_junction ? '#334155' : '#1e293b';
      ctx.lineWidth = st.is_junction ? 1.5 : 1;
      ctx.moveTo(this.margin.left, y);
      ctx.lineTo(this.width - this.margin.right, y);
      ctx.stroke();

      // Left Station Label (Code & Name)
      ctx.font = st.is_junction ? '700 12px Plus Jakarta Sans, sans-serif' : '500 11px Plus Jakarta Sans, sans-serif';
      ctx.fillStyle = st.is_junction ? '#f8fafc' : '#cbd5e1';
      ctx.textAlign = 'right';
      ctx.fillText(st.code, this.margin.left - 12, y + 4);

      // Station Km
      ctx.font = '400 9px JetBrains Mono, monospace';
      ctx.fillStyle = '#64748b';
      ctx.fillText(`${st.km} km`, this.margin.left - 50, y + 4);

      // Right Station Label
      ctx.textAlign = 'left';
      ctx.font = '500 11px Plus Jakarta Sans, sans-serif';
      ctx.fillStyle = '#94a3b8';
      ctx.fillText(st.name.split(' ')[0], this.width - this.margin.right + 12, y + 4);
    });

    // Chart outer border
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.strokeRect(this.margin.left, this.margin.top, plotWidth, plotHeight);
  }

  drawTrajectories() {
    const ctx = this.ctx;

    // Determine what schedules to draw based on viewMode
    if (this.viewMode === 'OVERLAY') {
      // Draw ghosted baseline first
      this.trains.forEach((train) => {
        this.renderTrainTrajectory(train, this.baselineSchedule[train.id], true, false);
      });
      // Draw optimized on top
      this.trains.forEach((train) => {
        this.renderTrainTrajectory(train, this.optimizedSchedule[train.id], false, true);
      });
    } else if (this.viewMode === 'BASELINE') {
      this.trains.forEach((train) => {
        this.renderTrainTrajectory(train, this.baselineSchedule[train.id], false, false);
      });
    } else if (this.viewMode === 'OPTIMIZED') {
      this.trains.forEach((train) => {
        this.renderTrainTrajectory(train, this.optimizedSchedule[train.id], false, false);
      });
    } else if (this.viewMode === 'SCHEDULED') {
      this.trains.forEach((train) => {
        this.renderScheduledTrajectory(train);
      });
    }
  }

  renderTrainTrajectory(train, schedData, isGhost = false, isOverlayOpt = false) {
    if (!schedData) return;
    const ctx = this.ctx;

    const isHovered = this.hoveredTrain && this.hoveredTrain.id === train.id;
    const color = isGhost ? 'rgba(148, 163, 184, 0.35)' : train.color_hex;

    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = isHovered ? 4 : (isGhost ? 1.5 : (train.priority_weight >= 90 ? 3 : 2));

    if (isGhost) {
      ctx.setLineDash([5, 5]);
    } else if (train.category === 'BOXN_COAL') {
      ctx.setLineDash([8, 3]);
    } else {
      ctx.setLineDash([]);
    }

    const stSeq = train.direction === 'DOWN' ? this.stations : [...this.stations].reverse();

    ctx.beginPath();
    let started = false;

    stSeq.forEach((st, idx) => {
      const entry = schedData[st.code];
      if (!entry) return;

      const arrX = this.timeToX(entry.arr);
      const depX = this.timeToX(entry.dep);
      const y = this.kmToY(st.km);

      if (!started) {
        ctx.moveTo(depX, y);
        started = true;
      } else {
        // Line from previous station departure to current station arrival
        ctx.lineTo(arrX, y);
        // Horizontal dwell line at this station
        if (entry.arr !== entry.dep) {
          ctx.lineTo(depX, y);
        }
      }
    });

    ctx.stroke();

    // Draw station dots & loop indicators
    if (!isGhost) {
      stSeq.forEach((st) => {
        const entry = schedData[st.code];
        if (!entry) return;

        const arrX = this.timeToX(entry.arr);
        const depX = this.timeToX(entry.dep);
        const y = this.kmToY(st.km);

        if (entry.is_looped) {
          // Yellow glow badge for loop line diversion
          ctx.beginPath();
          ctx.fillStyle = '#f59e0b';
          ctx.arc(arrX, y, 5, 0, Math.PI * 2);
          ctx.fill();

          ctx.beginPath();
          ctx.fillStyle = '#ef4444';
          ctx.arc(depX, y, 4, 0, Math.PI * 2);
          ctx.fill();
        } else if (isHovered) {
          ctx.beginPath();
          ctx.fillStyle = color;
          ctx.arc(arrX, y, 4, 0, Math.PI * 2);
          ctx.fill();
        }
      });
    }

    // Render train number label along the trajectory
    if (!isGhost && started) {
      const firstSt = stSeq[0];
      const firstEntry = schedData[firstSt.code];
      if (firstEntry) {
        const startX = this.timeToX(firstEntry.dep);
        const startY = this.kmToY(firstSt.km);

        ctx.font = '700 10px JetBrains Mono, monospace';
        ctx.fillStyle = isHovered ? '#ffffff' : color;
        ctx.textAlign = 'left';
        ctx.fillText(`${train.number}`, startX + 6, startY + (train.direction === 'DOWN' ? 14 : -6));
      }
    }

    ctx.restore();
  }

  renderScheduledTrajectory(train) {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = train.color_hex;
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);

    const stSeq = train.direction === 'DOWN' ? this.stations : [...this.stations].reverse();
    ctx.beginPath();
    let started = false;

    stSeq.forEach((st) => {
      const entry = train.schedule.find(e => e.station_code === st.code);
      if (!entry) return;

      const arrX = this.timeToX(entry.scheduled_arrival_sec);
      const depX = this.timeToX(entry.scheduled_departure_sec);
      const y = this.kmToY(st.km);

      if (!started) {
        ctx.moveTo(depX, y);
        started = true;
      } else {
        ctx.lineTo(arrX, y);
        if (arrX !== depX) ctx.lineTo(depX, y);
      }
    });

    ctx.stroke();
    ctx.restore();
  }

  drawOvertakeMarkers() {
    if (this.viewMode === 'BASELINE' || !this.overtakes) return;
    const ctx = this.ctx;

    this.overtakes.forEach((ot) => {
      const st = this.stations.find(s => s.code === ot.station_code);
      if (!st) return;

      const x = this.timeToX(ot.timestamp_sec);
      const y = this.kmToY(st.km);

      ctx.save();
      // Overtake badge diamond
      ctx.fillStyle = '#fbbf24';
      ctx.strokeStyle = '#78350f';
      ctx.lineWidth = 2;

      ctx.beginPath();
      ctx.moveTo(x, y - 8);
      ctx.lineTo(x + 8, y);
      ctx.lineTo(x, y + 8);
      ctx.lineTo(x - 8, y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Tooltip indicator
      ctx.font = '700 9px Plus Jakarta Sans, sans-serif';
      ctx.fillStyle = '#fef3c7';
      ctx.textAlign = 'center';
      ctx.fillText('OVERTAKE', x, y - 12);
      ctx.restore();
    });
  }

  drawSimTimeLine() {
    const ctx = this.ctx;
    const x = this.timeToX(this.currentSimTimeSec);
    if (x < this.margin.left || x > this.width - this.margin.right) return;

    ctx.save();
    ctx.strokeStyle = '#ef4444';
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 2]);

    ctx.beginPath();
    ctx.moveTo(x, this.margin.top);
    ctx.lineTo(x, this.height - this.margin.bottom);
    ctx.stroke();

    // Clock indicator header
    const hh = Math.floor(this.currentSimTimeSec / 3600);
    const mm = Math.floor((this.currentSimTimeSec % 3600) / 60);
    const ss = this.currentSimTimeSec % 60;
    const timeStr = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`;

    ctx.fillStyle = '#dc2626';
    ctx.beginPath();
    ctx.roundRect(x - 35, this.margin.top - 28, 70, 20, 4);
    ctx.fill();

    ctx.font = '700 11px JetBrains Mono, monospace';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.fillText(timeStr, x, this.margin.top - 14);

    ctx.restore();
  }

  handleMouseMove(mouseX, mouseY, clientX, clientY) {
    if (mouseX < this.margin.left || mouseX > this.width - this.margin.right ||
        mouseY < this.margin.top || mouseY > this.height - this.margin.bottom) {
      this.hoveredTrain = null;
      this.tooltip.classList.add('hidden');
      this.draw();
      return;
    }

    const mouseTime = this.xToTime(mouseX);
    let closestTrain = null;
    let closestDist = 18; // Pixel radius threshold
    let closestInfo = null;

    const activeSched = this.viewMode === 'BASELINE' ? this.baselineSchedule : this.optimizedSchedule;

    this.trains.forEach((train) => {
      const sched = activeSched[train.id];
      if (!sched) return;

      const stSeq = train.direction === 'DOWN' ? this.stations : [...this.stations].reverse();

      for (let i = 0; i < stSeq.length - 1; i++) {
        const s1 = stSeq[i];
        const s2 = stSeq[i + 1];

        const e1 = sched[s1.code];
        const e2 = sched[s2.code];
        if (!e1 || !e2) continue;

        const x1 = this.timeToX(e1.dep);
        const y1 = this.kmToY(s1.km);
        const x2 = this.timeToX(e2.arr);
        const y2 = this.kmToY(s2.km);

        const dist = this.pointToSegmentDistance(mouseX, mouseY, x1, y1, x2, y2);
        if (dist < closestDist) {
          closestDist = dist;
          closestTrain = train;
          closestInfo = {
            train,
            fromSt: s1,
            toSt: s2,
            entry1: e1,
            entry2: e2
          };
        }
      }
    });

    if (closestTrain) {
      this.hoveredTrain = closestTrain;
      this.showTooltip(clientX, clientY, closestInfo);
    } else {
      this.hoveredTrain = null;
      this.tooltip.classList.add('hidden');
    }

    this.draw();
  }

  showTooltip(clientX, clientY, info) {
    const t = info.train;
    const formatTime = (sec) => {
      const hh = Math.floor(sec / 3600);
      const mm = Math.floor((sec % 3600) / 60);
      return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
    };

    const sched = (this.viewMode === 'BASELINE' ? this.baselineSchedule : this.optimizedSchedule)[t.id] || {};
    const delayMins = Math.round((sched[info.toSt.code]?.delay_sec || 0) / 60);
    const track = sched[info.fromSt.code]?.track || 'MAIN_LINE';

    this.tooltip.innerHTML = `
      <div class="flex items-center space-x-2 border-b border-slate-700 pb-2 mb-2">
        <span class="w-3 h-3 rounded-full" style="background-color: ${t.color_hex}"></span>
        <span class="font-bold text-white font-mono text-sm">${t.number}</span>
        <span class="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-semibold">${t.category}</span>
        <span class="text-xs text-slate-400 font-mono">${t.direction}</span>
      </div>
      <div class="text-xs text-slate-200 font-medium mb-2">${t.name}</div>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span class="text-slate-400">Current Section:</span>
          <div class="font-semibold text-slate-100">${info.fromSt.code} → ${info.toSt.code}</div>
        </div>
        <div>
          <span class="text-slate-400">Track Type:</span>
          <div class="font-semibold ${track.includes('LOOP') ? 'text-amber-400' : 'text-emerald-400'}">${track}</div>
        </div>
        <div>
          <span class="text-slate-400">Dep ${info.fromSt.code}:</span>
          <div class="font-mono text-slate-100">${formatTime(info.entry1.dep)}</div>
        </div>
        <div>
          <span class="text-slate-400">Arr ${info.toSt.code}:</span>
          <div class="font-mono text-slate-100">${formatTime(info.entry2.arr)}</div>
        </div>
        <div>
          <span class="text-slate-400">Priority Weight:</span>
          <div class="font-bold text-purple-400">${t.priority_weight} / 100</div>
        </div>
        <div>
          <span class="text-slate-400">Status Delay:</span>
          <div class="font-bold font-mono ${delayMins > 5 ? 'text-rose-400' : 'text-emerald-400'}">+${delayMins} min</div>
        </div>
      </div>
    `;

    this.tooltip.style.left = `${clientX + 16}px`;
    this.tooltip.style.top = `${clientY + 16}px`;
    this.tooltip.classList.remove('hidden');
  }

  pointToSegmentDistance(px, py, x1, y1, x2, y2) {
    const l2 = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1);
    if (l2 === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (x1 + t * (x2 - x1)), py - (y1 + t * (y2 - y1)));
  }
}
