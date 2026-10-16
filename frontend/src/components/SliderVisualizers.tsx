import React, { useEffect, useRef } from 'react';

// Utility to read active CSS variable color from .app container or fallback
function getThemeColors() {
  let el: Element | null = null;
  try {
    el = document.querySelector('.app') || document.documentElement;
  } catch {
    el = null;
  }
  
  if (!el) {
    return {
      accent: '#fa7175',
      text: '#f5eedf',
      muted: '#b8a896',
      line: 'rgba(255,255,255,0.18)',
      panel: 'rgba(22, 20, 18, 0.85)',
      input: 'rgba(0, 0, 0, 0.45)',
    };
  }

  const style = getComputedStyle(el);
  return {
    accent: style.getPropertyValue('--accent').trim() || '#fa7175',
    text: style.getPropertyValue('--text').trim() || '#f5eedf',
    muted: style.getPropertyValue('--muted').trim() || '#b8a896',
    line: style.getPropertyValue('--line').trim() || 'rgba(255,255,255,0.18)',
    panel: style.getPropertyValue('--panel').trim() || 'rgba(22, 20, 18, 0.85)',
    input: style.getPropertyValue('--input').trim() || 'rgba(0, 0, 0, 0.45)',
  };
}

// Setup High-DPI canvas drawing context with exact pixel sizing
function setupCanvas(canvas: HTMLCanvasElement): {
  ctx: CanvasRenderingContext2D | null;
  width: number;
  height: number;
} {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(10, Math.floor(rect.width));
  const height = Math.max(10, Math.floor(rect.height));

  const targetW = Math.round(width * dpr);
  const targetH = Math.round(height * dpr);

  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
  }

  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  return { ctx, width, height };
}

// ============================================================================
// Visualizer 1: Orbital Face Constellation (distance_threshold: 0.30 - 0.65)
// Represents cluster cohesion and radius:
// - At 0.30 (strict): 1 solitary node spinning tightly around the nucleus.
// - Moving to right (up to 0.65): node count increases dynamically from 1 to 10
//   with expanding orbital radii, glowing filaments, and travelling energy pulses.
// ============================================================================
export const OrbitalClusterVisualizer: React.FC<{ value: number }> = ({ value }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let animId: number;
    let time = 0;

    const render = () => {
      const { ctx, width, height } = setupCanvas(canvas);
      if (!ctx || width <= 0 || height <= 0) {
        animId = requestAnimationFrame(render);
        return;
      }

      ctx.clearRect(0, 0, width, height);
      const colors = getThemeColors();

      const centerX = width / 2;
      const centerY = height / 2;

      // Normalization: 0.30 to 0.65 -> 0.0 to 1.0
      const norm = Math.max(0, Math.min(1, (value - 0.30) / (0.65 - 0.30)));
      
      // Node count: Exactly 1 node at minimum, scaling up to 10 nodes at maximum!
      const nodeCount = Math.round(1 + norm * 9);
      const baseRadius = 16 + norm * Math.min(width * 0.28, height * 0.35);

      time += 0.02 + norm * 0.015;

      // 1. Draw concentric orbit track rings
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius * 0.6, 0, Math.PI * 2);
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 4]);
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius, 0, Math.PI * 2);
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // 2. Compute dynamic node coordinates in 3D-angled orbit
      const nodes: Array<{ x: number; y: number; id: number }> = [];
      for (let i = 0; i < nodeCount; i++) {
        const tier = i % 2 === 0 ? 0.65 : 1.0;
        const speed = (i % 2 === 0 ? 1 : -0.8) * (0.75 + (i * 0.12));
        const angle = (i * (Math.PI * 2 / nodeCount)) + (time * speed);
        const r = baseRadius * tier + Math.sin(time * 2 + i) * 2;
        const x = centerX + Math.cos(angle) * r;
        const y = centerY + Math.sin(angle) * (r * 0.72); // angled perspective
        nodes.push({ x, y, id: i + 1 });
      }

      // 3. Draw luminous interconnecting filament lines between nodes
      let linkCount = 0;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.hypot(dx, dy);
          const maxLinkDist = baseRadius * 1.5;

          if (dist < maxLinkDist) {
            linkCount++;
            const alpha = (1 - dist / maxLinkDist) * (0.3 + norm * 0.5);
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = colors.accent;
            ctx.globalAlpha = alpha;
            ctx.lineWidth = 1.2;
            ctx.stroke();
            ctx.globalAlpha = 1.0;

            // Traveling data photon on chord
            const photonT = (time * 1.8 + (i * 2 + j)) % 1;
            const px = nodes[i].x + (nodes[j].x - nodes[i].x) * photonT;
            const py = nodes[i].y + (nodes[j].y - nodes[i].y) * photonT;
            ctx.beginPath();
            ctx.arc(px, py, 1.4, 0, Math.PI * 2);
            ctx.fillStyle = colors.text;
            ctx.fill();
          }
        }

        // Connecting tether line to seed anchor nucleus
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(nodes[i].x, nodes[i].y);
        ctx.strokeStyle = colors.line;
        ctx.globalAlpha = 0.22;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.globalAlpha = 1.0;
      }

      // 4. Draw Orbiting Face Nodes
      nodes.forEach((node) => {
        // Outer halo
        ctx.beginPath();
        ctx.arc(node.x, node.y, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = colors.accent;
        ctx.globalAlpha = 0.85;
        ctx.fill();
        ctx.globalAlpha = 1.0;

        // Inner core
        ctx.beginPath();
        ctx.arc(node.x, node.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = colors.text;
        ctx.fill();

        // Node index stamp
        ctx.fillStyle = colors.muted;
        ctx.font = '9px "JetBrains Mono", monospace';
        ctx.fillText(`F${node.id}`, node.x + 5, node.y - 3);
      });

      // 5. Draw Center Nucleus (Anchor Seed Face)
      const nucleusPulse = Math.sin(time * 3.5) * 1.5;
      ctx.beginPath();
      ctx.arc(centerX, centerY, 7.5 + nucleusPulse, 0, Math.PI * 2);
      ctx.fillStyle = colors.accent;
      ctx.globalAlpha = 0.25;
      ctx.fill();
      ctx.globalAlpha = 1.0;

      ctx.beginPath();
      ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
      ctx.fillStyle = colors.accent;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(centerX, centerY, 2.2, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      // Nucleus label
      ctx.fillStyle = colors.text;
      ctx.font = '8px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText('SEED', centerX, centerY + 14);

      // HUD Stats Readout
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillStyle = colors.muted;
      ctx.textAlign = 'left';
      ctx.fillText(`CLUSTER: ${nodeCount} ${nodeCount === 1 ? 'NODE' : 'NODES'}`, 8, 14);
      ctx.textAlign = 'right';
      ctx.fillStyle = colors.accent;
      ctx.fillText(`RADIUS: ${Math.round(baseRadius)}px`, width - 8, 14);

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [value]);

  return (
    <div className="w-full h-full relative overflow-hidden rounded bg-[var(--input)] border border-[var(--panel-border)] flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
    </div>
  );
};

// ============================================================================
// Visualizer 2: Gravitational Centroid Fusion (merge_threshold: 0.30 - 0.60)
// Represents automatic second-pass duplicate cluster consolidation:
// - Low (0.30): Cluster A and Cluster B remain separated by a repulsive barrier.
// - As slider moves right: Gravity pulls the two centroids together, arcing plasma
//   streams bridge between them, and above 0.48 they fuse into a single glowing unified core!
// ============================================================================
export const MergeFusionVisualizer: React.FC<{ value: number }> = ({ value }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let animId: number;
    let time = 0;

    const render = () => {
      const { ctx, width, height } = setupCanvas(canvas);
      if (!ctx || width <= 0 || height <= 0) {
        animId = requestAnimationFrame(render);
        return;
      }

      ctx.clearRect(0, 0, width, height);
      const colors = getThemeColors();

      const centerY = height / 2;
      const centerX = width / 2;

      // Normalization: 0.30 to 0.60 -> 0.0 to 1.0
      const norm = Math.max(0, Math.min(1, (value - 0.30) / (0.60 - 0.30)));
      const maxSeparation = width * 0.30;
      const separation = (1 - norm) * maxSeparation;
      const isFused = value >= 0.48;

      time += 0.025;

      const posA = centerX - separation;
      const posB = centerX + separation;

      // Gravitational ripple rings for Cluster A
      for (let r = 10; r <= 28; r += 9) {
        ctx.beginPath();
        ctx.arc(posA, centerY, r + Math.sin(time * 2 + r) * 1.5, 0, Math.PI * 2);
        ctx.strokeStyle = colors.line;
        ctx.lineWidth = 1;
        ctx.globalAlpha = Math.max(0.1, 0.4 - (r / 35));
        ctx.stroke();
      }

      // Gravitational ripple rings for Cluster B
      for (let r = 10; r <= 28; r += 9) {
        ctx.beginPath();
        ctx.arc(posB, centerY, r + Math.sin(time * 2.5 + r) * 1.5, 0, Math.PI * 2);
        ctx.strokeStyle = colors.line;
        ctx.lineWidth = 1;
        ctx.globalAlpha = Math.max(0.1, 0.4 - (r / 35));
        ctx.stroke();
      }
      ctx.globalAlpha = 1.0;

      if (isFused) {
        // FUSED STATE: Radiant unified core & plasma flux
        const glowPulse = Math.sin(time * 4) * 3;

        const gradient = ctx.createRadialGradient(centerX, centerY, 4, centerX, centerY, 34 + glowPulse);
        gradient.addColorStop(0, colors.accent);
        gradient.addColorStop(0.55, `${colors.accent}44`);
        gradient.addColorStop(1, 'transparent');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 36 + glowPulse, 0, Math.PI * 2);
        ctx.fill();

        // High-energy fusion bridge
        ctx.beginPath();
        ctx.moveTo(posA, centerY);
        ctx.lineTo(posB, centerY);
        ctx.strokeStyle = colors.accent;
        ctx.lineWidth = 8 + Math.sin(time * 5) * 2;
        ctx.stroke();

        // Swirling plasma particles
        for (let p = 0; p < 8; p++) {
          const pt = (time * 2 + p * 0.25) % 1;
          const px = posA + (posB - posA) * pt;
          const py = centerY + Math.sin(pt * Math.PI * 2 + time * 3) * 6;
          ctx.beginPath();
          ctx.arc(px, py, 1.8, 0, Math.PI * 2);
          ctx.fillStyle = colors.text;
          ctx.fill();
        }
      } else {
        // SEPARATE STATE: Central dashed boundary
        ctx.beginPath();
        ctx.moveTo(centerX, 18);
        ctx.lineTo(centerX, height - 18);
        ctx.strokeStyle = colors.line;
        ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1.2;
        ctx.stroke();
        ctx.setLineDash([]);

        // Repulsion arrow indicators
        const arrowOffset = Math.sin(time * 3) * 2.5;
        ctx.font = '11px "JetBrains Mono", monospace';
        ctx.fillStyle = colors.muted;
        ctx.textAlign = 'center';
        ctx.fillText('◂', posA + 12 - arrowOffset, centerY + 4);
        ctx.fillText('▸', posB - 12 + arrowOffset, centerY + 4);
      }

      // Draw Cluster A Centroid Core
      ctx.beginPath();
      ctx.arc(posA, centerY, 7.5, 0, Math.PI * 2);
      ctx.fillStyle = colors.accent;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(posA, centerY, 3, 0, Math.PI * 2);
      ctx.fillStyle = colors.text;
      ctx.fill();

      // Draw Cluster B Centroid Core
      ctx.beginPath();
      ctx.arc(posB, centerY, 7.5, 0, Math.PI * 2);
      ctx.fillStyle = isFused ? colors.accent : '#d97706';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(posB, centerY, 3, 0, Math.PI * 2);
      ctx.fillStyle = colors.text;
      ctx.fill();

      // Cluster Labels
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillStyle = colors.text;
      ctx.textAlign = 'center';
      ctx.fillText('CLUSTER A', posA, centerY - 14);
      ctx.fillText('CLUSTER B', posB, centerY - 14);

      // HUD Status
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.textAlign = 'left';
      ctx.fillStyle = isFused ? colors.accent : colors.muted;
      ctx.fillText(isFused ? 'STATUS: FUSED UNIFIED' : 'STATUS: SEPARATE CLUSTERS', 8, 14);
      ctx.textAlign = 'right';
      ctx.fillStyle = colors.muted;
      ctx.fillText(`CUTOFF: ${value.toFixed(2)}`, width - 8, 14);

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [value]);

  return (
    <div className="w-full h-full relative overflow-hidden rounded bg-[var(--input)] border border-[var(--panel-border)] flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
    </div>
  );
};

// ============================================================================
// Visualizer 3: Sonar Radar Hologram (maybe_threshold: 0.50 - 0.75)
// Represents suggestion candidate range:
// Higher threshold sweeps a wider radar horizon, pinging and flagging candidate pairs.
// ============================================================================
export const RadarSuggestionVisualizer: React.FC<{ value: number }> = ({ value }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let animId: number;
    let sweepAngle = 0;

    // Fixed candidates on the radar plane at normalized distances
    const candidates = [
      { id: 'P1', distVal: 0.52, angle: 0.85, matchPct: 94 },
      { id: 'P2', distVal: 0.58, angle: 2.15, matchPct: 86 },
      { id: 'P3', distVal: 0.63, angle: 3.70, matchPct: 79 },
      { id: 'P4', distVal: 0.67, angle: 4.80, matchPct: 71 },
      { id: 'P5', distVal: 0.71, angle: 1.45, matchPct: 63 },
      { id: 'P6', distVal: 0.74, angle: 5.60, matchPct: 55 },
    ];

    const render = () => {
      const { ctx, width, height } = setupCanvas(canvas);
      if (!ctx || width <= 0 || height <= 0) {
        animId = requestAnimationFrame(render);
        return;
      }

      ctx.clearRect(0, 0, width, height);
      const colors = getThemeColors();

      const centerX = width / 2;
      const centerY = height / 2;
      const maxRadarRadius = Math.min(width, height) * 0.44;

      sweepAngle = (sweepAngle + 0.035) % (Math.PI * 2);

      // Normalization: 0.50 to 0.75 -> 0.0 to 1.0
      const norm = Math.max(0, Math.min(1, (value - 0.50) / (0.75 - 0.50)));
      const activeSweepRadius = maxRadarRadius * (0.35 + norm * 0.65);

      // Radar concentric range rings
      [0.35, 0.65, 1.0].forEach((ratio, idx) => {
        ctx.beginPath();
        ctx.arc(centerX, centerY, maxRadarRadius * ratio, 0, Math.PI * 2);
        ctx.strokeStyle = colors.line;
        ctx.lineWidth = 1;
        ctx.setLineDash([idx === 2 ? 0 : 2, 3]);
        ctx.stroke();
      });
      ctx.setLineDash([]);

      // Crosshairs
      ctx.beginPath();
      ctx.moveTo(centerX - maxRadarRadius, centerY);
      ctx.lineTo(centerX + maxRadarRadius, centerY);
      ctx.moveTo(centerX, centerY - maxRadarRadius);
      ctx.lineTo(centerX, centerY + maxRadarRadius);
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 0.8;
      ctx.globalAlpha = 0.4;
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      // Active Detection Horizon Circle (Scales with Slider)
      ctx.beginPath();
      ctx.arc(centerX, centerY, activeSweepRadius, 0, Math.PI * 2);
      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 1.6;
      ctx.globalAlpha = 0.65;
      ctx.stroke();
      ctx.fillStyle = colors.accent;
      ctx.globalAlpha = 0.07;
      ctx.fill();
      ctx.globalAlpha = 1.0;

      // Radar Sweep Fan Beam
      const sweepSegments = 16;
      for (let i = 0; i < sweepSegments; i++) {
        const segAngle = sweepAngle - (i * 0.035);
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, activeSweepRadius, segAngle - 0.035, segAngle);
        ctx.closePath();
        ctx.fillStyle = colors.accent;
        ctx.globalAlpha = (1 - i / sweepSegments) * 0.22;
        ctx.fill();
      }
      ctx.globalAlpha = 1.0;

      // Leading Radar Sweep Line
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + Math.cos(sweepAngle) * activeSweepRadius,
        centerY + Math.sin(sweepAngle) * activeSweepRadius
      );
      ctx.strokeStyle = colors.text;
      ctx.lineWidth = 1.6;
      ctx.stroke();

      // Render Candidate Pings
      let detectedCount = 0;
      candidates.forEach((cand) => {
        const candNorm = (cand.distVal - 0.50) / (0.75 - 0.50);
        const candR = maxRadarRadius * (0.35 + candNorm * 0.65);
        const cx = centerX + Math.cos(cand.angle) * candR;
        const cy = centerY + Math.sin(cand.angle) * candR;
        const isDetected = value >= cand.distVal;

        if (isDetected) {
          detectedCount++;
          let diff = (sweepAngle - cand.angle) % (Math.PI * 2);
          if (diff < 0) diff += Math.PI * 2;
          const isPinged = diff < 0.6;

          // Target reticle
          ctx.beginPath();
          ctx.arc(cx, cy, isPinged ? 6 : 3.8, 0, Math.PI * 2);
          ctx.fillStyle = isPinged ? colors.text : colors.accent;
          ctx.fill();

          if (isPinged) {
            ctx.beginPath();
            ctx.arc(cx, cy, 9.5, 0, Math.PI * 2);
            ctx.strokeStyle = colors.accent;
            ctx.lineWidth = 1.2;
            ctx.stroke();

            // Match percentage stamp
            ctx.font = '9px "JetBrains Mono", monospace';
            ctx.fillStyle = colors.text;
            ctx.fillText(`${cand.matchPct}%`, cx + 8, cy - 2);
          }
        } else {
          // Inactive target outside horizon
          ctx.beginPath();
          ctx.arc(cx, cy, 2.2, 0, Math.PI * 2);
          ctx.fillStyle = colors.line;
          ctx.globalAlpha = 0.4;
          ctx.fill();
          ctx.globalAlpha = 1.0;
        }
      });

      // HUD Readout
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillStyle = colors.muted;
      ctx.textAlign = 'left';
      ctx.fillText(`SWEEP CAP: ${value.toFixed(2)}`, 8, 14);
      ctx.textAlign = 'right';
      ctx.fillStyle = colors.accent;
      ctx.fillText(`CANDIDATES: ${detectedCount} PAIRS`, width - 8, 14);

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [value]);

  return (
    <div className="w-full h-full relative overflow-hidden rounded bg-[var(--input)] border border-[var(--panel-border)] flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
    </div>
  );
};

// ============================================================================
// Visualizer 4: Quantum Laser Collision Shield (same_photo_merge_max: 0.20 - 0.50)
// Prevents two faces in the same photograph from being assigned to the same person.
// Lower = strict impenetrable forcefield; Higher = relaxed tolerance.
// ============================================================================
export const PhotoCollisionShieldVisualizer: React.FC<{ value: number }> = ({ value }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    let animId: number;
    let time = 0;

    const render = () => {
      const { ctx, width, height } = setupCanvas(canvas);
      if (!ctx || width <= 0 || height <= 0) {
        animId = requestAnimationFrame(render);
        return;
      }

      ctx.clearRect(0, 0, width, height);
      const colors = getThemeColors();

      time += 0.03;

      const centerX = width / 2;
      const centerY = height / 2;

      // Normalization: 0.20 (Strict Guard) to 0.50 (Relaxed Guard)
      const norm = Math.max(0, Math.min(1, (value - 0.20) / (0.50 - 0.20)));
      const isStrict = value <= 0.40;
      const shieldOpacity = 1 - norm * 0.65;

      // Viewfinder Photo Frame
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.strokeRect(18, 12, width - 36, height - 24);

      // Photo Frame Corner Brackets
      const bLen = 6;
      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 2;
      // Top-Left
      ctx.beginPath();
      ctx.moveTo(18, 12 + bLen); ctx.lineTo(18, 12); ctx.lineTo(18 + bLen, 12);
      ctx.stroke();
      // Top-Right
      ctx.beginPath();
      ctx.moveTo(width - 18 - bLen, 12); ctx.lineTo(width - 18, 12); ctx.lineTo(width - 18, 12 + bLen);
      ctx.stroke();
      // Bottom-Left
      ctx.beginPath();
      ctx.moveTo(18, height - 12 - bLen); ctx.lineTo(18, height - 12); ctx.lineTo(18 + bLen, height - 12);
      ctx.stroke();
      // Bottom-Right
      ctx.beginPath();
      ctx.moveTo(width - 18 - bLen, height - 12); ctx.lineTo(width - 18, height - 12); ctx.lineTo(width - 18, height - 12 - bLen);
      ctx.stroke();

      // Face #1 (Left Avatar Frame)
      const faceLeftX = Math.max(48, width * 0.2);
      ctx.fillStyle = 'rgba(255,255,255,0.05)';
      ctx.fillRect(faceLeftX - 16, centerY - 20, 32, 40);
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.strokeRect(faceLeftX - 16, centerY - 20, 32, 40);

      // Face silhouette icon left
      ctx.beginPath();
      ctx.arc(faceLeftX, centerY - 5, 6, 0, Math.PI * 2);
      ctx.fillStyle = colors.text;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(faceLeftX, centerY + 11, 9, Math.PI, 0);
      ctx.fill();

      // Face #2 (Right Avatar Frame)
      const faceRightX = Math.min(width - 48, width * 0.8);
      ctx.fillStyle = 'rgba(255,255,255,0.05)';
      ctx.fillRect(faceRightX - 16, centerY - 20, 32, 40);
      ctx.strokeStyle = colors.line;
      ctx.lineWidth = 1;
      ctx.strokeRect(faceRightX - 16, centerY - 20, 32, 40);

      // Face silhouette icon right
      ctx.beginPath();
      ctx.arc(faceRightX, centerY - 5, 6, 0, Math.PI * 2);
      ctx.fillStyle = colors.text;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(faceRightX, centerY + 11, 9, Math.PI, 0);
      ctx.fill();

      // Laser Forcefield / Quantum Shield (Down the Middle)
      const shieldTop = 14;
      const shieldBottom = height - 14;

      if (isStrict) {
        // STRICT GUARD: Impenetrable laser barrier with sparks and pulse
        const laserPulse = Math.sin(time * 6) * 1.5;

        // Outer glow barrier
        ctx.beginPath();
        ctx.moveTo(centerX, shieldTop);
        ctx.lineTo(centerX, shieldBottom);
        ctx.strokeStyle = colors.accent;
        ctx.lineWidth = 6 + laserPulse;
        ctx.globalAlpha = 0.25 * shieldOpacity;
        ctx.stroke();

        // Core laser beam
        ctx.beginPath();
        ctx.moveTo(centerX, shieldTop);
        ctx.lineTo(centerX, shieldBottom);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.9 * shieldOpacity;
        ctx.stroke();
        ctx.globalAlpha = 1.0;

        // Hexagonal defense nodes on the beam
        for (let y = shieldTop + 8; y <= shieldBottom - 8; y += 14) {
          const hexOffset = Math.sin(time * 4 + y) * 1.5;
          ctx.beginPath();
          ctx.arc(centerX + hexOffset, y, 3, 0, Math.PI * 2);
          ctx.fillStyle = colors.accent;
          ctx.fill();
        }

        // Deflection spark burst
        const sparkTime = (time * 3) % 2;
        if (sparkTime < 0.8) {
          const sparkY = centerY + Math.sin(time * 5) * 12;
          for (let s = 0; s < 4; s++) {
            const angle = Math.PI + (s - 1.5) * 0.4;
            ctx.beginPath();
            ctx.moveTo(centerX, sparkY);
            ctx.lineTo(centerX + Math.cos(angle) * 10 * sparkTime, sparkY + Math.sin(angle) * 10 * sparkTime);
            ctx.strokeStyle = colors.text;
            ctx.lineWidth = 1.2;
            ctx.stroke();
          }
        }
      } else {
        // RELAXED GUARD: Permeable dashed barrier with warning amber
        ctx.beginPath();
        ctx.moveTo(centerX, shieldTop);
        ctx.lineTo(centerX, shieldBottom);
        ctx.strokeStyle = '#f59e0b';
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.6;
        ctx.globalAlpha = 0.65;
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1.0;

        // Flux leakage connecting line
        ctx.beginPath();
        ctx.moveTo(faceLeftX + 16, centerY);
        ctx.lineTo(faceRightX - 16, centerY);
        ctx.strokeStyle = '#f59e0b';
        ctx.setLineDash([2, 5]);
        ctx.lineWidth = 1;
        ctx.globalAlpha = 0.4;
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1.0;
      }

      // Micro Labels
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.fillStyle = colors.muted;
      ctx.textAlign = 'center';
      ctx.fillText('FACE A', faceLeftX, centerY + 28);
      ctx.fillText('FACE B', faceRightX, centerY + 28);

      // HUD Status
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.textAlign = 'left';
      ctx.fillStyle = isStrict ? colors.accent : '#f59e0b';
      ctx.fillText(isStrict ? 'SHIELD: LOCKED (SAFE)' : 'SHIELD: PERMEABLE', 8, 14);
      ctx.textAlign = 'right';
      ctx.fillStyle = colors.muted;
      ctx.fillText(`GUARD: ${value.toFixed(2)}`, width - 8, 14);

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [value]);

  return (
    <div className="w-full h-full relative overflow-hidden rounded bg-[var(--input)] border border-[var(--panel-border)] flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
    </div>
  );
};

// ============================================================================
// Visualizer 5: Asset Dimension Scale Preview (Thumb & Face Crop Size)
// ============================================================================
export const DimensionPreviewVisualizer: React.FC<{
  thumbSize: number;
  faceCropSize: number;
}> = ({ thumbSize, faceCropSize }) => {
  return (
    <div className="flex items-center justify-around p-2.5 rounded bg-[var(--input)] border border-[var(--panel-border)]">
      {/* Thumbnail scale box */}
      <div className="flex items-center gap-3">
        <div
          className="border-2 border-[var(--accent)] bg-[var(--face-box-bg)] flex items-center justify-center relative transition-all duration-200"
          style={{
            width: `${Math.round(thumbSize / 9)}px`,
            height: `${Math.round(thumbSize / 9)}px`,
            maxWidth: '54px',
            maxHeight: '54px',
            boxShadow: '2px 2px 0px var(--line)',
          }}
          title={`Thumbnail: ${thumbSize}x${thumbSize}px`}
        >
          <span className="text-xs font-mono font-extrabold text-[var(--accent)]">
            {thumbSize}
          </span>
        </div>
        <div className="text-sm leading-tight">
          <span className="block font-bold text-[var(--text)]">Thumbnail</span>
          <span className="text-[var(--muted)] font-mono text-xs">{thumbSize}x{thumbSize}px</span>
        </div>
      </div>

      <div className="h-8 w-px bg-[var(--line)]" />

      {/* Face crop scale box */}
      <div className="flex items-center gap-3">
        <div
          className="border-2 border-[var(--line)] bg-[var(--input)] rounded-full flex items-center justify-center relative transition-all duration-200"
          style={{
            width: `${Math.round(faceCropSize / 7)}px`,
            height: `${Math.round(faceCropSize / 7)}px`,
            maxWidth: '44px',
            maxHeight: '44px',
            boxShadow: '1px 1px 0px var(--line)',
          }}
          title={`Face Crop: ${faceCropSize}x${faceCropSize}px`}
        >
          <span className="text-xs font-mono font-bold text-[var(--text)]">
            {faceCropSize}
          </span>
        </div>
        <div className="text-sm leading-tight">
          <span className="block font-bold text-[var(--text)]">Face Crop</span>
          <span className="text-[var(--muted)] font-mono text-xs">{faceCropSize}x{faceCropSize}px</span>
        </div>
      </div>
    </div>
  );
};
