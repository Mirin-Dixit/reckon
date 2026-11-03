"use client";

import { useEffect, useRef } from "react";
import { startParticleWave, type WaveHost } from "../lib/particle-wave";

/** A decorative, continuously flowing canvas mesh. It never represents evidence. */
export function ParticleWave() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const styles = getComputedStyle(canvas);
    const color = (name: string) => styles.getPropertyValue(name).trim();
    const host: WaveHost = {
      requestFrame: callback => requestAnimationFrame(callback),
      cancelFrame: id => cancelAnimationFrame(id),
      now: () => performance.now(),
      pixelRatio: window.devicePixelRatio || 1,
      lowPower: navigator.hardwareConcurrency <= 4,
      hidden: () => document.hidden,
      reducedMotion: () => motion.matches,
      onVisibility: callback => {
        document.addEventListener("visibilitychange", callback);
        return () => document.removeEventListener("visibilitychange", callback);
      },
      onMotion: callback => {
        motion.addEventListener("change", callback);
        return () => motion.removeEventListener("change", callback);
      },
      onSize: callback => {
        const resize = () => { const rect = canvas.getBoundingClientRect(); callback(rect.width, rect.height); };
        resize();
        if (typeof ResizeObserver === "undefined") {
          window.addEventListener("resize", resize);
          return () => window.removeEventListener("resize", resize);
        }
        const observer = new ResizeObserver(resize);
        observer.observe(canvas);
        return () => observer.disconnect();
      },
      onIntersection: callback => {
        if (typeof IntersectionObserver === "undefined") return () => undefined;
        const observer = new IntersectionObserver(entries => callback(entries.some(entry => entry.isIntersecting)));
        observer.observe(canvas);
        return () => observer.disconnect();
      },
    };
    return startParticleWave(canvas, host, {
      sage: color("--wave-sage"), emerald: color("--wave-green"),
      sea: color("--wave-sea"), deep: color("--wave-deep"),
    });
  }, []);
  return <canvas ref={ref} className="particle-wave" aria-hidden="true" />;
}
