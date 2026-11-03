/** Decorative geometry only: no measurements, randomness, networking, or RAG state. */
export interface WaveHost {
  requestFrame(callback: FrameRequestCallback): number;
  cancelFrame(id: number): void;
  now(): number;
  pixelRatio: number;
  lowPower: boolean;
  hidden(): boolean;
  reducedMotion(): boolean;
  onVisibility(callback: () => void): () => void;
  onMotion(callback: () => void): () => void;
  onSize(callback: (width: number, height: number) => void): () => void;
  onIntersection(callback: (visible: boolean) => void): () => void;
}

export interface WaveColors { sage: string; emerald: string; sea: string; deep: string }

export function wavePoint(u: number, v: number, time: number, width: number, height: number, layer = 0) {
  // Independent travelling harmonics and rotating cross-sections form intersecting
  // ribbons, rather than a single centre-line arch. Time never wraps or resets.
  const phase = u * Math.PI * 2.6 - time * .28 + layer * .65;
  const rotation = u * Math.PI * 2.15 - time * .19 + layer * .95;
  const spread = .12 + .10 * Math.sin(u * 4.2 + layer * .8) ** 2;
  const spine = .63 - .19 * u + .16 * Math.sin(phase)
    + .075 * Math.sin(u * Math.PI * 4.5 + time * .16 + layer * 1.3);
  return {
    x: (u + v * .018 * Math.sin(rotation)) * width,
    y: height * (spine + v * spread * Math.cos(rotation)
      + .045 * Math.sin(v * Math.PI + phase * 1.2) + (layer - 1) * .035),
    depth: .3 + .7 * (Math.sin(rotation + v * 1.8) + 1) / 2,
  };
}

/** Owns exactly one RAF at a time. Returns an idempotent full teardown. */
export function startParticleWave(canvas: HTMLCanvasElement, host: WaveHost, colors: WaveColors): () => void {
  const context = canvas.getContext("2d", { alpha: true });
  if (!context) return () => undefined;
  let width = 0, height = 0, frame: number | null = null;
  let disposed = false, visible = true, time = 0, previous: number | null = null;
  let quality = host.lowPower ? .55 : 1, slowFrames = 0;
  const ratio = Math.min(Math.max(host.pixelRatio, 1), host.lowPower ? 1 : 1.5);

  function draw() {
    if (!context || width <= 0 || height <= 0) return;
    context.clearRect(0, 0, width, height);
    const columns = Math.round((width < 650 ? 92 : 170) * quality);
    // Back-to-front surfaces have different phases, widths, and row counts.
    for (let layer = 2; layer >= 0; layer--) {
      const rows = Math.round((24 - layer * 5) * quality);
      for (let row = 0; row < rows; row++) {
        const v = row / Math.max(1, rows - 1) * 2 - 1;
        const color = row % 11 === 0 ? colors.sage : layer === 2 ? colors.deep
          : row % 3 ? colors.emerald : colors.sea;
        context.strokeStyle = color;
        context.fillStyle = color;
        context.lineWidth = .5;
        context.globalAlpha = (.14 + .15 * (1 - Math.abs(v))) * (1 - layer * .16);
        context.beginPath();
        for (let column = 0; column < columns; column++) {
          const p = wavePoint(column / (columns - 1), v, time, width, height, layer);
          if (column === 0) context.moveTo(p.x, p.y); else context.lineTo(p.x, p.y);
        }
        context.stroke();
        context.globalAlpha = (.48 + .45 * (1 - Math.abs(v))) * (1 - layer * .12);
        context.beginPath();
        for (let column = 0; column < columns; column++) {
          const p = wavePoint(column / (columns - 1), v, time, width, height, layer);
          const radius = .55 + p.depth * .8;
          context.moveTo(p.x + radius, p.y);
          context.arc(p.x, p.y, radius, 0, Math.PI * 2);
        }
        context.fill();
        // Sparse cross-strands reveal the mesh's twisting surface without a grid.
        if (row > 0 && row % 3 === 0) {
          context.globalAlpha = .10;
          context.beginPath();
          for (let column = 4; column < columns; column += 9) {
            const u = column / (columns - 1);
            const p = wavePoint(u, v, time, width, height, layer);
            const previous = wavePoint(u, (row - 3) / (rows - 1) * 2 - 1, time, width, height, layer);
            context.moveTo(previous.x, previous.y);
            context.lineTo(p.x, p.y);
          }
          context.stroke();
        }
      }
    }
    context.globalAlpha = 1;
  }

  function stop() {
    if (frame !== null) host.cancelFrame(frame);
    frame = null;
    previous = null;
  }
  function tick(timestamp: number) {
    frame = null;
    if (disposed || host.hidden() || !visible || host.reducedMotion()) return;
    const elapsed = previous === null ? 0 : Math.min(timestamp - previous, 50);
    previous = timestamp;
    time += Math.max(0, elapsed) / 1000;
    const before = host.now();
    draw();
    slowFrames = host.now() - before > 12 || elapsed > 25 ? slowFrames + 1 : Math.max(0, slowFrames - 1);
    if (slowFrames >= 30) { quality = Math.max(.4, quality * .75); slowFrames = 0; }
    frame = host.requestFrame(tick);
  }
  function sync() {
    stop();
    if (disposed || host.hidden() || !visible || width <= 0 || height <= 0) return;
    if (host.reducedMotion()) { time = 0; draw(); }
    else frame = host.requestFrame(tick);
  }
  const unsubscribe = [
    host.onVisibility(sync), host.onMotion(sync),
    host.onSize((w, h) => {
      if (disposed) return;
      width = Math.max(0, Math.min(w, 2200));
      height = Math.max(0, Math.min(h, 700));
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      sync();
    }),
    host.onIntersection(value => { visible = value; sync(); }),
  ];
  return () => {
    if (disposed) return;
    disposed = true;
    stop();
    unsubscribe.forEach(remove => remove());
    canvas.width = 0;
    canvas.height = 0;
  };
}
