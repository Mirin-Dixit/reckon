import test from "node:test";
import assert from "node:assert/strict";
import { startParticleWave, wavePoint, type WaveHost } from "../lib/particle-wave";

function harness(options: { reduced?: boolean; lowPower?: boolean; noContext?: boolean } = {}) {
  const frames = new Map<number, FrameRequestCallback>();
  let next = 0, hidden = false, reduced = !!options.reduced, clock = 0;
  let draws = 0, particles = 0, removed = 0;
  let visibility = () => {}, motion = () => {};
  let size: (width: number, height: number) => void = () => {};
  let intersection: (visible: boolean) => void = () => {};
  const context = {
    clearRect: () => { draws++; }, setTransform: () => {}, beginPath: () => {},
    moveTo: () => {}, lineTo: () => {}, stroke: () => {}, fill: () => {},
    arc: () => { particles++; },
  };
  const canvas = { width: 0, height: 0, getContext: () => options.noContext ? null : context } as unknown as HTMLCanvasElement;
  const host: WaveHost = {
    requestFrame: callback => { frames.set(++next, callback); return next; },
    cancelFrame: id => { frames.delete(id); }, now: () => clock,
    pixelRatio: 4, lowPower: !!options.lowPower,
    hidden: () => hidden, reducedMotion: () => reduced,
    onVisibility: callback => { visibility = callback; return () => { removed++; }; },
    onMotion: callback => { motion = callback; return () => { removed++; }; },
    onSize: callback => { size = callback; callback(1000, 340); return () => { removed++; }; },
    onIntersection: callback => { intersection = callback; return () => { removed++; }; },
  };
  const dispose = startParticleWave(canvas, host, { sage: "#b5e5c6", emerald: "#46dc8c", sea: "#39bca2", deep: "#168360" });
  return {
    canvas, frames, dispose,
    get draws() { return draws; }, get particles() { return particles; }, get removed() { return removed; },
    step(delta = 16.67) { clock += delta; const callbacks = [...frames.values()]; frames.clear(); callbacks.forEach(callback => callback(clock)); },
    hide(value: boolean) { hidden = value; visibility(); },
    reduce(value: boolean) { reduced = value; motion(); },
    intersect(value: boolean) { intersection(value); },
    resize: (w: number, h: number) => size(w, h),
  };
}

test("wave geometry changes continuously without a finite animation duration or wrapping time", () => {
  for (const time of [0, 1, 60, 3600]) {
    const p = wavePoint(.62, .3, time, 1440, 340);
    const next = wavePoint(.62, .3, time + .016, 1440, 340);
    assert.notEqual(p.y, next.y);
    assert.ok(Math.abs(p.y - next.y) < 2);
    assert.ok(Number.isFinite(p.y));
  }
  const h = harness();
  for (let i = 0; i < 240; i++) { h.step(); assert.equal(h.frames.size, 1); }
  assert.equal(h.draws, 240);
  h.dispose();
});

test("hidden and offscreen waves stop scheduling; visibility resumes exactly one loop", () => {
  const h = harness(); h.step();
  h.hide(true); assert.equal(h.frames.size, 0);
  h.step(); assert.equal(h.draws, 1);
  h.hide(false); assert.equal(h.frames.size, 1);
  h.intersect(false); assert.equal(h.frames.size, 0);
  h.intersect(true); h.intersect(true); assert.equal(h.frames.size, 1);
  h.dispose();
});

test("reduced motion draws a static wave and responds to preference changes", () => {
  const h = harness({ reduced: true });
  assert.equal(h.draws, 1); assert.equal(h.frames.size, 0);
  h.step(); assert.equal(h.draws, 1);
  h.reduce(false); h.step(); assert.equal(h.frames.size, 1);
  h.reduce(true); assert.equal(h.frames.size, 0); assert.equal(h.draws, 3);
  h.dispose();
});

test("unmount cancels RAF, disconnects all subscriptions and releases the canvas", () => {
  const h = harness(); h.dispose(); h.dispose();
  assert.equal(h.frames.size, 0); assert.equal(h.removed, 4);
  assert.equal(h.canvas.width, 0); assert.equal(h.canvas.height, 0);
  h.resize(500, 300); h.hide(false); h.step(); assert.equal(h.frames.size, 0);
});

test("DPR and backing buffer are capped; zero-size surfaces do not animate", () => {
  const h = harness();
  assert.equal(h.canvas.width, 1500);
  h.resize(10000, 10000); assert.equal(h.canvas.width, 3300); assert.equal(h.canvas.height, 1050);
  h.resize(0, 0); assert.equal(h.frames.size, 0);
  h.resize(390, 230); assert.equal(h.frames.size, 1);
  h.dispose();
});

test("low-power devices use fewer particles and sustained slow frames lower quality", () => {
  const normal = harness(), low = harness({ lowPower: true });
  normal.step(); low.step();
  const initialParticles = normal.particles;
  assert.ok(low.particles < normal.particles);
  assert.equal(low.canvas.width, 1000);
  for (let i = 0; i < 40; i++) normal.step(33);
  const before = normal.particles; normal.step();
  assert.ok(normal.particles - before < initialParticles);
  normal.dispose(); low.dispose();
});

test("a browser without Canvas support fails quietly", () => {
  const h = harness({ noContext: true }); assert.equal(h.frames.size, 0); h.dispose();
});


test("three twisting mesh layers span the hero and occupy substantial vertical space", () => {
  for (const time of [0, 8, 24]) {
    const ys: number[] = [];
    const xs: number[] = [];
    for (let layer = 0; layer < 3; layer++) {
      for (let column = 0; column <= 100; column++) {
        for (const v of [-1, 0, 1]) {
          const p = wavePoint(column / 100, v, time, 1440, 370, layer);
          xs.push(p.x); ys.push(p.y);
        }
      }
    }
    assert.ok(Math.max(...xs) - Math.min(...xs) >= 1440);
    assert.ok(Math.max(...ys) - Math.min(...ys) > 370 * .5);
  }
  const surfaces = [0, 1, 2].map(layer => wavePoint(.6, .5, 0, 1440, 370, layer).y);
  assert.equal(new Set(surfaces.map(y => Math.round(y))).size, 3);
});
