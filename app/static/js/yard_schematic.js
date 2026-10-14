/**
 * Indian Railways Centralised Traffic Control (CTC) & OCC Mega Video Wall Mimic Panel
 * Accurately replicates Railway Operations Control Centre (OCC) Synoptic Display:
 * - Upper Section: Full 106 km Corridor Panoramic Track & Signaling Mimic Display
 * - Lower Section: Station Yard Interlocking Zoom (Dankaur & Dadri Yard with Crossovers & Sidings)
 */

class OccVideoWallRenderer {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');

    this.stations = [];
    this.livePositions = [];
    this.signals = [];
    this.speedRestrictions = [];
    this.selectedSignal = null;
    this.hoveredItem = null;

    this.resize();
    this.initEvents();
  }

  setData(data) {
    this.stations = data.corridor?.stations || [];
    this.livePositions = data.live_positions || [];
    this.signals = data.signals || [];
    this.speedRestrictions = data.corridor?.speed_restrictions || [];
    this.draw();
  }

  resize() {
    const isFullscreen = !!document.fullscreenElement || this.canvas.parentElement.classList.contains('fullscreen-active');
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const targetHeight = isFullscreen ? window.innerHeight : 450;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = targetHeight * dpr;
    this.canvas.style.width = `${rect.width}px`;
    this.canvas.style.height = `${targetHeight}px`;
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = targetHeight;
    this.draw();
  }

  initEvents() {
    window.addEventListener('resize', () => this.resize());

    this.canvas.addEventListener('mousemove', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      this.handleMouseMove(mouseX, mouseY);
    });

    this.canvas.addEventListener('click', (e) => {
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      this.handleClick(mouseX, mouseY);
    });
  }

  kmToXTop(km) {
    const margin = 70;
    const maxKm = 106.0;
    return margin + (km / maxKm) * (this.width - 2 * margin);
  }

  draw() {
    if (!this.width || !this.height) return;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.width, this.height);

    // Deep pitch-black OCC screen background
    ctx.fillStyle = '#01040a';
    ctx.fillRect(0, 0, this.width, this.height);

    // 1. Draw Display Bezels / Tile Gridlines (Simulating multi-screen video wall)
    this.drawVideoWallGrid();

    // 2. Upper Half: Master Corridor Panoramic Track & Signaling Mimic
    this.drawPanoramicCorridorOverview();

    // 3. Lower Section: Detailed Station Yard Interlocking (Dankaur DKDE & Dadri DER)
    this.drawYardInterlockingZoom();
  }

  drawVideoWallGrid() {
    const ctx = this.ctx;
    ctx.save();
    ctx.strokeStyle = '#0a101f';
    ctx.lineWidth = 1.5;

    // Horizontal split between upper corridor and lower yard zoom
    const midY = Math.round(this.height * 0.50);
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(this.width, midY);
    ctx.stroke();

    ctx.restore();
  }

  // =========================================================================
  // UPPER SECTION: PANORAMIC CORRIDOR TRACK & SIGNALING OVERVIEW
  // =========================================================================
  drawPanoramicCorridorOverview() {
    const ctx = this.ctx;

    // Section Header
    ctx.save();
    ctx.font = '700 12px Plus Jakarta Sans, sans-serif';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'center';
    ctx.fillText('Indian Railways - North Central Railway • Centralised Traffic Control (CTC)', this.width / 2, 22);

    ctx.font = '600 10px JetBrains Mono, monospace';
    ctx.fillStyle = '#00d2ff';
    ctx.fillText('MAIN CORRIDOR OVERVIEW: GHAZIABAD (GZB) - ALIGARH (ALJN) • 106 KM AUTOMATIC BLOCK SYSTEM', this.width / 2, 38);
    ctx.restore();

    const yUpLoop = Math.round(this.height * 0.13);
    const yUpMain = Math.round(this.height * 0.19);
    const yDownMain = Math.round(this.height * 0.32);
    const yDownLoop = Math.round(this.height * 0.38);

    // 1. Base Rails
    const margin = 70;
    ctx.save();
    // Track line labels
    ctx.font = '700 9px JetBrains Mono, monospace';
    ctx.fillStyle = '#38bdf8';
    ctx.textAlign = 'left';
    ctx.fillText('UP MAIN (To New Delhi) ◀', margin, yUpMain - 14);
    ctx.fillText('DOWN MAIN (To Kanpur) ▶', margin, yDownMain + 22);

    // UP & DOWN Main Rails (Default Cyan when normal/idle)
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = '#0084c7';

    // UP Track
    ctx.beginPath();
    ctx.moveTo(margin, yUpMain);
    ctx.lineTo(this.width - margin, yUpMain);
    ctx.stroke();

    // DOWN Track
    ctx.beginPath();
    ctx.moveTo(margin, yDownMain);
    ctx.lineTo(this.width - margin, yDownMain);
    ctx.stroke();

    // Station Loop Sidings & Station Blocks
    this.stations.forEach((st) => {
      const x = this.kmToXTop(st.km);

      // Station Vertical Reference
      ctx.beginPath();
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 4]);
      ctx.moveTo(x, yUpLoop - 8);
      ctx.lineTo(x, yDownLoop + 8);
      ctx.stroke();
      ctx.setLineDash([]);

      // Station Platform Boxes (White CTC Box)
      const pfW = 34;
      const pfH = 8;

      // Platform 1 (Up)
      ctx.fillStyle = '#0f172a';
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      ctx.strokeRect(x - pfW / 2, yUpMain - 15, pfW, pfH);

      // Platform 2 (Down)
      ctx.strokeRect(x - pfW / 2, yDownMain + 7, pfW, pfH);

      // Station Loop Turnouts
      const loopW = 32;
      // UP Loop siding
      ctx.beginPath();
      ctx.strokeStyle = '#0084c7';
      ctx.lineWidth = 2;
      ctx.moveTo(x - loopW, yUpMain);
      ctx.lineTo(x - loopW + 10, yUpLoop);
      ctx.lineTo(x + loopW - 10, yUpLoop);
      ctx.lineTo(x + loopW, yUpMain);
      ctx.stroke();

      // DOWN Loop siding
      ctx.beginPath();
      ctx.moveTo(x - loopW, yDownMain);
      ctx.lineTo(x - loopW + 10, yDownLoop);
      ctx.lineTo(x + loopW - 10, yDownLoop);
      ctx.lineTo(x + loopW, yDownMain);
      ctx.stroke();

      // Station Name & Km - dynamically centered between UP and DOWN tracks
      const stMidY = (yUpMain + yDownMain) / 2;
      ctx.font = '800 10px Plus Jakarta Sans, sans-serif';
      ctx.fillStyle = st.is_junction ? '#facc15' : '#e2e8f0';
      ctx.textAlign = 'center';
      ctx.fillText(st.code, x, stMidY - 2);

      ctx.font = '500 8px JetBrains Mono, monospace';
      ctx.fillStyle = '#64748b';
      ctx.fillText(`${st.km}k`, x, stMidY + 10);
    });

    // 2. Crossovers between UP and DOWN tracks at Junctions (GZB, DER, KRJ, ALJN)
    [0.0, 22.0, 65.0, 106.0].forEach(km => {
      const x = this.kmToXTop(km);
      ctx.beginPath();
      ctx.strokeStyle = '#0084c7';
      ctx.lineWidth = 1.5;
      ctx.moveTo(x - 20, yUpMain);
      ctx.lineTo(x + 20, yDownMain);
      ctx.moveTo(x + 20, yUpMain);
      ctx.lineTo(x - 20, yDownMain);
      ctx.stroke();
    });

    // 3. Occupied Track Circuits & Train Rakes (Scaling with train length: 500m to 1000m)
    this.livePositions.forEach((pos) => {
      if (pos.status !== 'RUNNING' && pos.status !== 'DWELLING_AT_STATION') return;
      const xFront = this.kmToXTop(pos.current_km);
      const isUp = pos.direction === 'UP';

      // Train length in km (500m to 1000m based on category)
      const lenMeters = pos.length_meters || 650;
      const lenKm = lenMeters / 1000.0;
      const rearKm = isUp ? (pos.current_km + lenKm) : (pos.current_km - lenKm);
      const xRear = this.kmToXTop(rearKm);

      let y = isUp ? yUpMain : yDownMain;
      if (pos.track && pos.track.includes('LOOP')) {
        y = isUp ? yUpLoop : yDownLoop;
      }

      // Glowing Red Occupied Track Circuit Segment spanning exact physical rake length
      ctx.save();
      ctx.strokeStyle = '#ff1744';
      ctx.lineWidth = 4;
      ctx.shadowColor = '#ff1744';
      ctx.shadowBlur = 12;
      ctx.beginPath();
      ctx.moveTo(xRear, y);
      ctx.lineTo(xFront, y);
      ctx.stroke();

      // Train Locomotive Front Marker (Small Direction Arrowhead)
      ctx.fillStyle = pos.color_hex || '#facc15';
      ctx.shadowColor = pos.color_hex || '#facc15';
      ctx.shadowBlur = 8;
      ctx.beginPath();
      if (isUp) {
        ctx.moveTo(xFront, y);
        ctx.lineTo(xFront + 6, y - 4);
        ctx.lineTo(xFront + 6, y + 4);
      } else {
        ctx.moveTo(xFront, y);
        ctx.lineTo(xFront - 6, y - 4);
        ctx.lineTo(xFront - 6, y + 4);
      }
      ctx.closePath();
      ctx.fill();

      // CTC Train Berthing Box centered on the rake
      const xMid = (xFront + xRear) / 2;
      const boxW = 56;
      const boxH = 16;
      const boxY = isUp ? y - 26 : y + 10;

      ctx.fillStyle = '#05070f';
      ctx.strokeStyle = pos.color_hex || '#facc15';
      ctx.lineWidth = 1.5;
      ctx.shadowBlur = 6;
      ctx.beginPath();
      ctx.roundRect(xMid - boxW / 2, boxY, boxW, boxH, 2);
      ctx.fill();
      ctx.stroke();

      // Train Number Inside Box
      ctx.font = '800 9px JetBrains Mono, monospace';
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.shadowBlur = 0;
      ctx.fillText(pos.train_number, xMid, boxY + 11);

      // Speed Tag
      ctx.font = '600 8px JetBrains Mono, monospace';
      ctx.fillStyle = '#00e676';
      ctx.fillText(`${pos.current_speed_kmh}k/h`, xMid, isUp ? boxY - 4 : boxY + 25);
      ctx.restore();
    });

    // 4. CTC Signal Aspect Heads (Indian Railways 4-Aspect MACLS spaced every 1 km)
    this.signals.forEach((sig) => {
      const x = this.kmToXTop(sig.km);
      const isUp = sig.direction === 'UP';
      const ySig = isUp ? yUpMain - 8 : yDownMain + 8;
      const headW = 5;
      const headH = 16;
      const headY = isUp ? ySig - headH - 2 : ySig + 2;

      ctx.save();
      // Signal post mast
      ctx.beginPath();
      ctx.strokeStyle = '#475569';
      ctx.lineWidth = 1;
      ctx.moveTo(x, ySig);
      ctx.lineTo(x, isUp ? headY + headH : headY);
      ctx.stroke();

      // White circular "A" marker disc for Automatic Block Signals (ABS)
      if (sig.signal_type === 'AUTOMATIC') {
        const markerY = isUp ? headY + headH + 3 : headY - 3;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, markerY, 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#000000';
        ctx.font = '700 3px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('A', x, markerY);
      } else if (sig.signal_type === 'HOME') {
        // Station Entry Home Signal (1 km before station): highlighted gold cap
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(x - headW / 2 - 0.5, isUp ? headY + headH - 1 : headY - 1, headW + 1, 2);
      }

      // Signal Head Housing (Black hood with subtle border)
      const isSelected = (this.hoveredItem?.id === sig.id || this.selectedSignal?.id === sig.id);
      ctx.fillStyle = '#050811';
      ctx.strokeStyle = isSelected ? '#00d2ff' : (sig.signal_type === 'HOME' ? '#f59e0b' : '#1e293b');
      ctx.lineWidth = isSelected ? 1.5 : 1;
      ctx.beginPath();
      ctx.roundRect(x - headW / 2, headY, headW, headH, 2);
      ctx.fill();
      ctx.stroke();

      // 4 Lenses: Top Yellow, Green, Bottom Yellow, Red
      const lensSpacing = 3.4;
      const startLensY = headY + 2.5;
      const lenses = [
        { name: 'YELLOW1', y: startLensY, baseColor: '#ff9100' },
        { name: 'GREEN',   y: startLensY + lensSpacing, baseColor: '#00e676' },
        { name: 'YELLOW2', y: startLensY + lensSpacing * 2, baseColor: '#ffd600' },
        { name: 'RED',     y: startLensY + lensSpacing * 3, baseColor: '#ff1744' }
      ];

      const asp = (sig.is_failed || sig.aspect === 'RED') ? 'RED' : sig.aspect;

      lenses.forEach(l => {
        let isLit = false;
        if (asp === 'RED' && l.name === 'RED') isLit = true;
        else if (asp === 'YELLOW' && l.name === 'YELLOW1') isLit = true;
        else if (asp === 'DOUBLE_YELLOW' && (l.name === 'YELLOW1' || l.name === 'YELLOW2')) isLit = true;
        else if (asp === 'GREEN' && l.name === 'GREEN') isLit = true;

        ctx.beginPath();
        ctx.arc(x, l.y, 1.2, 0, Math.PI * 2);
        if (isLit) {
          ctx.fillStyle = l.baseColor;
          ctx.shadowColor = l.baseColor;
          ctx.shadowBlur = 8;
          ctx.fill();
        } else {
          ctx.fillStyle = '#111827';
          ctx.shadowBlur = 0;
          ctx.fill();
        }
      });

      // Route Feather (Junction Indicator) when active on Home Signal
      if (sig.route_feather_active) {
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#ffffff';
        ctx.shadowBlur = 8;
        const fY = isUp ? headY - 4 : headY + headH + 4;
        for (let fi = -2; fi <= 2; fi++) {
          ctx.beginPath();
          ctx.arc(x + fi * 2, fY - fi * 1.2, 1, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Signal Label when hovered or selected
      if (isSelected) {
        ctx.shadowBlur = 0;
        ctx.font = '700 8px JetBrains Mono, monospace';
        ctx.fillStyle = '#38bdf8';
        ctx.textAlign = 'center';
        ctx.fillText(`${sig.name} [${asp}]`, x, isUp ? headY - 8 : headY + headH + 12);
      }

      ctx.restore();
    });

    ctx.restore();
  }

  // =========================================================================
  // LOWER-LEFT SECTION: STATION YARD INTERLOCKING ZOOM (DANKAUR & DADRI)
  // =========================================================================
  // =========================================================================
  // LOWER SECTION: STATION YARD INTERLOCKING (DANKAUR & DADRI YARD)
  // =========================================================================
  drawYardInterlockingZoom() {
    const ctx = this.ctx;
    const panelX = 20;
    const panelY = Math.round(this.height * 0.51);
    const panelW = this.width - 40;
    const remH = this.height - panelY;

    ctx.save();
    // Sub-panel Title
    ctx.font = '700 11px Plus Jakarta Sans, sans-serif';
    ctx.fillStyle = '#00e676';
    ctx.textAlign = 'left';
    ctx.fillText('DANKAUR (DKDE) & DADRI YARD INTERLOCKING', panelX + 10, panelY + 22);

    ctx.font = '500 9px JetBrains Mono, monospace';
    ctx.fillStyle = '#64748b';
    ctx.fillText('ELECTRONIC INTERLOCKING (EI) • DFC JUNCTION & LOOP OVERTAKE BERTHS', panelX + 10, panelY + 36);

    // Track ladder coordinates
    const y1 = panelY + Math.round(remH * 0.20);   // UP Loop
    const y2 = panelY + Math.round(remH * 0.36);  // UP Main Through
    const y3 = panelY + Math.round(remH * 0.52);  // DOWN Main Through
    const y4 = panelY + Math.round(remH * 0.68);  // DOWN Loop Siding (Overtake Hold Line)
    const y5 = panelY + Math.round(remH * 0.84);  // Goods Yard / DFC Link Line

    const startX = panelX + 40;
    const endX = panelX + panelW - 40;

    // Draw Yard Tracks in crisp SCADA style
    const tracks = [
      { y: y1, name: 'UP LOOP SIDING', color: '#00d2ff' },
      { y: y2, name: 'UP MAIN (PF 1)', color: '#00d2ff' },
      { y: y3, name: 'DOWN MAIN (PF 2)', color: '#00d2ff' },
      { y: y4, name: 'DOWN LOOP SIDING (BERTH 1)', color: '#00d2ff' },
      { y: y5, name: 'DFC INTERCHANGE YARD LEAD', color: '#64748b' }
    ];

    tracks.forEach(tr => {
      ctx.beginPath();
      ctx.strokeStyle = tr.color;
      ctx.lineWidth = 2;
      ctx.moveTo(startX, tr.y);
      ctx.lineTo(endX, tr.y);
      ctx.stroke();

      ctx.font = '600 8px JetBrains Mono, monospace';
      ctx.fillStyle = '#64748b';
      ctx.textAlign = 'left';
      ctx.fillText(tr.name, startX, tr.y - 6);
    });

    // Crossover Turnout Links
    const midX = (startX + endX) / 2;

    // Crossover 101A/B (Turnout from DN Main into DN Loop for Goods Overtake)
    ctx.beginPath();
    ctx.strokeStyle = '#facc15';
    ctx.lineWidth = 2;
    ctx.moveTo(midX - 220, y3);
    ctx.lineTo(midX - 140, y4);
    ctx.lineTo(midX + 140, y4);
    ctx.lineTo(midX + 220, y3);
    ctx.stroke();

    // Turnout Point Indicators
    ctx.font = '700 8px JetBrains Mono, monospace';
    ctx.fillStyle = '#facc15';
    ctx.fillText('PT 101A [REV]', midX - 200, y3 - 8);
    ctx.fillText('PT 101B [REV]', midX + 160, y3 - 8);

    // Diamond Scissors Crossover between UP and DOWN main lines
    ctx.beginPath();
    ctx.strokeStyle = '#00d2ff';
    ctx.lineWidth = 1.5;
    ctx.moveTo(midX - 90, y2);
    ctx.lineTo(midX + 90, y3);
    ctx.moveTo(midX + 90, y2);
    ctx.lineTo(midX - 90, y3);
    ctx.stroke();

    // Interlocked Starter & Home Signals at Dankaur (Dynamically synced to live signals)
    const dkHome = this.signals.find(s => s.id === 'SIG_DN_HOME_DKDE');
    const dkStr = this.signals.find(s => s.id === 'SIG_DN_STR_DKDE');
    const dkAdv = this.signals.find(s => s.id === 'SIG_DN_ADV_DKDE');

    const getSigColor = (sig, fallback) => {
      if (!sig) return fallback;
      if (sig.is_failed || sig.aspect === 'RED') return '#ff1744';
      if (sig.aspect === 'YELLOW') return '#ff9100';
      if (sig.aspect === 'DOUBLE_YELLOW') return '#ffea00';
      if (sig.aspect === 'GREEN') return '#00e676';
      return fallback;
    };

    // Find if any train is currently in Dankaur loop or main line
    const loopTrain = this.livePositions.find(p => 
      p.direction === 'DOWN' && 
      p.current_km >= 29.0 && p.current_km <= 35.0 && 
      p.track && p.track.includes('LOOP')
    );

    const throughTrain = this.livePositions.find(p => 
      p.direction === 'DOWN' && 
      p.current_km >= 28.0 && p.current_km <= 36.0 && 
      (!p.track || !p.track.includes('LOOP')) &&
      p.status === 'RUNNING'
    );

    const sigs = [
      { x: midX - 280, y: y3 - 10, name: 'DKDE-1S (HOME)', color: getSigColor(dkHome, '#ffea00'), feather: dkHome?.route_feather_active },
      { x: midX - 150, y: y4 - 10, name: 'DKDE-L1 (LOOP STR)', color: loopTrain ? '#ff1744' : '#00e676' },
      { x: midX + 150, y: y3 - 10, name: 'DKDE-2S (MAIN STR)', color: getSigColor(dkStr, '#00e676') },
      { x: midX + 280, y: y3 - 10, name: 'DKDE-ADV (ADV STR)', color: getSigColor(dkAdv, '#00e676') },
    ];

    sigs.forEach(s => {
      ctx.fillStyle = s.color;
      ctx.shadowColor = s.color;
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(s.x, s.y, 4, 0, Math.PI * 2);
      ctx.fill();

      if (s.feather) {
        ctx.fillStyle = '#ffffff';
        ctx.shadowColor = '#ffffff';
        ctx.shadowBlur = 8;
        ctx.fillRect(s.x - 6, s.y - 7, 12, 2.5);
      }

      ctx.shadowBlur = 0;
      ctx.font = '600 7px JetBrains Mono, monospace';
      ctx.fillStyle = '#94a3b8';
      ctx.textAlign = 'center';
      ctx.fillText(s.name, s.x, s.y - 8);
    });

    ctx.save();
    // Dynamic Train Berthing in Dankaur Loop Siding
    if (loopTrain) {
      // Loop occupied track circuit in vivid red
      ctx.strokeStyle = '#ff1744';
      ctx.lineWidth = 3.5;
      ctx.shadowColor = '#ff1744';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.moveTo(midX - 120, y4);
      ctx.lineTo(midX + 120, y4);
      ctx.stroke();

      const boxW = 130;
      const boxH = 18;
      ctx.fillStyle = '#05070f';
      ctx.strokeStyle = loopTrain.color_hex || '#f59e0b';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.roundRect(midX - boxW / 2, y4 - 9, boxW, boxH, 2);
      ctx.fill();
      ctx.stroke();

      ctx.font = '800 8px JetBrains Mono, monospace';
      ctx.fillStyle = '#fef08a';
      ctx.textAlign = 'center';
      ctx.fillText(`${loopTrain.train_number} [HOLD IN LOOP]`, midX, y4 + 3);
    } else {
      ctx.font = '600 8px JetBrains Mono, monospace';
      ctx.fillStyle = '#334155';
      ctx.textAlign = 'center';
      ctx.fillText('LOOP SIDING CLEAR • NO BERTH', midX, y4 + 3);
    }

    // Dynamic Train Running Through Dankaur Main Line
    if (throughTrain) {
      const vbX = midX + 60;
      ctx.strokeStyle = '#00e676';
      ctx.lineWidth = 3.5;
      ctx.shadowColor = '#00e676';
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.moveTo(vbX - 80, y3);
      ctx.lineTo(vbX + 80, y3);
      ctx.stroke();

      ctx.fillStyle = '#05070f';
      ctx.strokeStyle = throughTrain.color_hex || '#8b5cf6';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.roundRect(vbX - 60, y3 - 9, 120, 18, 2);
      ctx.fill();
      ctx.stroke();

      ctx.font = '800 8px JetBrains Mono, monospace';
      ctx.fillStyle = '#c084fc';
      ctx.textAlign = 'center';
      ctx.fillText(`${throughTrain.train_number} [${throughTrain.current_speed_kmh}k/h]`, vbX, y3 + 3);
    }

    ctx.restore();
    ctx.restore();
  }

  handleMouseMove(mouseX, mouseY) {
    const yUpSig = Math.round(this.height * 0.19) - 12;
    const yDownSig = Math.round(this.height * 0.32) + 12;

    let hovered = null;
    for (const sig of this.signals) {
      const x = this.kmToXTop(sig.km);
      const isUp = sig.direction === 'UP';
      const y = isUp ? yUpSig : yDownSig;

      if (Math.hypot(mouseX - x, mouseY - y) < 8) {
        hovered = sig;
        break;
      }
    }

    if (this.hoveredItem !== hovered) {
      this.hoveredItem = hovered;
      this.draw();
    }
  }

  handleClick(mouseX, mouseY) {
    const yUpSig = Math.round(this.height * 0.19) - 12;
    const yDownSig = Math.round(this.height * 0.32) + 12;

    for (const sig of this.signals) {
      const x = this.kmToXTop(sig.km);
      const isUp = sig.direction === 'UP';
      const y = isUp ? yUpSig : yDownSig;

      if (Math.hypot(mouseX - x, mouseY - y) < 10) {
        this.selectedSignal = sig;
        if (window.onSignalSelected) {
          window.onSignalSelected(sig);
        }
        this.draw();
        return;
      }
    }
  }
}
