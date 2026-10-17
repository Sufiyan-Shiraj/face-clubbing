import React from 'react';
import { RisoTheme } from './Header';

export interface BrandLogoProps {
  theme?: RisoTheme;
  onClick?: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  theme = 't-dark',
  onClick,
  className = '',
  size = 'md',
  showSubtitle = true,
}) => {
  const iconSize = size === 'sm' ? 28 : size === 'lg' ? 44 : 36;
  const titleSize = size === 'sm' ? '18px' : size === 'lg' ? '24px' : '20px';

  return (
    <div
      className={`brand-logo-container flex items-center gap-3 cursor-pointer select-none group transition-all duration-200 ${className}`}
      onClick={onClick}
      title="PhotoSorter - Event Organizer"
      data-testid="brand-logo"
      style={{ textDecoration: 'none' }}
    >
      {/* Dynamic Vector Risograph Logo Mark */}
      <div
        className="relative flex items-center justify-center flex-shrink-0 transition-transform duration-300 ease-out group-hover:scale-105"
        style={{ width: `${iconSize}px`, height: `${iconSize}px` }}
      >
        <svg
          viewBox="0 0 44 44"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full overflow-visible"
        >
          {/* Card 1: Back rotated card (Riso ink shadow) */}
          <rect
            x="4"
            y="4"
            width="30"
            height="30"
            rx="5"
            transform="rotate(-9 19 19)"
            className="transition-transform duration-300 group-hover:rotate-[-14deg]"
            style={{
              transformOrigin: '19px 19px',
              fill: 'var(--panel)',
              stroke: 'var(--accent)',
              strokeWidth: '1.75',
              strokeOpacity: 0.65,
            }}
          />

          {/* Card 2: Mid card (Misregistration layer) */}
          <rect
            x="7"
            y="7"
            width="30"
            height="30"
            rx="5"
            transform="rotate(7 22 22)"
            className="transition-transform duration-300 group-hover:rotate-[11deg]"
            style={{
              transformOrigin: '22px 22px',
              fill: 'var(--input)',
              stroke: 'var(--line)',
              strokeWidth: '1.75',
            }}
          />

          {/* Card 3: Front primary photo frame */}
          <rect
            x="6"
            y="6"
            width="32"
            height="32"
            rx="5"
            style={{
              fill: 'var(--panel)',
              stroke: 'var(--text)',
              strokeWidth: '2',
            }}
          />

          {/* Camera Aperture Blades radiating in circle */}
          <g
            className="transition-transform duration-500 ease-out group-hover:rotate-45"
            style={{ transformOrigin: '22px 22px' }}
          >
            {/* Aperture iris lines */}
            <path
              d="M14 15 L22 10 M30 15 L34 22 M30 29 L22 34 M14 29 L10 22 M22 10 L30 15 M22 34 L14 29"
              style={{
                stroke: 'var(--line)',
                strokeWidth: '1.2',
                strokeLinecap: 'round',
              }}
            />

            {/* Aperture inner circle */}
            <circle
              cx="22"
              cy="22"
              r="9.5"
              style={{
                fill: 'var(--bg)',
                stroke: 'var(--accent)',
                strokeWidth: '2',
              }}
            />
          </g>

          {/* Friendly face silhouette in center of aperture */}
          {/* Eyes: Happy arched curves */}
          <path
            d="M17.5 19.5 C18 18 19.5 18 20 19.5"
            style={{
              stroke: 'var(--text)',
              strokeWidth: '1.75',
              strokeLinecap: 'round',
              fill: 'none',
            }}
          />
          <path
            d="M24 19.5 C24.5 18 26 18 26.5 19.5"
            style={{
              stroke: 'var(--text)',
              strokeWidth: '1.75',
              strokeLinecap: 'round',
              fill: 'none',
            }}
          />

          {/* Smile: Warm Riso smile curve */}
          <path
            d="M18 23.5 C19.2 26.5 24.8 26.5 26 23.5"
            className="transition-transform duration-200 group-hover:translate-y-[-0.5px]"
            style={{
              stroke: 'var(--accent-ink)',
              strokeWidth: '2',
              strokeLinecap: 'round',
              fill: 'none',
            }}
          />

          {/* Top-right corner photo card registration dot */}
          <circle
            cx="33"
            cy="11"
            r="1.5"
            style={{ fill: 'var(--accent)' }}
          />
        </svg>
      </div>

      {/* Typography: Risograph Misregistration Brand Wordmark */}
      <div className="flex flex-col justify-center leading-none">
        <div className="relative flex items-center">
          {/* Riso offset drop shadow text */}
          <span
            aria-hidden="true"
            className="absolute left-[1.5px] top-[1.5px] font-black tracking-tight select-none pointer-events-none"
            style={{
              fontSize: titleSize,
              fontFamily: "'Archivo Black', 'Inter', sans-serif",
              color: 'var(--accent)',
              opacity: 0.85,
            }}
          >
            PhotoSorter
          </span>

          {/* Primary Crisp Brand Typography */}
          <span
            className="relative font-black tracking-tight transition-colors duration-150"
            style={{
              fontSize: titleSize,
              fontFamily: "'Archivo Black', 'Inter', sans-serif",
              color: 'var(--text)',
              letterSpacing: '-0.02em',
            }}
          >
            PhotoSorter
          </span>
        </div>

        {showSubtitle && (
          <div
            className="flex items-center gap-1.5 mt-0.5 tracking-wider font-mono font-bold uppercase"
            style={{
              fontSize: '9px',
              color: 'var(--accent-ink)',
              letterSpacing: '0.14em',
            }}
          >
            <span>EVENT ORGANIZER</span>
          </div>
        )}
      </div>
    </div>
  );
};
