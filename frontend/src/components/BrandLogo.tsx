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
      title="CatLog — Who was at the event?"
      data-testid="brand-logo"
      style={{ textDecoration: 'none' }}
    >
      {/* CatLog Camera Cat Mascot Icon */}
      <div
        className="relative flex items-center justify-center flex-shrink-0 transition-transform duration-300 ease-out group-hover:scale-110"
        style={{ width: `${iconSize}px`, height: `${iconSize}px` }}
      >
        <img
          src="/catlog-icon.png"
          alt="CatLog"
          className="w-full h-full object-contain filter drop-shadow-sm"
          onError={(e) => {
            // Fallback to geometric camera mark if image fails
            (e.target as HTMLElement).style.display = 'none';
          }}
        />
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
            CatLog
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
            CatLog
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
            <span>WHO WAS AT THE EVENT?</span>
          </div>
        )}
      </div>
    </div>
  );
};
