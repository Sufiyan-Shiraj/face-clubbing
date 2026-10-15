import React, { useEffect, useRef } from 'react';

// Utility to read active CSS variable color or fallback
function getThemeColor(varName: string, fallback: string): string {
  try {
    const val = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    return val || fallback;
  } catch {
    return fallback;
  }
}

// ============================================================================
// Visualizer 1: Orbital Face Constellation (distance_threshold: 0.30 - 0.65)
// Represents cluster cohesion and radius: higher distance = looser, larger cluster
// with more orbiting interconnected face nodes.
// ============================================================================
export const OrbitalClusterVisualizer: React.FC<{ value: number }> = ({ value }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof canvas.getContext !== 'function') return;
    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext('2d');
    } catch {
      return;
    }
    if (!ctx) return;

    let animId: number;
    let time = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const accent = getThemeColor('--accent', '#fa7175');
      const text = getThemeColor('--text', '#f5eedf');
      const muted = getThemeColor('--muted', '#b8a896');
      const line = getThemeColor('--line', 'rgba(255,255,255,0.15)');

      const centerX = width / 2;
      const centerY = height / 2;

      // Normalization: 0.30 to 0.65 -> 0.0 to 1.0
      const norm = Math.max(0, Math.min(1, (value - 0.30) / (0.65 - 0.30)));
      // Node count: 2 (tight/strict) to 8 (loose/inclusive)
      const nodeCount = Math.round(2 + norm * 6);
      const baseRadius = 18 + norm * 18;

      time += 0.02 + norm * 0.015;

      // Draw faint orbit tracks
      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius * 0.65, 0, Math.PI * 2);
      ctx.strokeStyle = line;
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 4]);
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(centerX, centerY, baseRadius, 0, Math.PI * 2);
      ctx.strokeStyle = line;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Compute node positions
      const nodes: Array<{ x: number; y: number; r: number }> = [];
      for (let i = 0; i < nodeCount; i++) {
        // Multi-tier orbital radii
        const tier = i % 2 === 0 ? 0.72 : 1.0;
        const speed = (i % 2 === 0 ? 1 : -0.75) * (0.8 + (i * 0.15));
        const angle = (i * (Math.PI * 2 / nodeCount)) + (time * speed);
        const r = baseRadius * tier + Math.sin(time * 2 + i) * 2;
        const x = centerX + Math.cos(angle) * r;
        const y = centerY + Math.sin(angle) * (r * 0.75); // slight 3D perspective slant
        nodes.push({ x, y, r });
      }

      // Draw interconnecting filament lines between nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dist = Math.hypot(dx, dy);
          const maxLinkDist = baseRadius * 1.6;

          if (dist < maxLinkDist) {
            const alpha = (1 - dist / maxLinkDist) * (0.35 + norm * 0.45);
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.strokeStyle = accent;
            ctx.globalAlpha = alpha;
            ctx.lineWidth = 1.2;
            ctx.stroke();
            ctx.globalAlpha = 1.0;

            // Traveling energy particle on connection chord
            const particleProgress = (time * 1.5 + (i * 3 + j)) % 1;
            const px = nodes[i].x + (nodes[j].x - nodes[i].x) * particleProgress;
            const py = nodes[i].y + (nodes[j].y - nodes[i].y) * particleProgress;
            ctx.beginPath();
            ctx.arc(px, py, 1.2, 0, Math.PI * 2);
            ctx.fillStyle = text;
            ctx.fill();
          }
        }

        // Connect to center nucleus
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(nodes[i].x, nodes[i].y);
        ctx.strokeStyle = line;
        ctx.globalAlpha = 0.25;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.globalAlpha = 1.0;
      }

      // Draw Orbiting Nodes
      nodes.forEach((node, idx) => {
        // Outer halo
        ctx.beginPath();
        ctx.arc(node.x, node.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = accent;
        ctx.globalAlpha = 0.85;
        ctx.fill();
        ctx.globalAlpha = 1.0;

        // Inner core
        ctx.beginPath();
        ctx.arc(node.x, node.y, 2, 0, Math.PI * 2);
        ctx.fillStyle = text;
        ctx.fill();

        // Node index micro-tag
        ctx.fillStyle = muted;
        ctx.font = '8px "JetBrains Mono", monospace';
        ctx.fillText(`F${idx + 1}`, node.x + 5, node.y - 3);
      });

      // Draw Center Nucleus (Seed Face Anchor)
      const nucleusPulse = Math.sin(time * 3) * 1.5;
      ctx.beginPath();
      ctx.arc(centerX, centerY, 7 + nucleusPulse, 0, Math.PI * 2);
      ctx.fillStyle = accent;
      ctx.globalAlpha = 0.3;
      ctx.fill();
      ctx.globalAlpha = 1.0;

      ctx.beginPath();
      ctx.arc(centerX, centerY, 5, 0, Math.PI * 2);
      ctx.fillStyle = accent;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(centerX, centerY, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      // Mini HUD stats
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.fillStyle = muted;
      ctx.textAlign = 'left';
      ctx.fillText(`ORBIT NODES: ${nodeCount}`, 8, 14);
      ctx.textAlign = 'right';
      ctx.fillText(`RADIUS: ${(baseRadius).toFixed(0)}px`, width - 8, 14);

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
        width={280}
        height={85}
        className="w-full h-full block"
      />
    </div>
  );
};

// ============================================================================
// Visualizer 2: Gravitational Centroid Fusion (merge_threshold: 0.30 - 0.60)
// Represents automatic second-pass duplicate reduction:
// Higher threshold pulls two separate identity clusters together into a unified core.
// ============================================================================
export const MergeFusionVisualizer: React.FC<{ value: number }> = ({ value }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof canvas.getContext !== 'function') return;
    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext('2d');
    } catch {
      return;
    }
    if (!ctx) return;

    let animId: number;
    let time = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const accent = getThemeColor('--accent', '#fa7175');
      const text = getThemeColor('--text', '#f5eedf');
      const muted = getThemeColor('--muted', '#b8a896');
      const line = getThemeColor('--line', 'rgba(255,255,255,0.15)');

      const centerY = height / 2;
      const centerX = width / 2;

      // Normalization: 0.30 to 0.60 -> 0.0 to 1.0
      const norm = Math.max(0, Math.min(1, (value - 0.30) / (0.60 - 0.30)));
      // Separation distance between Cluster A and Cluster B
      const maxSeparation = width * 0.32;
      const separation = (1 - norm) * maxSeparation;
      const isFused = value >= 0.48;

      time += 0.025;

      const posA = centerX - separation;
      const posB = centerX + separation;

      // Draw gravitational field rings for Cluster A
      for (let r = 10; r <= 28; r += 9) {
        ctx.beginPath();
        ctx.arc(posA, centerY, r + Math.sin(time * 2 + r) * 1.5, 0, Math.PI * 2);
        ctx.strokeStyle = line;
        ctx.lineWidth = 1;
        ctx.globalAlpha = Math.max(0.1, 0.4 - (r / 35));
        ctx.stroke();
      }

      // Draw gravitational field rings for Cluster B
      for (let r = 10; r <= 28; r += 9) {
        ctx.beginPath();
        ctx.arc(posB, centerY, r + Math.sin(time * 2.5 + r) * 1.5, 0, Math.PI * 2);
        ctx.strokeStyle = line;
        ctx.lineWidth = 1;
        ctx.globalAlpha = Math.max(0.1, 0.4 - (r / 35));
        ctx.stroke();
      }
      ctx.globalAlpha = 1.0;

      if (isFused) {
        // FUSED STATE: Glowing Venn / Metaball Fusion Core
        const glowPulse = Math.sin(time * 4) * 3;

        // Radiant Outer Glow
        const gradient = ctx.createRadialGradient(centerX, centerY, 4, centerX, centerY, 32 + glowPulse);
        gradient.addColorStop(0, accent);
        gradient.addColorStop(0.6, `${accent}44`);
        gradient.addColorStop(1, 'transparent');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(centerX, centerY, 34 + glowPulse, 0, Math.PI * 2);
        ctx.fill();

        // Connecting bridge flux
        ctx.beginPath();
        ctx.moveTo(posA, centerY);
        ctx.lineTo(posB, centerY);
        ctx.strokeStyle = accent;
        ctx.lineWidth = 8 + Math.sin(time * 5) * 2;
        ctx.stroke();

        // Swirling plasma particles between the two centroids
        for (let p = 0; p < 7; p++) {
          const pt = (time * 2 + p * 0.3) % 1;
          const px = posA + (posB - posA) * pt;
          const py = centerY + Math.sin(pt * Math.PI * 2 + time * 3) * 6;
          ctx.beginPath();
          ctx.arc(px, py, 1.8, 0, Math.PI * 2);
          ctx.fillStyle = text;
          ctx.fill();
        }
      } else {
        // SEPARATE STATE: Central dividing boundary line
        ctx.beginPath();
        ctx.moveTo(centerX, 18);
        ctx.lineTo(centerX, height - 18);
        ctx.strokeStyle = line;
        ctx.setLineDash([3, 3]);
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.setLineDash([]);

        // Repulsion arrow indicators
        const arrowOffset = Math.sin(time * 3) * 2;
        ctx.font = '10px "JetBrains Mono", monospace';
        ctx.fillStyle = muted;
        ctx.textAlign = 'center';
        ctx.fillText('◂', posA + 12 - arrowOffset, centerY + 3);
        ctx.fillText('▸', posB - 12 + arrowOffset, centerY + 3);
      }

      // Draw Cluster A Centroid Core
      ctx.beginPath();
      ctx.arc(posA, centerY, 7, 0, Math.PI * 2);
      ctx.fillStyle = accent;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(posA, centerY, 3, 0, Math.PI * 2);
      ctx.fillStyle = text;
      ctx.fill();

      // Draw Cluster B Centroid Core
      ctx.beginPath();
      ctx.arc(posB, centerY, 7, 0, Math.PI * 2);
      ctx.fillStyle = isFused ? accent : '#d97706';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(posB, centerY, 3, 0, Math.PI * 2);
      ctx.fillStyle = text;
      ctx.fill();

      // Cluster Labels
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.fillStyle = text;
      ctx.textAlign = 'center';
      ctx.fillText('CLS A', posA, centerY - 13);
      ctx.fillText('CLS B', posB, centerY - 13);

      // HUD Status
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.textAlign = 'left';
      ctx.fillStyle = isFused ? accent : muted;
      ctx.fillText(isFused ? 'STATUS: FUSED UNIFIED' : 'STATUS: SEPARATE CLUSTERS', 8, 14);
      ctx.textAlign = 'right';
      ctx.fillStyle = muted;
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
        width={280}
        height={85}
        className="w-full h-full block"
      />
    </div>
  );
};

// ============================================================================
// Visualizer 3: Sonar Radar Hologram (maybe_threshold: 0.50 - 0.75)
// Represents suggestion candidate range: higher threshold sweeps wider radar horizon,
// flagging more candidate pairs for organizer review.
// ============================================================================
export const RadarSuggestionVisualizer: React.FC<{ value: number }> = ({ value }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof canvas.getContext !== 'function') return;
    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext('2d');
    } catch {
      return;
    }
    if (!ctx) return;

    let animId: number;
    let sweepAngle = 0;

    // Fixed candidates on the radar plane at normalized distances
    const candidates = [
      { id: 'P1', distVal: 0.52, angle: 0.85, matchPct: 92 },
      { id: 'P2', distVal: 0.58, angle: 2.15, matchPct: 83 },
      { id: 'P3', distVal: 0.63, angle: 3.70, matchPct: 76 },
      { id: 'P4', distVal: 0.67, angle: 4.80, matchPct: 69 },
      { id: 'P5', distVal: 0.71, angle: 1.45, matchPct: 61 },
      { id: 'P6', distVal: 0.74, angle: 5.60, matchPct: 54 },
    ];

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const accent = getThemeColor('--accent', '#fa7175');
      const text = getThemeColor('--text', '#f5eedf');
      const muted = getThemeColor('--muted', '#b8a896');
      const line = getThemeColor('--line', 'rgba(255,255,255,0.15)');

      const centerX = width / 2;
      const centerY = height / 2;
      const maxRadarRadius = Math.min(width, height) * 0.42;

      sweepAngle = (sweepAngle + 0.035) % (Math.PI * 2);

      // Normalization: 0.50 to 0.75 -> 0.0 to 1.0
      const norm = Math.max(0, Math.min(1, (value - 0.50) / (0.75 - 0.50)));
      const activeSweepRadius = maxRadarRadius * (0.35 + norm * 0.65);

      // Radar concentric rings
      [0.35, 0.65, 1.0].forEach((ratio, idx) => {
        ctx.beginPath();
        ctx.arc(centerX, centerY, maxRadarRadius * ratio, 0, Math.PI * 2);
        ctx.strokeStyle = line;
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
      ctx.strokeStyle = line;
      ctx.lineWidth = 0.8;
      ctx.globalAlpha = 0.4;
      ctx.stroke();
      ctx.globalAlpha = 1.0;

      // Active Detection Horizon Circle (Scales with Slider)
      ctx.beginPath();
      ctx.arc(centerX, centerY, activeSweepRadius, 0, Math.PI * 2);
      ctx.strokeStyle = accent;
      ctx.lineWidth = 1.5;
      ctx.globalAlpha = 0.6;
      ctx.stroke();
      ctx.fillStyle = accent;
      ctx.globalAlpha = 0.06;
      ctx.fill();
      ctx.globalAlpha = 1.0;

      // Radar Sweep Fan Beam
      const sweepSegments = 16;
      for (let i = 0; i < sweepSegments; i++) {
        const segAngle = sweepAngle - (i * 0.03);
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, activeSweepRadius, segAngle - 0.03, segAngle);
        ctx.closePath();
        ctx.fillStyle = accent;
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
      ctx.strokeStyle = text;
      ctx.lineWidth = 1.5;
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
          // Angle difference with sweep line for ping flash
          let diff = (sweepAngle - cand.angle) % (Math.PI * 2);
          if (diff < 0) diff += Math.PI * 2;
          const isPinged = diff < 0.6;

          // Target reticle
          ctx.beginPath();
          ctx.arc(cx, cy, isPinged ? 5.5 : 3.5, 0, Math.PI * 2);
          ctx.fillStyle = isPinged ? text : accent;
          ctx.fill();

          if (isPinged) {
            ctx.beginPath();
            ctx.arc(cx, cy, 9, 0, Math.PI * 2);
            ctx.strokeStyle = accent;
            ctx.lineWidth = 1;
            ctx.stroke();

            // Match percentage callout
            ctx.font = '8px "JetBrains Mono", monospace';
            ctx.fillStyle = text;
            ctx.fillText(`${cand.matchPct}%`, cx + 7, cy - 2);
          }
        } else {
          // Out of range (inactive target)
          ctx.beginPath();
          ctx.arc(cx, cy, 2, 0, Math.PI * 2);
          ctx.fillStyle = line;
          ctx.globalAlpha = 0.4;
          ctx.fill();
          ctx.globalAlpha = 1.0;
        }
      });

      // HUD
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.fillStyle = muted;
      ctx.textAlign = 'left';
      ctx.fillText(`SWEEP CAP: ${value.toFixed(2)}`, 8, 14);
      ctx.textAlign = 'right';
      ctx.fillStyle = accent;
      ctx.fillText(`MATCHES: ${detectedCount} PAIRS`, width - 8, 14);

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
        width={280}
        height={85}
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
    if (!canvas || typeof canvas.getContext !== 'function') return;
    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas.getContext('2d');
    } catch {
      return;
    }
    if (!ctx) return;

    let animId: number;
    let time = 0;

    const render = () => {
      const width = canvas.width;
      const height = canvas.height;
      ctx.clearRect(0, 0, width, height);

      const accent = getThemeColor('--accent', '#fa7175');
      const text = getThemeColor('--text', '#f5eedf');
      const muted = getThemeColor('--muted', '#b8a896');
      const line = getThemeColor('--line', 'rgba(255,255,255,0.15)');

      time += 0.03;

      const centerX = width / 2;
      const centerY = height / 2;

      // Normalization: 0.20 (Strict Guard) to 0.50 (Relaxed Guard)
      const norm = Math.max(0, Math.min(1, (value - 0.20) / (0.50 - 0.20)));
      const isStrict = value <= 0.40;
      const shieldOpacity = 1 - norm * 0.65;

      // Outer Photo Frame
      ctx.strokeStyle = line;
      ctx.lineWidth = 1;
      ctx.strokeRect(18, 12, width - 36, height - 24);

      // Photo Frame Corner Brackets
      const bLen = 6;
      ctx.strokeStyle = accent;
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
      const faceLeftX = 48;
      ctx.fillStyle = 'rgba(255,255,255,0.05)';
      ctx.fillRect(faceLeftX - 16, centerY - 20, 32, 40);
      ctx.strokeStyle = line;
      ctx.lineWidth = 1;
      ctx.strokeRect(faceLeftX - 16, centerY - 20, 32, 40);

      // Face silhouette icon left
      ctx.beginPath();
      ctx.arc(faceLeftX, centerY - 5, 6, 0, Math.PI * 2);
      ctx.fillStyle = text;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(faceLeftX, centerY + 11, 9, Math.PI, 0);
      ctx.fill();

      // Face #2 (Right Avatar Frame)
      const faceRightX = width - 48;
      ctx.fillStyle = 'rgba(255,255,255,0.05)';
      ctx.fillRect(faceRightX - 16, centerY - 20, 32, 40);
      ctx.strokeStyle = line;
      ctx.lineWidth = 1;
      ctx.strokeRect(faceRightX - 16, centerY - 20, 32, 40);

      // Face silhouette icon right
      ctx.beginPath();
      ctx.arc(faceRightX, centerY - 5, 6, 0, Math.PI * 2);
      ctx.fillStyle = text;
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
        ctx.strokeStyle = accent;
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
          ctx.fillStyle = accent;
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
            ctx.strokeStyle = text;
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
        ctx.lineWidth = 1.5;
        ctx.globalAlpha = 0.6;
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
      ctx.font = '8px "JetBrains Mono", monospace';
      ctx.fillStyle = muted;
      ctx.textAlign = 'center';
      ctx.fillText('FACE A', faceLeftX, centerY + 28);
      ctx.fillText('FACE B', faceRightX, centerY + 28);

      // HUD Status
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.textAlign = 'left';
      ctx.fillStyle = isStrict ? accent : '#f59e0b';
      ctx.fillText(isStrict ? 'SHIELD: LOCKED (SAFE)' : 'SHIELD: PERMEABLE', 8, 14);
      ctx.textAlign = 'right';
      ctx.fillStyle = muted;
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
        width={280}
        height={85}
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
    <div className="flex items-center gap-4 p-2 rounded bg-[var(--input)] border border-[var(--panel-border)]">
      {/* Thumbnail scale box */}
      <div className="flex items-center gap-2">
        <div
          className="border-2 border-[var(--accent)] bg-[var(--face-box-bg)] flex items-center justify-center relative transition-all duration-200"
          style={{
            width: `${Math.round(thumbSize / 10)}px`,
            height: `${Math.round(thumbSize / 10)}px`,
            maxWidth: '56px',
            maxHeight: '56px',
          }}
          title={`Thumbnail: ${thumbSize}x${thumbSize}px`}
        >
          <span className="text-[9px] font-mono font-bold text-[var(--accent)]">
            {thumbSize}
          </span>
        </div>
        <div className="text-[11px] leading-tight">
          <span className="block font-semibold text-[var(--text)]">Thumbnail</span>
          <span className="text-[var(--muted)] font-mono">{thumbSize}x{thumbSize}px</span>
        </div>
      </div>

      <div className="h-8 w-px bg-[var(--line)]" />

      {/* Face crop scale box */}
      <div className="flex items-center gap-2">
        <div
          className="border border-[var(--line)] bg-[var(--input)] rounded-full flex items-center justify-center relative transition-all duration-200"
          style={{
            width: `${Math.round(faceCropSize / 8)}px`,
            height: `${Math.round(faceCropSize / 8)}px`,
            maxWidth: '44px',
            maxHeight: '44px',
          }}
          title={`Face Crop: ${faceCropSize}x${faceCropSize}px`}
        >
          <span className="text-[9px] font-mono text-[var(--text)]">
            {faceCropSize}
          </span>
        </div>
        <div className="text-[11px] leading-tight">
          <span className="block font-semibold text-[var(--text)]">Face Crop</span>
          <span className="text-[var(--muted)] font-mono">{faceCropSize}x{faceCropSize}px</span>
        </div>
      </div>
    </div>
  );
};
